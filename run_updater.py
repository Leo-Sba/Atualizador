"""
run_updater.py
Orquestrador central em cascata (4 Estágios) da rotina diária fundamentalista (B3 & CVM).

Suporta execução modular por estágio (ideal para jobs encadeados no GitHub Actions)
ou execução completa sequencial:
  - python run_updater.py --stage 1  -> Ingestão de Mercado (Limpeza, Cotações B3/Yahoo e Proventos/Splits)
  - python run_updater.py --stage 2  -> Motor de Cálculo Fundamentalista (P/L, P/VP, ROE, LPA, VPA e DY 12M)
  - python run_updater.py --stage 3  -> Consolidação de Índices (IBOV, IFNC) e Calendário de Resultados
  - python run_updater.py --stage 4  -> Auto-Cura (Self-Healing) e Auditoria Contínua de Anomalias
  - python run_updater.py            -> Executa os 4 estágios em sequência na ordem contábil correta
"""

import sys
import time
import logging
import argparse
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def run_step_with_retry(step_label, func, *args, retries=2, delay_sec=10, critical=False, **kwargs):
    """
    Executa uma etapa do pipeline com retentativa automática (backoff) para
    prevenir falhas transitórias de rede (Yahoo Finance / B3) ou conexão com o Supabase.
    """
    total_attempts = retries + 1
    for attempt in range(1, total_attempts + 1):
        try:
            logging.info(f">>> {step_label} (Tentativa {attempt}/{total_attempts})...")
            func(*args, **kwargs)
            logging.info(f"[OK] {step_label} concluído com sucesso.")
            return True
        except Exception as e:
            logging.warning(f"[FALHA] {step_label} na tentativa {attempt}/{total_attempts}: {e}")
            if attempt < total_attempts:
                logging.info(f"Aguardando {delay_sec}s para nova tentativa...")
                time.sleep(delay_sec)
            else:
                if critical:
                    logging.error(f"[ERRO CRÍTICO] {step_label} falhou após {total_attempts} tentativas. Abortando estágio.")
                    sys.exit(1)
                else:
                    logging.warning(f"[AVISO] {step_label} não pôde ser concluído, mas o pipeline prosseguirá.")
                    return False


def run_stage_1_ingestion():
    """
    ESTÁGIO 1: Ingestão de Mercado (Preços, Duplicidades e Proventos/Eventos Societários)
    """
    logging.info("=" * 65)
    logging.info("ESTÁGIO 1/4: INGESTÃO DE MERCADO (LIMPEZA, COTAÇÕES E PROVENTOS)")
    logging.info("=" * 65)

    # 1.1 Limpeza preventiva de duplicidades
    from clean_duplicates import clean_duplicate_securities
    run_step_with_retry(
        "1.1 Limpeza preventiva de duplicidades (clean_duplicates)",
        clean_duplicate_securities,
        retries=1,
        critical=False,
    )

    # 1.2 Cotações recentes dos últimos 15 dias de pregão
    start_date = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
    from import_prices import fetch_and_save_prices
    run_step_with_retry(
        f"1.2 Download de cotações diárias B3 desde {start_date} (import_prices)",
        fetch_and_save_prices,
        start_date=start_date,
        retries=2,
        delay_sec=15,
        critical=True,
    )

    # 1.3 Proventos e Eventos Societários recentes
    current_year = datetime.now().year
    from import_distributions import import_distributions_and_splits
    run_step_with_retry(
        f"1.3 Importação de proventos e eventos societários de {current_year} (import_distributions)",
        import_distributions_and_splits,
        current_year,
        retries=2,
        delay_sec=15,
        critical=False,
    )

    # 1.4 Histórico Oficial de Eventos Societários B3 (Splits, Inplits, Bonificações e Cisões)
    from fetch_b3_events import run_b3_events_extraction
    run_step_with_retry(
        "1.4 Sincronização de eventos societários oficiais B3 (fetch_b3_events)",
        run_b3_events_extraction,
        retries=1,
        delay_sec=10,
        critical=False,
    )


def run_stage_2_metrics():
    """
    ESTÁGIO 2: Motor de Cálculo Fundamentalista (Múltiplos Diários e Dividend Yield)
    """
    logging.info("=" * 65)
    logging.info("ESTÁGIO 2/4: MOTOR DE CÁLCULO FUNDAMENTALISTA (P/L, P/VP, ROE, DY)")
    logging.info("=" * 65)

    # 2.1 Recálculo das Métricas Fundamentalistas (P/L, P/VP, ROE, LPA, VPA, Units)
    from calculate_metrics import calculate_metrics
    run_step_with_retry(
        "2.1 Recálculo de múltiplos fundamentalistas (calculate_metrics)",
        calculate_metrics,
        retries=2,
        delay_sec=10,
        critical=True,
    )

    # 2.2 Recálculo do Dividend Yield Móvel (12M)
    dy_start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    from calculate_dividend_yield import calculate_dividend_yield
    run_step_with_retry(
        f"2.2 Recálculo de Dividend Yield móvel desde {dy_start} (calculate_dividend_yield)",
        calculate_dividend_yield,
        start_date=dy_start,
        retries=2,
        delay_sec=10,
        critical=True,
    )


def run_stage_3_indices():
    """
    ESTÁGIO 3: Consolidação de Índices (IBOV e IFNC) e Calendário de Resultados
    Importante: Roda APÓS o Estágio 2 para utilizar os múltiplos recém-calculados do dia!
    """
    logging.info("=" * 65)
    logging.info("ESTÁGIO 3/4: CONSOLIDAÇÃO DE ÍNDICES (IBOV, IFNC) E CALENDÁRIO")
    logging.info("=" * 65)

    # 3.1 Composição e P/L Consolidado do IBOV
    from fetch_ibov_composition import calculate_and_save_ibov_pe
    run_step_with_retry(
        "3.1 Atualização da carteira e P/L consolidado do IBOV (fetch_ibov_composition)",
        calculate_and_save_ibov_pe,
        retries=2,
        delay_sec=15,
        critical=False,
    )

    # 3.2 Composição e Métricas do IFNC (FIND11)
    from fetch_ifnc_composition import fetch_and_calculate_ifnc
    run_step_with_retry(
        "3.2 Atualização da carteira e métricas do IFNC (fetch_ifnc_composition)",
        fetch_and_calculate_ifnc,
        retries=2,
        delay_sec=15,
        critical=False,
    )

    # 3.3 Calendário de Divulgação de Resultados
    from fetch_earnings_calendar import fetch_and_save_earnings_calendar
    run_step_with_retry(
        "3.3 Atualização do calendário de resultados (fetch_earnings_calendar)",
        fetch_and_save_earnings_calendar,
        retries=1,
        delay_sec=10,
        critical=False,
    )


def run_stage_4_audit():
    """
    ESTÁGIO 4: Auto-Cura (Self-Healing) e Auditoria Contínua de Anomalias
    """
    logging.info("=" * 65)
    logging.info("ESTÁGIO 4/4: AUTO-CURA (SELF-HEALING) E AUDITORIA DE ANOMALIAS")
    logging.info("=" * 65)

    # 4.1 Motor de Auto-Cura (SQL Determinístico + Recálculo Seletivo + Fallback Externo)
    from auto_heal_anomalies import run_self_healing_pipeline
    run_step_with_retry(
        "4.1 Motor de Auto-Cura de Anomalias (auto_heal_anomalies)",
        run_self_healing_pipeline,
        retries=1,
        delay_sec=10,
        critical=False,
    )

    # 4.2 Detector e Persistência de Logs de Auditoria (audit_anomaly_logs)
    from detect_anomalies import run_anomaly_detection
    run_step_with_retry(
        "4.2 Auditoria Contínua Pós-Cura (detect_anomalies)",
        run_anomaly_detection,
        retries=2,
        delay_sec=10,
        critical=True,
    )


def run_stage_5_macro():
    """
    ESTÁGIO 5 (FIM DA FILA DE DADOS): Coleta Macro & Juros (Curva Tesouro, Copom, Selic, CDI, IPCA, Focus)
    Executa após toda a fila fundamentalista B3/CVM com critical=False para nunca bloquear o deploy de ações.
    """
    logging.info("=" * 65)
    logging.info("ESTÁGIO 5/6: COLETA MACRO & CURVA DE JUROS (FIM DA FILA DE DADOS)")
    logging.info("=" * 65)

    from fetch_macro_data import run_macro_collection
    run_step_with_retry(
        "5.1 Coleta Macro BCB/Focus & Curva Tesouro Transparente (fetch_macro_data)",
        run_macro_collection,
        retries=1,
        delay_sec=10,
        critical=False,
    )


def run_stage_6_export():
    """
    ESTÁGIO 6 (FINAL ABSOLUTO): Compilação e Geração do Dashboard Estático (dashboard_data.json e dashboard.html)
    """
    logging.info("=" * 65)
    logging.info("ESTÁGIO 6/6: COMPILAÇÃO DO DASHBOARD (EXPORTAÇÃO DE DADOS & HTML)")
    logging.info("=" * 65)

    from export_dashboard_data import export_dashboard_data
    run_step_with_retry(
        "6.1 Exportação de dados e compilação do dashboard.html (export_dashboard_data)",
        export_dashboard_data,
        retries=2,
        delay_sec=10,
        critical=True,
    )


def main():
    parser = argparse.ArgumentParser(description="Orquestrador em Cascata B3 & CVM")
    parser.add_argument(
        "--stage",
        choices=["1", "2", "3", "4", "5", "6", "all"],
        default="all",
        help="Estágio específico a executar (1=Ingestão, 2=Métricas, 3=Índices, 4=Auditoria, 5=Macro, 6=Dashboard, all=Todos)",
    )
    args = parser.parse_args()

    if args.stage == "1":
        run_stage_1_ingestion()
    elif args.stage == "2":
        run_stage_2_metrics()
    elif args.stage == "3":
        run_stage_3_indices()
    elif args.stage == "4":
        run_stage_4_audit()
    elif args.stage == "5":
        run_stage_5_macro()
    elif args.stage == "6":
        run_stage_6_export()
    else:
        run_stage_1_ingestion()
        run_stage_2_metrics()
        run_stage_3_indices()
        run_stage_4_audit()
        run_stage_5_macro()
        run_stage_6_export()

    logging.info("=" * 65)
    logging.info(f"EXECUÇÃO FINALIZADA COM SUCESSO! (Modo: --stage {args.stage})")
    logging.info("=" * 65)


if __name__ == "__main__":
    main()
