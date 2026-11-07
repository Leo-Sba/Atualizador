"""
Script diário para buscar a composição oficial do Índice Bovespa (IBOV) na B3,
armazenar os pesos de cada ativo e calcular o P/L Médio (ponderado e simples) do índice.

Pode ser executado diretamente ou agendado no cron / GitHub Actions diariamente.
"""

import os
import json
import base64
import requests
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        connect_timeout=20
    )

def fetch_ibov_composition():
    """
    Busca a composição oficial da carteira do IBOV direto do endpoint público da B3.
    """
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
    # Data no formato dd/mm/yy ou dd/mm/yyyy
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

    tickers = [x["ticker"] for x in items]

    # Busca o P/L mais recente de cada ativo da carteira
    cur.execute("""
        WITH latest_date AS (
            SELECT security_id, MAX(reference_date) as max_date
            FROM daily_metrics
            GROUP BY security_id
        )
        SELECT s.ticker, dm.price_earnings, dm.reference_date
        FROM daily_metrics dm
        JOIN latest_date ld ON dm.security_id = ld.security_id AND dm.reference_date = ld.max_date
        JOIN securities s ON dm.security_id = s.id
        WHERE s.ticker = ANY(%s)
    """, (tickers,))

    db_metrics = {r[0]: (float(r[1]) if r[1] is not None else None, str(r[2])) for r in cur.fetchall()}

    weighted_pe_sum = 0.0
    covered_weight = 0.0
    valid_pes = []

    # Salva cada ativo da carteira na tabela ibov_portfolio_history
    for it in items:
        tk = it["ticker"]
        pe = db_metrics.get(tk, (None, None))[0]
        it["pe"] = pe

        if pe is not None and 0 < pe < 250:  # Filtra lucros positivos e anomalias extremas
            weighted_pe_sum += pe * it["weight"]
            covered_weight += it["weight"]
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

    weighted_pe = (weighted_pe_sum / covered_weight) if covered_weight > 0 else 0.0
    simple_pe = (sum(valid_pes) / len(valid_pes)) if valid_pes else 0.0
    
    valid_pes_sorted = sorted(valid_pes)
    mid = len(valid_pes_sorted) // 2
    median_pe = valid_pes_sorted[mid] if valid_pes_sorted else 0.0

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
        covered_weight
    ))

    conn.commit()
    conn.close()

    result = {
        "index": "IBOV",
        "date": portfolio_date,
        "weighted_pe": round(weighted_pe, 2),
        "simple_pe": round(simple_pe, 2),
        "median_pe": round(median_pe, 2),
        "total_assets": len(items),
        "covered_weight_pct": round(covered_weight * 100, 2)
    }

    # Salva um snapshot json para uso fácil no dashboard
    with open("ibov_metric.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\n[SUCESSO] Cálculo do IBOV finalizado:")
    print(f" -> Data: {result['date']}")
    print(f" -> P/L Médio Ponderado: {result['weighted_pe']}x")
    print(f" -> P/L Médio Simples: {result['simple_pe']}x")
    print(f" -> Cobertura da carteira: {result['covered_weight_pct']}%")

    return result

if __name__ == "__main__":
    calculate_and_save_ibov_pe()
