"""
clean_duplicates.py
Rotina para consolidar e limpar registros duplicados na tabela 'securities'
e suas tabelas filhas (daily_prices, daily_metrics, shareholder_distributions,
corporate_actions, ibov_memberships, security_share_history, price_adjustments).

Pode ser executado individualmente ou como rotina semanal agendada (aos sabados).
"""

import sys
import logging
import psycopg2
from calculate_metrics import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def clean_duplicate_securities():
    logging.info("Iniciando varredura de securities duplicadas...")
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Identificar tickers com mais de 1 registro em securities
    cur.execute("""
        SELECT ticker, count(*) 
        FROM securities 
        GROUP BY ticker 
        HAVING count(*) > 1;
    """)
    dup_rows = cur.fetchall()

    if not dup_rows:
        logging.info("[OK] Nenhuma duplicidade encontrada na tabela 'securities'. Tudo limpo!")
        conn.close()
        return 0

    logging.info(f"Encontrados {len(dup_rows)} tickers duplicados: {[r[0] for r in dup_rows]}")

    deleted_count = 0

    for ticker, _ in dup_rows:
        # Selecionar todos os securities com esse ticker
        cur.execute("""
            SELECT s.id,
                   (SELECT count(*) FROM daily_prices WHERE security_id = s.id AND price_source = 'B3_COTAHIST') as b3_count,
                   (SELECT count(*) FROM daily_prices WHERE security_id = s.id) as dp_total,
                   (SELECT count(*) FROM daily_metrics WHERE security_id = s.id) as dm_total
            FROM securities s
            WHERE s.ticker = %s;
        """, (ticker,))
        candidates = cur.fetchall()

        # O registro principal (Primary) sera aquele com mais cotacoes oficiais B3 e mais registros
        candidates.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
        primary_id = candidates[0][0]
        duplicates = [c[0] for c in candidates[1:]]

        logging.info(f"[{ticker}] Manter Primary ID={primary_id} | Remover Duplicatas={duplicates}")

        for dup_id in duplicates:
            # Copiar precos que possam existir na duplicata e nao existam no primary
            cur.execute("""
                INSERT INTO daily_prices (
                    security_id, price_date, close_price, close_split_adjusted, volume, price_source
                )
                SELECT %s, price_date, close_price, close_split_adjusted, volume, price_source
                FROM daily_prices
                WHERE security_id = %s
                  AND price_date NOT IN (SELECT price_date FROM daily_prices WHERE security_id = %s)
                ON CONFLICT DO NOTHING;
            """, (primary_id, dup_id, primary_id))

            # Excluir registros dependentes do dup_id
            cur.execute("DELETE FROM daily_metrics WHERE security_id = %s;", (dup_id,))
            cur.execute("DELETE FROM daily_prices WHERE security_id = %s;", (dup_id,))
            cur.execute("DELETE FROM shareholder_distributions WHERE security_id = %s;", (dup_id,))
            cur.execute("DELETE FROM corporate_actions WHERE security_id = %s;", (dup_id,))
            cur.execute("DELETE FROM ibov_memberships WHERE security_id = %s;", (dup_id,))
            cur.execute("DELETE FROM security_share_history WHERE security_id = %s;", (dup_id,))
            cur.execute("DELETE FROM price_adjustments WHERE security_id = %s;", (dup_id,))

            # Excluir a security duplicada
            cur.execute("DELETE FROM securities WHERE id = %s;", (dup_id,))
            deleted_count += 1

        conn.commit()

    logging.info(f"[SUCESSO] Limpeza concluida! {deleted_count} securities duplicadas removidas com sucesso.")

    # Tentar criar indice/constraint UNIQUE se possivel
    try:
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_securities_ticker'
                ) THEN
                    ALTER TABLE securities ADD CONSTRAINT uq_securities_ticker UNIQUE (ticker);
                END IF;
            END $$;
        """)
        conn.commit()
        logging.info("[OK] Restricao UNIQUE(ticker) ativa em 'securities'.")
    except Exception as e:
        conn.rollback()
        logging.warning(f"Nao foi possivel aplicar UNIQUE constraint: {e}")

    conn.close()
    return deleted_count

if __name__ == "__main__":
    clean_duplicate_securities()
