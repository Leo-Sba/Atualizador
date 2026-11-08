"""
fetch_b3_events.py
Extrai histórico oficial de Proventos em Dinheiro (Dividendos, JCP)
e Eventos de Capital (Desdobramentos/Splits, Grupamentos/Inplits, Bonificações)
diretamente da API oficial da B3 para todos os tickers do Dashboard.
Gera arquivos em 'events_data/{ticker}.json' e um consolidado 'events_data.json'.
"""

import os
import json
import time
import base64
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEPLOY_DIR = os.path.join(os.path.dirname(BASE_DIR), "Dashboard_Deploy")
PUBLIC_DIR = DEPLOY_DIR
EVENTS_OUT_DIR = os.path.join(BASE_DIR, "events_data")
DEPLOY_EVENTS_DIR = os.path.join(DEPLOY_DIR, "events")

os.makedirs(EVENTS_OUT_DIR, exist_ok=True)
if os.path.exists(DEPLOY_DIR):
    os.makedirs(DEPLOY_EVENTS_DIR, exist_ok=True)

def create_session():
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=20)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    })
    return session

def format_factor_and_ratio(label, factor_str):
    try:
        clean_str = factor_str.replace(".", "").replace(",", ".")
        val = float(clean_str)
    except:
        return factor_str, factor_str

    lbl = label.upper()
    if "GRUPAMENTO" in lbl:
        if val > 0 and val < 1.0:
            ratio_int = round(1.0 / val)
            return f"{ratio_int}:1", f"{ratio_int} ações viram 1"
        return f"{val:g}", f"Fator {val:g}"
    elif "DESDOBRAMENTO" in lbl:
        if val >= 100:
            mult = round((val / 100.0) + 1.0)
            return f"1:{mult}", f"1 ação vira {mult}"
        elif val > 0:
            mult = round(val + 1.0)
            return f"1:{mult}", f"1 ação vira {mult}"
        return f"{val:g}%", f"Desdobramento {val:g}%"
    elif "BONIFICACAO" in lbl or "BONIFICAÇÃO" in lbl:
        return f"{val:g}%", f"Bonificação de {val:g}%"
    return f"{val:g}", f"{val:g}"

def parse_float_br(val_str):
    if not val_str:
        return 0.0
    try:
        return float(str(val_str).replace(".", "").replace(",", "."))
    except:
        return 0.0

def fetch_ticker_events(ticker, trading_name, session):
    code = ticker[:4]
    tn = trading_name or code

    stock_divs_raw = []
    cash_supp_raw = []
    cash_hist_raw = []

    # 1. Endpoint GetListedSupplementCompany
    p1 = {"issuingCompany": code, "language": "pt-br"}
    b64_1 = base64.b64encode(json.dumps(p1).encode("utf-8")).decode("utf-8")
    url1 = f"https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedSupplementCompany/{b64_1}"

    try:
        r1 = session.get(url1, timeout=12)
        if r1.status_code == 200:
            d1 = r1.json()
            if d1 and isinstance(d1, list):
                item = d1[0]
                stock_divs_raw = item.get("stockDividends", []) or []
                cash_supp_raw = item.get("cashDividends", []) or []
    except Exception as e:
        logging.warning(f"[{ticker}] Erro no Supplement B3: {e}")

    # 2. Endpoint GetListedCashDividends
    p2 = {"language": "pt-br", "pageNumber": 1, "pageSize": 100, "tradingName": tn}
    b64_2 = base64.b64encode(json.dumps(p2).encode("utf-8")).decode("utf-8")
    url2 = f"https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/GetListedCashDividends/{b64_2}"

    try:
        r2 = session.get(url2, timeout=12)
        if r2.status_code == 200:
            d2 = r2.json()
            if isinstance(d2, dict):
                cash_hist_raw = d2.get("results", []) or []
    except Exception as e:
        logging.warning(f"[{ticker}] Erro no CashDividends B3: {e}")

    # Determinar tipo de ação (ON, PN, Unit)
    is_on = ticker.endswith("3")
    is_pn = ticker.endswith("4") or ticker.endswith("5") or ticker.endswith("6")
    is_unit = ticker.endswith("11")

    # Mapear pagamentos de cash_supp por (data-com, label) para pegar paymentDate
    payment_dates_map = {}
    for c in cash_supp_raw:
        dt_com = c.get("lastDatePrior", "").strip()
        lbl = c.get("label", "").strip().upper()
        pgto = c.get("paymentDate", "").strip()
        isin = c.get("isinCode", "").strip()
        if dt_com and pgto:
            key = f"{dt_com}_{lbl}"
            payment_dates_map[key] = pgto

    # Processar Proventos em Dinheiro
    divs_list = []
    seen_divs = set()

    # Prioridade para cash_hist_raw
    for ch in cash_hist_raw:
        st_type = (ch.get("typeStock") or "").strip().upper()
        # Filtro de tipo de ação
        if is_on and "ON" not in st_type and st_type != "":
            continue
        if is_pn and "PN" not in st_type and "PR" not in st_type and st_type != "":
            continue
        if is_unit and "UNT" not in st_type and "UNIT" not in st_type and st_type != "":
            # Units às vezes agrupam ON e PN
            pass

        corp_act = (ch.get("corporateAction") or "PROVENTO").strip()
        val = parse_float_br(ch.get("valueCash"))
        dt_com = (ch.get("lastDatePriorEx") or "").strip()
        dt_app = (ch.get("dateApproval") or "").strip()

        key = f"{dt_com}_{corp_act}_{val:.6f}"
        if key in seen_divs:
            continue
        seen_divs.add(key)

        # Buscar data de pagamento no mapa do suplemento
        supp_key = f"{dt_com}_{corp_act}"
        dt_pgto = payment_dates_map.get(supp_key, "-")

        divs_list.append({
            "type": corp_act,
            "value": round(val, 6),
            "date_com": dt_com,
            "date_payment": dt_pgto,
            "date_approval": dt_app,
            "stock_type": st_type
        })

    # Se cash_hist_raw foi vazio, usar cash_supp_raw
    if not divs_list and cash_supp_raw:
        for cs in cash_supp_raw:
            isin = cs.get("isinCode", "").strip()
            # Filtrar por ISIN se aplicável
            if is_on and "ON" not in isin and "OR" not in isin:
                continue
            if is_pn and "PN" not in isin and "PR" not in isin:
                continue
            
            corp_act = cs.get("label", "DIVIDENDO").strip()
            val = parse_float_br(cs.get("rate"))
            dt_com = cs.get("lastDatePrior", "").strip()
            dt_pgto = cs.get("paymentDate", "-").strip()
            dt_app = cs.get("approvedOn", "").strip()

            key = f"{dt_com}_{corp_act}_{val:.6f}"
            if key in seen_divs:
                continue
            seen_divs.add(key)

            divs_list.append({
                "type": corp_act,
                "value": round(val, 6),
                "date_com": dt_com,
                "date_payment": dt_pgto,
                "date_approval": dt_app,
                "stock_type": "ON" if is_on else ("PN" if is_pn else "UNT")
            })

    # Processar Eventos Societários (Splits, Grupamentos, Bonificações)
    splits_list = []
    inplits_list = []
    bonuses_list = []
    seen_events = set()

    for sd in stock_divs_raw:
        lbl = (sd.get("label") or "").strip().upper()
        factor_raw = (sd.get("factor") or "").strip()
        dt_com = (sd.get("lastDatePrior") or "").strip()
        dt_app = (sd.get("approvedOn") or "").strip()
        isin = (sd.get("isinCode") or "").strip()

        # Filtrar classe se necessário (evitar duplicar evento que atinge ON e PN)
        event_key = f"{lbl}_{dt_com}_{factor_raw}"
        if event_key in seen_events:
            continue
        seen_events.add(event_key)

        ratio_display, description = format_factor_and_ratio(lbl, factor_raw)

        item_event = {
            "type": lbl,
            "ratio": ratio_display,
            "description": description,
            "date_com": dt_com,
            "date_approval": dt_app
        }

        if "GRUPAMENTO" in lbl:
            inplits_list.append(item_event)
        elif "DESDOBRAMENTO" in lbl:
            splits_list.append(item_event)
        else:
            bonuses_list.append(item_event)

    return {
        "ticker": ticker,
        "company": tn,
        "splits": splits_list,
        "inplits": inplits_list,
        "bonuses": bonuses_list,
        "dividends": divs_list
    }

def sync_events_to_supabase(consolidated_data):
    """
    Sincroniza o histórico oficial de eventos societários da B3 (Splits, Inplits, Bonificações e Cisões)
    na tabela 'b3_corporate_events_cache' do Supabase para alimentar a estrutura em cascata.
    """
    try:
        import psycopg2
        from psycopg2.extras import execute_batch
        from dotenv import load_dotenv
        load_dotenv()

        db_host = os.getenv("DB_HOST")
        if not db_host:
            return

        conn = psycopg2.connect(
            host=db_host,
            port=os.getenv("DB_PORT", 5432),
            dbname=os.getenv("DB_NAME", "postgres"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            connect_timeout=20
        )
        cur = conn.cursor()
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
        records = []
        for ticker, ev in consolidated_data.items():
            records.append((
                ticker,
                ev.get("company") or ticker,
                json.dumps(ev.get("splits", []), ensure_ascii=False),
                json.dumps(ev.get("inplits", []), ensure_ascii=False),
                json.dumps(ev.get("bonuses", []), ensure_ascii=False),
            ))
        if records:
            execute_batch(cur, """
                INSERT INTO b3_corporate_events_cache (ticker, company, splits, inplits, bonuses, updated_at)
                VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, NOW())
                ON CONFLICT (ticker) DO UPDATE SET
                    company = EXCLUDED.company,
                    splits = EXCLUDED.splits,
                    inplits = EXCLUDED.inplits,
                    bonuses = EXCLUDED.bonuses,
                    updated_at = NOW();
            """, records, page_size=100)
        conn.commit()
        conn.close()
        logging.info(f"[OK] {len(records)} ativos sincronizados na tabela 'b3_corporate_events_cache' (Supabase).")
    except Exception as e:
        logging.warning(f"Aviso ao sincronizar eventos B3 com Supabase: {e}")


def load_tickers_from_db_or_local():
    from clean_duplicates import IGNORED_INACTIVE_TICKERS
    dash_data_path = os.path.join(BASE_DIR, "dashboard_data.json")
    if os.path.exists(dash_data_path):
        with open(dash_data_path, "r", encoding="utf-8") as f:
            dash_data = json.load(f)
        tickers = {
            t: dash_data[t].get("company", t)
            for t in dash_data.keys()
            if t not in ["IBOV", "IFNC", "SEGUROS"] and t not in IGNORED_INACTIVE_TICKERS
        }
        return tickers

    # Fallback para o banco de dados Supabase (usado no GitHub Actions / Atualizador)
    import psycopg2
    from dotenv import load_dotenv
    load_dotenv()
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=20
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT s.ticker, c.trading_name
        FROM securities s
        JOIN companies c ON c.id = s.company_id
        ORDER BY s.ticker;
    """)
    tickers = {
        row[0]: (row[1] or row[0])
        for row in cur.fetchall()
        if row[0] not in ["IBOV", "IFNC", "SEGUROS"] and row[0] not in IGNORED_INACTIVE_TICKERS
    }
    conn.close()
    return tickers


def run_b3_events_extraction():
    logging.info("Carregando lista de ativos...")
    try:
        tickers_map = load_tickers_from_db_or_local()
    except Exception as e:
        logging.error(f"Não foi possível carregar a lista de ativos: {e}")
        return

    tickers = list(tickers_map.keys())
    logging.info(f"Total de ações para processar: {len(tickers)}")

    # Carregar nomes de pregão
    mapping_path = os.path.join(BASE_DIR, "b3_names_mapping.json")
    mapping = {}
    if os.path.exists(mapping_path):
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)

    session = create_session()
    consolidated_data = {}

    def worker(t):
        tn = mapping.get(t, [None])[0]
        if not tn:
            tn = tickers_map.get(t, t)
        res = fetch_ticker_events(t, tn, session)
        return t, res

    logging.info("Consultando API oficial da B3 via multithreading...")
    completed = 0
    has_deploy_dir = os.path.exists(DEPLOY_DIR)
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(worker, t): t for t in tickers}
        for future in as_completed(futures):
            t = futures[future]
            try:
                ticker, res = future.result()
                consolidated_data[ticker] = res

                # Salvar JSON individual
                ind_file = os.path.join(EVENTS_OUT_DIR, f"{ticker}.json")
                with open(ind_file, "w", encoding="utf-8") as f:
                    json.dump(res, f, ensure_ascii=False)

                # Salvar na pasta public do deploy (se existir localmente)
                if has_deploy_dir:
                    dep_file = os.path.join(DEPLOY_EVENTS_DIR, f"{ticker}.json")
                    with open(dep_file, "w", encoding="utf-8") as f:
                        json.dump(res, f, ensure_ascii=False)

                completed += 1
                if completed % 25 == 0 or completed == len(tickers):
                    logging.info(f"Progresso: {completed}/{len(tickers)} ativos processados.")
            except Exception as e:
                logging.error(f"Erro ao processar {t}: {e}")

    # Salvar consolidado events_data.json
    cons_file = os.path.join(BASE_DIR, "events_data.json")
    with open(cons_file, "w", encoding="utf-8") as f:
        json.dump(consolidated_data, f, ensure_ascii=False)

    if has_deploy_dir:
        deploy_cons_file = os.path.join(PUBLIC_DIR, "events_data.json")
        with open(deploy_cons_file, "w", encoding="utf-8") as f:
            json.dump(consolidated_data, f, ensure_ascii=False)

    # Sincronizar com Supabase para a estrutura em cascata
    sync_events_to_supabase(consolidated_data)

    logging.info(f"[OK] Extração finalizada com sucesso! Total de ativos consolidados: {len(consolidated_data)}")

if __name__ == "__main__":
    run_b3_events_extraction()
