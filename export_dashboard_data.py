"""
export_dashboard_data.py
Gera o arquivo dashboard_data.json consolidado a partir do PostgreSQL (Supabase),
garantindo SEMPRE a inclusão dos 3 índices fundamentais:
1. IBOV (Ibovespa com pontuação real em pontos e P/L Agregado Consolidado oficial)
2. IFNC (Índice Financeiro B3 baseado no FIND11 em R$)
3. SEGUROS (Sub-índice sintético Base 100 de BBSE3, CXSE3 e PSSA3 com pesos iguais)

Em seguida, aciona a regeneração de dashboard.html.
"""

import os
import json
import logging
import psycopg2
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

load_dotenv()

def build_seguros_index(data):
    """
    Constrói dinamicamente o índice SEGUROS (Base 100 ponderada com pesos iguais)
    a partir das séries diárias de BBSE3, CXSE3 e PSSA3 presentes em data.
    """
    bbse = data.get("BBSE3")
    cxse = data.get("CXSE3")
    pssa = data.get("PSSA3")
    
    if not (bbse and cxse and pssa):
        logging.warning("Não foi possível construir o índice SEGUROS: ações constituintes ausentes.")
        return None

    common_dates = sorted(list(set(bbse["dates"]) & set(cxse["dates"]) & set(pssa["dates"])))
    if not common_dates:
        return None

    bbse_prices = dict(zip(bbse["dates"], bbse["prices"]))
    cxse_prices = dict(zip(cxse["dates"], cxse["prices"]))
    pssa_prices = dict(zip(pssa["dates"], pssa["prices"]))

    bbse_pl = dict(zip(bbse["dates"], bbse["pl"]))
    cxse_pl = dict(zip(cxse["dates"], cxse["pl"]))
    pssa_pl = dict(zip(pssa["dates"], pssa["pl"]))

    b0 = bbse_prices[common_dates[0]]
    c0 = cxse_prices[common_dates[0]]
    p0 = pssa_prices[common_dates[0]]

    synth_prices = []
    synth_pls = []

    for dt in common_dates:
        # Preço sintético Base 100
        ret_b = bbse_prices[dt] / b0
        ret_c = cxse_prices[dt] / c0
        ret_p = pssa_prices[dt] / p0
        synth_prices.append(round(100.0 * (ret_b + ret_c + ret_p) / 3.0, 2))

        # P/L Agregado Consolidado via média harmônica (Earnings Yield ponderado)
        b_pe = bbse_pl.get(dt)
        c_pe = cxse_pl.get(dt)
        p_pe = pssa_pl.get(dt)

        if b_pe and c_pe and p_pe and b_pe > 0 and c_pe > 0 and p_pe > 0:
            synth_pe = 3.0 / ((1.0 / b_pe) + (1.0 / c_pe) + (1.0 / p_pe))
            synth_pls.append(round(synth_pe, 2))
        else:
            synth_pls.append(None)

    return {
        "company": "Índice Seguros (BBSE3, CXSE3, PSSA3)",
        "dates": common_dates,
        "prices": synth_prices,
        "pl": synth_pls,
        "pvp": [None] * len(common_dates),
        "roe": [None] * len(common_dates),
        "dy": [None] * len(common_dates)
    }

def export_dashboard_data():
    logging.info("Conectando ao banco de dados para exportar metricas...")
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=25
    )
    cur = conn.cursor()

    query = """
        SELECT 
            s.ticker, 
            c.trading_name, 
            dm.reference_date, 
            dm.close_price, 
            dm.price_earnings, 
            dm.price_to_book, 
            dm.roe_ttm, 
            dm.dividend_yield_ttm
        FROM daily_metrics dm
        JOIN securities s ON dm.security_id = s.id
        JOIN companies c ON s.company_id = c.id
        WHERE dm.reference_date >= '2015-01-01'
        ORDER BY s.ticker, dm.reference_date ASC;
    """

    logging.info("Executando consulta de series historicas de acoes...")
    cur.execute(query)
    rows = cur.fetchall()
    logging.info(f"Total de registros de acoes recuperados: {len(rows)}")

    data = {}
    from clean_duplicates import IGNORED_INACTIVE_TICKERS
    from datetime import datetime, timedelta
    for ticker, comp_name, dt, price, pe, pb, roe, dy in rows:
        if ticker in IGNORED_INACTIVE_TICKERS:
            continue
        if ticker not in data:
            data[ticker] = {
                "company": comp_name,
                "dates": [],
                "prices": [],
                "pl": [],
                "pvp": [],
                "roe": [],
                "dy": []
            }
        data[ticker]["dates"].append(str(dt))
        data[ticker]["prices"].append(float(price) if price is not None else None)
        data[ticker]["pl"].append(float(pe) if pe is not None else None)
        data[ticker]["pvp"].append(float(pb) if pb is not None else None)
        data[ticker]["roe"].append(float(roe * 100) if roe is not None else None)
        data[ticker]["dy"].append(float(dy) if dy is not None else None)

    # Filtrar automaticamente qualquer ação sem negociação nos últimos 90 dias em relação ao pregão mais recente
    if data:
        max_dt_str = max(v["dates"][-1] for v in data.values() if v.get("dates"))
        cutoff_90_str = (datetime.strptime(max_dt_str, "%Y-%m-%d") - timedelta(days=90)).strftime("%Y-%m-%d")
        inactive_found = [t for t, v in data.items() if not v.get("dates") or v["dates"][-1] < cutoff_90_str]
        for t in inactive_found:
            logging.info(f"Ignorando ativo sem negociação recente (> 90 dias): {t}")
            del data[t]

    active_stock_tickers = set(data.keys())

    # 1. Carregar IBOV Consolidado Oficial
    try:
        cur.execute("SELECT reference_date, ibov_close, pe_ratio FROM ibov_daily_consolidated ORDER BY reference_date ASC;")
        ibov_rows = cur.fetchall()
        if ibov_rows:
            ibov_dates = [str(r[0]) for r in ibov_rows]
            ibov_prices = [float(r[1]) if r[1] is not None else None for r in ibov_rows]
            ibov_pls = [float(r[2]) if r[2] is not None else None for r in ibov_rows]
            data["IBOV"] = {
                "company": "Índice Bovespa (^BVSP)",
                "dates": ibov_dates,
                "prices": ibov_prices,
                "pl": ibov_pls,
                "pvp": [None] * len(ibov_dates),
                "roe": [None] * len(ibov_dates),
                "dy": [None] * len(ibov_dates)
            }
            logging.info(f"[OK] IBOV inserido com {len(ibov_dates)} pregões.")
    except Exception as e:
        logging.error(f"Erro ao carregar IBOV: {e}")

    # 2. Carregar IFNC Consolidado Oficial
    try:
        cur.execute("SELECT reference_date, ifnc_close, pe_ratio FROM ifnc_daily_consolidated ORDER BY reference_date ASC;")
        ifnc_rows = cur.fetchall()
        if ifnc_rows:
            ifnc_dates = [str(r[0]) for r in ifnc_rows]
            ifnc_prices = [float(r[1]) if r[1] is not None else None for r in ifnc_rows]
            ifnc_pls = [float(r[2]) if r[2] is not None else None for r in ifnc_rows]
            data["IFNC"] = {
                "company": "Índice Financeiro B3 (FIND11)",
                "dates": ifnc_dates,
                "prices": ifnc_prices,
                "pl": ifnc_pls,
                "pvp": [None] * len(ifnc_dates),
                "roe": [None] * len(ifnc_dates),
                "dy": [None] * len(ifnc_dates)
            }
            logging.info(f"[OK] IFNC inserido com {len(ifnc_dates)} pregões.")
    except Exception as e:
        logging.error(f"Erro ao carregar IFNC: {e}")

    # 2.5 Sincronizar Histórico de Eventos Societários B3 (Splits, Inplits, Bonificações, Cisões)
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS b3_corporate_events_cache (
                ticker TEXT PRIMARY KEY,
                company TEXT,
                splits JSONB DEFAULT '[]'::jsonb,
                inplits JSONB DEFAULT '[]'::jsonb,
                bonuses JSONB DEFAULT '[]'::jsonb,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.execute("SELECT ticker, company, splits, inplits, bonuses FROM b3_corporate_events_cache;")
        ev_rows = cur.fetchall()
        events_path = "events_data.json"
        local_events = {}
        if os.path.exists(events_path):
            with open(events_path, "r", encoding="utf-8") as f:
                local_events = json.load(f)

        if ev_rows:
            for t_ev, comp_ev, sp, inp, bon in ev_rows:
                if t_ev in IGNORED_INACTIVE_TICKERS or t_ev not in active_stock_tickers:
                    continue
                if t_ev not in local_events:
                    local_events[t_ev] = {"ticker": t_ev, "company": comp_ev, "dividends": []}
                local_events[t_ev]["company"] = comp_ev or local_events[t_ev].get("company", t_ev)
                local_events[t_ev]["splits"] = sp if sp is not None else []
                local_events[t_ev]["inplits"] = inp if inp is not None else []
                local_events[t_ev]["bonuses"] = bon if bon is not None else []
            # Remover de local_events quaisquer ativos deslistados/inativos
            for k_ev in list(local_events.keys()):
                if k_ev in IGNORED_INACTIVE_TICKERS or k_ev not in active_stock_tickers:
                    del local_events[k_ev]
            with open(events_path, "w", encoding="utf-8") as f:
                json.dump(local_events, f, ensure_ascii=False)
            logging.info(f"[OK] Eventos societários B3 sincronizados do Supabase ({len(local_events)} ativos ativos).")
        elif local_events:
            from fetch_b3_events import sync_events_to_supabase
            sync_events_to_supabase(local_events)
    except Exception as e:
        logging.warning(f"Aviso ao sincronizar b3_corporate_events_cache: {e}")

    # 2.6 Sincronizar Snapshot Macro & Juros (Copom, Focus, Curva Tesouro Direto) do Supabase
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS macro_data_cache (
                cache_key TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                payload_hash TEXT,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        conn.commit()
        cur.execute("SELECT payload FROM macro_data_cache WHERE cache_key = 'macro_snapshot';")
        macro_row = cur.fetchone()
        if macro_row and isinstance(macro_row[0], dict):
            with open("macro_data.json", "w", encoding="utf-8") as f:
                json.dump(macro_row[0], f, ensure_ascii=False, separators=(",", ":"))
            logging.info("[OK] macro_data.json sincronizado do Supabase (macro_data_cache).")
        elif not os.path.exists("macro_data.json"):
            logging.info("macro_data_cache vazio; executando coleta inicial via fetch_macro_data...")
            from fetch_macro_data import run_macro_collection
            run_macro_collection()
    except Exception as e:
        logging.warning(f"Aviso ao sincronizar macro_data_cache: {e}")

    conn.close()

    # 3. Gerar Índice SEGUROS Sintético
    seguros_data = build_seguros_index(data)
    if seguros_data:
        data["SEGUROS"] = seguros_data
        logging.info(f"[OK] SEGUROS inserido com {len(seguros_data['dates'])} pregões.")

    logging.info(f"Gravando dashboard_data.json com {len(data)} ativos/índices...")
    with open("dashboard_data.json", "w", encoding="utf-8") as f:
        json.dump(data, f)

    logging.info("[OK] dashboard_data.json atualizado com sucesso!")

    # 4. Executar / Sincronizar detecção de anomalias (anomalies_data.json)
    try:
        import subprocess
        import sys
        logging.info("Sincronizando auditoria de anomalias (detect_anomalies.py)...")
        subprocess.run([sys.executable, "detect_anomalies.py"], check=True)
        logging.info("[OK] anomalies_data.json sincronizado com sucesso!")
    except Exception as e:
        logging.warning(f"Aviso ao executar detect_anomalies.py: {e}")

    # Regenerar dashboard.html
    import subprocess
    import sys
    logging.info("Regenerando dashboard.html...")
    subprocess.run([sys.executable, "generate_dashboard.py"], check=True)
    logging.info("[OK] dashboard.html gerado com sucesso!")

if __name__ == "__main__":
    export_dashboard_data()
