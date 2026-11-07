"""
fetch_earnings_calendar.py
Busca o calendário oficial de divulgação de resultados das empresas listadas na B3
e consolida as datas do próximo balanço e o momento (Antes da abertura / Após o fechamento).
Salva em 'earnings_calendar.json'.
"""

import os
import json
import logging
import re
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(BASE_DIR, "earnings_calendar.json")

# Ações que habitualmente divulgam antes da abertura do pregão (padrão de mercado B3)
BEFORE_MARKET_PREFIXES = {"ABEV", "WEGE", "SANB", "KLBN", "USIM", "BPAN", "GMAT", "MULT"}

def fetch_and_save_earnings_calendar():
    logging.info("Buscando calendário de resultados corporativos...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8",
    }
    
    url = "https://statusinvest.com.br/acoes/agenda-de-resultados"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            logging.warning(f"Resposta inesperada ao buscar agenda: HTTP {resp.status_code}")
            return False

        soup = BeautifulSoup(resp.text, "html.parser")
        raw_events = {}
        for table in soup.find_all("table"):
            for tr in table.find_all("tr")[1:]:
                tds = tr.find_all("td")
                if len(tds) >= 3:
                    emp_text = tds[0].text.strip()
                    date_str = tds[1].text.strip()
                    m = re.search(r"\(([A-Z0-9]{4,6})\)", emp_text)
                    if m and date_str:
                        ticker = m.group(1).upper()
                        raw_events[ticker] = date_str

        logging.info(f"Coletados {len(raw_events)} eventos brutos da agenda.")

        calendar_map = {}
        for ticker, date_val in raw_events.items():
            base = ticker[:4]
            timing = "Antes da abertura" if base in BEFORE_MARKET_PREFIXES else "Após o fechamento"
            calendar_map[ticker] = {
                "date": date_val,
                "timing": timing,
                "confirmed": True
            }

        with open(OUT_FILE, "w", encoding="utf-8") as f:
            json.dump(calendar_map, f, ensure_ascii=False, indent=2)

        logging.info(f"[OK] Calendário salvo com sucesso em '{OUT_FILE}' ({len(calendar_map)} empresas).")
        return True

    except Exception as e:
        logging.error(f"Erro ao atualizar calendário de resultados: {e}")
        return False

if __name__ == "__main__":
    fetch_and_save_earnings_calendar()
