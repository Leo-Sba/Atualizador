"""
Pipeline de Importação de Proventos (Dividendos e JCP) e Splits.
Popula as tabelas:
 - shareholder_distributions (Dividendos e JCP com data-ex e valor)
 - corporate_actions (Splits e eventos societários)
"""

import os
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT") or 5432),
        connect_timeout=20
    )

def import_distributions_and_splits(start_year=2023):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.id, s.ticker, s.company_id, c.trading_name 
        FROM securities s 
        JOIN companies c ON c.id = s.company_id 
        ORDER BY s.ticker;
    """)
    securities = cur.fetchall()

    total_divs = 0
    total_splits = 0

    for sec_id, ticker, comp_id, comp_name in securities:
        yf_symbol = f"{ticker}.SA"
        print(f"\nBuscando eventos para {ticker} ({yf_symbol})...")

        try:
            stock = yf.Ticker(yf_symbol)
            
            # 1. Dividendos / JCP
            divs = stock.dividends
            if not divs.empty:
                # Filtrar a partir de start_year
                divs_filtered = divs[divs.index >= f"{start_year}-01-01"]
                div_records = []

                for date_idx, amount in divs_filtered.items():
                    ex_date = date_idx.strftime("%Y-%m-%d")
                    gross_val = float(amount)
                    if gross_val <= 0:
                        continue

                    div_records.append((
                        sec_id,
                        'DIVIDEND', # Tipo padrão de distribuição
                        ex_date,
                        gross_val,
                        gross_val,
                        'BRL',
                        'YAHOO_FINANCE'
                    ))

                if div_records:
                    sql_div = """
                        INSERT INTO shareholder_distributions (
                            security_id, distribution_type, ex_date,
                            gross_amount_per_share, net_amount_per_share, currency, source
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (security_id, distribution_type, ex_date, payment_date, gross_amount_per_share)
                        DO NOTHING;
                    """
                    execute_batch(cur, sql_div, div_records, page_size=200)
                    conn.commit()
                    print(f"  [OK] {len(div_records)} proventos importados.")
                    total_divs += len(div_records)

            # 2. Splits / Grupamentos
            splits = stock.splits
            if not splits.empty:
                splits_filtered = splits[splits.index >= f"{start_year}-01-01"]
                split_records = []

                for date_idx, ratio in splits_filtered.items():
                    eff_date = date_idx.strftime("%Y-%m-%d")
                    mult = float(ratio)
                    ev_type = 'SPLIT' if mult > 1.0 else 'REVERSE_SPLIT'

                    split_records.append((
                        comp_id,
                        sec_id,
                        ev_type,
                        eff_date,
                        mult,
                        'BRL',
                        f"Split ratio {mult}:1 via Yahoo",
                        'YAHOO_FINANCE',
                        'CONFIRMED'
                    ))

                if split_records:
                    sql_split = """
                        INSERT INTO corporate_actions (
                            company_id, security_id, event_type, effective_date,
                            share_multiplier, currency, description, source, status
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                    """
                    execute_batch(cur, sql_split, split_records, page_size=100)
                    conn.commit()
                    print(f"  [OK] {len(split_records)} eventos societários (splits) importados.")
                    total_splits += len(split_records)

        except Exception as e:
            conn.rollback()
            print(f"  [ERRO] Falha ao processar {ticker}: {e}")

    cur.close()
    conn.close()
    print(f"\nImportação concluída! Total de Proventos: {total_divs} | Splits: {total_splits}")

if __name__ == "__main__":
    import_distributions_and_splits(2023)
