"""
detect_anomalies.py
Sistema de Auditoria Contínua, Integridade Contábil e Detecção de Anomalias Estatísticas B3/CVM.

Executado automaticamente às 20:30 BRT (23:30 UTC) no GitHub Actions pós-atualização diária.
Validações implementadas:
1. Base Acionária e Quotas CVM (company_share_capital):
   - Saltos > 3x ou < 0.33x sem registro correspondente em corporate_actions.
   - total_shares <= 0 ou distorções de quotas.
2. Cotações e Ações Corporativas (daily_prices vs corporate_actions):
   - Desvios diários com |Z-Score| > 4.0 vs média móvel de 30 pregões.
   - Splits/inplits recentes não ajustados retroativamente gerando saltos artificiais.
3. Múltiplos Fundamentalistas e Units (daily_metrics):
   - Verificação mandatória de aplicação do UNIT_SHARES_RATIO em tickers 11 (BPAC11, KLBN11, SANB11, etc.).
   - P/L com salto diário > 3x sem nova demonstração CVM; P/L extremo persistente > 500x ou < -500x.
   - ROE TTM > 150% ou < -150% (avaliação de PL negativo/baixo, DRE individual vs consolidada).
   - P/VP < 0 ou saltos > 50x.
   - Dividend Yield TTM > 40% (duplicação de proventos ou denominador incorreto).
4. Fatos Contábeis (financial_facts & financial_reports):
   - Duplicatas exatas por (report_id, account_code, period_start, period_end).
   - Ausência ou não priorização de demonstrativos consolidados.
"""

import os
import json
import math
import logging
from datetime import datetime, date, timedelta
import psycopg2
from psycopg2.extras import execute_batch
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
load_dotenv()

UNIT_SHARES_RATIO = {
    'BPAC11': 3.0,
    'KLBN11': 5.0,
    'SANB11': 2.0,
    'TAEE11': 3.0,
    'ALUP11': 3.0,
    'ENGI11': 5.0,
    'SAPR11': 5.0,
    'IGTI11': 3.0,
    'RANI11': 3.0,
    'SULA11': 3.0,
}

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=30
    )

def audit_share_capital(cur):
    """
    Audita variações na base acionária (company_share_capital) e compara com corporate_actions.
    """
    logging.info("Auditor: Verificando base acionária e quotas CVM...")
    anomalies = []

    # 1. Total shares nulo ou zerado
    cur.execute("""
        SELECT c.trading_name, s.ticker, sc.reference_date, sc.total_shares
        FROM company_share_capital sc
        JOIN companies c ON sc.company_id = c.id
        LEFT JOIN securities s ON s.company_id = c.id
        WHERE sc.total_shares IS NULL OR sc.total_shares <= 0;
    """)
    for comp_name, ticker, ref_date, total_shares in cur.fetchall():
        tick = ticker or "N/A"
        anomalies.append({
            "ticker": tick,
            "company_name": comp_name,
            "metric_name": "total_shares",
            "previous_value": None,
            "current_value": float(total_shares) if total_shares is not None else 0.0,
            "variation_pct": None,
            "severity": "CRITICAL",
            "category": "SHARE_CAPITAL",
            "diagnosis": f"Base acionária inválida (total_shares = {total_shares}) em {ref_date}."
        })

    # 2. Variação abrupta de total_shares (> 3x ou < 0.33x) no período ativo pós-IPO sem corporate_actions compatível
    cur.execute("""
        WITH first_prices AS (
            SELECT company_id, MIN(p.price_date) as min_price_date
            FROM securities s
            JOIN daily_prices p ON p.security_id = s.id
            GROUP BY company_id
        ),
        lagged AS (
            SELECT 
                c.id AS company_id,
                c.trading_name,
                s.ticker,
                sc.reference_date,
                sc.total_shares,
                LAG(sc.total_shares) OVER (PARTITION BY c.id, s.ticker ORDER BY sc.reference_date) as prev_shares,
                LAG(sc.reference_date) OVER (PARTITION BY c.id, s.ticker ORDER BY sc.reference_date) as prev_date,
                fp.min_price_date
            FROM company_share_capital sc
            JOIN companies c ON sc.company_id = c.id
            JOIN securities s ON s.company_id = c.id
            LEFT JOIN first_prices fp ON fp.company_id = c.id
            WHERE sc.total_shares > 0
              AND sc.reference_date >= '2023-01-01'
        )
        SELECT company_id, trading_name, ticker, reference_date, prev_date, total_shares, prev_shares
        FROM lagged
        WHERE prev_shares > 0 
          AND (min_price_date IS NULL OR prev_date >= min_price_date)
          AND (total_shares / prev_shares > 3.0 OR total_shares / prev_shares < 0.33)
        ORDER BY reference_date DESC;
    """)
    variations = cur.fetchall()

    for comp_id, comp_name, ticker, ref_date, prev_date, cur_shares, prev_shares in variations:
        tick = ticker or "N/A"
        cur_sh = float(cur_shares)
        prev_sh = float(prev_shares)
        ratio = cur_sh / prev_sh
        var_pct = round((ratio - 1.0) * 100, 2)

        # Checar se existe desdobramento/grupamento/aumento de capital (corporate_actions) registrado entre as datas (usando effective_date ou ex_date com janela de +-45 dias)
        cur.execute("""
            SELECT event_type, share_multiplier 
            FROM corporate_actions 
            WHERE company_id = %s 
              AND event_type IN ('SPLIT', 'REVERSE_SPLIT', 'INPLIT', 'BONUS', 'DESDOBRAMENTO', 'GRUPAMENTO', 'CAPITAL_INCREASE')
              AND COALESCE(effective_date, ex_date) BETWEEN (%s::date - INTERVAL '45 days') AND (%s::date + INTERVAL '45 days');
        """, (comp_id, prev_date, ref_date))
        corp_matches = cur.fetchall()

        if not corp_matches:
            severity = "CRITICAL" if (ratio > 5.0 or ratio < 0.2) else "WARNING"
            anomalies.append({
                "ticker": tick,
                "company_name": comp_name,
                "metric_name": "total_shares",
                "previous_value": prev_sh,
                "current_value": cur_sh,
                "variation_pct": var_pct,
                "severity": severity,
                "category": "SHARE_CAPITAL",
                "diagnosis": f"Variação de {var_pct:+.1f}% nas quotas de capital entre {prev_date} e {ref_date} sem registro de split/inplit em corporate_actions."
            })

    return anomalies

def audit_prices_and_splits(cur):
    """
    Audita desvios estatísticos de cotações (|Z-score| > 4.0 nos últimos 30 pregões)
    e inplits/splits não ajustados.
    """
    logging.info("Auditor: Verificando integridade de cotações e ações corporativas...")
    anomalies = []

    # Busca os últimos 40 pregões para cada security ativo
    cur.execute("""
        WITH ranked_prices AS (
            SELECT 
                s.ticker,
                c.trading_name,
                dp.price_date,
                dp.close_price,
                dp.split_adjustment_factor,
                ROW_NUMBER() OVER (PARTITION BY s.id ORDER BY dp.price_date DESC) as rn
            FROM daily_prices dp
            JOIN securities s ON dp.security_id = s.id
            JOIN companies c ON s.company_id = c.id
            WHERE dp.close_price > 0
        )
        SELECT ticker, trading_name, price_date, close_price, split_adjustment_factor, rn
        FROM ranked_prices
        WHERE rn <= 35
        ORDER BY ticker, rn ASC;
    """)
    rows = cur.fetchall()

    series_by_ticker = {}
    for ticker, comp_name, dt, price, factor, rn in rows:
        if ticker not in series_by_ticker:
            series_by_ticker[ticker] = {
                "name": comp_name,
                "prices": [],
                "dates": [],
                "factors": []
            }
        series_by_ticker[ticker]["prices"].append(float(price))
        series_by_ticker[ticker]["dates"].append(str(dt))
        series_by_ticker[ticker]["factors"].append(float(factor) if factor else 1.0)

    for ticker, d in series_by_ticker.items():
        prices = d["prices"] # rn=1 primeiro (recente)
        if len(prices) < 15:
            continue

        latest_price = prices[0]
        hist_window = prices[1:31]
        mean_price = sum(hist_window) / len(hist_window)
        variance = sum((p - mean_price) ** 2 for p in hist_window) / len(hist_window)
        std_price = math.sqrt(variance) if variance > 0 else 0

        if std_price > 0:
            z_score = (latest_price - mean_price) / std_price
            prev_price = prices[1]
            day_return_pct = round(((latest_price / prev_price) - 1.0) * 100, 2)

            if abs(z_score) > 4.0:
                severity = "CRITICAL" if abs(day_return_pct) >= 45.0 else "WARNING"
                anomalies.append({
                    "ticker": ticker,
                    "company_name": d["name"],
                    "metric_name": "close_price",
                    "previous_value": round(prev_price, 2),
                    "current_value": round(latest_price, 2),
                    "variation_pct": day_return_pct,
                    "severity": severity,
                    "category": "SPLIT_PRICE",
                    "diagnosis": f"Desvio severo (|Z| = {abs(z_score):.2f} > 4.0, retorno {day_return_pct:+.1f}%) no pregão {d['dates'][0]}. Possível split/inplit não compensado ou spike de liquidez."
                })
            elif 2.5 < abs(z_score) <= 4.0 and abs(day_return_pct) >= 25.0:
                anomalies.append({
                    "ticker": ticker,
                    "company_name": d["name"],
                    "metric_name": "close_price",
                    "previous_value": round(prev_price, 2),
                    "current_value": round(latest_price, 2),
                    "variation_pct": day_return_pct,
                    "severity": "WARNING",
                    "category": "SPLIT_PRICE",
                    "diagnosis": f"Variação atípica moderada (|Z| = {abs(z_score):.2f}, variação {day_return_pct:+.1f}%)."
                })

    return anomalies

def audit_units_and_multiples(cur):
    """
    Audita consistência de Units (UNIT_SHARES_RATIO), variações anormais de P/L, ROE TTM, P/VP e Dividend Yield.
    """
    logging.info("Auditor: Verificando múltiplos fundamentalistas e conformidade de Units...")
    anomalies = []

    # 1. Auditoria específica de Units (final 11)
    for unit_ticker, expected_ratio in UNIT_SHARES_RATIO.items():
        cur.execute("""
            SELECT c.trading_name, dm.reference_date, dm.price_earnings, dm.book_value_per_share, dm.earnings_per_share_ttm, dm.shares_outstanding, sc.total_shares
            FROM daily_metrics dm
            JOIN securities s ON dm.security_id = s.id
            JOIN companies c ON s.company_id = c.id
            LEFT JOIN company_share_capital sc ON sc.company_id = c.id AND sc.reference_date = dm.financial_data_as_of
            WHERE s.ticker = %s
            ORDER BY dm.reference_date DESC
            LIMIT 1;
        """, (unit_ticker,))
        row = cur.fetchone()
        if row:
            comp_name, ref_date, pe, vpa, lpa, dm_shares, sc_shares = row
            if dm_shares and sc_shares:
                dm_sh = float(dm_shares)
                sc_sh = float(sc_shares)
                implied_ratio = sc_sh / dm_sh
                # Se as ações em daily_metrics forem iguais à total_shares da CVM, o unit ratio NÃO foi aplicado!
                if abs(implied_ratio - expected_ratio) > 0.5:
                    anomalies.append({
                        "ticker": unit_ticker,
                        "company_name": comp_name,
                        "metric_name": "UNIT_SHARES_RATIO",
                        "previous_value": expected_ratio,
                        "current_value": round(implied_ratio, 2),
                        "variation_pct": round(((implied_ratio / expected_ratio) - 1.0) * 100, 2),
                        "severity": "CRITICAL",
                        "category": "UNIT_RATIO",
                        "diagnosis": f"Falha mandatória de Unit: {unit_ticker} requer fator {expected_ratio}x, mas está com razão implícita {implied_ratio:.2f}x. Múltiplos P/L e P/VP distorcidos!"
                    })

    # 2. Variação de P/L de um dia para o outro sem nova DFP/ITR e Outliers persistentes
    cur.execute("""
        WITH ranked_m AS (
            SELECT 
                s.ticker,
                c.trading_name,
                dm.reference_date,
                dm.financial_data_as_of,
                dm.price_earnings,
                dm.price_to_book,
                dm.roe_ttm,
                dm.dividend_yield_ttm,
                LAG(dm.price_earnings) OVER (PARTITION BY s.id ORDER BY dm.reference_date) as prev_pe,
                LAG(dm.financial_data_as_of) OVER (PARTITION BY s.id ORDER BY dm.reference_date) as prev_financial_as_of,
                ROW_NUMBER() OVER (PARTITION BY s.id ORDER BY dm.reference_date DESC) as rn
            FROM daily_metrics dm
            JOIN securities s ON dm.security_id = s.id
            JOIN companies c ON s.company_id = c.id
        )
        SELECT ticker, trading_name, reference_date, financial_data_as_of, prev_financial_as_of, price_earnings, prev_pe, price_to_book, roe_ttm, dividend_yield_ttm
        FROM ranked_m
        WHERE rn = 1;
    """)
    recent_metrics = cur.fetchall()

    for ticker, comp_name, dt, fin_as_of, prev_fin_as_of, pe, prev_pe, pvp, roe, dy in recent_metrics:
        # P/L Jump sem nova demonstração contábil
        if pe is not None and prev_pe is not None and prev_pe != 0:
            pe_val = float(pe)
            prev_pe_val = float(prev_pe)
            if fin_as_of == prev_fin_as_of and (pe_val > 0 and prev_pe_val > 0):
                ratio = pe_val / prev_pe_val
                if ratio > 3.0 or ratio < 0.33:
                    var_pct = round((ratio - 1.0) * 100, 2)
                    anomalies.append({
                        "ticker": ticker,
                        "company_name": comp_name,
                        "metric_name": "price_earnings",
                        "previous_value": round(prev_pe_val, 2),
                        "current_value": round(pe_val, 2),
                        "variation_pct": var_pct,
                        "severity": "CRITICAL" if (ratio > 5.0 or ratio < 0.2) else "WARNING",
                        "category": "OUTLIER_MULTIPLE",
                        "diagnosis": f"Salto de P/L de {prev_pe_val:.1f}x para {pe_val:.1f}x ({var_pct:+.1f}%) em um único pregão sem divulgação de novo ITR/DFP."
                    })

        # P/L extremo persistente
        if pe is not None:
            pe_val = float(pe)
            if pe_val > 500.0 or pe_val < -500.0:
                anomalies.append({
                    "ticker": ticker,
                    "company_name": comp_name,
                    "metric_name": "price_earnings",
                    "previous_value": None,
                    "current_value": round(pe_val, 1),
                    "variation_pct": None,
                    "severity": "WARNING",
                    "category": "OUTLIER_MULTIPLE",
                    "diagnosis": f"P/L com valor extremo ({pe_val:.1f}x). Pode indicar lucro líquido próximo de zero (break-even operacional) ou inconsistência na base de ações."
                })

        # ROE TTM > 150% ou < -150%
        if roe is not None:
            roe_pct = float(roe) * 100.0 if abs(float(roe)) < 15.0 else float(roe)
            if abs(roe_pct) > 150.0:
                severity = "CRITICAL" if abs(roe_pct) > 500.0 else "WARNING"
                anomalies.append({
                    "ticker": ticker,
                    "company_name": comp_name,
                    "metric_name": "roe_ttm",
                    "previous_value": None,
                    "current_value": round(roe_pct, 2),
                    "variation_pct": None,
                    "severity": severity,
                    "category": "ACCOUNTING_TTM",
                    "diagnosis": f"ROE TTM anômalo ({roe_pct:.1f}%). Investigar se decorre de Patrimônio Líquido residual próximo a zero, item contábil não recorrente ou divergência DRE individual vs consolidada."
                })

        # P/VP negativo ou saltos > 50x
        if pvp is not None:
            pvp_val = float(pvp)
            if pvp_val < 0:
                anomalies.append({
                    "ticker": ticker,
                    "company_name": comp_name,
                    "metric_name": "price_to_book",
                    "previous_value": None,
                    "current_value": round(pvp_val, 2),
                    "variation_pct": None,
                    "severity": "WARNING",
                    "category": "ACCOUNTING_TTM",
                    "diagnosis": f"P/VP negativo ({pvp_val:.2f}x). Empresa operando com Patrimônio Líquido negativo (Passivo a Descoberto)."
                })
            elif pvp_val > 50.0:
                anomalies.append({
                    "ticker": ticker,
                    "company_name": comp_name,
                    "metric_name": "price_to_book",
                    "previous_value": None,
                    "current_value": round(pvp_val, 2),
                    "variation_pct": None,
                    "severity": "CRITICAL",
                    "category": "OUTLIER_MULTIPLE",
                    "diagnosis": f"P/VP excepcionalmente alto ({pvp_val:.1f}x). Verificar se o VPA está depreciado por erro no fator da Unit ou base acionária não conciliada."
                })

        # Dividend Yield TTM > 40%
        if dy is not None:
            dy_val = float(dy)
            if dy_val > 40.0:
                anomalies.append({
                    "ticker": ticker,
                    "company_name": comp_name,
                    "metric_name": "dividend_yield_ttm",
                    "previous_value": None,
                    "current_value": round(dy_val, 2),
                    "variation_pct": None,
                    "severity": "WARNING",
                    "category": "OUTLIER_MULTIPLE",
                    "diagnosis": f"Dividend Yield TTM atípico ({dy_val:.1f}%). Possível duplicidade na importação de proventos ou dividendo extraordinário/recapitalização."
                })

    return anomalies

def audit_accounting_facts(cur):
    """
    Audita integridade de fatos contábeis:
    - Duplicatas exatas dentro do mesmo report_id por (report_id, statement_type, account_code, period_start, period_end)
    - Verificação de empresas sem qualquer cobertura de métricas calculadas por ausência de relatórios contábeis.
    """
    logging.info("Auditor: Verificando integridade dos fatos contábeis (CVM)...")
    anomalies = []

    # 1. Duplicatas exatas reais dentro do mesmo report_id em financial_facts
    cur.execute("""
        SELECT 
            c.trading_name,
            c.cvm_code,
            s.ticker,
            ff.report_id,
            ff.account_code,
            ff.period_start,
            ff.period_end,
            COUNT(*) as dup_count
        FROM financial_facts ff
        JOIN financial_reports fr ON ff.report_id = fr.id
        JOIN companies c ON fr.company_id = c.id
        LEFT JOIN securities s ON s.company_id = c.id
        GROUP BY c.trading_name, c.cvm_code, s.ticker, ff.report_id, ff.statement_type, ff.account_code, ff.period_start, ff.period_end
        HAVING COUNT(*) > 1
        LIMIT 50;
    """)
    dups = cur.fetchall()
    for comp_name, cvm_code, ticker, rep_id, acc_code, p_start, p_end, dup_count in dups:
        tick = ticker or f"CVM:{cvm_code}"
        anomalies.append({
            "ticker": tick,
            "company_name": comp_name,
            "metric_name": f"dup_{acc_code}",
            "previous_value": 1.0,
            "current_value": float(dup_count),
            "variation_pct": None,
            "severity": "CRITICAL",
            "category": "ACCOUNTING_TTM",
            "diagnosis": f"Fato contábil {acc_code} duplicado ({dup_count} ocorrências no mesmo relatório {rep_id}) no período {p_start} a {p_end}."
        })

    # 2. Empresas com relatórios contábeis mas sem nenhuma métrica gerada em daily_metrics
    cur.execute("""
        SELECT c.trading_name, s.ticker, COUNT(DISTINCT fr.id) as rep_count, COUNT(DISTINCT dm.reference_date) as dm_count
        FROM companies c
        JOIN securities s ON s.company_id = c.id
        LEFT JOIN financial_reports fr ON fr.company_id = c.id
        LEFT JOIN daily_metrics dm ON dm.security_id = s.id AND dm.price_earnings IS NOT NULL
        GROUP BY c.trading_name, s.ticker
        HAVING COUNT(DISTINCT fr.id) = 0;
    """)
    missing_reps = cur.fetchall()
    for comp_name, ticker, rep_count, dm_count in missing_reps:
        anomalies.append({
            "ticker": ticker,
            "company_name": comp_name,
            "metric_name": "financial_reports",
            "previous_value": 1.0,
            "current_value": 0.0,
            "variation_pct": None,
            "severity": "CRITICAL",
            "category": "ACCOUNTING_TTM",
            "diagnosis": f"Ativo {ticker} não possui demonstrativos contábeis vinculados na CVM (0 relatórios DFP/ITR)."
        })

    return anomalies

def run_anomaly_detection():
    logging.info("=" * 70)
    logging.info("INICIANDO SUBSISTEMA DE AUDITORIA E DETECÇÃO DE ANOMALIAS B3/CVM")
    logging.info(f"Horário de execução: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    logging.info("=" * 70)

    conn = get_db_connection()
    cur = conn.cursor()

    all_anomalies = []

    try:
        all_anomalies.extend(audit_share_capital(cur))
        all_anomalies.extend(audit_prices_and_splits(cur))
        all_anomalies.extend(audit_units_and_multiples(cur))
        all_anomalies.extend(audit_accounting_facts(cur))

        logging.info(f"Auditoria finalizada. Total de anomalias encontradas: {len(all_anomalies)}")

        # Deduplicar anomalias por (ticker, metric_name, category)
        unique_anomalies = []
        seen = set()
        for a in all_anomalies:
            key = (a["ticker"], a["metric_name"], a["category"])
            if key not in seen:
                seen.add(key)
                unique_anomalies.append(a)

        logging.info(f"Anomalias únicas consolidadas: {len(unique_anomalies)}")

        # Atualizar no banco Supabase: marcar anteriores como RESOLVED e inserir a nova rodada
        cur.execute("UPDATE audit_anomaly_logs SET status = 'RESOLVED' WHERE status = 'ACTIVE';")

        if unique_anomalies:
            insert_query = """
                INSERT INTO audit_anomaly_logs (
                    executed_at, ticker, company_name, metric_name,
                    previous_value, current_value, variation_pct,
                    severity, category, diagnosis, status
                ) VALUES (
                    NOW(), %(ticker)s, %(company_name)s, %(metric_name)s,
                    %(previous_value)s, %(current_value)s, %(variation_pct)s,
                    %(severity)s, %(category)s, %(diagnosis)s, 'ACTIVE'
                );
            """
            execute_batch(cur, insert_query, unique_anomalies)

        conn.commit()
        logging.info("[OK] Tabela audit_anomaly_logs atualizada com sucesso no banco de dados!")

        # Exportar arquivo leve local para o front-end estático
        export_payload = {
            "executed_at": datetime.now().strftime("%d/%m/%Y às %H:%M"),
            "total_active": len(unique_anomalies),
            "critical_count": sum(1 for a in unique_anomalies if a["severity"] == "CRITICAL"),
            "warning_count": sum(1 for a in unique_anomalies if a["severity"] == "WARNING"),
            "anomalies": unique_anomalies
        }

        with open("anomalies_data.json", "w", encoding="utf-8") as f:
            json.dump(export_payload, f, ensure_ascii=False, indent=2)
        logging.info("[OK] anomalies_data.json gerado com sucesso!")

    except Exception as e:
        conn.rollback()
        logging.exception(f"Erro durante a execução do detector de anomalias: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    run_anomaly_detection()
