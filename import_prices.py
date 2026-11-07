"""
Pipeline de Importação de Preços Diários via Yahoo Finance (yfinance).
Grava na tabela daily_prices do Supabase.
"""

import os
import sys
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd
from datetime import datetime

# Carregar variáveis do .env
load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        connect_timeout=15
    )

def fetch_and_save_prices(start_date="2023-01-01"):
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Obter todas as ações cadastradas no banco
    cur.execute("SELECT id, ticker FROM securities ORDER BY ticker;")
    securities = cur.fetchall()
    print(f"Encontradas {len(securities)} ações no banco de dados.")

    total_records = 0

    for sec_id, ticker in securities:
        yf_symbol = f"{ticker}.SA"
        print(f"\nBaixando histórico de {ticker} ({yf_symbol}) desde {start_date}...")

        try:
            stock = yf.Ticker(yf_symbol)
            # auto_adjust=False para preservar o fechamento original não ajustado e podermos ver split / dividendos separados
            hist = stock.history(start=start_date, auto_adjust=False)

            if hist.empty:
                print(f"  [AVISO] Nenhum dado retornado para {yf_symbol}")
                continue

            records = []
            for date_idx, row in hist.iterrows():
                price_date = date_idx.strftime("%Y-%m-%d")
                close_price = float(row["Close"])
                # Se houver Adj Close disponível pelo yfinance
                adj_close = float(row["Adj Close"]) if "Adj Close" in row and pd.notnull(row["Adj Close"]) else close_price
                volume = int(row["Volume"]) if pd.notnull(row["Volume"]) else 0

                records.append((
                    sec_id,
                    price_date,
                    close_price,
                    adj_close,
                    volume,
                    "YAHOO_FINANCE"
                ))

            # Bulk insert com ON CONFLICT (atualiza se já existir)
            insert_query = """
                INSERT INTO daily_prices (
                    security_id, 
                    price_date, 
                    close_price, 
                    close_split_adjusted, 
                    volume, 
                    price_source
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (security_id, price_date) 
                DO UPDATE SET
                    close_price = EXCLUDED.close_price,
                    close_split_adjusted = EXCLUDED.close_split_adjusted,
                    volume = EXCLUDED.volume,
                    imported_at = NOW();
            """

            execute_batch(cur, insert_query, records, page_size=500)
            conn.commit()
            print(f"  [OK] {len(records)} pregões importados para {ticker}.")
            total_records += len(records)

        except Exception as e:
            conn.rollback()
            print(f"  [ERRO] Falha ao processar {ticker}: {e}")

    cur.close()
    conn.close()
    print(f"\nCarga de preços finalizada com sucesso! Total de registros gravados: {total_records}")

if __name__ == "__main__":
    start = sys.argv[1] if len(sys.argv) > 1 else "2023-01-01"
    fetch_and_save_prices(start_date=start)
