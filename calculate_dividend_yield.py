"""
Calculador de Dividend Yield Histórico dos últimos 2 anos.
Popula a coluna dividend_yield_ttm na tabela daily_metrics para todos os pregões:
 - Para cada pregão dos últimos 2 anos (a partir de 2024-01-01):
     * Soma todos os proventos (dividendos + JCP) pagos nos 365 dias anteriores à data
     * Dividend Yield (%) = (Soma Proventos / Preço de Fechamento do dia) * 100
"""

import os
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
from datetime import timedelta

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

def calculate_dividend_yield(start_date="2024-01-01"):
    conn = get_db_connection()
    cur = conn.cursor()

    print(f"Calculando histórico diário de Dividend Yield a partir de {start_date} (últimos 2 anos)...")

    # 1. Carregar todas as ações
    cur.execute("SELECT id, ticker FROM securities ORDER BY ticker;")
    securities = cur.fetchall()

    total_updated = 0

    for sec_id, ticker in securities:
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

        # Carregar preços da ação dos últimos 2 anos
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
            sum_divs_12m = sum(float(d[1]) for d in divs if one_year_prior <= d[0] <= ref_date)

            dy_pct = (sum_divs_12m / float(close_price)) * 100.0 if sum_divs_12m > 0 else 0.0

            updates.append((dy_pct, sec_id, ref_date))

        if updates:
            sql_upd = """
                UPDATE daily_metrics
                SET dividend_yield_ttm = %s
                WHERE security_id = %s AND reference_date = %s;
            """
            execute_batch(cur, sql_upd, updates, page_size=1000)
            conn.commit()
            total_updated += len(updates)
            print(f"  [OK] {ticker}: {len(updates)} pregões atualizados com Dividend Yield.")

    cur.close()
    conn.close()
    print(f"\nFinalizado! Total de registros atualizados com Dividend Yield: {total_updated:,}")

if __name__ == "__main__":
    calculate_dividend_yield("2024-01-01")
