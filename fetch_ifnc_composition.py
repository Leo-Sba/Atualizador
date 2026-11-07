"""
fetch_ifnc_composition.py
Busca a composição oficial da carteira do Índice Financeiro (IFNC) na B3,
aplica a regra de cap de posição máxima de 20% por ativo (com redistribuição proporcional),
calcula o P/L ponderado e P/L agregado consolidado via Earnings Yield,
e persiste os resultados nas tabelas 'ifnc_portfolio_history', 'ifnc_history'
e 'ifnc_daily_consolidated' no Supabase (PostgreSQL).
"""

import os
import json
import logging
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

load_dotenv()

B3_IFNC_URL = "https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/eyJpbmRleCI6IklGTkMiLCJsYW5ndWFnZSI6InB0LWJyIn0="

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        connect_timeout=25
    )

def apply_weight_cap(raw_items, max_cap=0.20):
    """
    Aplica o teto de 20% por ativo na carteira:
    Se algum ativo ultrapassar 20%, seu peso é travado em 20% e o excedente
    é redistribuído proporcionalmente entre os demais ativos elegíveis.
    """
    weights = {item["cod"]: item["weight"] for item in raw_items}
    
    # Processo iterativo de redistribuição
    while True:
        excess = 0.0
        capped_keys = set()
        uncapped_sum = 0.0
        
        for k, w in weights.items():
            if w > max_cap + 1e-7:
                excess += (w - max_cap)
                weights[k] = max_cap
                capped_keys.add(k)
            else:
                uncapped_sum += w
                
        if excess <= 1e-7 or uncapped_sum == 0:
            break
            
        # Redistribui proporcionalmente para quem não foi travado
        for k in weights:
            if k not in capped_keys:
                weights[k] += excess * (weights[k] / uncapped_sum)
                
    # Normalização final para somar exatamente 1.0 (100%)
    total_w = sum(weights.values())
    if total_w > 0:
        for k in weights:
            weights[k] = weights[k] / total_w
            
    for item in raw_items:
        item["capped_weight"] = weights[item["cod"]]
        
    return raw_items

def fetch_and_calculate_ifnc():
    logging.info("Buscando composição oficial do IFNC na B3...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*"
    }
    
    try:
        resp = requests.get(B3_IFNC_URL, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logging.error(f"Erro ao acessar API da B3 para o IFNC: {e}")
        return None

    results = data.get("results", [])
    header = data.get("header", {})
    date_str = header.get("date")  # DD/MM/YY
    
    if date_str:
        try:
            portfolio_date = datetime.strptime(date_str, "%d/%m/%y").strftime("%Y-%m-%d")
        except Exception:
            portfolio_date = datetime.now().strftime("%Y-%m-%d")
    else:
        portfolio_date = datetime.now().strftime("%Y-%m-%d")

    logging.info(f"Composição IFNC obtida com {len(results)} ativos para a data: {portfolio_date}")

    raw_items = []
    for item in results:
        cod = item.get("cod")
        asset = item.get("asset")
        stype = item.get("type", "")
        part_str = item.get("part", "0").replace(".", "").replace(",", ".")
        qty_str = item.get("theoricalQty", "0").replace(".", "").replace(",", ".")
        
        try:
            weight = float(part_str) / 100.0
            theorical_qty = float(qty_str)
        except ValueError:
            continue

        raw_items.append({
            "cod": cod,
            "asset": asset,
            "type": stype,
            "weight": weight,
            "theorical_qty": theorical_qty
        })

    # Aplica o teto de 20%
    capped_items = apply_weight_cap(raw_items, max_cap=0.20)

    # Conectar ao banco para buscar P/L mais recente de cada ativo
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ifnc_portfolio_history (
            id SERIAL PRIMARY KEY,
            portfolio_date DATE NOT NULL,
            ticker VARCHAR(10) NOT NULL,
            asset_name VARCHAR(100),
            share_type VARCHAR(20),
            raw_weight NUMERIC(10, 6) NOT NULL,
            capped_weight NUMERIC(10, 6) NOT NULL,
            theorical_qty NUMERIC(20, 2),
            pe_ratio NUMERIC(10, 4),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE (portfolio_date, ticker)
        );
    """)

    # Obter P/L recente de cada ativo
    tickers = [i["cod"] for i in capped_items]
    cur.execute("""
        SELECT DISTINCT ON (s.ticker) s.ticker, dm.price_earnings, dm.reference_date
        FROM securities s
        JOIN daily_metrics dm ON s.id = dm.security_id
        WHERE s.ticker = ANY(%s) AND dm.price_earnings IS NOT NULL
        ORDER BY s.ticker, dm.reference_date DESC;
    """, (tickers,))
    db_metrics = {r[0]: float(r[1]) for r in cur.fetchall()}

    # Inserir no histórico de carteira
    for item in capped_items:
        t = item["cod"]
        pe = db_metrics.get(t)
        cur.execute("""
            INSERT INTO ifnc_portfolio_history (
                portfolio_date, ticker, asset_name, share_type,
                raw_weight, capped_weight, theorical_qty, pe_ratio
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (portfolio_date, ticker) DO UPDATE SET
                raw_weight = EXCLUDED.raw_weight,
                capped_weight = EXCLUDED.capped_weight,
                theorical_qty = EXCLUDED.theorical_qty,
                pe_ratio = EXCLUDED.pe_ratio,
                created_at = NOW();
        """, (
            portfolio_date,
            t,
            item["asset"],
            item["type"],
            item["weight"],
            item["capped_weight"],
            item["theorical_qty"],
            pe
        ))

    # Cálculo dos índices agregados
    # 1. P/L Ponderado tradicional (empresas positivas)
    pos_items = [i for i in capped_items if db_metrics.get(i["cod"]) is not None and db_metrics[i["cod"]] > 0]
    pos_weight = sum(i["capped_weight"] for i in pos_items)
    
    if pos_weight > 0:
        weighted_pe = sum(db_metrics[i["cod"]] * i["capped_weight"] for i in pos_items) / pos_weight
    else:
        weighted_pe = 0.0

    # 2. P/L Agregado Consolidado via Earnings Yield (E/P ponderado)
    ey_items = [i for i in capped_items if db_metrics.get(i["cod"]) is not None and db_metrics[i["cod"]] != 0]
    ey_weight = sum(i["capped_weight"] for i in ey_items)
    
    if ey_weight > 0:
        avg_earnings_yield = sum((1.0 / db_metrics[i["cod"]]) * i["capped_weight"] for i in ey_items) / ey_weight
        aggregated_pe = (1.0 / avg_earnings_yield) if avg_earnings_yield > 0 else None
    else:
        avg_earnings_yield = 0.0
        aggregated_pe = None

    simple_pe = (sum(db_metrics[i["cod"]] for i in pos_items) / len(pos_items)) if pos_items else 0.0

    # Obter pontuação recente do IFNC (ou ETF FIND11 / IFNC.SA)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ifnc_history (
            reference_date DATE PRIMARY KEY,
            weighted_pe NUMERIC(10, 4) NOT NULL,
            simple_pe NUMERIC(10, 4),
            aggregated_pe_all NUMERIC(10, 4),
            earnings_yield_all NUMERIC(10, 4),
            covered_weight_pct NUMERIC(6, 2),
            total_coverage_pct NUMERIC(6, 2),
            stocks_count INT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        INSERT INTO ifnc_history (
            reference_date, weighted_pe, simple_pe, aggregated_pe_all, earnings_yield_all,
            covered_weight_pct, total_coverage_pct, stocks_count
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (reference_date) DO UPDATE SET
            weighted_pe = EXCLUDED.weighted_pe,
            simple_pe = EXCLUDED.simple_pe,
            aggregated_pe_all = EXCLUDED.aggregated_pe_all,
            earnings_yield_all = EXCLUDED.earnings_yield_all,
            covered_weight_pct = EXCLUDED.covered_weight_pct,
            total_coverage_pct = EXCLUDED.total_coverage_pct,
            stocks_count = EXCLUDED.stocks_count,
            created_at = NOW();

        CREATE TABLE IF NOT EXISTS ifnc_daily_consolidated (
            reference_date DATE PRIMARY KEY,
            ifnc_close NUMERIC(15, 2),
            pe_ratio NUMERIC(10, 4) NOT NULL,
            data_source VARCHAR(50) NOT NULL,
            is_interpolated BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        INSERT INTO ifnc_daily_consolidated (reference_date, pe_ratio, data_source, is_interpolated)
        VALUES (%s, %s, 'OUR_METHODOLOGY_DAILY', FALSE)
        ON CONFLICT (reference_date) DO UPDATE SET
            pe_ratio = EXCLUDED.pe_ratio,
            data_source = EXCLUDED.data_source;
    """, (
        portfolio_date,
        weighted_pe,
        simple_pe,
        round(aggregated_pe, 4) if aggregated_pe else None,
        round(avg_earnings_yield * 100, 4) if avg_earnings_yield else None,
        round(pos_weight * 100, 2),
        round(ey_weight * 100, 2),
        len(capped_items),
        portfolio_date,
        round(aggregated_pe or weighted_pe, 4)
    ))

    conn.commit()
    conn.close()

    logging.info(f"[SUCESSO] IFNC Calculado para {portfolio_date}:")
    logging.info(f" -> Cobertura da carteira: {pos_weight*100:.2f}% ({len(pos_items)} de {len(capped_items)} ativos)")
    logging.info(f" -> P/L Ponderado (Positivos): {weighted_pe:.2f}x")
    logging.info(f" -> P/L Agregado Consolidado: {aggregated_pe:.2f}x (Earnings Yield: {avg_earnings_yield*100:.2f}%)")
    
    return {
        "index": "IFNC",
        "date": portfolio_date,
        "weighted_pe": round(weighted_pe, 2),
        "aggregated_pe_all": round(aggregated_pe, 2) if aggregated_pe else None,
        "earnings_yield_all_pct": round(avg_earnings_yield * 100, 2) if avg_earnings_yield else None,
        "covered_weight_pct": round(pos_weight * 100, 2),
        "total_assets": len(capped_items)
    }

if __name__ == "__main__":
    res = fetch_and_calculate_ifnc()
    if res:
        with open("ifnc_metric.json", "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
        print("ifnc_metric.json gerado com sucesso!")
