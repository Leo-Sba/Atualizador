"""
fetch_fiscal_data.py
Coletor oficial da Série Histórica de Receitas e Despesas do Governo Central (RTN / Tesouro Transparente)
e Dívida Bruta do Governo Geral (% PIB - BCB SGS 4537 & 13762) desde 2003 até o presente.

Metodologia Oficial Reproduzida:
  - Receita (R$ bi - deflacionado): Média móvel de 12 meses da Receita Total do Governo Central
    (Tabela 1.1-A do RTN, deflacionada pelo IPCA oficial da STN para base Jan/2003 e também a preços atuais).
  - Despesa (R$ bi - deflacionado): Média móvel de 12 meses da Despesa Total + Transferências por Repartição
    de Receita do Governo Central (Tabela 1.1-A do RTN, deflacionada pelo IPCA oficial da STN).
  - Dívida/PIB (%): Média móvel de 12 meses da Dívida Bruta do Governo Geral (% PIB - SGS 4537 / FMI)
    e leitura pontual da DBGG BCB (SGS 13762).

Salva o cache local em `macro_fiscal_cache.json` e sincroniza automaticamente com o
Cloud Firestore (`macro_fiscal/governo_central_historico`) via `sync-fiscal-firestore.js`.
"""

import os
import io
import json
import time
import logging
import subprocess
import datetime as dt
import requests
import openpyxl

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BRT = dt.timezone(dt.timedelta(hours=-3))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, */*",
}

CKAN_RTN_API = "https://www.tesourotransparente.gov.br/ckan/api/3/action/package_search?q=resultado+do+tesouro+nacional"
FALLBACK_RTN_XLSX_URL = (
    "https://www.tesourotransparente.gov.br/ckan/dataset/"
    "ab56485b-9c40-4efb-8563-9ce3e1973c4b/resource/"
    "527ccdb1-3059-42f3-bf23-b5e3ab4c6dc6/download/seriehistoricajul26.xlsx"
)
CACHE_FILE = "macro_fiscal_cache.json"


def fetch_with_retry(url, retries=3, delay=6, timeout=30):
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Baixando {url} (tentativa {attempt}/{retries})...")
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            return resp
        except Exception as e:
            last_err = e
            logging.warning(f"Falha na tentativa {attempt}/{retries} para {url}: {e}")
            if attempt < retries:
                time.sleep(delay)
    raise RuntimeError(f"Falha após {retries} tentativas ao acessar {url}: {last_err}")


def resolve_rtn_xlsx_url():
    """Descobre dinamicamente a URL mais recente da planilha mensal do RTN no CKAN do Tesouro Transparente."""
    try:
        resp = fetch_with_retry(CKAN_RTN_API, retries=2, delay=3, timeout=15)
        results = resp.json().get("result", {}).get("results", [])
        for pkg in results:
            if pkg.get("name") == "resultado-do-tesouro-nacional":
                for res in pkg.get("resources", []):
                    fmt = str(res.get("format", "")).upper()
                    name = str(res.get("name", "")).lower()
                    url = res.get("url", "")
                    if fmt == "XLSX" and ("mensal" in name or "seriehistorica" in url.lower()):
                        logging.info(f"URL dinâmica do RTN localizada: {url}")
                        return url
    except Exception as e:
        logging.warning(f"Não foi possível consultar API CKAN ({e}). Usando URL de fallback.")
    return FALLBACK_RTN_XLSX_URL


def fetch_bcb_sgs_series(series_code, start_date="01/01/2002", end_date="31/12/2027"):
    """Retorna dicionário {'YYYY-MM': float} para uma série mensal do SGS do Banco Central."""
    url = (
        f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados"
        f"?formato=json&dataInicial={start_date}&dataFinal={end_date}"
    )
    try:
        resp = fetch_with_retry(url, retries=3, delay=5, timeout=20)
        rows = resp.json()
        out = {}
        for item in rows:
            raw_date = str(item.get("data", ""))
            raw_val = item.get("valor")
            if len(raw_date) == 10 and raw_val is not None and str(raw_val).strip() != "":
                # Converte DD/MM/YYYY -> YYYY-MM
                yyyy_mm = f"{raw_date[6:10]}-{raw_date[3:5]}"
                out[yyyy_mm] = float(str(raw_val).replace(",", "."))
        return out
    except Exception as e:
        logging.warning(f"Aviso ao buscar SGS {series_code}: {e}")
        return {}


def parse_ym(cell):
    if cell is None:
        return None
    if isinstance(cell, (dt.datetime, dt.date)):
        return f"{cell.year:04d}-{cell.month:02d}"
    s = str(cell).strip()
    if len(s) >= 7 and s[4] == "-":
        return s[:7]
    return None


def build_fiscal_dataset():
    xlsx_url = resolve_rtn_xlsx_url()
    xlsx_bytes = fetch_with_retry(xlsx_url, retries=3, delay=8, timeout=45).content

    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True, read_only=True)
    if "1.1" not in wb.sheetnames or "1.1-A" not in wb.sheetnames:
        raise RuntimeError(f"Abas '1.1' ou '1.1-A' não encontradas na planilha RTN: {wb.sheetnames}")

    rows_corr = list(wb["1.1"].iter_rows(values_only=True))
    rows_real = list(wb["1.1-A"].iter_rows(values_only=True))

    # Extrai o cabeçalho de datas (linha índice 4)
    header_row = rows_real[4]
    months = []
    col_indices = []
    for col_idx in range(1, len(header_row)):
        ym = parse_ym(header_row[col_idx])
        if ym:
            months.append(ym)
            col_indices.append(col_idx)

    if not months:
        raise RuntimeError("Nenhuma coluna mensal identificada na aba 1.1-A do RTN.")

    # Localiza as linhas de Receita Total, Transferências, Receita Líquida e Despesa Total pelo rótulo
    idx_rec_total = 5
    idx_transf = 28
    idx_rec_liq = 37
    idx_desp_total = 38

    for r_i, row in enumerate(rows_real[:45]):
        label = str(row[0] or "").upper()
        if "1. RECEITA TOTAL" in label:
            idx_rec_total = r_i
        elif "2. TRANSF" in label:
            idx_transf = r_i
        elif "3. RECEITA LÍQUIDA" in label or "3. RECEITA LIQUIDA" in label:
            idx_rec_liq = r_i
        elif "4. DESPESA TOTAL" in label:
            idx_desp_total = r_i

    # Fator deflator IPCA entre 2003-01 e o último mês da planilha (para manter a escala clássica 0-80 bi de 2003)
    pos_2003 = months.index("2003-01") if "2003-01" in months else 0
    col_2003 = col_indices[pos_2003]
    val_real_2003 = float(rows_real[idx_rec_total][col_2003] or 1.0)
    val_corr_2003 = float(rows_corr[idx_rec_total][col_2003] or 1.0)
    ipca_factor_since_2003 = (val_real_2003 / val_corr_2003) if val_corr_2003 > 0 else 3.671575

    # Extrai séries mensais em R$ bilhões (tanto em base constante 2003 quanto em preços de hoje)
    rec_base2003 = []
    desp_base2003 = []
    rec_hoje = []
    desp_hoje = []

    for c_idx in col_indices:
        r_tot = float(rows_real[idx_rec_total][c_idx] or 0.0) / 1000.0  # R$ milhões -> R$ bilhões (preços atuais)
        trf = float(rows_real[idx_transf][c_idx] or 0.0) / 1000.0
        d_tot = float(rows_real[idx_desp_total][c_idx] or 0.0) / 1000.0
        desp_full = d_tot + trf

        rec_hoje.append(r_tot)
        desp_hoje.append(desp_full)
        rec_base2003.append(r_tot / ipca_factor_since_2003)
        desp_base2003.append(desp_full / ipca_factor_since_2003)

    # Busca séries de Dívida Bruta / PIB (%) no SGS do Banco Central
    # 4537: DBGG % PIB (Conceito FMI / Série histórica contínua desde 2001)
    # 13762: DBGG % PIB (Metodologia BCB vigente desde 12/2006)
    sgs_4537 = fetch_bcb_sgs_series(4537)
    sgs_13762 = fetch_bcb_sgs_series(13762)

    # Calcula médias móveis de 12 meses a partir de 2003-01
    series_out = []
    last_valid_div_mm = 73.5
    last_valid_bcb = None

    for i, ym in enumerate(months):
        if ym < "2003-01" or i < 11:
            continue

        mm_rec = round(sum(rec_base2003[i - 11 : i + 1]) / 12.0, 2)
        mm_desp = round(sum(desp_base2003[i - 11 : i + 1]) / 12.0, 2)
        mm_rec_hoje = round(sum(rec_hoje[i - 11 : i + 1]) / 12.0, 2)
        mm_desp_hoje = round(sum(desp_hoje[i - 11 : i + 1]) / 12.0, 2)

        # Média móvel de 12 meses para Dívida/PIB (SGS 4537) para suavidade idêntica ao gráfico de referência
        window_months = months[i - 11 : i + 1]
        div_vals = [sgs_4537[m] for m in window_months if m in sgs_4537]
        if div_vals:
            div_mm = round(sum(div_vals) / len(div_vals), 1)
            last_valid_div_mm = div_mm
        else:
            div_mm = last_valid_div_mm

        bcb_spot = sgs_13762.get(ym, last_valid_bcb)
        if bcb_spot is not None:
            bcb_spot = round(bcb_spot, 1)
            last_valid_bcb = bcb_spot

        series_out.append({
            "m": ym,
            "rec": mm_rec,
            "desp": mm_desp,
            "div": div_mm,
            "rec_atual": mm_rec_hoje,
            "desp_atual": mm_desp_hoje,
            "div_bcb": bcb_spot if bcb_spot is not None else div_mm,
        })

    if len(series_out) < 100:
        raise RuntimeError(f"Série fiscal gerada muito curta ({len(series_out)} pontos). Abortando para evitar corrupção.")

    latest = series_out[-1]
    now_brt = dt.datetime.now(BRT).strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "updated_at": now_brt,
        "schedule_info": "Atualizado diariamente às 03:00 BRT via GitHub Actions",
        "reference_month": latest["m"],
        "source": "Tesouro Transparente (RTN - Série Histórica Mensal IPCA) & Banco Central do Brasil (SGS 4537 / 13762)",
        "ipca_deflator_factor": round(ipca_factor_since_2003, 4),
        "kpis": {
            "receita_bi": latest["rec"],
            "despesa_bi": latest["desp"],
            "resultado_primario_bi": round(latest["rec"] - latest["desp"], 2),
            "receita_atual_bi": latest["rec_atual"],
            "despesa_atual_bi": latest["desp_atual"],
            "resultado_atual_bi": round(latest["rec_atual"] - latest["desp_atual"], 2),
            "divida_pib_pct": latest["div"],
            "divida_bcb_pct": latest["div_bcb"],
        },
        "series": series_out,
    }
    return payload


def main():
    try:
        payload = build_fiscal_dataset()
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        logging.info(
            f"[OK] {CACHE_FILE} salvo com {len(payload['series'])} meses "
            f"(Último: {payload['reference_month']} | Rec: R$ {payload['kpis']['receita_bi']} bi | "
            f"Desp: R$ {payload['kpis']['despesa_bi']} bi | Dív/PIB: {payload['kpis']['divida_pib_pct']}%)"
        )
    except Exception as e:
        logging.error(f"[ERRO] Falha ao atualizar dados fiscais: {e}")
        if os.path.exists(CACHE_FILE):
            logging.info("Mantendo macro_fiscal_cache.json existente (proteção contra queda da API na madrugada).")
        else:
            raise

    # Sincroniza com o Firebase Cloud Firestore se o script Node estiver presente
    if os.path.exists("sync-fiscal-firestore.js"):
        logging.info("Sincronizando documento macro_fiscal/governo_central_historico no Firebase Firestore...")
        res = subprocess.run(["node", "sync-fiscal-firestore.js"], capture_output=False)
        if res.returncode != 0:
            logging.warning(f"sync-fiscal-firestore.js retornou código {res.returncode}")


if __name__ == "__main__":
    main()
