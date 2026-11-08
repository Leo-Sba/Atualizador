"""
adjust_splits.py
Mecanismo inteligente e incremental de ajuste retroativo de desdobramentos (splits) e grupamentos (reverse splits).

Funcionamento:
1. Consulta a tabela de controle 'split_adjustment_log' contra a tabela 'corporate_actions'.
2. Identifica se houve NOVOS splits/inplits pendentes de processamento.
3. Se houver novos eventos, processa SOMENTE os ativos impactados:
   - Calcula os fatores retroativos de ajuste para cada pregão histórico em 'daily_prices'.
   - Atualiza 'close_split_adjusted' daquele ativo específico.
   - Recalcula as métricas diárias ('daily_metrics' e 'company_daily_metrics') para a empresa afetada.
   - Registra o evento na tabela de controle 'split_adjustment_log'.
4. Suporta execução por ativo:
   python adjust_splits.py --ticker BPAC11
   ou forçado para todos os ativos com ações corporativas:
   python adjust_splits.py --all
"""

import os
import sys
import bisect
import logging
import argparse
import datetime
from collections import defaultdict
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

load_dotenv()

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
        connect_timeout=25
    )

def ensure_control_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS split_adjustment_log (
                id SERIAL PRIMARY KEY,
                security_id UUID NOT NULL,
                ticker TEXT NOT NULL,
                action_id UUID REFERENCES corporate_actions(id) ON DELETE CASCADE,
                effective_date DATE NOT NULL,
                share_multiplier NUMERIC NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                status TEXT DEFAULT 'APPLIED',
                CONSTRAINT uq_split_log_action UNIQUE(action_id)
            );
        """)
        conn.commit()

def get_pending_actions(conn, ticker=None, force_all=False):
    with conn.cursor() as cur:
        if force_all:
            query = """
                SELECT 
                    ca.id,
                    ca.security_id,
                    s.ticker,
                    s.company_id,
                    ca.effective_date,
                    ca.share_multiplier
                FROM corporate_actions ca
                JOIN securities s ON s.id = ca.security_id
                ORDER BY s.ticker, ca.effective_date ASC;
            """
            cur.execute(query)
        elif ticker:
            query = """
                SELECT 
                    ca.id,
                    ca.security_id,
                    s.ticker,
                    s.company_id,
                    ca.effective_date,
                    ca.share_multiplier
                FROM corporate_actions ca
                JOIN securities s ON s.id = ca.security_id
                WHERE s.ticker = %s
                ORDER BY ca.effective_date ASC;
            """
            cur.execute(query, (ticker.upper(),))
        else:
            query = """
                SELECT 
                    ca.id,
                    ca.security_id,
                    s.ticker,
                    s.company_id,
                    ca.effective_date,
                    ca.share_multiplier
                FROM corporate_actions ca
                JOIN securities s ON s.id = ca.security_id
                LEFT JOIN split_adjustment_log sal ON sal.action_id = ca.id
                WHERE sal.id IS NULL
                ORDER BY s.ticker, ca.effective_date ASC;
            """
            cur.execute(query)
        return cur.fetchall()

def recalculate_single_company_metrics(conn, comp_id):
    """
    Recalcula daily_metrics e company_daily_metrics estritamente para a empresa afetada
    utilizando o close_split_adjusted atualizado.
    """
    cur = conn.cursor()

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
        return

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
        SELECT p.security_id, p.price_date, COALESCE(p.close_split_adjusted, p.close_price)
        FROM daily_prices p
        JOIN securities s ON s.id = p.security_id
        WHERE s.company_id = %s
        ORDER BY p.price_date ASC;
    """, (comp_id,))
    prices = cur.fetchall()

    if not prices:
        return

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

        for yr, (dfp_end, dfp_val) in dfps.items():
            if dfp_end not in quarters:
                m9_end = datetime.date(yr, 9, 30)
                if (yr, m9_end) in cumulatives:
                    quarters[dfp_end] = dfp_val - cumulatives[(yr, m9_end)]

        sorted_q = sorted(quarters.keys())
        if len(sorted_q) >= 4:
            net_income_ttm = sum(quarters[d] for d in sorted_q[-4:])
        else:
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

        base_lpa = (net_income_ttm / total_shares) if (net_income_ttm and total_shares and total_shares > 0) else None
        base_vpa = (latest_equity / total_shares) if (latest_equity and total_shares and total_shares > 0) else None

        for sec_id, close_p in day_prices.items():
            ticker_code, stype = sec_dict[sec_id]
            unit_ratio = UNIT_SHARES_RATIO.get(ticker_code, 1.0)

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
        execute_batch(cur, sql_comp, company_metrics_to_insert, page_size=1000)

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
    cur.close()

def process_splits(ticker=None, force_all=False):
    conn = get_db_connection()
    ensure_control_table(conn)

    pending_actions = get_pending_actions(conn, ticker=ticker, force_all=force_all)
    if not pending_actions:
        logging.info("Nenhum novo desdobramento/inplit pendente de ajuste no banco de controle.")
        conn.close()
        return

    # Agrupar ações por security_id
    actions_by_sec = defaultdict(list)
    sec_info = {}
    for act_id, sec_id, tkr, comp_id, eff_date, mult in pending_actions:
        actions_by_sec[sec_id].append({
            "id": act_id,
            "effective_date": eff_date,
            "multiplier": float(mult)
        })
        sec_info[sec_id] = (tkr, comp_id)

    logging.info(f"Identificados {len(actions_by_sec)} ativos com eventos societários para ajuste.")

    with conn.cursor() as cur:
        for sec_id, actions in actions_by_sec.items():
            tkr, comp_id = sec_info[sec_id]
            logging.info(f"Processando ajuste de split para {tkr} ({len(actions)} eventos)...")

            # Buscar TODAS as corporate_actions para esse ativo (garantir consistencia sequencial)
            cur.execute("""
                SELECT id, effective_date, share_multiplier
                FROM corporate_actions
                WHERE security_id = %s
                ORDER BY effective_date ASC;
            """, (sec_id,))
            all_sec_actions = cur.fetchall()

            act_dates = [a[1] for a in all_sec_actions]
            mults = [float(a[2]) for a in all_sec_actions]
            k = len(all_sec_actions)

            # Suffix products para ajuste retroativo
            suffix_products = [1.0] * (k + 1)
            for i in range(k - 1, -1, -1):
                suffix_products[i] = suffix_products[i + 1] * mults[i]

            # Buscar precos do ativo
            cur.execute("""
                SELECT price_date, close_price
                FROM daily_prices
                WHERE security_id = %s
                ORDER BY price_date ASC;
            """, (sec_id,))
            prices = cur.fetchall()

            updates = []
            for p_date, c_p in prices:
                idx = bisect.bisect_right(act_dates, p_date)
                cum_mult = suffix_products[idx]
                adj_p = round(float(c_p) / cum_mult, 4)
                updates.append((adj_p, sec_id, p_date))

            # Atualizar daily_prices em lote
            update_sql = """
                UPDATE daily_prices
                SET close_split_adjusted = %s
                WHERE security_id = %s AND price_date = %s;
            """
            execute_batch(cur, update_sql, updates, page_size=1000)
            conn.commit()

            # Recalcular metricas da empresa
            logging.info(f"Recalculando metricas fundamentalistas para {tkr}...")
            recalculate_single_company_metrics(conn, comp_id)

            # Registrar na tabela de controle
            log_entries = []
            for a in all_sec_actions:
                log_entries.append((sec_id, tkr, a[0], a[1], a[2]))

            log_sql = """
                INSERT INTO split_adjustment_log (security_id, ticker, action_id, effective_date, share_multiplier, status)
                VALUES (%s, %s, %s, %s, %s, 'APPLIED')
                ON CONFLICT (action_id) DO UPDATE SET applied_at = NOW();
            """
            execute_batch(cur, log_sql, log_entries, page_size=500)
            conn.commit()
            logging.info(f"[OK] {tkr} ajustado e registrado com sucesso!")

    conn.close()
    logging.info("Processo de ajuste de desdobramentos/grupamentos finalizado!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ajuste de desdobramentos/grupamentos incremental.")
    parser.add_argument("--ticker", type=str, help="Ticker especifico para processar (ex: BPAC11)")
    parser.add_argument("--all", action="store_true", help="Processar todos os ativos com eventos societarios")
    args = parser.parse_args()

    process_splits(ticker=args.ticker, force_all=args.all)
