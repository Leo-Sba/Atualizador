"""
Motor de Cálculo dos Indicadores Fundamentalistas Históricos Diários.
Calcula e popula daily_metrics e company_daily_metrics no Supabase:
 - Lucro TTM (Últimos 12 meses, respeitando receipt_date)
 - Patrimônio Líquido mais recente:
     * Identifica automaticamente a conta oficial de Patrimônio Líquido Consolidado (2.03, 2.07 ou 2.08)
 - Preço/Lucro (P/L) da Empresa e P/L por Ação
 - Preço/Valor Patrimonial (P/VP)
 - Retorno sobre Patrimônio Líquido (ROE TTM)
"""

import os
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        connect_timeout=20
    )

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
                r.period_start,
                r.period_end,
                r.receipt_date,
                f.account_code,
                f.account_description,
                f.account_value
            FROM financial_facts f
            JOIN financial_reports r ON r.id = f.report_id
            WHERE r.company_id = %s
              AND (
                  f.account_code IN ('3.11', '3.09')
                  OR (f.account_code IN ('2.03', '2.07', '2.08') AND f.account_description ILIKE '%%Patrimônio Líquido%%')
              )
            ORDER BY r.receipt_date ASC, r.period_end ASC;
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
            SELECT id, ticker, share_type
            FROM securities
            WHERE company_id = %s;
        """, (comp_id,))
        securities = cur.fetchall()
        sec_dict = {s[0]: (s[1], s[2]) for s in securities}

        cur.execute("""
            SELECT p.security_id, p.price_date, p.close_price
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

            equity_facts = [
                f for f in known_facts 
                if 'patrimônio líquido' in f[6].lower()
            ]
            latest_equity = float(equity_facts[-1][7]) if equity_facts else None

            profit_facts = [
                f for f in known_facts 
                if f[5] in ('3.11', '3.09') and ('líquido' in f[6].lower() or 'lucro/prejuízo' in f[6].lower() or 'lucro consolidado' in f[6].lower())
            ]
            if not profit_facts:
                profit_facts = [f for f in known_facts if f[5] in ('3.11', '3.09')]

            if not profit_facts:
                continue

            latest_profit_fact = max(profit_facts, key=lambda x: x[3])
            fin_as_of = latest_profit_fact[3]

            dfp_profits = [f for f in profit_facts if f[0] == 'DFP']
            latest_dfp = dfp_profits[-1] if dfp_profits else None
            net_income_ttm = float(latest_dfp[7]) if latest_dfp else float(latest_profit_fact[7])

            known_shares = [
                s for s in shares_history 
                if s[1] and s[1] <= ref_date
            ]
            if known_shares:
                latest_shares = known_shares[-1]
                total_shares = float(latest_shares[4])
                common_shares = float(latest_shares[2])
                preferred_shares = float(latest_shares[3])
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

            lpa_ttm = (net_income_ttm / total_shares) if (net_income_ttm and total_shares and total_shares > 0) else None
            vpa = (latest_equity / total_shares) if (latest_equity and total_shares and total_shares > 0) else None

            for sec_id, close_p in day_prices.items():
                stype = sec_dict[sec_id][1]
                sec_shares = common_shares if stype == 'ON' else (preferred_shares if stype == 'PN' else total_shares)
                sec_market_cap = (close_p * sec_shares) if sec_shares else None

                stock_pe = (close_p / lpa_ttm) if (lpa_ttm and lpa_ttm > 0) else None
                stock_pvp = (close_p / vpa) if (vpa and vpa > 0) else None

                daily_metrics_to_insert.append((
                    sec_id,
                    ref_date,
                    fin_as_of,
                    close_p,
                    net_income_ttm,
                    lpa_ttm,
                    stock_pe,
                    vpa,
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
