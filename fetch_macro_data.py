"""
fetch_macro_data.py
Coletor oficial de dados Macro & Juros para o Dashboard Fundamentalista B3/CVM:
1. Séries do Banco Central (SGS): Selic Meta (432), CDI (4389), IPCA 12M (13522) e IPCA Mensal (433).
2. Histórico dinâmico das reuniões do Copom (2026 e 2027) preenchido via SGS 432.
3. Boletim Focus (API Olinda/BCB): IPCA, Selic, PIB Total, Câmbio e IGP-M.
4. Curva de Juros do Tesouro Direto (Prefixado e IPCA+) via Tesouro Transparente (CSV oficial, últimos 45 pregões).

Salva o snapshot consolidado em Supabase (tabela macro_data_cache) e grava macro_data.json localmente,
detectando se houve alteração real nos dados de mercado (para deploys intradiários inteligentes).
"""

import os
import io
import csv
import json
import hashlib
import logging
import datetime as dt
from urllib.parse import quote
import requests
import psycopg2
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BRT = dt.timezone(dt.timedelta(hours=-3))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept": "application/json, text/csv, */*",
}

CSV_TESOURO_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "df56aa42-484a-4a59-8184-7676580c81e3/resource/"
    "796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv"
)

# Calendários oficiais divulgados pelo Banco Central do Brasil (Copom) e Federal Reserve (FOMC)
COPOM_DATES = {
    2026: [
        "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
        "2026-08-05", "2026-09-16", "2026-11-04", "2026-12-09",
    ],
    2027: [
        "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-16",
        "2027-08-04", "2027-09-22", "2027-10-27", "2027-12-08",
    ],
}

FOMC_DATES = [
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-17",
    "2026-07-29", "2026-09-16", "2026-10-28", "2026-12-09",
    "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09",
    "2027-07-28", "2027-09-15", "2027-10-27", "2027-12-08",
]

FOCUS_INDICATORS = ["IPCA", "Selic", "PIB Total", "Câmbio", "IGP-M"]


def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        connect_timeout=20,
    )


def ensure_macro_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS macro_data_cache (
                cache_key TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                payload_hash TEXT,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        conn.commit()


def load_existing_snapshot(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT payload, payload_hash FROM macro_data_cache WHERE cache_key = 'macro_snapshot';")
        row = cur.fetchone()
        if row and isinstance(row[0], dict):
            return row[0], row[1]
    if os.path.exists("macro_data.json"):
        try:
            with open("macro_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            return data, None
        except Exception:
            pass
    return {}, None


def fetch_sgs_last(series_code, count=1, timeout=12):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados/ultimos/{count}?formato=json"
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    rows = r.json()
    return [{"date": item["data"], "value": float(str(item["valor"]).replace(",", "."))} for item in rows]


def fetch_sgs_range(series_code, start_br, end_br, timeout=15):
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados"
        f"?formato=json&dataInicial={start_br}&dataFinal={end_br}"
    )
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return {item["data"]: float(str(item["valor"]).replace(",", ".")) for item in r.json()}


def format_copom_label(rate, prev_rate):
    rate_str = f"{rate:.2f}".replace(".", ",") + "%"
    if prev_rate is None:
        return rate_str
    diff = round(rate - prev_rate, 2)
    if abs(diff) < 1e-6:
        return f"{rate_str} (manutenção)"
    sign = "+" if diff > 0 else "−"
    return f"{rate_str} ({sign}{abs(diff):.2f}".replace(".", ",") + ")"


def build_copom_and_indicators(today_brt, existing_snapshot):
    prev_indicators = existing_snapshot.get("indicators") or {}
    indicators = dict(prev_indicators)

    # 1. Selic histórica (2026 até amanhã para capturar decisões pós-18h30 em D+1)
    end_dt = today_brt + dt.timedelta(days=2)
    sgs_selic_map = {}
    try:
        sgs_selic_map = fetch_sgs_range(432, "01/01/2026", end_dt.strftime("%d/%m/%Y"))
        today_key = today_brt.strftime("%d/%m/%Y")
        # Selecionar o registro mais recente com data <= hoje
        valid_selic = []
        for d_str, val in sgs_selic_map.items():
            d_obj = dt.datetime.strptime(d_str, "%d/%m/%Y").date()
            if d_obj <= today_brt:
                valid_selic.append((d_obj, val))
        if valid_selic:
            valid_selic.sort(key=lambda x: x[0])
            last_d, last_val = valid_selic[-1]
            indicators["selic"] = {
                "value": round(last_val, 2),
                "date": last_d.strftime("%d/%m/%Y"),
                "src": "BCB · SGS 432",
            }
            logging.info(f"[OK] Selic Meta SGS 432: {last_val:.2f}% ({last_d.strftime('%d/%m/%Y')})")
    except Exception as e:
        logging.warning(f"[AVISO] Falha ao buscar Selic SGS 432: {e}")

    # 2. CDI (4389), IPCA 12M (13522), IPCA Mensal (433)
    for code, key, is_monthly, src in [
        (4389, "cdi", False, "BCB · SGS 4389"),
        (13522, "ipca12m", True, "IBGE via BCB · SGS 13522"),
        (433, "ipcaMes", True, "IBGE via BCB · SGS 433"),
    ]:
        try:
            rows = fetch_sgs_last(code, count=1)
            if rows:
                d_str = rows[0]["date"][3:] if is_monthly else rows[0]["date"]
                indicators[key] = {"value": round(rows[0]["value"], 2), "date": d_str, "src": src}
                logging.info(f"[OK] {key}: {rows[0]['value']:.2f}% ({d_str})")
        except Exception as e:
            logging.warning(f"[AVISO] Falha ao buscar {key} (SGS {code}): {e}")

    selic_v = (indicators.get("selic") or {}).get("value")
    ipca_v = (indicators.get("ipca12m") or {}).get("value")
    if selic_v is not None and ipca_v is not None and (1 + ipca_v / 100.0) > 0:
        indicators["realRate"] = round((((1 + selic_v / 100.0) / (1 + ipca_v / 100.0)) - 1) * 100.0, 2)

    # 3. Reuniões do Copom preenchidas dinamicamente via SGS 432
    existing_copom = existing_snapshot.get("copom_meetings") or {}
    copom_meetings = {}
    for year, dates in COPOM_DATES.items():
        y_str = str(year)
        prev_entries = {e["date"]: e for e in existing_copom.get(y_str, []) if isinstance(e, dict) and e.get("date")}
        year_list = []
        for idx, iso_d in enumerate(dates):
            m_dt = dt.date.fromisoformat(iso_d)
            rate = None
            label = None
            if m_dt <= today_brt:
                day_after_key = (m_dt + dt.timedelta(days=1)).strftime("%d/%m/%Y")
                day_key = m_dt.strftime("%d/%m/%Y")
                rate_after = sgs_selic_map.get(day_after_key)
                rate_before = sgs_selic_map.get(day_key)
                if rate_after is not None:
                    rate = round(rate_after, 2)
                    label = format_copom_label(rate, rate_before)
                elif iso_d in prev_entries and prev_entries[iso_d].get("rate") is not None:
                    rate = prev_entries[iso_d]["rate"]
                    label = prev_entries[iso_d].get("label")
            year_list.append({"date": iso_d, "rate": rate, "label": label})
        copom_meetings[y_str] = year_list

    return indicators, copom_meetings


def fetch_focus_snapshot(today_brt, existing_snapshot):
    years = [str(today_brt.year + i) for i in range(4)]
    out = dict(existing_snapshot.get("focus") or {})
    updated_any = False

    for ind in FOCUS_INDICATORS:
        flt = quote(f"Indicador eq '{ind}' and baseCalculo eq 0")
        sel = quote("Indicador,IndicadorDetalhe,Data,DataReferencia,Mediana,numeroRespondentes")
        url = (
            "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/"
            f"ExpectativasMercadoAnuais?$top=50&$filter={flt}&$orderby=Data%20desc&$format=json&$select={sel}"
        )
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            rows = [
                row for row in (r.json().get("value") or [])
                if not row.get("IndicadorDetalhe") or row.get("IndicadorDetalhe") == "null"
            ]
            latest_date = rows[0]["Data"] if rows else None
            by_year = {}
            prev_by_year = {}
            for yr in years:
                same_y = [row for row in rows if str(row.get("DataReferencia")) == yr]
                if same_y:
                    by_year[yr] = round(float(same_y[0]["Mediana"]), 2)
                    prev = next((row for row in same_y if row["Data"] < same_y[0]["Data"]), None)
                    if prev:
                        prev_by_year[yr] = round(float(prev["Mediana"]), 2)
            out[ind] = {"date": latest_date, "byYear": by_year, "prevByYear": prev_by_year}
            updated_any = True
        except Exception as e:
            logging.warning(f"[AVISO] Falha ao buscar Focus '{ind}': {e}")

    if updated_any:
        logging.info("[OK] Boletim Focus (Olinda/BCB) atualizado.")
    return out


def classify_bond_type(title):
    low = (title or "").lower()
    if "renda+" in low or "educa+" in low or "semestrais" in low:
        return None
    if "prefixado" in low:
        return "pre"
    if "ipca" in low:
        return "ipca"
    return None


def fetch_tesouro_curve(today_brt, existing_snapshot):
    prev_curva = existing_snapshot.get("curva") or {}
    hist = dict(prev_curva.get("historico") or {})
    cutoff = today_brt - dt.timedelta(days=70)
    fontes = list(prev_curva.get("fontes") or [])

    try:
        logging.info("Baixando CSV oficial do Tesouro Transparente (Curva de Juros)...")
        r = requests.get(CSV_TESOURO_URL, headers=HEADERS, timeout=90)
        r.raise_for_status()
        text = r.content.decode("latin-1")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")

        parsed = {}
        seen_points = set()
        for row in reader:
            try:
                base_dt = dt.datetime.strptime(row["Data Base"], "%d/%m/%Y").date()
            except (KeyError, ValueError):
                continue
            if base_dt < cutoff:
                continue
            kind = classify_bond_type(row.get("Tipo Titulo", ""))
            if not kind:
                continue
            try:
                venc_dt = dt.datetime.strptime(row["Data Vencimento"], "%d/%m/%Y").date()
                taxa = float(row["Taxa Compra Manha"].replace(",", "."))
            except (KeyError, ValueError):
                continue

            anos = (venc_dt - base_dt).days / 365.25
            if anos <= 0.05:
                continue

            base_iso = base_dt.isoformat()
            venc_iso = venc_dt.isoformat()
            dedup_key = (base_iso, kind, venc_iso)
            if dedup_key in seen_points:
                continue
            seen_points.add(dedup_key)

            parsed.setdefault(base_iso, {"pre": [], "ipca": [], "fonte": "csv"})[kind].append({
                "titulo": f"{row['Tipo Titulo']} {venc_dt.year}",
                "venc": venc_iso,
                "anos": round(anos, 2),
                "taxa": round(taxa, 2),
            })

        if parsed:
            for d_iso, day_obj in parsed.items():
                day_obj["pre"] = sorted(day_obj["pre"], key=lambda p: p["anos"])
                day_obj["ipca"] = sorted(day_obj["ipca"], key=lambda p: p["anos"])
                hist[d_iso] = day_obj
            fontes = ["Tesouro Transparente"]
            logging.info(f"[OK] Tesouro Transparente processado ({len(parsed)} pregões recentes).")
    except Exception as e:
        logging.warning(f"[AVISO] Falha ao baixar CSV do Tesouro Transparente (mantendo cache existente): {e}")

    # Manter os últimos 45 pregões ordenados (cobre 1 mês útil com folga)
    if hist:
        sorted_keys = sorted(hist.keys())[-45:]
        hist = {k: hist[k] for k in sorted_keys}

    return {
        "atualizado_em": dt.datetime.now(BRT).isoformat(timespec="seconds"),
        "fontes": fontes or ["Tesouro Transparente"],
        "historico": hist,
    }


def compute_content_hash(snapshot):
    """Hash determinístico apenas dos dados de mercado (ignora timestamps de execução)."""
    core = {
        "indicators": snapshot.get("indicators"),
        "copom_meetings": snapshot.get("copom_meetings"),
        "fomc_dates": snapshot.get("fomc_dates"),
        "focus": snapshot.get("focus"),
        "curva_historico": (snapshot.get("curva") or {}).get("historico"),
    }
    raw = json.dumps(core, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def run_macro_collection(write_flag_file=False):
    today_brt = dt.datetime.now(BRT).date()
    conn = get_db_connection()
    ensure_macro_table(conn)

    existing_snapshot, old_hash = load_existing_snapshot(conn)
    if not old_hash and existing_snapshot:
        old_hash = compute_content_hash(existing_snapshot)

    indicators, copom_meetings = build_copom_and_indicators(today_brt, existing_snapshot)
    focus = fetch_focus_snapshot(today_brt, existing_snapshot)
    curva = fetch_tesouro_curve(today_brt, existing_snapshot)

    snapshot = {
        "atualizado_em": dt.datetime.now(BRT).isoformat(timespec="seconds"),
        "indicators": indicators,
        "copom_meetings": copom_meetings,
        "fomc_dates": FOMC_DATES,
        "focus": focus,
        "curva": curva,
    }

    new_hash = compute_content_hash(snapshot)
    changed = (old_hash != new_hash) or not existing_snapshot

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO macro_data_cache (cache_key, payload, payload_hash, updated_at)
            VALUES ('macro_snapshot', %s::jsonb, %s, NOW())
            ON CONFLICT (cache_key)
            DO UPDATE SET
                payload = EXCLUDED.payload,
                payload_hash = EXCLUDED.payload_hash,
                updated_at = NOW();
            """,
            (json.dumps(snapshot, ensure_ascii=False), new_hash),
        )
        conn.commit()
    conn.close()

    with open("macro_data.json", "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, separators=(",", ":"))

    if write_flag_file:
        with open("macro_changed.flag", "w", encoding="utf-8") as f:
            f.write("1" if changed else "0")

    latest_curve_date = max(curva["historico"].keys()) if curva.get("historico") else "N/A"
    logging.info(
        f"[OK] macro_data_cache salvo (última curva: {latest_curve_date} | "
        f"alterado={'SIM' if changed else 'NÃO'} | hash={new_hash[:12]})."
    )
    return changed


if __name__ == "__main__":
    flag_mode = "--check-change" in os.sys.argv
    run_macro_collection(write_flag_file=flag_mode)
