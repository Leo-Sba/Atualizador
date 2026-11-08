"""
Motor de Cálculo dos Indicadores Fundamentalistas Históricos Diários.
Calcula e popula daily_metrics e company_daily_metrics no Supabase:
 - Lucro TTM (Últimos 12 meses, respeitando receipt_date)
 - Patrimônio Líquido mais recente:
     * Identifica automaticamente a conta oficial de Patrimônio Líquido Consolidado (2.03, 2.07 ou 2.08)
 - Preço/Lucro (P/L) da Empresa e P/L por Ação (usando close_split_adjusted e ações ajustadas pós-split)
 - Preço/Valor Patrimonial (P/VP)
 - Retorno sobre Patrimônio Líquido (ROE TTM)
"""

import os
import datetime
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

load_dotenv()

# Proporção oficial de ações agrupadas em cada Unit (UNT) negociada na B3:
UNIT_SHARES_RATIO = {
    'BPAC11': 3.0,  # 1 ON + 2 PN
    'KLBN11': 5.0,  # 1 ON + 4 PN
    'SANB11': 2.0,  # 1 ON + 1 PN
    'TAEE11': 3.0,  # 1 ON + 2 PN
    'ALUP11': 3.0,  # 1 ON + 2 PN
    'ENGI11': 5.0,  # 1 ON + 4 PN
    'SAPR11': 5.0,  # 1 ON + 4 PN
    'IGTI11': 3.0   # 1 ON + 2 PN
}

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        connect_timeout=20
    )

def get_split_multiplier_for_shares(sh_ref_date, raw_total_shares, shares_history, comp_actions):
    """
    Converte a quantidade histórica de ações da CVM (em sh_ref_date) para a mesma base
    acionária pós-split de close_split_adjusted, evitando quedas artificiais de P/L e P/VP
    após desdobramentos ou grupamentos.
    """
    if not comp_actions or not raw_total_shares or raw_total_shares <= 0 or not sh_ref_date:
        return 1.0
    mult_factor = 1.0
    for eff_date, mult in comp_actions:
        if sh_ref_date < eff_date:
            post_records = [
                float(s[4]) for s in shares_history
                if s[0] and s[0] >= eff_date and s[4] and float(s[4]) > 0
            ]
            if post_records:
                first_post = post_records[0]
                if abs(mult - 1.0) > 0.15 and abs(raw_total_shares - first_post) / first_post < 0.15:
                    continue
            mult_factor *= mult
    return mult_factor

def calculate_metrics():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, legal_name, trading_name, sector FROM companies ORDER BY trading_name;")
    companies = cur.fetchall()

    for comp_id, legal_name, trading_name, sector in companies:
        cur.execute("""
            SELECT 
                r.source_type,
                r.fiscal_year,
                f.period_start,
                f.period_end,
                r.receipt_date,
                f.account_code,
                f.account_description,
                f.account_value,
                r.is_consolidated
            FROM financial_facts f
            JOIN financial_reports r ON r.id = f.report_id
            WHERE r.company_id = %s
              AND (
                  f.account_code IN ('3.11', '3.09')
                  OR (f.account_code IN ('2.03', '2.07', '2.08') AND f.account_description ILIKE '%%Patrimônio Líquido%%')
              )
            ORDER BY r.receipt_date ASC, f.period_end ASC;
        """, (comp_id,))
        facts = cur.fetchall()

        if not facts:
            continue

        cur.execute("""
            SELECT reference_date, known_date, common_shares, preferred_shares, total_shares
            FROM company_share_capital
            WHERE company_id = %s
            ORDER BY known_date ASC;
        """, (comp_id,))
        shares_history = cur.fetchall()

        cur.execute("""
            SELECT effective_date, MAX(share_multiplier)
            FROM corporate_actions
            WHERE company_id = %s
            GROUP BY effective_date
            ORDER BY effective_date ASC;
        """, (comp_id,))
        comp_actions = [(r[0], float(r[1])) for r in cur.fetchall() if r[0] and r[1]]

        cur.execute("""
            SELECT id, ticker, share_type
            FROM securities
            WHERE company_id = %s;
        """, (comp_id,))
        securities = cur.fetchall()
        sec_dict = {s[0]: (s[1], s[2]) for s in securities}

        cur.execute("""
            SELECT p.security_id, p.price_date, COALESCE(p.close_split_adjusted, p.close_price)
            FROM daily_prices p
            JOIN securities s ON s.id = p.security_id
            WHERE s.company_id = %s
            ORDER BY p.price_date ASC;
        """, (comp_id,))
        prices = cur.fetchall()

        if not prices:
            continue

        prices_by_date = {}
        for sec_id, p_date, close_p in prices:
            if p_date not in prices_by_date:
                prices_by_date[p_date] = {}
            prices_by_date[p_date][sec_id] = float(close_p)

        company_metrics_to_insert = []
        daily_metrics_to_insert = []

        sorted_dates = sorted(prices_by_date.keys())

        for ref_date in sorted_dates:
            known_facts = [
                f for f in facts 
                if f[4] and f[4].date() <= ref_date
            ]

            if not known_facts:
                continue

            # Priorizar demonstrativos consolidados se disponíveis
            has_cons = any(f[8] is True for f in known_facts)
            if has_cons:
                known_facts = [f for f in known_facts if f[8] is True]

            equity_facts = [
                f for f in known_facts 
                if 'patrim' in f[6].lower() and 'quido' in f[6].lower()
            ]
            latest_equity = float(equity_facts[-1][7]) if equity_facts else None

            profit_facts = [
                f for f in known_facts 
                if f[5] in ('3.11', '3.09') and any(t in f[6].lower() for t in ['quido', 'preju', 'consolidado'])
            ]
            if not profit_facts:
                profit_facts = [f for f in known_facts if f[5] in ('3.11', '3.09')]

            if not profit_facts:
                continue

            latest_profit_fact = max(profit_facts, key=lambda x: x[3])
            fin_as_of = latest_profit_fact[3]

            # Cálculo robusto do Lucro TTM (Trailing Twelve Months):
            # Prioridade 1: Soma dos últimos 4 trimestres consecutivos disponíveis
            quarters = {}
            cumulatives = {}
            dfps = {}

            for f in profit_facts:
                if not f[2] or not f[3]:
                    continue
                delta = (f[3] - f[2]).days
                val = float(f[7])
                if 80 <= delta <= 100:
                    quarters[f[3]] = val
                elif f[0] == 'DFP' and delta > 350:
                    dfps[f[1]] = (f[3], val)
                elif f[0] == 'ITR' and delta > 100:
                    cumulatives[(f[1], f[3])] = val

            # Deriva o 4º trimestre se DFP anual e acumulado de 9M existirem: Q4 = DFP - 9M
            for yr, (dfp_end, dfp_val) in dfps.items():
                if dfp_end not in quarters:
                    m9_end = datetime.date(yr, 9, 30)
                    if (yr, m9_end) in cumulatives:
                        quarters[dfp_end] = dfp_val - cumulatives[(yr, m9_end)]

            sorted_q = sorted(quarters.keys())
            if len(sorted_q) >= 4:
                net_income_ttm = sum(quarters[d] for d in sorted_q[-4:])
            else:
                # Prioridade 2: Última DFP anual entregue
                dfp_profits = [f for f in profit_facts if f[0] == 'DFP']
                latest_dfp = dfp_profits[-1] if dfp_profits else None
                net_income_ttm = float(latest_dfp[7]) if latest_dfp else float(latest_profit_fact[7])

            known_shares = [
                s for s in shares_history 
                if s[1] and s[1] <= ref_date
            ]
            if known_shares:
                latest_shares = known_shares[-1]
                sh_ref_date = latest_shares[0]
                raw_tot = float(latest_shares[4]) if latest_shares[4] is not None else 0.0
                raw_on = float(latest_shares[2]) if latest_shares[2] is not None else 0.0
                raw_pn = float(latest_shares[3]) if latest_shares[3] is not None else 0.0
                sh_mult = get_split_multiplier_for_shares(sh_ref_date, raw_tot, shares_history, comp_actions)
                total_shares = raw_tot * sh_mult if raw_tot > 0 else None
                common_shares = raw_on * sh_mult if raw_on > 0 else 0.0
                preferred_shares = raw_pn * sh_mult if raw_pn > 0 else 0.0
            else:
                total_shares = None
                common_shares = None
                preferred_shares = None

            day_prices = prices_by_date[ref_date]
            total_market_cap = 0.0

            for sec_id, close_p in day_prices.items():
                stype = sec_dict[sec_id][1]
                if stype == 'ON' and common_shares and common_shares > 0:
                    total_market_cap += close_p * common_shares
                elif stype == 'PN' and preferred_shares and preferred_shares > 0:
                    total_market_cap += close_p * preferred_shares
                elif total_shares and total_shares > 0:
                    total_market_cap += close_p * (total_shares / len(day_prices))

            if total_market_cap == 0 and total_shares and total_shares > 0:
                avg_p = sum(day_prices.values()) / len(day_prices)
                total_market_cap = avg_p * total_shares

            company_pe = (total_market_cap / net_income_ttm) if (net_income_ttm and net_income_ttm > 0 and total_market_cap > 0) else None
            roe_ttm = (net_income_ttm / latest_equity) if (net_income_ttm and latest_equity and latest_equity > 0) else None

            company_metrics_to_insert.append((
                comp_id,
                ref_date,
                fin_as_of,
                net_income_ttm,
                total_market_cap if total_market_cap > 0 else None,
                company_pe,
                total_shares,
                roe_ttm,
                1
            ))

            base_lpa = (net_income_ttm / total_shares) if (net_income_ttm and total_shares and total_shares > 0) else None
            base_vpa = (latest_equity / total_shares) if (latest_equity and total_shares and total_shares > 0) else None

            for sec_id, close_p in day_prices.items():
                ticker_code, stype = sec_dict[sec_id]
                unit_ratio = UNIT_SHARES_RATIO.get(ticker_code, 1.0)

                # Ajuste de LPA e VPA caso seja Unit (multiplica pela quantidade de ações do pacote)
                sec_lpa = (base_lpa * unit_ratio) if base_lpa else None
                sec_vpa = (base_vpa * unit_ratio) if base_vpa else None

                if stype == 'ON':
                    sec_shares = common_shares
                elif stype == 'PN':
                    sec_shares = preferred_shares
                elif unit_ratio > 1.0 and total_shares:
                    sec_shares = total_shares / unit_ratio
                else:
                    sec_shares = total_shares

                sec_market_cap = (close_p * sec_shares) if sec_shares else None
                stock_pe = (close_p / sec_lpa) if (sec_lpa and sec_lpa > 0) else None
                stock_pvp = (close_p / sec_vpa) if (sec_vpa and sec_vpa > 0) else None

                daily_metrics_to_insert.append((
                    sec_id,
                    ref_date,
                    fin_as_of,
                    close_p,
                    net_income_ttm,
                    sec_lpa,
                    stock_pe,
                    sec_vpa,
                    stock_pvp,
                    roe_ttm,
                    sec_shares,
                    sec_market_cap,
                    1
                ))

        if company_metrics_to_insert:
            sql_comp = """
                INSERT INTO company_daily_metrics (
                    company_id, reference_date, financial_data_as_of, net_income_ttm,
                    total_market_cap, company_price_earnings, total_shares_outstanding,
                    roe_ttm, calculation_version
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (company_id, reference_date, calculation_version)
                DO UPDATE SET
                    net_income_ttm = EXCLUDED.net_income_ttm,
                    total_market_cap = EXCLUDED.total_market_cap,
                    company_price_earnings = EXCLUDED.company_price_earnings,
                    total_shares_outstanding = EXCLUDED.total_shares_outstanding,
                    roe_ttm = EXCLUDED.roe_ttm,
                    calculated_at = NOW();
            """
            execute_batch(cur, sql_comp, company_metrics_to_insert, page_size=500)
            conn.commit()

        if daily_metrics_to_insert:
            sql_daily = """
                INSERT INTO daily_metrics (
                    security_id, reference_date, financial_data_as_of, close_price,
                    net_income_ttm, earnings_per_share_ttm, price_earnings,
                    book_value_per_share, price_to_book, roe_ttm,
                    shares_outstanding, market_cap, calculation_version
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (security_id, reference_date, calculation_version)
                DO UPDATE SET
                    close_price = EXCLUDED.close_price,
                    net_income_ttm = EXCLUDED.net_income_ttm,
                    earnings_per_share_ttm = EXCLUDED.earnings_per_share_ttm,
                    price_earnings = EXCLUDED.price_earnings,
                    book_value_per_share = EXCLUDED.book_value_per_share,
                    price_to_book = EXCLUDED.price_to_book,
                    roe_ttm = EXCLUDED.roe_ttm,
                    shares_outstanding = EXCLUDED.shares_outstanding,
                    market_cap = EXCLUDED.market_cap,
                    calculated_at = NOW();
            """
            execute_batch(cur, sql_daily, daily_metrics_to_insert, page_size=1000)
            conn.commit()
            print(f"  [OK] {trading_name}: métricas salvas.")

    cur.close()
    conn.close()
    print("\nCálculo de métricas finalizado com sucesso!")

if __name__ == "__main__":
    calculate_metrics()
