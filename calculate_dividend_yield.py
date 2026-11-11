"""
Calculador de Dividend Yield Histórico Completo.
Popula a coluna dividend_yield_ttm na tabela daily_metrics para todos os pregões:
 - Para cada pregão histórico:
     * Soma todos os proventos (dividendos + JCP) pagos nos 365 dias anteriores à data
     * Dividend Yield (%) = (Soma Proventos 12M / Preço de Fechamento do dia) * 100
Utiliza algoritmo O(log N) com bisect e execute_values para máxima performance.
"""

import os
import bisect
import logging
from datetime import timedelta
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT") or 5432),
        connect_timeout=25
    )

def calculate_dividend_yield(start_date="2014-01-01"):
    conn = get_db_connection()
    cur = conn.cursor()

    logging.info(f"Calculando histórico diário de Dividend Yield a partir de {start_date}...")

    # 1. Carregar todas as ações
    cur.execute("SELECT id, ticker FROM securities ORDER BY ticker;")
    securities = cur.fetchall()

    total_updated = 0

    for idx, (sec_id, ticker) in enumerate(securities):
        # Carregar proventos da ação
        cur.execute("""
            SELECT ex_date, gross_amount_per_share
            FROM shareholder_distributions
            WHERE security_id = %s
            ORDER BY ex_date ASC;
        """, (sec_id,))
        divs = cur.fetchall()

        if not divs:
            continue

        # Preparar busca binária com prefix sums
        div_dates = [d[0] for d in divs]
        prefix_sums = [0.0]
        for d in divs:
            prefix_sums.append(prefix_sums[-1] + float(d[1] or 0.0))

        # Carregar preços da ação a partir de start_date
        cur.execute("""
            SELECT reference_date, close_price
            FROM daily_metrics
            WHERE security_id = %s AND reference_date >= %s
            ORDER BY reference_date ASC;
        """, (sec_id, start_date))
        metrics = cur.fetchall()

        if not metrics:
            continue

        updates = []
        for ref_date, close_price in metrics:
            if not close_price or close_price <= 0:
                continue

            one_year_prior = ref_date - timedelta(days=365)
            # Soma dos proventos com ex_date entre (ref_date - 365) e ref_date
            idx_left = bisect.bisect_left(div_dates, one_year_prior)
            idx_right = bisect.bisect_right(div_dates, ref_date)
            sum_divs_12m = prefix_sums[idx_right] - prefix_sums[idx_left]

            dy_pct = (sum_divs_12m / float(close_price)) * 100.0 if sum_divs_12m > 0 else 0.0
            updates.append((sec_id, ref_date, dy_pct))

        if updates:
            execute_values(cur, """
                UPDATE daily_metrics AS dm
                SET dividend_yield_ttm = v.dy
                FROM (VALUES %s) AS v(sec_id, ref_date, dy)
                WHERE dm.security_id = v.sec_id::uuid AND dm.reference_date = v.ref_date::date;
            """, updates, page_size=2000)
            conn.commit()
            total_updated += len(updates)
            logging.info(f"[{idx+1}/{len(securities)}] {ticker}: {len(updates)} pregões atualizados com Dividend Yield.")

    cur.close()
    conn.close()
    logging.info(f"[OK] Total de registros atualizados com Dividend Yield: {total_updated:,}")

if __name__ == "__main__":
    calculate_dividend_yield("2014-01-01")
