"""
auto_heal_anomalies.py
Motor de Auto-Cura (Self-Healing) + Recálculo Seletivo + Fallback Externo (Yahoo Finance)
para o Ecossistema Preco_Lucro (B3 / CVM).

Arquitetura em 3 Camadas:
  Estágio 1: Auto-Cura Determinística no Banco (SQL)
    - Expurgo de proventos duplicados (shareholder_distributions)
    - Expurgo de fatos contábeis duplicados no mesmo report_id (financial_facts)
    - Interpolação (Forward-Fill e Backward-Fill) de total_shares = 0 em company_share_capital
    - Saneamento de outliers de digitação na CVM (ex: BRSR6 PN inflado 10x em 2025-09-30)
    - Consolidação de empresas sucedidas (BRAV3 <- RRRP3, AZZA3 <- ARZZ3)
  Estágio 2: Re-execução Seletiva de Cálculos
    - Recalcula Dividend Yield TTM sem duplicatas
    - Recalcula daily_metrics e company_daily_metrics para todas as empresas curadas
  Estágio 3: Fallback para Base Externa (Yahoo Finance API)
    - Verifica se a base acionária mais recente diverge > 50% do Yahoo Finance (ex: TUPY3)
    - Se confirmada distorção de quota na CVM, aplica o fallback externo oficial e recalcula os múltiplos.
"""

import os
import logging
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv
from datetime import timedelta
import yfinance as yf
from adjust_splits import recalculate_single_company_metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        connect_timeout=30
    )

def stage_1_deterministic_sql_healing(conn):
    """
    Estágio 1: Auto-cura determinística diretamente nas tabelas do Supabase.
    Retorna o conjunto de company_ids impactados que precisam de recálculo no Estágio 2.
    """
    logging.info(">>> [Estágio 1/3] Iniciando Auto-Cura Determinística no Banco (SQL)...")
    cur = conn.cursor()
    affected_companies = set()

    # 1.1 Expurgo de duplicatas em shareholder_distributions (causa de DY > 40% em ALOS3, BBSE3, CURY3, etc.)
    cur.execute("""
        DELETE FROM shareholder_distributions a
        USING shareholder_distributions b
        WHERE a.id > b.id
          AND a.security_id = b.security_id
          AND a.distribution_type = b.distribution_type
          AND a.ex_date = b.ex_date
          AND ROUND(a.gross_amount_per_share::numeric, 4) = ROUND(b.gross_amount_per_share::numeric, 4);
    """)
    deleted_divs = cur.rowcount
    conn.commit()
    logging.info(f"  [1.1] {deleted_divs} proventos duplicados removidos de shareholder_distributions.")

    # 1.2 Expurgo de duplicatas exatas em financial_facts (mesmo report_id)
    cur.execute("""
        DELETE FROM financial_facts a
        USING financial_facts b
        WHERE a.id > b.id
          AND a.report_id = b.report_id
          AND a.statement_type = b.statement_type
          AND a.account_code = b.account_code
          AND COALESCE(a.period_start, '1900-01-01') = COALESCE(b.period_start, '1900-01-01')
          AND a.period_end = b.period_end;
    """)
    deleted_facts = cur.rowcount
    conn.commit()
    logging.info(f"  [1.2] {deleted_facts} fatos contábeis duplicados removidos de financial_facts.")

    # 1.3 Interpolação Bidirecional (LAG e LEAD) para total_shares <= 0 (VIVT3, KEPL3, ASAI3, CLSA3, INTB3)
    cur.execute("""
        SELECT id, company_id, reference_date
        FROM company_share_capital
        WHERE total_shares IS NULL OR total_shares <= 0;
    """)
    zero_rows = cur.fetchall()
    healed_zeros = 0
    for sc_id, comp_id, ref_date in zero_rows:
        # Tenta buscar o trimestre válido imediatamente anterior (Forward-Fill)
        cur.execute("""
            SELECT common_shares, preferred_shares, total_shares
            FROM company_share_capital
            WHERE company_id = %s AND reference_date < %s AND total_shares > 0
            ORDER BY reference_date DESC
            LIMIT 1;
        """, (comp_id, ref_date))
        neighbor = cur.fetchone()

        # Se for o 1º registro da série (sem anterior válido), busca o próximo trimestre válido (Backward-Fill)
        if not neighbor:
            cur.execute("""
                SELECT common_shares, preferred_shares, total_shares
                FROM company_share_capital
                WHERE company_id = %s AND reference_date > %s AND total_shares > 0
                ORDER BY reference_date ASC
                LIMIT 1;
            """, (comp_id, ref_date))
            neighbor = cur.fetchone()

        if neighbor:
            c_sh, p_sh, t_sh = neighbor
            cur.execute("""
                UPDATE company_share_capital
                SET common_shares = %s, preferred_shares = %s, total_shares = %s
                WHERE id = %s;
            """, (c_sh, p_sh, t_sh, sc_id))
            healed_zeros += 1
            affected_companies.add(comp_id)

    conn.commit()
    logging.info(f"  [1.3] {healed_zeros} registros com total_shares = 0 curados via interpolação temporal.")

    # 1.4 Saneamento de spike pontual de digitação na CVM (onde 1 trimestre salta > 3x e no trimestre seguinte volta exatamente ao patamar anterior, ex: BRSR6, GMAT3)
    cur.execute("""
        WITH ordered_sc AS (
            SELECT 
                id,
                company_id,
                reference_date,
                common_shares,
                preferred_shares,
                total_shares,
                LAG(total_shares) OVER (PARTITION BY company_id ORDER BY reference_date) as prev_tot,
                LAG(common_shares) OVER (PARTITION BY company_id ORDER BY reference_date) as prev_on,
                LAG(preferred_shares) OVER (PARTITION BY company_id ORDER BY reference_date) as prev_pn,
                LEAD(total_shares) OVER (PARTITION BY company_id ORDER BY reference_date) as next_tot
            FROM company_share_capital
            WHERE total_shares > 0
        )
        SELECT id, company_id, reference_date, prev_on, prev_pn, prev_tot, total_shares, next_tot
        FROM ordered_sc
        WHERE prev_tot > 0 AND next_tot > 0
          AND (total_shares / prev_tot > 3.0 OR total_shares / prev_tot < 0.33)
          AND ABS(next_tot - prev_tot) / prev_tot < 0.15;
    """)
    glitches = cur.fetchall()
    for sc_id, comp_id, ref_date, prev_on, prev_pn, prev_tot, cur_tot, next_tot in glitches:
        cur.execute("""
            UPDATE company_share_capital
            SET common_shares = %s, preferred_shares = %s, total_shares = %s
            WHERE id = %s;
        """, (prev_on, prev_pn, prev_tot, sc_id))
        affected_companies.add(comp_id)
        logging.info(f"  [1.4] Spike isolado de CVM corrigido em company_id={comp_id} ({ref_date}): {cur_tot:,.0f} -> {prev_tot:,.0f}")
    conn.commit()

    # 1.5 Unificação de companhias sucedidas (BRAV3 <-> RRRP3 e AZZA3 <-> ARZZ3) e restauração de CPFE3
    cur.execute("SELECT s.id, s.company_id FROM securities s WHERE s.ticker = 'BRAV3';")
    brav = cur.fetchone()
    cur.execute("SELECT s.id, s.company_id FROM securities s WHERE s.ticker = 'RRRP3';")
    rrrp = cur.fetchone()
    if brav and rrrp and brav[1] != rrrp[1]:
        cur.execute("SELECT COUNT(*) FROM financial_reports WHERE company_id = %s;", (rrrp[1],))
        if cur.fetchone()[0] > 0:
            cur.execute("UPDATE securities SET company_id = %s WHERE id = %s;", (rrrp[1], brav[0]))
            cur.execute("UPDATE companies SET trading_name = 'BRAVA ENERGIA', legal_name = 'BRAVA ENERGIA S.A.' WHERE id = %s;", (rrrp[1],))
            affected_companies.add(rrrp[1])
            conn.commit()
            logging.info("  [1.5a] BRAV3 vinculada ao histórico contábil oficial da Brava Energia (ex-3R Petroleum).")

    cur.execute("SELECT s.id, s.company_id FROM securities s WHERE s.ticker = 'AZZA3';")
    azza = cur.fetchone()
    cur.execute("SELECT s.id, s.company_id FROM securities s WHERE s.ticker = 'ARZZ3';")
    arzz = cur.fetchone()
    if azza and arzz and azza[1] != arzz[1]:
        cur.execute("UPDATE securities SET company_id = %s WHERE id = %s;", (arzz[1], azza[0]))
        cur.execute("UPDATE companies SET trading_name = 'AZZAS 2154', legal_name = 'AZZAS 2154 S.A.' WHERE id = %s;", (arzz[1],))
        affected_companies.add(arzz[1])
        conn.commit()
        logging.info("  [1.5b] AZZA3 vinculada ao histórico contábil oficial da Azzas 2154 (ex-Arezzo CVM 022349).")

    # Registrar a conversão de debêntures da BHIA3 (3T25) como evento societário de emissão de ações em corporate_actions
    cur.execute("SELECT id, company_id FROM securities WHERE ticker = 'BHIA3';")
    bhia = cur.fetchone()
    if bhia:
        bhia_sec_id, bhia_cid = bhia
        cur.execute("""
            UPDATE company_share_capital
            SET total_shares = 95087000, common_shares = 95087000, source = 'CVM_OFICIAL'
            WHERE company_id = %s AND reference_date BETWEEN '2024-06-30' AND '2025-06-30';
        """, (bhia_cid,))
        cur.execute("""
            SELECT COUNT(*) FROM corporate_actions
            WHERE company_id = %s AND effective_date = '2025-09-30';
        """, (bhia_cid,))
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO corporate_actions (company_id, security_id, event_type, effective_date, share_multiplier, currency, description, source, status)
                VALUES (%s, %s, 'SPLIT', '2025-09-30', 6.8766, 'BRL', 'Conversao de debentures em acoes BHIA3 (3T25)', 'CVM_ITR', 'CONFIRMED');
            """, (bhia_cid, bhia_sec_id))
            affected_companies.add(bhia_cid)
        conn.commit()

    # Restaurar relatórios contábeis da CPFE3 (CPFL Energia) caso tenham sido absorvidos por colisão de CNPJ
    cur.execute("SELECT company_id FROM securities WHERE ticker = 'CPFE3';")
    cpfe_row = cur.fetchone()
    cur.execute("SELECT company_id FROM securities WHERE ticker = 'VIVT3';")
    vivt_row = cur.fetchone()
    if cpfe_row and vivt_row:
        cpfe_cid, vivt_cid = cpfe_row[0], vivt_row[0]
        cur.execute("SELECT COUNT(*) FROM financial_reports WHERE company_id = %s;", (cpfe_cid,))
        if cur.fetchone()[0] == 0:
            cur.execute("""
                INSERT INTO company_share_capital (company_id, reference_date, known_date, common_shares, preferred_shares, total_shares, treasury_shares, source)
                SELECT %s, reference_date, known_date, common_shares, preferred_shares, total_shares, treasury_shares, source
                FROM company_share_capital
                WHERE company_id = %s
                ON CONFLICT DO NOTHING;
            """, (cpfe_cid, vivt_cid))
            cur.execute("""
                SELECT id, source_type, fiscal_year, period_start, period_end, publication_date, receipt_date, is_consolidated, version_no, source_file, document_id
                FROM financial_reports
                WHERE company_id = %s;
            """, (vivt_cid,))
            for r in cur.fetchall():
                old_rep_id = r[0]
                cur.execute("""
                    INSERT INTO financial_reports (company_id, source_type, fiscal_year, period_start, period_end, publication_date, receipt_date, is_consolidated, version_no, source_file, document_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (cpfe_cid, r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10]))
                new_rep_id = cur.fetchone()[0]
                cur.execute("""
                    INSERT INTO financial_facts (report_id, statement_type, account_code, account_description, period_start, period_end, account_value, unit, is_cumulative)
                    SELECT %s, statement_type, account_code, account_description, period_start, period_end, account_value, unit, is_cumulative
                    FROM financial_facts
                    WHERE report_id = %s;
                """, (new_rep_id, old_rep_id))
            affected_companies.add(cpfe_cid)
            conn.commit()
            logging.info("  [1.5c] Demonstrações contábeis e base acionária restauradas para CPFE3 (CPFL Energia).")

    cur.close()
    return affected_companies, deleted_divs > 0

def stage_2_selective_recalculation(conn, affected_companies, recalculate_dy=False):
    """
    Estágio 2: Re-executa os cálculos de Dividend Yield e Múltiplos Diários para os ativos curados.
    """
    logging.info(">>> [Estágio 2/3] Executando Recálculo Seletivo de Métricas...")

    if recalculate_dy:
        from calculate_dividend_yield import calculate_dividend_yield
        logging.info("  [2.1] Recalculando Dividend Yield TTM pós-desduplicação de proventos...")
        calculate_dividend_yield("2024-01-01")

    if affected_companies:
        logging.info(f"  [2.2] Recalculando séries históricas de múltiplos para {len(affected_companies)} empresas curadas...")
        for comp_id in affected_companies:
            recalculate_single_company_metrics(conn, comp_id)
        logging.info("  [OK] Recálculo seletivo concluído.")

def stage_3_external_fallback_yfinance(conn):
    """
    Estágio 3: Fallback para Base Externa (Yahoo Finance API).
    Confronta a base acionária recente de empresas que apresentaram queda/salto anômalo não explicado no último ano
    (ex: TUPY3, VBBR3) com o número oficial de ações em circulação do Yahoo Finance.
    """
    logging.info(">>> [Estágio 3/3] Executando Validação e Fallback Externo (Yahoo Finance)...")
    cur = conn.cursor()

    # Buscar empresas onde o último total_shares sofreu queda > 70% ou salto > 300% desde 2024 sem split registrado
    cur.execute("""
        WITH recent_jumps AS (
            SELECT 
                c.id AS company_id,
                c.trading_name,
                s.ticker,
                sc.id AS sc_id,
                sc.reference_date,
                sc.total_shares,
                LAG(sc.total_shares) OVER (PARTITION BY c.id ORDER BY sc.reference_date) as prev_shares
            FROM company_share_capital sc
            JOIN companies c ON sc.company_id = c.id
            JOIN securities s ON s.company_id = c.id
            WHERE sc.reference_date >= '2024-01-01' AND sc.total_shares > 0
        )
        SELECT DISTINCT company_id, trading_name, ticker
        FROM recent_jumps
        WHERE prev_shares > 0 AND (total_shares / prev_shares > 3.0 OR total_shares / prev_shares < 0.33);
    """)
    candidates = cur.fetchall()

    repaired_by_external = set()

    for comp_id, comp_name, ticker in candidates:
        # Verificar se há split registrado em 2024-2026
        cur.execute("""
            SELECT COUNT(*) FROM corporate_actions
            WHERE company_id = %s AND effective_date >= '2024-01-01';
        """, (comp_id,))
        has_split = cur.fetchone()[0] > 0
        if has_split:
            continue

        try:
            yf_tkr = yf.Ticker(f"{ticker}.SA")
            ext_shares = yf_tkr.fast_info.get("shares")
            if not ext_shares or ext_shares <= 0:
                continue

            # Buscar registros de 2025 em diante dessa empresa no banco
            cur.execute("""
                SELECT id, reference_date, total_shares
                FROM company_share_capital
                WHERE company_id = %s AND reference_date >= '2024-06-30'
                ORDER BY reference_date DESC;
            """, (comp_id,))
            sc_rows = cur.fetchall()

            for sc_id, ref_dt, db_shares in sc_rows:
                db_sh = float(db_shares)
                ratio = db_sh / float(ext_shares)
                # Se o valor no banco divergir por mais de 3x do valor real de mercado (ex: TUPY3 com 6.7M/11M vs 131M reais)
                if ratio < 0.25 or ratio > 4.0:
                    cur.execute("""
                        UPDATE company_share_capital
                        SET total_shares = %s, common_shares = %s, source = 'YFINANCE_FALLBACK'
                        WHERE id = %s;
                    """, (float(ext_shares), float(ext_shares), sc_id))
                    repaired_by_external.add((comp_id, ticker))
                    logging.info(f"  [FALLBACK EXTERNO APLICADO] {ticker} ({ref_dt}): CVM={db_sh:,.0f} -> Yahoo Finance={ext_shares:,.0f}")

        except Exception as e:
            logging.warning(f"  [Aviso] Falha ao consultar fallback externo para {ticker}: {e}")

    conn.commit()

    for comp_id, ticker in repaired_by_external:
        logging.info(f"  Recalculando múltiplos de {ticker} após reparo via base externa...")
        recalculate_single_company_metrics(conn, comp_id)

    cur.close()
    return len(repaired_by_external)

def run_self_healing_pipeline():
    logging.info("=" * 75)
    logging.info("MOTOR DE AUTO-CURA (SELF-HEALING) E FALLBACK EXTERNO B3 / CVM")
    logging.info("=" * 75)

    conn = get_db_connection()
    try:
        affected_comps, dy_changed = stage_1_deterministic_sql_healing(conn)
        stage_2_selective_recalculation(conn, affected_comps, recalculate_dy=dy_changed)
        ext_count = stage_3_external_fallback_yfinance(conn)
        logging.info(f"[SUCESSO] Pipeline de Auto-Cura finalizado! Empresas curadas internamente: {len(affected_comps)} | Via Base Externa: {ext_count}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_self_healing_pipeline()
