"""
clean_duplicates.py
Rotina para consolidar e limpar registros duplicados na tabela 'securities',
além de remover automaticamente ações inativas/deslistadas (> 90 dias sem negociação na B3
ou constantes na lista IGNORED_INACTIVE_TICKERS) do banco de dados e tabelas filhas.

Executado diariamente no Estágio 1.1 da estrutura em cascata (run_updater.py).
"""

import os
import sys
import logging
from datetime import timedelta
import psycopg2
from calculate_metrics import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Lista oficial de tickers deslistados, incorporados ou que mudaram de código na B3 (> 90 dias sem negociação)
IGNORED_INACTIVE_TICKERS = {
    "AESB3", "ARZZ3", "AZUL4", "BPAN4", "BRFS3", "CCRO3", "CIEL3", "CLSA3",
    "CPLE6", "CRFB3", "ELET3", "ELET6", "EMBR3", "ENAT3", "GUAR3", "JBSS3",
    "MRFG3", "NEOE3", "NTCO3", "ODPV3", "PETZ3", "PORT3", "RRRP3", "SOMA3",
    "SRNA3", "STBP3", "TRPL4"
}


def purge_security_by_id(cur, sec_id, ticker):
    """Remove todos os registros dependentes de um security_id e o próprio registro em securities."""
    cur.execute("""
        DELETE FROM split_adjustment_log
        WHERE security_id = %s
           OR action_id IN (SELECT id FROM corporate_actions WHERE security_id = %s);
    """, (sec_id, sec_id))
    cur.execute("""
        DELETE FROM price_adjustments
        WHERE security_id = %s
           OR corporate_action_id IN (SELECT id FROM corporate_actions WHERE security_id = %s);
    """, (sec_id, sec_id))
    cur.execute("""
        DELETE FROM shareholder_distributions
        WHERE security_id = %s
           OR corporate_action_id IN (SELECT id FROM corporate_actions WHERE security_id = %s);
    """, (sec_id, sec_id))
    cur.execute("DELETE FROM corporate_actions WHERE security_id = %s;", (sec_id,))
    cur.execute("DELETE FROM daily_metrics WHERE security_id = %s;", (sec_id,))
    cur.execute("DELETE FROM daily_prices WHERE security_id = %s;", (sec_id,))
    cur.execute("DELETE FROM ibov_memberships WHERE security_id = %s;", (sec_id,))
    cur.execute("DELETE FROM security_share_history WHERE security_id = %s;", (sec_id,))
    cur.execute("DELETE FROM securities WHERE id = %s;", (sec_id,))

    # Limpar tabelas auxiliares por ticker (se existirem)
    cur.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'b3_corporate_events_cache') THEN
                DELETE FROM b3_corporate_events_cache WHERE ticker = %s;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_anomaly_logs') THEN
                DELETE FROM audit_anomaly_logs WHERE ticker = %s;
            END IF;
        END $$;
    """, (ticker, ticker))


def purge_inactive_securities(conn, max_inactive_days=90):
    """
    Identifica e remove do banco de dados todas as ações na lista de ignore (IGNORED_INACTIVE_TICKERS)
    ou cujo último pregão negociado em daily_prices tenha mais de max_inactive_days dias em relação
    ao pregão mais recente do mercado.
    """
    cur = conn.cursor()
    cur.execute("SELECT MAX(price_date) FROM daily_prices;")
    row_max = cur.fetchone()
    max_market_date = row_max[0] if row_max and row_max[0] else None

    if not max_market_date:
        return 0

    cutoff_date = max_market_date - timedelta(days=max_inactive_days)
    logging.info(f"Verificando ativos sem negociação desde {cutoff_date} (> {max_inactive_days} dias do pregão {max_market_date})...")

    cur.execute("""
        SELECT s.id, s.ticker, s.company_id, MAX(dp.price_date) as last_trade
        FROM securities s
        LEFT JOIN daily_prices dp ON dp.security_id = s.id
        GROUP BY s.id, s.ticker, s.company_id
        ORDER BY s.ticker;
    """)
    all_secs = cur.fetchall()

    to_purge = []
    for sec_id, ticker, comp_id, last_trade in all_secs:
        if ticker in ("IBOV", "IFNC", "SEGUROS"):
            continue
        if ticker in IGNORED_INACTIVE_TICKERS or last_trade is None or last_trade < cutoff_date:
            to_purge.append((sec_id, ticker, comp_id, last_trade))

    if not to_purge:
        logging.info("[OK] Nenhum ativo inativo (> 90 dias) encontrado no banco de dados.")
        return 0

    logging.info(f"Removendo {len(to_purge)} ativos inativos/deslistados (> {max_inactive_days} dias): {[x[1] for x in to_purge]}")

    affected_companies = set()
    for sec_id, ticker, comp_id, last_trade in to_purge:
        logging.info(f"  -> Excluindo {ticker} (último pregão: {last_trade})...")
        purge_security_by_id(cur, sec_id, ticker)
        if comp_id:
            affected_companies.add(comp_id)
    conn.commit()

    # Limpar empresas órfãs que não possuem mais nenhuma security ativa
    orphan_companies_removed = 0
    for comp_id in affected_companies:
        cur.execute("SELECT COUNT(*) FROM securities WHERE company_id = %s;", (comp_id,))
        remaining = cur.fetchone()[0]
        if remaining == 0:
            cur.execute("""
                DELETE FROM split_adjustment_log
                WHERE action_id IN (SELECT id FROM corporate_actions WHERE company_id = %s);
            """, (comp_id,))
            cur.execute("""
                DELETE FROM price_adjustments
                WHERE corporate_action_id IN (SELECT id FROM corporate_actions WHERE company_id = %s);
            """, (comp_id,))
            cur.execute("""
                DELETE FROM shareholder_distributions
                WHERE corporate_action_id IN (SELECT id FROM corporate_actions WHERE company_id = %s);
            """, (comp_id,))
            cur.execute("DELETE FROM corporate_actions WHERE company_id = %s;", (comp_id,))
            cur.execute("DELETE FROM company_daily_metrics WHERE company_id = %s;", (comp_id,))
            cur.execute("DELETE FROM company_share_capital WHERE company_id = %s;", (comp_id,))
            cur.execute("""
                DELETE FROM financial_facts
                WHERE report_id IN (SELECT id FROM financial_reports WHERE company_id = %s);
            """, (comp_id,))
            cur.execute("DELETE FROM financial_reports WHERE company_id = %s;", (comp_id,))
            cur.execute("DELETE FROM companies WHERE id = %s;", (comp_id,))
            orphan_companies_removed += 1
    conn.commit()

    logging.info(
        f"[OK] {len(to_purge)} ativos inativos e {orphan_companies_removed} empresas deslistadas órfãs removidos do Supabase!"
    )
    return len(to_purge)


def clean_duplicate_securities():
    logging.info("Iniciando varredura de securities duplicadas e ativos inativos (> 90 dias)...")
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

    deleted_count = 0

    if not dup_rows:
        logging.info("[OK] Nenhuma duplicidade encontrada na tabela 'securities'.")
    else:
        logging.info(f"Encontrados {len(dup_rows)} tickers duplicados: {[r[0] for r in dup_rows]}")

        for ticker, _ in dup_rows:
            cur.execute("""
                SELECT s.id,
                       (SELECT count(*) FROM daily_prices WHERE security_id = s.id AND price_source = 'B3_COTAHIST') as b3_count,
                       (SELECT count(*) FROM daily_prices WHERE security_id = s.id) as dp_total,
                       (SELECT count(*) FROM daily_metrics WHERE security_id = s.id) as dm_total
                FROM securities s
                WHERE s.ticker = %s;
            """, (ticker,))
            candidates = cur.fetchall()

            candidates.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)
            primary_id = candidates[0][0]
            duplicates = [c[0] for c in candidates[1:]]

            logging.info(f"[{ticker}] Manter Primary ID={primary_id} | Remover Duplicatas={duplicates}")

            for dup_id in duplicates:
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

                purge_security_by_id(cur, dup_id, ticker)
                deleted_count += 1

            conn.commit()

        logging.info(f"[SUCESSO] {deleted_count} securities duplicadas removidas com sucesso.")

    # 2. Expurgar ativos sem negociação nos últimos 90 dias ou na lista de ignore
    purged_inactive = purge_inactive_securities(conn, max_inactive_days=90)

    # 3. Garantir restrição UNIQUE(ticker)
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
    return deleted_count + purged_inactive


if __name__ == "__main__":
    clean_duplicate_securities()
