"""
Script diário para buscar a composição oficial do Índice Bovespa (IBOV) na B3,
armazenar os pesos de cada ativo e calcular tanto o P/L Ponderado (apenas empresas lucrativas)
quanto o P/L Agregado Consolidado (incluindo prejuízos via Earnings Yield ponderado),
com suporte a mapa de tickers recentes/fusões e cálculo anualizado de lucros.

Salva o histórico contínuo nas tabelas 'index_metrics_history' e 'ibov_history' no PostgreSQL (Supabase).
"""

import os
import json
import base64
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Mapeamento de tickers que mudaram de código na B3 ou decorrentes de fusão
# Permite herdar o histórico de balanço e cotação oficial
TICKER_ALIAS = {
    "EMBJ3": "EMBR3",  # Embraer
    "MBRF3": "MRFG3",  # Marfrig
    "NATU3": "NTCO3",  # Natura
    "MOTV3": "CCRO3",  # Motiva (ex-CCR)
    "AXIA3": "ELET3",  # Axia Energia (ex-Eletrobras)
    "BRAV3": "RRRP3",  # Brava Energia (fusão 3R Petroleum + Enauta - anualizado)
}

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT") or 5432),
        connect_timeout=20
    )

def fetch_ibov_composition():
    payload = {
        "language": "pt-br",
        "pageNumber": 1,
        "pageSize": 150,
        "index": "IBOV",
        "segment": "1"
    }
    payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode()
    url = f"https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetPortfolioDay/{payload_b64}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[ERRO] Falha ao consultar endpoint da B3: {e}")
        return None, []

    header = data.get("header", {})
    date_str = header.get("date")
    portfolio_date = None
    if date_str:
        parts = date_str.split("/")
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2:
                year = "20" + year
            portfolio_date = f"{year}-{month}-{day}"
    
    if not portfolio_date:
        portfolio_date = datetime.now().strftime("%Y-%m-%d")

    results = data.get("results", [])
    parsed_items = []
    for item in results:
        cod = item.get("cod", "").strip()
        asset = item.get("asset", "").strip()
        share_type = item.get("type", "").strip()
        part_str = item.get("part", "0").replace(".", "").replace(",", ".")
        qty_str = item.get("theoricalQty", "0").replace(".", "")

        try:
            weight = float(part_str) / 100.0
        except ValueError:
            weight = 0.0

        try:
            qty = int(qty_str)
        except ValueError:
            qty = 0

        if cod:
            parsed_items.append({
                "ticker": cod,
                "asset": asset,
                "type": share_type,
                "weight": weight,
                "qty": qty
            })

    return portfolio_date, parsed_items

def calculate_and_save_ibov_pe():
    conn = get_db_connection()
    cur = conn.cursor()

    portfolio_date, items = fetch_ibov_composition()
    if not items:
        print("[ERRO] Nenhum item retornado da B3.")
        conn.close()
        return None

    print(f"[INFO] Composição IBOV obtida: {len(items)} ativos para a data de referência {portfolio_date}")

    # Lista todos os tickers da carteira e os possíveis aliases
    search_tickers = set([x["ticker"] for x in items] + list(TICKER_ALIAS.values()))

    cur.execute("""
        WITH latest_date AS (
            SELECT security_id, MAX(reference_date) as max_date
            FROM daily_metrics
            GROUP BY security_id
        )
        SELECT s.ticker, dm.close_price, dm.earnings_per_share_ttm, dm.price_earnings, dm.reference_date
        FROM daily_metrics dm
        JOIN latest_date ld ON dm.security_id = ld.security_id AND dm.reference_date = ld.max_date
        JOIN securities s ON dm.security_id = s.id
        WHERE s.ticker = ANY(%s)
    """, (list(search_tickers),))

    db_metrics = {}
    for r in cur.fetchall():
        db_metrics[r[0]] = {
            "price": float(r[1]) if r[1] is not None else None,
            "lpa": float(r[2]) if r[2] is not None else None,
            "pe": float(r[3]) if r[3] is not None else None,
            "ref_date": str(r[4])
        }

    # 1. P/L Clássico (apenas empresas lucrativas: 0 < P/L < 250)
    pos_pe_sum = 0.0
    pos_weight = 0.0
    valid_pes = []

    # 2. P/L Agregado Consolidado (inclui prejuízos via Earnings Yield ponderado)
    ey_sum = 0.0
    ey_weight = 0.0

    for it in items:
        tk = it["ticker"]
        target_tk = tk if tk in db_metrics else TICKER_ALIAS.get(tk, tk)
        metric = db_metrics.get(target_tk, {})

        price = metric.get("price")
        lpa = metric.get("lpa")
        pe = metric.get("pe")
        it["pe"] = pe

        # Acúmulo de Earnings Yield (com lucros e prejuízos)
        if price and lpa is not None and price > 0:
            earnings_yield = lpa / price
            ey_sum += earnings_yield * it["weight"]
            ey_weight += it["weight"]

        # Acúmulo de P/L clássico (apenas lucrativas)
        if pe is not None and 0 < pe < 250:
            pos_pe_sum += pe * it["weight"]
            pos_weight += it["weight"]
            valid_pes.append(pe)

        cur.execute("""
            INSERT INTO ibov_portfolio_history (
                portfolio_date, ticker, asset_name, share_type, weight, theorical_qty, pe_ratio
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (portfolio_date, ticker) DO UPDATE SET
                weight = EXCLUDED.weight,
                theorical_qty = EXCLUDED.theorical_qty,
                pe_ratio = EXCLUDED.pe_ratio,
                asset_name = EXCLUDED.asset_name,
                share_type = EXCLUDED.share_type;
        """, (
            portfolio_date,
            it["ticker"],
            it["asset"],
            it["type"],
            it["weight"],
            it["qty"],
            pe
        ))

    # Cálculos finais
    weighted_pe = (pos_pe_sum / pos_weight) if pos_weight > 0 else 0.0
    simple_pe = (sum(valid_pes) / len(valid_pes)) if valid_pes else 0.0

    valid_pes_sorted = sorted(valid_pes)
    mid = len(valid_pes_sorted) // 2
    median_pe = valid_pes_sorted[mid] if valid_pes_sorted else 0.0

    # P/L Agregado com Prejuízos = 1 / Earnings Yield Ponderado
    avg_earnings_yield = (ey_sum / ey_weight) if ey_weight > 0 else 0.0
    aggregated_pe = (1.0 / avg_earnings_yield) if avg_earnings_yield > 0 else 0.0

    # 1. Salva na tabela index_metrics_history
    cur.execute("""
        INSERT INTO index_metrics_history (
            index_name, reference_date, weighted_pe, simple_pe, median_pe, total_assets, covered_weight
        ) VALUES ('IBOV', %s, %s, %s, %s, %s, %s)
        ON CONFLICT (index_name, reference_date) DO UPDATE SET
            weighted_pe = EXCLUDED.weighted_pe,
            simple_pe = EXCLUDED.simple_pe,
            median_pe = EXCLUDED.median_pe,
            total_assets = EXCLUDED.total_assets,
            covered_weight = EXCLUDED.covered_weight;
    """, (
        portfolio_date,
        weighted_pe,
        simple_pe,
        median_pe,
        len(items),
        pos_weight
    ))

    # 2. Salva na tabela ibov_history com histórico de P/L clássico e com prejuízos
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ibov_history (
            reference_date DATE PRIMARY KEY,
            weighted_pe NUMERIC(10, 4) NOT NULL,
            simple_pe NUMERIC(10, 4),
            covered_weight_pct NUMERIC(6, 2),
            stocks_count INT,
            aggregated_pe_all NUMERIC(10, 4),
            earnings_yield_all NUMERIC(8, 4),
            total_coverage_pct NUMERIC(6, 2),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        INSERT INTO ibov_history (
            reference_date, weighted_pe, simple_pe, covered_weight_pct, stocks_count,
            aggregated_pe_all, earnings_yield_all, total_coverage_pct
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (reference_date) DO UPDATE SET
            weighted_pe = EXCLUDED.weighted_pe,
            simple_pe = EXCLUDED.simple_pe,
            covered_weight_pct = EXCLUDED.covered_weight_pct,
            stocks_count = EXCLUDED.stocks_count,
            aggregated_pe_all = EXCLUDED.aggregated_pe_all,
            earnings_yield_all = EXCLUDED.earnings_yield_all,
            total_coverage_pct = EXCLUDED.total_coverage_pct,
            created_at = NOW();

        -- Sincroniza tambem na tabela de serie temporal continua do dashboard
        CREATE TABLE IF NOT EXISTS ibov_daily_consolidated (
            reference_date DATE PRIMARY KEY,
            ibov_close NUMERIC(15, 2),
            pe_ratio NUMERIC(10, 4) NOT NULL,
            data_source VARCHAR(50) NOT NULL,
            is_interpolated BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        INSERT INTO ibov_daily_consolidated (reference_date, pe_ratio, data_source, is_interpolated)
        VALUES (%s, %s, 'OUR_METHODOLOGY_DAILY', FALSE)
        ON CONFLICT (reference_date) DO UPDATE SET
            pe_ratio = EXCLUDED.pe_ratio,
            data_source = EXCLUDED.data_source;
    """, (
        portfolio_date,
        weighted_pe,
        simple_pe,
        round(pos_weight * 100, 2),
        len(items),
        round(aggregated_pe, 2),
        round(avg_earnings_yield * 100, 2),
        round(ey_weight * 100, 2),
        portfolio_date,
        round(aggregated_pe, 2)
    ))

    conn.commit()
    conn.close()

    result = {
        "index": "IBOV",
        "date": portfolio_date,
        "weighted_pe": round(weighted_pe, 2),
        "aggregated_pe_all": round(aggregated_pe, 2),
        "earnings_yield_all_pct": round(avg_earnings_yield * 100, 2),
        "simple_pe": round(simple_pe, 2),
        "median_pe": round(median_pe, 2),
        "total_assets": len(items),
        "covered_weight_pct": round(pos_weight * 100, 2),
        "total_coverage_pct": round(ey_weight * 100, 2)
    }

    with open("ibov_metric.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\n[SUCESSO] Cálculo do IBOV finalizado e persistido no histórico:")
    print(f" -> Data: {result['date']}")
    print(f" -> P/L Ponderado (Positivos): {result['weighted_pe']}x (Cobertura: {result['covered_weight_pct']}%)")
    print(f" -> P/L Agregado (Com Prejuízos): {result['aggregated_pe_all']}x (Cobertura Total: {result['total_coverage_pct']}%)")
    print(f" -> Earnings Yield da Bolsa: {result['earnings_yield_all_pct']}%")
    print(f" -> Gravado em: index_metrics_history e ibov_history no Supabase")

    return result

if __name__ == "__main__":
    calculate_and_save_ibov_pe()
