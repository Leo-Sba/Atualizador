"""
run_updater.py
Orquestrador central da rotina diária de atualização fundamentalista.
Executa em sequência no GitHub Actions:
  1. Limpeza preventiva de duplicidades (clean_duplicates.py)
  2. Cotações recentes dos últimos pregões da B3 via Yahoo Finance (import_prices.py)
  3. Atualização da composição e P/L médio do IBOV via B3 (fetch_ibov_composition.py)
  4. Proventos e eventos societários recentes (import_distributions.py)
  5. Recálculo pregão a pregão de P/L, P/VP, ROE, LPA e VPA (calculate_metrics.py)
  6. Recálculo do Dividend Yield móvel de 12 meses (calculate_dividend_yield.py)
"""

import sys
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def run_pipeline():
    logging.info("=" * 60)
    logging.info("INICIANDO ROTINA DE ATUALIZAÇÃO FUNDAMENTALISTA (B3 & CVM)")
    logging.info("=" * 60)

    # 1. Limpeza preventiva de duplicidades
    try:
        logging.info(">>> PASSO 1/6: Verificando integridade e removendo duplicidades...")
        from clean_duplicates import clean_duplicate_securities
        clean_duplicate_securities()
        logging.info("[OK] Passo 1 concluído.")
    except Exception as e:
        logging.error(f"[AVISO] Falha no passo de limpeza: {e}")

    # 2. Cotações recentes dos últimos pregões
    try:
        # Busca últimos 15 dias de cotações para garantir pregões recentes
        start_date = (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d")
        logging.info(f">>> PASSO 2/6: Baixando cotações diárias desde {start_date}...")
        from import_prices import fetch_and_save_prices
        fetch_and_save_prices(start_date=start_date)
        logging.info("[OK] Passo 2 concluído.")
    except Exception as e:
        logging.error(f"[ERRO] Falha ao importar preços: {e}")
        sys.exit(1)

    # 3. Composição e P/L do IBOV
    try:
        logging.info(">>> PASSO 3/6: Atualizando composição e métricas do IBOV...")
        from fetch_ibov_composition import calculate_and_save_ibov_pe
        calculate_and_save_ibov_pe()
        logging.info("[OK] Passo 3 concluído.")
    except Exception as e:
        logging.warning(f"[AVISO] Falha ao buscar IBOV (pode estar fora do ar): {e}")

    # 4. Proventos e Splits recentes
    try:
        current_year = datetime.now().year
        logging.info(f">>> PASSO 4/6: Atualizando proventos e eventos societários ({current_year})...")
        from import_distributions import import_distributions_and_splits
        import_distributions_and_splits(current_year)
        logging.info("[OK] Passo 4 concluído.")
    except Exception as e:
        logging.warning(f"[AVISO] Falha ao importar proventos: {e}")

    # 5. Recálculo das Métricas Fundamentalistas
    try:
        logging.info(">>> PASSO 5/6: Recalculando métricas fundamentalistas (P/L, P/VP, ROE)...")
        from calculate_metrics import calculate_metrics
        calculate_metrics()
        logging.info("[OK] Passo 5 concluído.")
    except Exception as e:
        logging.error(f"[ERRO] Falha ao calcular métricas: {e}")
        sys.exit(1)

    # 6. Recálculo do Dividend Yield Móvel
    try:
        dy_start = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        logging.info(f">>> PASSO 6/6: Recalculando Dividend Yield móvel desde {dy_start}...")
        from calculate_dividend_yield import calculate_dividend_yield
        calculate_dividend_yield(start_date=dy_start)
        logging.info("[OK] Passo 6 concluído.")
    except Exception as e:
        logging.error(f"[ERRO] Falha ao calcular Dividend Yield: {e}")
        sys.exit(1)

    logging.info("=" * 60)
    logging.info("ROTINA DIÁRIA CONCLUÍDA COM SUCESSO!")
    logging.info("=" * 60)

if __name__ == "__main__":
    run_pipeline()
