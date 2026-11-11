import json

import os



with open("dashboard_data.json", "r", encoding="utf-8") as f:

    raw_data = f.read()




earnings_data = {}
if os.path.exists("earnings_calendar.json"):
    try:
        with open("earnings_calendar.json", "r", encoding="utf-8") as f:
            earnings_data = json.load(f)
    except Exception:
        pass

corporate_events_summary = {}
corporate_events_full = {}
if os.path.exists("events_data.json"):
    try:
        with open("events_data.json", "r", encoding="utf-8") as f:
            raw_events = json.load(f)
        corporate_events_full = raw_events
        for tk, ev_obj in raw_events.items():
            s_list = ev_obj.get("splits", []) or []
            i_list = ev_obj.get("inplits", []) or []
            b_list = ev_obj.get("bonuses", []) or []
            if s_list or i_list or b_list:
                corporate_events_summary[tk] = {
                    "company": ev_obj.get("company") or tk,
                    "splits": s_list,
                    "inplits": i_list,
                    "bonuses": b_list
                }
    except Exception:
        pass

ibov_info = {"aggregated_pe_all": 10.16, "weighted_pe": 17.00, "simple_pe": 19.22, "date": "2026-11-09"}

if os.path.exists("ibov_metric.json"):

    try:

        with open("ibov_metric.json", "r", encoding="utf-8") as f:

            ibov_info = json.load(f)

    except Exception:

        pass

ifr_cache = {}
if os.path.exists("entradas_ifr_cache.json"):
    try:
        with open("entradas_ifr_cache.json", "r", encoding="utf-8") as f:
            ifr_cache = json.load(f)
    except Exception:
        pass

macro_snapshot = {}
if os.path.exists("macro_data.json"):
    try:
        with open("macro_data.json", "r", encoding="utf-8") as f:
            macro_snapshot = json.load(f)
    except Exception:
        pass



template = """<!DOCTYPE html>

<html lang="pt-BR">

<head>

    <meta charset="UTF-8">

    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

    <title>Dashboard Fundamentalista IBOV / B3</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <!-- Firebase SDK (Compat) para Leitura Pública em Tempo Real do Firestore -->
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore-compat.js"></script>

    <style>

        :root {
            /* TEMA PADRÃO: OBSIDIAN DARK (Preto OLED / Terminal / Alta Performance) */
            --bg: #090a0f;
            --card-bg: #111319;
            --border: #222634;
            --text-main: #f1f5f9;
            --text-muted: #8492a6;
            --grid-color: rgba(255, 255, 255, 0.07);
            --slider-bg: rgba(17, 19, 25, 0.85);
            --slider-track: #1e2230;
            --accent-blue: #00d2ff;
            --accent-green: #00e676;
            --accent-orange: #ff9100;
            --accent-red: #ff3366;
            --accent-yellow: #ffd600;
            --mean-line: #94a3b8;
            --radius: 12px;
        }

        /* TEMA CLARO: PURE LIGHT (Clean / Institucional / Alta Legibilidade em Ambientes Iluminados) */
        body.theme-light {
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --border: #cbd5e1;
            --text-main: #0f172a;
            --text-muted: #334155;
            --grid-color: rgba(15, 23, 42, 0.09);
            --slider-bg: #f1f5f9;
            --slider-track: #cbd5e1;
            --accent-blue: #0369a1;      /* Azul Royal de alto contraste */
            --accent-green: #15803d;     /* Verde Floresta escuro */
            --accent-orange: #c2410c;    /* Laranja queimado intenso */
            --accent-red: #b91c1c;       /* Vermelho vivo escuro */
            --accent-yellow: #a16207;    /* Dourado âmbar escuro */
            --mean-line: #475569;
            --color-pos: #15803d;        /* Verde positivo para tabelas */
            --color-neg: #b91c1c;        /* Vermelho negativo para tabelas */
        }

        body.theme-light .chart-box {
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        }

        body.theme-light .card {
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
        }

        body.theme-light .period-selector {
            background: #e2e8f0 !important;
            border-color: #cbd5e1 !important;
        }

        body.theme-light .period-btn {
            color: #475569;
        }

        body.theme-light .period-btn.active {
            background: #0284c7;
            color: #ffffff;
        }

        body.theme-light select {
            color: #0f172a;
            background: #ffffff;
            border-color: #cbd5e1;
        }

        body.theme-light .title-area h1 {
            color: #0f172a;
        }

        body.theme-light .card-value {
            color: #0f172a;
        }

        body.theme-light .chart-slider-box {
            background: #f8fafc;
            border-color: #e2e8f0;
            color: #64748b;
        }

        body.theme-light .btn-reset-slider {
            background: #e2e8f0;
            color: #334155;
            border-color: #cbd5e1;
        }

        body.theme-light .time-slider-wrapper {
            background: #f8fafc !important;
            border-color: #cbd5e1 !important;
        }

        body.theme-light .btn-fullscreen {
            border-color: #cbd5e1;
            color: #64748b;
        }

        body.theme-light .btn-fullscreen:hover {
            background: #e2e8f0;
            color: #0f172a;
        }

        body.theme-light .earnings-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-main);
            letter-spacing: 0.2px;
        }
        .timing-badge {
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 11.5px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .timing-after {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }
        .timing-before {
            background: rgba(251, 191, 36, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.3);
        }
        .timing-none {
            background: rgba(148, 163, 184, 0.15);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.3);
        }
        .ibov-pe-badge {
            background: #e0f2fe;
            border-color: #bae6fd;
        }

        body.theme-light .ibov-pe-badge .tag {
            color: #0369a1;
        }

        body.theme-light .ibov-pe-badge .val {
            color: #0284c7;
        }

        body.theme-light .ibov-pe-badge .desc {
            color: #64748b;
        }

        body.theme-light span[id^="sliderVal"] {
            color: #0f172a !important;
        }


        * {

            margin: 0;

            padding: 0;

            box-sizing: border-box;

            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;

            -webkit-tap-highlight-color: transparent;

        }



        body {

            background-color: var(--bg);

            color: var(--text-main);

            padding: 16px;

            min-height: 100vh;

            display: flex;

            flex-direction: column;

        }



        @media (min-width: 768px) {

            body {

                padding: 24px;

            }

        }



        .container {
            max-width: 1440px;
            margin: 0 auto;
            width: 100%;
            padding: 0 12px;
            transition: max-width 0.25s ease-in-out;
        }

        /* Modos de Layout controlados via body class */
        body.mode-compact .container {
            max-width: 1180px;
        }

        body.mode-expanded .container {
            max-width: 98vw;
            padding: 0 12px;
        }



        /* Header Responsivo */

        .header {

            display: flex;

            flex-direction: column;

            gap: 16px;

            margin-bottom: 20px;

            padding-bottom: 16px;

            border-bottom: 1px solid var(--border);

        }



        @media (min-width: 992px) {

            .header {

                flex-direction: row;

                justify-content: space-between;

                align-items: center;

            }

        }



        .title-area h1 {

            font-size: 20px;

            font-weight: 700;

            color: #fff;

            display: flex;

            align-items: center;

            flex-wrap: wrap;

            gap: 8px;

        }



        @media (min-width: 768px) {

            .title-area h1 {

                font-size: 24px;

            }

        }



        .badge {

            font-size: 11px;

            background: #0284c7;

            color: #fff;

            padding: 3px 8px;

            border-radius: 6px;

            text-transform: uppercase;

            font-weight: 600;

        }



        .title-area p {

            font-size: 13px;

            color: var(--text-muted);

            margin-top: 4px;

        }



        /* Controles Responsivos (Filtros e Botões) */

        .controls {

            display: flex;

            flex-direction: column;

            gap: 12px;

            width: 100%;

        }



        @media (min-width: 640px) {

            .controls {

                flex-direction: row;

                align-items: center;

                flex-wrap: wrap;

            }

        }



        @media (min-width: 992px) {

            .controls {

                width: auto;

                justify-content: flex-end;

            }

        }



        .control-group {

            display: flex;

            align-items: center;

            gap: 8px;

            width: 100%;

        }



        @media (min-width: 640px) {

            .control-group {

                width: auto;

            }

        }



        select {

            background: var(--card-bg);

            color: #fff;

            border: 1px solid var(--border);

            padding: 10px 14px;

            border-radius: 8px;

            font-size: 14px;

            font-weight: 600;

            cursor: pointer;

            outline: none;

            width: 100%;

            transition: all 0.2s;

        }



        @media (min-width: 640px) {

            select {

                min-width: 220px;

                width: auto;

            }

        }



        /* Estilos do Combobox Pesquisável */
.custom-combobox-wrapper {
    position: relative;
    width: 100%;
    min-width: 260px;
}
@media (min-width: 640px) {
    .custom-combobox-wrapper {
        width: 320px;
    }
}
.combobox-input {
    width: 100%;
    background: var(--card-bg);
    color: #fff;
    border: 1px solid var(--border);
    padding: 10px 36px 10px 14px;
    border-radius: 8px;
    font-size: 13.5px;
    font-weight: 600;
    cursor: text;
    outline: none;
    transition: all 0.2s;
    box-sizing: border-box;
}
.combobox-input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.25);
}
body.theme-light .combobox-input {
    background: #ffffff;
    color: #0f172a;
    border-color: #cbd5e1;
}
body.theme-light .combobox-input:focus {
    border-color: #0284c7;
    box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.2);
}
.combobox-arrow {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 10px;
    color: var(--text-muted);
    pointer-events: auto;
    cursor: pointer;
    transition: transform 0.2s;
    user-select: none;
}
.combobox-dropdown {
    display: none;
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    right: 0;
    max-height: 380px;
    overflow-y: auto;
    background: rgba(15, 23, 42, 0.98);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 8px;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6);
    z-index: 1000;
}
body.theme-light .combobox-dropdown {
    background: #ffffff;
    border-color: #cbd5e1;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
}
.combobox-item {
    padding: 9px 14px;
    font-size: 13px;
    color: var(--text-main);
    cursor: pointer;
    border-bottom: 1px solid rgba(148, 163, 184, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    transition: background 0.15s;
}
.combobox-item:hover, .combobox-item.active {
    background: rgba(56, 189, 248, 0.18);
    color: var(--accent);
}
body.theme-light .combobox-item:hover, body.theme-light .combobox-item.active {
    background: #f0f9ff;
    color: #0284c7;
}
.combobox-item-ticker {
    font-weight: 700;
}
.combobox-item-name {
    font-size: 12px;
    color: var(--text-muted);
    margin-left: 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 170px;
}
.combobox-empty {
    padding: 16px;
    text-align: center;
    color: var(--text-muted);
    font-size: 13px;
}

select:focus {

            border-color: var(--accent-blue);

            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2);

        }



        /* Badge IBOV P/L Médio */

        .earnings-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 13px;
            font-weight: 500;
            color: var(--text-main);
            letter-spacing: 0.2px;
        }
        .timing-badge {
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 11.5px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
        }
        .timing-after {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }
        .timing-before {
            background: rgba(251, 191, 36, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.3);
        }
        .timing-none {
            background: rgba(148, 163, 184, 0.15);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.3);
        }
        .ibov-pe-badge {
            display: flex;
            align-items: center;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95));
            border: 1px solid var(--accent-blue);
            padding: 8px 16px;
            border-radius: 8px;
            gap: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25);
            white-space: nowrap;
        }

        .ibov-pe-badge .tag {
            font-size: 13px;
            font-weight: 800;
            color: var(--accent-blue);
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }

        .ibov-pe-badge .val {
            font-size: 18px;
            font-weight: 900;
            color: #ffffff;
            letter-spacing: 0.2px;
        }

        .ibov-pe-badge .desc {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-muted);
        }


        .period-selector {

            display: flex;

            background: #0f172a;

            border: 1px solid var(--border);

            border-radius: 8px;

            padding: 3px;

            gap: 3px;

            width: 100%;

            overflow-x: auto;

            -webkit-overflow-scrolling: touch;

        }



        @media (min-width: 640px) {

            .period-selector {

                width: auto;

            }

        }



        .period-btn {

            flex: 1;

            text-align: center;

            white-space: nowrap;

            background: transparent;

            color: var(--text-muted);

            border: none;

            padding: 8px 12px;

            font-size: 12px;

            font-weight: 600;

            border-radius: 6px;

            cursor: pointer;

            transition: all 0.2s;

        }



        @media (min-width: 768px) {

            .period-btn {

                padding: 8px 14px;

                font-size: 13px;

            }

        }



        .period-btn:hover {

            color: #fff;

            background: rgba(255, 255, 255, 0.05);

        }



        .period-btn.active {

            background: var(--accent-blue);

            color: #0f172a;

            font-weight: 700;

        }



        /* Grid de Cards KPI */

        .cards-grid {

            display: grid;

            grid-template-columns: repeat(2, 1fr);

            gap: 12px;

            margin-bottom: 20px;

        }



        @media (min-width: 768px) {

            .cards-grid {

                grid-template-columns: repeat(3, 1fr);

                gap: 16px;

            }

        }



        @media (min-width: 1024px) {

            .cards-grid {

                grid-template-columns: repeat(5, 1fr);

            }

        }



        .card {

            background: var(--card-bg);

            border: 1px solid var(--border);

            border-radius: var(--radius);

            padding: 14px 16px;

            display: flex;

            flex-direction: column;

            gap: 4px;

            position: relative;

            overflow: hidden;

        }



        .card::before {

            content: "";

            position: absolute;

            top: 0;

            left: 0;

            width: 4px;

            height: 100%;

        }



        .card.card-blue::before { background: var(--accent-blue); }

        .card.card-green::before { background: var(--accent-green); }

        .card.card-orange::before { background: var(--accent-orange); }

        .card.card-yellow::before { background: var(--accent-yellow); }

        .card.card-red::before { background: var(--accent-red); }



        .card-label {

            font-size: 11px;

            font-weight: 600;

            color: var(--text-muted);

            text-transform: uppercase;

            letter-spacing: 0.5px;

        }



        .card-value {

            font-size: 20px;

            font-weight: 700;

            color: #fff;

        }



        @media (min-width: 768px) {

            .card-value {

                font-size: 22px;

            }

        }



        .card-sub {

            font-size: 11px;

            color: var(--text-muted);

        }



        /* Grid de Gráficos Responsivo */

        .charts-container {
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
        }

        @media (min-width: 1024px) {
            .charts-container {
                grid-template-columns: repeat(2, 1fr);
                gap: 18px;
            }
        }

        /* No modo Expandido em telas grandes, usa 3 colunas para manter a proporção áurea */
        @media (min-width: 1560px) {
            body.mode-expanded .charts-container {
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
            }
        }

        .chart-box {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 16px;
            height: 360px;
            display: flex;
            flex-direction: column;
            transition: all 0.2s ease;
        }

        @media (min-width: 768px) {
            .chart-box {
                padding: 16px 18px;
                height: 380px;
            }
        }

        /* Ajustes de altura conforme o modo de visualização */
        body.mode-compact .chart-box {
            height: 340px;
            padding: 14px 16px;
        }

        body.mode-expanded .chart-box {
            height: 390px;
        }

        /* Suporte a tela cheia / maximização individual de gráfico */
        .chart-box.fullscreen-card {
            position: fixed !important;
            top: 20px !important;
            left: 20px !important;
            right: 20px !important;
            bottom: 20px !important;
            width: auto !important;
            height: auto !important;
            z-index: 9999 !important;
            box-shadow: 0 0 50px rgba(0, 0, 0, 0.85);
            border: 2px solid var(--accent-blue);
        }

        .btn-fullscreen {
            background: transparent;
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: var(--text-muted);
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 11px;
            cursor: pointer;
            transition: all 0.15s;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        }

        .btn-fullscreen:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.1);
            border-color: var(--accent-blue);
        }


        .chart-header {

            display: flex;

            justify-content: space-between;

            align-items: center;

            margin-bottom: 12px;

            gap: 8px;

        }



        .chart-title {

            font-size: 14px;

            font-weight: 600;

            color: var(--text-main);

        }



        @media (min-width: 768px) {

            .chart-title {

                font-size: 15px;

            }

        }



        .chart-mean {

            font-size: 11px;

            background: rgba(255, 255, 255, 0.05);

            padding: 3px 8px;

            border-radius: 4px;

            color: var(--text-muted);

            white-space: nowrap;

        }



        /* Controles de Slider no Box do Gráfico (Dual Range Min & Max) */

        .chart-slider-box {

            display: flex;

            align-items: center;

            justify-content: space-between;

            background: rgba(15, 23, 42, 0.7);

            border: 1px solid rgba(51, 65, 85, 0.6);

            border-radius: 6px;

            padding: 5px 10px;

            margin-bottom: 8px;

            font-size: 11px;

            color: var(--text-muted);

            gap: 12px;

        }



        .dual-slider-container {

            position: relative;

            flex: 1;

            height: 18px;

            display: flex;

            align-items: center;

        }



        .slider-track {

            position: absolute;

            width: 100%;

            height: 4px;

            background: #334155;

            border-radius: 2px;

        }



        .slider-range-fill {

            position: absolute;

            height: 4px;

            background: var(--accent-blue);

            border-radius: 2px;

            pointer-events: none;

        }



        .dual-slider-container input[type="range"] {

            position: absolute;

            width: 100%;

            height: 4px;

            -webkit-appearance: none;

            appearance: none;

            background: transparent;

            pointer-events: none;

            outline: none;

            margin: 0;

        }



        .dual-slider-container input[type="range"]::-webkit-slider-thumb {

            -webkit-appearance: none;

            appearance: none;

            width: 14px;

            height: 14px;

            border-radius: 50%;

            background: #f8fafc;

            border: 2px solid var(--accent-blue);

            cursor: pointer;

            pointer-events: auto;

            box-shadow: 0 0 4px rgba(0,0,0,0.6);

            transition: transform 0.1s;

        }



        .dual-slider-container input[type="range"]::-webkit-slider-thumb:hover {

            transform: scale(1.25);

            background: var(--accent-blue);

        }



        .dual-slider-container input[type="range"]::-moz-range-thumb {

            width: 14px;

            height: 14px;

            border-radius: 50%;

            background: #f8fafc;

            border: 2px solid var(--accent-blue);

            cursor: pointer;

            pointer-events: auto;

            box-shadow: 0 0 4px rgba(0,0,0,0.6);

        }



        .chart-slider-box .btn-reset-slider {

            background: transparent;

            border: 1px solid rgba(148, 163, 184, 0.3);

            color: var(--text-muted);

            border-radius: 4px;

            padding: 2px 7px;

            font-size: 10px;

            cursor: pointer;

            transition: all 0.2s;

            white-space: nowrap;

        }



        .chart-slider-box .btn-reset-slider:hover {

            color: #fff;

            border-color: var(--accent-blue);

        }



        .chart-canvas-wrapper {

            position: relative;

            flex: 1;

            width: 100%;

            height: 100%;

        }



        .val-table-container {

            flex: 1;

            width: 100%;

            display: flex;

            flex-direction: column;

            justify-content: center;

            overflow-x: auto;

        }



        .val-table {

            width: 100%;

            border-collapse: collapse;

            font-size: 13px;

            color: var(--text-main);

        }



        .val-table th {

            text-align: left;

            padding: 8px 10px;

            color: var(--text-muted);

            border-bottom: 1px solid var(--border);

            font-weight: 500;

            font-size: 11px;

            text-transform: uppercase;

            letter-spacing: 0.5px;

        }



        .val-table td {

            padding: 9px 10px;

            border-bottom: 1px solid #33415533;

        }



        .val-table tr:last-child td {

            border-bottom: none;

        }



        .val-tag {

            display: inline-block;

            padding: 2px 7px;

            border-radius: 4px;

            font-size: 11px;

            font-weight: 600;

        }



        .val-tag-current {

            background: #38bdf820;

            color: #38bdf8;

            border: 1px solid #38bdf840;

        }



        .val-tag-mean {

            background: #4ade8020;

            color: #4ade80;

            border: 1px solid #4ade8040;

        }



        .val-tag-discount {

            background: #facc1520;

            color: #facc15;

            border: 1px solid #facc1540;

        }



        .val-tag-deep {

            background: #a855f720;

            color: #c084fc;

            border: 1px solid #a855f740;

        }



        .val-tag-max {

            background: #ef444420;

            color: #f87171;

            border: 1px solid #ef444440;

        }



        .val-tag-min {

            background: #0ea5e920;

            color: #38bdf8;

            border: 1px solid #0ea5e940;

        }

    
        /* Dual Slider Time Range thumb styles */
        #sliderTimeStart::-webkit-slider-thumb, #sliderTimeEnd::-webkit-slider-thumb {
            pointer-events: auto;
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #38bdf8;
            cursor: pointer;
            box-shadow: 0 0 6px rgba(56, 189, 248, 0.8);
            border: 2px solid #0f172a;
        }
        #sliderTimeStart::-moz-range-thumb, #sliderTimeEnd::-moz-range-thumb {
            pointer-events: auto;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #38bdf8;
            cursor: pointer;
            box-shadow: 0 0 6px rgba(56, 189, 248, 0.8);
            border: 2px solid #0f172a;
        }

        /* Alto contraste nas tags e escritas coloridas do Tema Claro */
        body.theme-light .val-tag-current {
            background: #e0f2fe;
            color: #0369a1;
            border-color: #7dd3fc;
            font-weight: 700;
        }

        body.theme-light .val-tag-mean {
            background: #dcfce7;
            color: #15803d;
            border-color: #86efac;
            font-weight: 700;
        }

        body.theme-light .val-tag-discount {
            background: #fef9c3;
            color: #854d0e;
            border-color: #fde047;
            font-weight: 700;
        }

        body.theme-light .val-tag-deep {
            background: #f3e8ff;
            color: #7e22ce;
            border-color: #d8b4fe;
            font-weight: 700;
        }

        body.theme-light .val-tag-max {
            background: #fee2e2;
            color: #b91c1c;
            border-color: #fca5a5;
            font-weight: 700;
        }

        body.theme-light .val-tag-min {
            background: #e0f2fe;
            color: #0284c7;
            border-color: #7dd3fc;
            font-weight: 700;
        }

        body.theme-light .chart-mean {
            background: #f1f5f9;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            font-weight: 600;
        }

        body.theme-light .card.card-blue .card-label { color: #0369a1; font-weight: 700; }
        body.theme-light .card.card-green .card-label { color: #15803d; font-weight: 700; }
        body.theme-light .card.card-orange .card-label { color: #c2410c; font-weight: 700; }
        body.theme-light .card.card-yellow .card-label { color: #854d0e; font-weight: 700; }
        body.theme-light .card.card-red .card-label { color: #b91c1c; font-weight: 700; }

        body.theme-light .card-sub {
            color: #475569;
            font-weight: 600;
        }

        body.theme-light .val-table th {
            color: #334155;
            font-weight: 700;
            border-bottom: 2px solid #cbd5e1;
        }

        body.theme-light .val-table td {
            color: #0f172a;
            border-bottom: 1px solid #e2e8f0;
        }

        body.theme-light #timeSliderLabel {
            color: #0369a1 !important;
            font-weight: 800 !important;
        }

        /* Estilos do Histórico de Eventos Societários & Proventos (B3) */
        .btn-toggle-events {
            background: var(--bg-hover, rgba(255,255,255,0.05));
            border: 1px solid var(--border-color, rgba(255,255,255,0.15));
            color: var(--text-main);
            font-size: 12px;
            font-weight: 600;
            padding: 6px 14px;
            border-radius: 6px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }
        .btn-toggle-events:hover {
            background: rgba(56, 189, 248, 0.12);
            border-color: rgba(56, 189, 248, 0.4);
            color: #38bdf8;
        }
        .events-tab-btn {
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-muted);
            font-size: 12px;
            font-weight: 600;
            padding: 5px 12px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .events-tab-btn:hover {
            color: var(--text-main);
            background: var(--bg-hover, rgba(255,255,255,0.05));
        }
        .events-tab-btn.active {
            background: rgba(56, 189, 248, 0.15);
            border-color: rgba(56, 189, 248, 0.35);
            color: var(--text-main);
        }
        .events-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }
        .events-table th {
            padding: 8px 10px;
            background: var(--bg-hover, rgba(255, 255, 255, 0.04));
            color: var(--text-muted);
            font-weight: 600;
            text-align: left;
            position: sticky;
            top: 0;
            z-index: 1;
            border-bottom: 1px solid var(--border-color, rgba(255,255,255,0.1));
        }
        .events-table td {
            padding: 7px 10px;
            border-bottom: 1px solid var(--border-color, rgba(255, 255, 255, 0.04));
            color: var(--text-main);
        }
        .events-table tr:hover td {
            background: var(--bg-hover, rgba(255, 255, 255, 0.03));
        }
        .event-badge {
            display: inline-block;
            padding: 2px 7px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.3px;
        }
        .badge-div {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
        }
        .badge-jcp {
            background: rgba(34, 197, 94, 0.15);
            color: #22c55e;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }
        .badge-split {
            background: rgba(245, 158, 11, 0.15);
            color: #f59e0b;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        .badge-inplit {
            background: rgba(239, 68, 68, 0.15);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .badge-bonus {
            background: rgba(20, 184, 166, 0.15);
            color: #14b8a6;
            border: 1px solid rgba(20, 184, 166, 0.3);
        }
        .badge-other {
            background: rgba(168, 85, 247, 0.15);
            color: #a855f7;
            border: 1px solid rgba(168, 85, 247, 0.3);
        }

        body.theme-light .btn-toggle-events {
            background: #f1f5f9;
            border-color: #cbd5e1;
            color: #0f172a;
        }
        body.theme-light .btn-toggle-events:hover {
            background: #e2e8f0;
            border-color: #0284c7;
            color: #0284c7;
        }
        body.theme-light .events-tab-btn.active {
            background: rgba(2, 132, 199, 0.12);
            border-color: rgba(2, 132, 199, 0.3);
            color: #0284c7;
        }
        body.theme-light .events-table th {
            background: #f1f5f9;
            color: #475569;
            border-bottom: 2px solid #cbd5e1;
        }
        body.theme-light .events-table td {
            color: #0f172a;
            border-bottom: 1px solid #e2e8f0;
        }
        body.theme-light .badge-div {
            background: rgba(2, 132, 199, 0.12);
            color: #0284c7;
            border-color: rgba(2, 132, 199, 0.25);
        }
        body.theme-light .badge-jcp {
            background: rgba(22, 163, 74, 0.12);
            color: #16a34a;
            border-color: rgba(22, 163, 74, 0.25);
        }
        body.theme-light .badge-split {
            background: rgba(217, 119, 6, 0.12);
            color: #d97706;
            border-color: rgba(217, 119, 6, 0.25);
        }
        body.theme-light .badge-inplit {
            background: rgba(220, 38, 38, 0.12);
            color: #dc2626;
            border-color: rgba(220, 38, 38, 0.25);
        }
        body.theme-light .badge-bonus {
            background: rgba(13, 148, 136, 0.12);
            color: #0d9488;
            border-color: rgba(13, 148, 136, 0.25);
        }


        /* =========================================================
           ESTILOS DO HEATMAP DE MERCADO (POR SETOR & FAIXAS DE P/L)
           ========================================================= */
        .app-tab-nav {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 12px;
        }

        .app-tab-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 9px 18px;
            font-size: 14px;
            font-weight: 600;
            color: var(--text-muted);
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.25s ease;
            user-select: none;
        }

        .app-tab-btn:hover {
            color: var(--text-main);
            background: rgba(255, 255, 255, 0.07);
            border-color: rgba(255, 255, 255, 0.2);
        }

        .app-tab-btn.active {
            color: #ffffff;
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.35), rgba(59, 130, 246, 0.35));
            border-color: #38bdf8;
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
        }

        body.theme-light .app-tab-btn {
            background: #ffffff;
            border-color: #e2e8f0;
            color: #64748b;
        }

        body.theme-light .app-tab-btn:hover {
            background: #f1f5f9;
            color: #0f172a;
        }

        body.theme-light .app-tab-btn.active {
            color: #0369a1;
            background: #e0f2fe;
            border-color: #38bdf8;
            box-shadow: 0 2px 8px rgba(14, 165, 233, 0.2);
        }

        /* Container da Aba Heatmap */
        #tabHeatmapContent {
            display: none;
            width: 100%;
            animation: fadeInTab 0.3s ease;
        }

        #tabDetailContent {
            display: block;
            width: 100%;
            animation: fadeInTab 0.3s ease;
        }

        @keyframes fadeInTab {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Cabeçalho de Filtros do Heatmap */
        .heatmap-header-card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 18px 24px;
            margin-bottom: 22px;
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }

        .heatmap-filters {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 12px;
        }

        .heatmap-search-box {
            position: relative;
            min-width: 240px;
        }

        .heatmap-search-box input {
            width: 100%;
            padding: 8px 14px 8px 32px;
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid var(--border);
            border-radius: 6px;
            color: var(--text-main);
            font-size: 13px;
            outline: none;
            transition: all 0.2s ease;
        }

        body.theme-light .heatmap-search-box input {
            background: #ffffff;
            border-color: #cbd5e1;
        }

        .heatmap-search-box input:focus {
            border-color: #38bdf8;
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
        }

        .heatmap-search-icon {
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 13px;
            color: var(--text-muted);
            pointer-events: none;
        }

        /* Legenda das Cores */
        .heatmap-legend {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 10px;
            font-size: 12px;
        }

        .legend-item {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            border-radius: 6px;
            font-weight: 600;
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            user-select: none;
        }

        .legend-item:hover {
            transform: translateY(-2px);
            filter: brightness(1.2);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
        }

        .legend-item.active {
            outline: 2px solid #ffffff;
            outline-offset: 2px;
            transform: scale(1.04);
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.4);
        }

        body.theme-light .legend-item.active {
            outline: 2px solid #0f172a;
            box-shadow: 0 0 12px rgba(15, 23, 42, 0.3);
        }

        .legend-item-all {
            background: rgba(255, 255, 255, 0.08);
            border-color: var(--border);
            color: var(--text-main);
        }
        body.theme-light .legend-item-all {
            background: #e2e8f0;
            color: #1e293b;
        }

        /* Cores das Faixas — Sugestão A: Obsidian Velvet / TradingView Pro */
        /* 0 - 8 Esmeralda Profundo (Excelente Desconto) */
        .color-pl-limao {
            background: linear-gradient(160deg, rgba(16, 185, 129, 0.14), rgba(5, 150, 105, 0.08));
            border-color: rgba(16, 185, 129, 0.32) !important;
            color: #34d399 !important;
        }
        body.theme-light .color-pl-limao {
            background: linear-gradient(135deg, rgba(0, 200, 83, 0.15), rgba(16, 185, 129, 0.22));
            border-color: #00c853 !important;
            color: #008738 !important;
        }

        /* 8 - 15 Teal / Verde-Água Suave (Atrativo) */
        .color-pl-verde {
            background: linear-gradient(160deg, rgba(20, 184, 166, 0.12), rgba(13, 148, 136, 0.06));
            border-color: rgba(20, 184, 166, 0.28) !important;
            color: #2dd4bf !important;
        }
        body.theme-light .color-pl-verde {
            background: linear-gradient(135deg, rgba(22, 163, 74, 0.12), rgba(21, 128, 61, 0.18));
            border-color: #16a34a !important;
            color: #15803d !important;
        }

        /* 15 - 25 Azul-Ciano Calmo / Neutro Intermediário */
        .color-pl-claro {
            background: linear-gradient(160deg, rgba(56, 189, 248, 0.11), rgba(14, 165, 233, 0.05));
            border-color: rgba(56, 189, 248, 0.26) !important;
            color: #38bdf8 !important;
        }
        body.theme-light .color-pl-claro {
            background: linear-gradient(135deg, rgba(14, 165, 233, 0.10), rgba(2, 132, 199, 0.16));
            border-color: #0284c7 !important;
            color: #0369a1 !important;
        }

        /* 25 - 50 Âmbar Dourado Suave (Esticado) */
        .color-pl-vm-claro {
            background: linear-gradient(160deg, rgba(245, 158, 11, 0.12), rgba(217, 119, 6, 0.06));
            border-color: rgba(245, 158, 11, 0.28) !important;
            color: #fbbf24 !important;
        }
        body.theme-light .color-pl-vm-claro {
            background: linear-gradient(135deg, rgba(234, 88, 12, 0.12), rgba(220, 38, 38, 0.16));
            border-color: #ea580c !important;
            color: #c2410c !important;
        }

        /* > 50 ou Prejuízo Rosa-Rubi Suave / Alerta */
        .color-pl-vm-forte {
            background: linear-gradient(160deg, rgba(244, 63, 94, 0.13), rgba(190, 18, 60, 0.07));
            border-color: rgba(244, 63, 94, 0.30) !important;
            color: #fb7185 !important;
        }
        body.theme-light .color-pl-vm-forte {
            background: linear-gradient(135deg, rgba(220, 38, 38, 0.14), rgba(185, 28, 28, 0.22));
            border-color: #dc2626 !important;
            color: #b91c1c !important;
        }

        /* Sem dados de P/L */
        .color-pl-nd {
            background: rgba(39, 39, 42, 0.45);
            border-color: rgba(82, 82, 91, 0.35) !important;
            color: #94a3b8 !important;
        }
        body.theme-light .color-pl-nd {
            background: rgba(148, 163, 184, 0.12);
            border-color: rgba(148, 163, 184, 0.4) !important;
            color: #64748b !important;
        }

        /* Grid por Setores */
        .heatmap-sectors-container {
            display: flex;
            flex-direction: column;
            gap: 22px;
            width: 100%;
        }

        .sector-group {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 18px 20px 22px 20px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
        }

        .sector-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }

        .sector-title-text {
            font-size: 15px;
            font-weight: 700;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .sector-count-badge {
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
        }

        body.theme-light .sector-count-badge {
            background: #e2e8f0;
            color: #475569;
        }

        /* Grade de Cards das Ações */
        .sector-cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(138px, 1fr));
            gap: 10px;
        }

        .heatmap-stock-tile {
            position: relative;
            padding: 10px 10px 8px 10px;
            border-radius: 8px;
            border: 1px solid;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            min-height: 82px;
            text-align: left;
            user-select: none;
            overflow: hidden;
        }

        .heatmap-stock-tile:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35);
            z-index: 10;
        }

        body.theme-light .heatmap-stock-tile:hover {
            box-shadow: 0 8px 18px rgba(0, 0, 0, 0.12);
        }

        .tile-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 4px;
        }

        .tile-ticker {
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.02em;
            color: #f8fafc;
        }

        body.theme-light .tile-ticker {
            color: #0f172a;
        }

        .tile-price {
            font-size: 11px;
            font-weight: 600;
            color: #cbd5e1;
        }

        body.theme-light .tile-price {
            color: #334155;
        }

        .tile-name {
            font-size: 10px;
            color: #94a3b8;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-bottom: 6px;
        }

        body.theme-light .tile-name {
            color: #475569;
            font-weight: 500;
        }

        .tile-bottom {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            margin-top: auto;
            padding-top: 5px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
        }

        body.theme-light .tile-bottom {
            border-top: 1px solid rgba(0, 0, 0, 0.06);
        }

        .tile-pl-val {
            font-size: 14px;
            font-weight: 800;
        }

        .tile-pl-tag {
            font-size: 10.5px;
            font-weight: 700;
            letter-spacing: 0.2px;
            display: inline-flex;
            align-items: center;
            gap: 2px;
            padding: 2px 7px;
            border-radius: 999px;
            background: rgba(9, 9, 11, 0.45);
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        body.theme-light .tile-pl-tag {
            background: rgba(0, 0, 0, 0.05);
            border-color: rgba(0, 0, 0, 0.06);
        }

        .diff-tag-discount {
            color: #6ee7b7;
        }
        body.theme-light .diff-tag-discount {
            color: #15803d;
        }

        .diff-tag-premium {
            color: #fda4af;
        }
        body.theme-light .diff-tag-premium {
            color: #b91c1c;
        }

        .diff-tag-neutral {
            color: var(--text-muted);
        }

        /* Tooltip rápido ao pairar */
        .heatmap-stock-tile .tile-view-hint {
            position: absolute;
            right: 6px;
            top: 6px;
            font-size: 10px;
            opacity: 0;
            transition: opacity 0.2s ease;
        }

        .heatmap-stock-tile:hover .tile-view-hint {
            opacity: 0.9;
        }
    
</style>

<style id="glass-pro-design-system">
/* =====================================================================
   GLASS PRO DESIGN SYSTEM + RESPONSIVIDADE & CORREÇÃO DE OVERFLOW
   ===================================================================== */
:root {
    --bg: #09090b;                              /* zinc-950 */
    --card-bg: rgba(24, 24, 27, 0.55);          /* zinc-900/55 */
    --border: #27272a;                          /* zinc-800 */
    --border-strong: #3f3f46;                   /* zinc-700 */
    --text-main: #fafafa;                       /* zinc-50 */
    --text-muted: #a1a1aa;                      /* zinc-400 */
    --text-faint: #71717a;                      /* zinc-500 */
    --grid-color: rgba(255, 255, 255, 0.05);
    --slider-bg: rgba(24, 24, 27, 0.8);
    --slider-track: #27272a;
    --accent: #38bdf8;
    --accent-blue: #38bdf8;
    --accent-green: #34d399;
    --accent-orange: #fb923c;
    --accent-red: #fb7185;
    --accent-yellow: #fbbf24;
    --mean-line: #71717a;
    --radius: 14px;
    --glass-bg: rgba(24, 24, 27, 0.8);          /* bg-zinc-900/80 */
    --glass-border: #27272a;                    /* border-zinc-800 */
    --glass-blur: blur(12px);                   /* backdrop-blur-md */
    --surface-blur: blur(10px) saturate(140%);
    --surface-highlight: inset 0 1px 0 0 rgba(255, 255, 255, 0.04);
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.35);
    --shadow-lg: 0 24px 60px -16px rgba(0, 0, 0, 0.75);
    --hover-bg: rgba(255, 255, 255, 0.05);
    --inset-bg: rgba(9, 9, 11, 0.45);
    --font-sans: 'Inter', ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    --font-mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}

body.theme-light {
    --bg: #f4f4f5;                              /* zinc-100 */
    --card-bg: rgba(255, 255, 255, 0.72);
    --border: #e4e4e7;                          /* zinc-200 */
    --border-strong: #d4d4d8;                   /* zinc-300 */
    --text-main: #09090b;
    --text-muted: #52525b;                      /* zinc-600 */
    --text-faint: #71717a;
    --grid-color: rgba(9, 9, 11, 0.06);
    --accent: #0284c7;
    --mean-line: #71717a;
    --glass-bg: rgba(255, 255, 255, 0.82);
    --glass-border: #e4e4e7;
    --surface-highlight: inset 0 1px 0 0 rgba(255, 255, 255, 0.9);
    --shadow-sm: 0 1px 2px rgba(9, 9, 11, 0.06);
    --shadow-lg: 0 24px 60px -16px rgba(9, 9, 11, 0.22);
    --hover-bg: rgba(9, 9, 11, 0.04);
    --inset-bg: rgba(244, 244, 245, 0.75);
}

/* ---------- Base, Tipografia e Prevenção de Quebra Horizontal ---------- */
* { font-family: var(--font-sans); box-sizing: border-box; }
html, body {
    background: var(--bg);
    overflow-x: hidden;
    max-width: 100vw;
}
body {
    background-color: var(--bg);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-feature-settings: 'cv02', 'cv03', 'cv04', 'cv11';
    text-rendering: optimizeLegibility;
    position: relative;
    isolation: isolate;
}
::selection { background: rgba(56, 189, 248, 0.28); color: inherit; }
* { scrollbar-width: thin; scrollbar-color: #3f3f46 transparent; }
body.theme-light * { scrollbar-color: #d4d4d8 transparent; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 999px; border: 3px solid transparent; background-clip: content-box; }
body.theme-light ::-webkit-scrollbar-thumb { background: #d4d4d8; border: 3px solid transparent; background-clip: content-box; }
button:focus-visible, input:focus-visible, select:focus-visible { outline: 2px solid rgba(56, 189, 248, 0.55); outline-offset: 2px; }

/* IMPORTANTE: Desativa a transition de max-width no .container para que o Chart.js
   não leia larguras intermediárias de animação quando troca de Expandido -> Conforto/Compacto */
.container {
    transition: none !important;
    width: 100%;
    max-width: 1440px;
}
body.mode-compact .container {
    max-width: 1180px;
}
body.mode-expanded .container {
    max-width: 100%;
    padding: 0 12px;
}

/* Garante que filhos de Grid/Flex encolham em vez de estourar a página para a direita */
.charts-container > *,
.cards-grid > *,
.chart-box,
.card,
.chart-canvas-wrapper {
    min-width: 0 !important;
    max-width: 100%;
}
.charts-container {
    grid-template-columns: minmax(0, 1fr);
}
@media (min-width: 1024px) {
    .charts-container {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}
@media (min-width: 1560px) {
    body.mode-expanded .charts-container {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}
.cards-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
}
@media (min-width: 768px) {
    .cards-grid {
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }
}
@media (min-width: 1024px) {
    .cards-grid {
        grid-template-columns: repeat(5, minmax(0, 1fr));
    }
}
.chart-canvas-wrapper {
    flex: 1 1 0% !important;
    min-height: 170px;
    height: auto !important;
    overflow: hidden;
}
.chart-canvas-wrapper canvas {
    max-width: 100% !important;
}

/* Ambiente: brilhos suaves + grade técnica esmaecida */
body::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    background:
        radial-gradient(60rem 38rem at 8% -12%, rgba(56, 189, 248, 0.11), transparent 60%),
        radial-gradient(52rem 34rem at 96% -4%, rgba(139, 92, 246, 0.09), transparent 60%),
        radial-gradient(48rem 36rem at 50% 112%, rgba(16, 185, 129, 0.06), transparent 60%);
}
body::after {
    content: "";
    position: fixed;
    inset: 0;
    z-index: -1;
    pointer-events: none;
    background-image:
        linear-gradient(rgba(255, 255, 255, 0.028) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.028) 1px, transparent 1px);
    background-size: 44px 44px;
    -webkit-mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, #000 35%, transparent 80%);
    mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, #000 35%, transparent 80%);
}
body.theme-light::before {
    background:
        radial-gradient(60rem 38rem at 8% -12%, rgba(56, 189, 248, 0.16), transparent 60%),
        radial-gradient(52rem 34rem at 96% -4%, rgba(139, 92, 246, 0.10), transparent 60%),
        radial-gradient(48rem 36rem at 50% 112%, rgba(16, 185, 129, 0.08), transparent 60%);
}
body.theme-light::after {
    background-image:
        linear-gradient(rgba(9, 9, 11, 0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(9, 9, 11, 0.045) 1px, transparent 1px);
}

@keyframes glassPopIn {
    from { opacity: 0; transform: translateY(-4px) scale(0.985); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes glassModalIn {
    from { opacity: 0; transform: scale(0.97); }
    to   { opacity: 1; transform: scale(1); }
}
@keyframes glassFadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}

/* ---------- Barra de navegação superior (menu flutuante em vidro) ---------- */
.app-tab-nav {
    position: sticky;
    top: 10px;
    z-index: 900;
    gap: 4px;
    padding: 5px;
    margin-bottom: 20px;
    flex-wrap: wrap;
    background: var(--glass-bg);
    -webkit-backdrop-filter: var(--glass-blur) saturate(150%);
    backdrop-filter: var(--glass-blur) saturate(150%);
    border: 1px solid var(--glass-border);
    border-radius: 14px;
    box-shadow: 0 10px 30px -14px rgba(0, 0, 0, 0.65), var(--surface-highlight);
}
body.theme-light .app-tab-nav { box-shadow: 0 10px 30px -14px rgba(9, 9, 11, 0.18), var(--surface-highlight); }
.app-tab-theme-toggle {
    margin-left: auto;
    display: flex;
    align-items: center;
}
.brand {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 2px 6px 2px 3px;
    user-select: none;
}
.brand-mark {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    display: inline-grid;
    place-items: center;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #ffffff;
    background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 60%, #8b5cf6 100%);
    box-shadow: 0 4px 14px -4px rgba(99, 102, 241, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.25);
}
.brand-text { display: flex; flex-direction: column; line-height: 1.1; }
.brand-text strong { font-size: 13px; font-weight: 700; letter-spacing: -0.01em; color: var(--text-main); }
.brand-text small { font-size: 10px; font-weight: 500; color: var(--text-faint); letter-spacing: 0.04em; }
.app-tab-divider { width: 1px; height: 22px; background: var(--border); margin: 0 2px; }
.app-tab-btn {
    padding: 7px 10px;
    font-size: 12.5px;
    font-weight: 500;
    color: var(--text-muted);
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    white-space: nowrap;
    transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}
.app-tab-btn:hover { color: var(--text-main); background: var(--hover-bg); border-color: transparent; }
.app-tab-btn.active {
    color: #fafafa;
    background: #27272a;
    border-color: #3f3f46;
    box-shadow: var(--shadow-sm), inset 0 1px 0 rgba(255, 255, 255, 0.06);
}
body.theme-light .app-tab-btn { background: transparent; border-color: transparent; color: #52525b; }
body.theme-light .app-tab-btn:hover { background: rgba(9, 9, 11, 0.04); color: #09090b; }
body.theme-light .app-tab-btn.active {
    color: #09090b;
    background: #ffffff;
    border-color: #e4e4e7;
    box-shadow: 0 1px 3px rgba(9, 9, 11, 0.08);
}
.app-tab-btn .sector-count-badge {
    font-size: 10px;
    font-weight: 600;
    padding: 1px 6px;
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.04);
    font-variant-numeric: tabular-nums;
}

/* ---------- Header ---------- */
.header { border-bottom: 1px solid var(--border); padding-bottom: 18px; margin-bottom: 20px; }
.title-area h1 { font-weight: 700; letter-spacing: -0.025em; }
.badge {
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.06em;
    padding: 3px 9px;
    border-radius: 999px;
    color: #7dd3fc;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.25);
}
body.theme-light .badge { color: #0369a1; background: rgba(2, 132, 199, 0.08); border-color: rgba(2, 132, 199, 0.25); }
.title-area p { color: var(--text-muted); }
@media (min-width: 992px) {
    .header { gap: 24px; }
    .title-area { flex: 0 0 auto; }
    .controls { flex: 1 1 0; min-width: 0; }
}
.earnings-badge { flex-wrap: wrap; row-gap: 4px; }
.earnings-badge strong { font-variant-numeric: tabular-nums; }
.timing-badge { border-radius: 999px; font-size: 10.5px; padding: 2px 8px; }

/* Badge P/L IBOV */
.ibov-pe-badge,
body.theme-light .ibov-pe-badge {
    background: var(--card-bg);
    -webkit-backdrop-filter: var(--surface-blur);
    backdrop-filter: var(--surface-blur);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 7px 14px;
    box-shadow: var(--surface-highlight), var(--shadow-sm);
}
.ibov-pe-badge .tag { font-size: 11px; font-weight: 600; letter-spacing: 0.06em; color: var(--text-muted); }
.ibov-pe-badge .val { font-size: 17px; font-weight: 700; letter-spacing: -0.02em; color: var(--accent); font-variant-numeric: tabular-nums; }
.ibov-pe-badge .desc { font-size: 11px; font-weight: 500; color: var(--text-faint); }
body.theme-light .ibov-pe-badge .tag { color: #52525b; }
body.theme-light .ibov-pe-badge .val { color: #0284c7; }

/* ---------- Inputs / Combobox / Select ---------- */
select,
.combobox-input,
.heatmap-search-box input,
#heatmapSectorFilter {
    background: var(--card-bg) !important;
    color: var(--text-main) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-weight: 500;
    -webkit-backdrop-filter: var(--surface-blur);
    backdrop-filter: var(--surface-blur);
    box-shadow: var(--surface-highlight);
    transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}
select:hover, .combobox-input:hover, .heatmap-search-box input:hover { border-color: var(--border-strong) !important; }
select:focus,
.combobox-input:focus,
.heatmap-search-box input:focus,
body.theme-light .combobox-input:focus {
    border-color: rgba(56, 189, 248, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.15) !important;
    outline: none;
}
.combobox-input::placeholder, .heatmap-search-box input::placeholder { color: var(--text-faint); }
select option { background: #18181b; color: #fafafa; }
body.theme-light select option { background: #ffffff; color: #09090b; }

/* Popover do combobox — Glass (bg-zinc-900/80 backdrop-blur-md border-zinc-800) */
.combobox-dropdown,
body.theme-light .combobox-dropdown {
    top: calc(100% + 6px);
    padding: 4px;
    background: var(--glass-bg) !important;
    -webkit-backdrop-filter: var(--glass-blur) saturate(150%);
    backdrop-filter: var(--glass-blur) saturate(150%);
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px;
    box-shadow: var(--shadow-lg), var(--surface-highlight) !important;
    animation: glassPopIn 0.16s cubic-bezier(0.16, 1, 0.3, 1);
    transform-origin: top center;
}
.combobox-item {
    border-bottom: none;
    border-radius: 8px;
    padding: 8px 10px;
    transition: background 0.12s ease, color 0.12s ease;
}
.combobox-item:hover, .combobox-item.active { background: rgba(255, 255, 255, 0.06); color: #fafafa; }
body.theme-light .combobox-item:hover, body.theme-light .combobox-item.active { background: rgba(9, 9, 11, 0.05); color: #09090b; }
.combobox-item-ticker { font-weight: 600; letter-spacing: 0.01em; }
.combobox-item-name { color: var(--text-faint); }
.combobox-arrow { color: var(--text-faint); font-size: 9px; }

/* ---------- Segmented controls (Tema / Layout / Período) ---------- */
.period-selector,
body.theme-light .period-selector {
    background: var(--card-bg) !important;
    -webkit-backdrop-filter: var(--surface-blur);
    backdrop-filter: var(--surface-blur);
    border: 1px solid var(--border) !important;
    border-radius: 10px;
    padding: 3px !important;
    gap: 2px;
    box-shadow: var(--surface-highlight);
}
.period-btn {
    color: var(--text-muted);
    font-weight: 500;
    border-radius: 7px;
    transition: color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}
.period-btn:hover { color: var(--text-main); background: var(--hover-bg); }
.period-btn.active {
    background: #27272a;
    color: #fafafa;
    font-weight: 600;
    box-shadow: var(--shadow-sm), inset 0 1px 0 rgba(255, 255, 255, 0.07);
}
body.theme-light .period-btn { color: #52525b; }
body.theme-light .period-btn.active {
    background: #ffffff;
    color: #09090b;
    box-shadow: 0 1px 3px rgba(9, 9, 11, 0.1), 0 0 0 1px rgba(9, 9, 11, 0.04);
}

/* ---------- Superfícies de vidro (KPI cards, gráficos, heatmap) ---------- */
.card,
.chart-box,
.heatmap-header-card,
.sector-group {
    background: var(--card-bg);
    -webkit-backdrop-filter: var(--surface-blur);
    backdrop-filter: var(--surface-blur);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--surface-highlight), var(--shadow-sm);
}
body.theme-light .card,
body.theme-light .chart-box,
body.theme-light .sector-group,
body.theme-light .heatmap-header-card {
    box-shadow: var(--surface-highlight), 0 1px 3px rgba(9, 9, 11, 0.05), 0 8px 24px -12px rgba(9, 9, 11, 0.08);
}
.chart-box {
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.chart-box:hover, .sector-group:hover { border-color: var(--border-strong); }

/* KPI cards */
.cards-grid { gap: 14px; margin-bottom: 22px; }
.card { padding: 16px 18px; gap: 6px; transition: border-color 0.2s ease, transform 0.2s ease; }
.card:hover { border-color: var(--border-strong); transform: translateY(-1px); }
.card.card-blue   { --card-accent: var(--accent-blue); }
.card.card-green  { --card-accent: var(--accent-green); }
.card.card-orange { --card-accent: var(--accent-orange); }
.card.card-yellow { --card-accent: var(--accent-yellow); }
.card.card-red    { --card-accent: var(--accent-red); }
.card.card-blue::before,
.card.card-green::before,
.card.card-orange::before,
.card.card-yellow::before,
.card.card-red::before {
    top: 0;
    left: 14px;
    right: 14px;
    width: auto;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--card-accent), transparent);
    opacity: 0.9;
}
.card::after {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background: radial-gradient(120% 90% at 0% 0%, color-mix(in srgb, var(--card-accent, #38bdf8) 9%, transparent), transparent 60%);
}
.card-label {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.06em;
    color: var(--text-muted);
}
.card-label::before {
    content: "";
    width: 6px;
    height: 6px;
    border-radius: 999px;
    background: var(--card-accent, var(--accent));
    box-shadow: 0 0 10px var(--card-accent, var(--accent));
    flex-shrink: 0;
}
.card-value {
    font-size: 24px;
    font-weight: 650;
    letter-spacing: -0.025em;
    font-variant-numeric: tabular-nums;
    line-height: 1.2;
}
.card-sub { font-size: 11.5px; color: var(--text-faint); font-variant-numeric: tabular-nums; }

/* Cartões de gráfico + Altura especial para o Card de Preço que contém o Slider Temporal */
.chart-box { padding: 16px 18px; }
.chart-box:has(.time-slider-wrapper) {
    height: 440px;
}
@media (min-width: 768px) {
    .chart-box:has(.time-slider-wrapper) {
        height: 430px;
    }
}
body.mode-compact .chart-box:has(.time-slider-wrapper) {
    height: 405px;
}
body.mode-expanded .chart-box:has(.time-slider-wrapper) {
    height: 440px;
}
.charts-container { gap: 18px; }
.chart-header { margin-bottom: 10px; flex-wrap: wrap; }
.chart-title { font-size: 14px; font-weight: 600; letter-spacing: -0.01em; color: var(--text-main); }
.chart-mean,
body.theme-light .chart-mean {
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 999px;
    color: var(--text-muted);
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border);
    font-variant-numeric: tabular-nums;
}
body.theme-light .chart-mean { background: rgba(9, 9, 11, 0.03); color: #3f3f46; }
.btn-fullscreen,
body.theme-light .btn-fullscreen {
    min-width: 28px;
    height: 28px;
    justify-content: center;
    border-radius: 8px;
    border: 1px solid var(--border);
    color: var(--text-muted);
    background: transparent;
    transition: all 0.15s ease;
}
.btn-fullscreen:hover { color: var(--text-main); background: var(--hover-bg); border-color: var(--border-strong); }
body.theme-light .btn-fullscreen:hover { background: rgba(9, 9, 11, 0.05); color: #09090b; border-color: #d4d4d8; }

/* Sliders e Time Slider Wrapper (responsivo dentro do card) */
.chart-slider-box,
body.theme-light .chart-slider-box {
    background: var(--inset-bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 5px 10px;
    color: var(--text-faint);
    flex-shrink: 0;
}
.slider-track,
#containerTime .slider-track { background: #27272a !important; }
body.theme-light .slider-track,
body.theme-light #containerTime .slider-track { background: #e4e4e7 !important; }
.slider-range-fill { background: linear-gradient(90deg, #0ea5e9, #38bdf8); }
#fillTime { background: linear-gradient(90deg, #0ea5e9, #818cf8) !important; }
.dual-slider-container input[type="range"]::-webkit-slider-thumb,
#sliderTimeStart::-webkit-slider-thumb,
#sliderTimeEnd::-webkit-slider-thumb {
    background: #fafafa;
    border: 2px solid #0ea5e9;
    box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.15), 0 2px 6px rgba(0, 0, 0, 0.5);
}
.dual-slider-container input[type="range"]::-moz-range-thumb,
#sliderTimeStart::-moz-range-thumb,
#sliderTimeEnd::-moz-range-thumb {
    background: #fafafa;
    border: 2px solid #0ea5e9;
    box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.15), 0 2px 6px rgba(0, 0, 0, 0.5);
}
span[id^="sliderVal"] { font-family: var(--font-mono); font-size: 11px; font-variant-numeric: tabular-nums; }
.chart-slider-box .btn-reset-slider,
body.theme-light .btn-reset-slider {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-muted);
    border-radius: 7px;
    padding: 3px 9px;
    font-size: 10.5px;
    font-weight: 500;
}
.chart-slider-box .btn-reset-slider:hover { color: var(--text-main); border-color: var(--border-strong); background: var(--hover-bg); }
.time-slider-wrapper,
body.theme-light .time-slider-wrapper {
    background: var(--inset-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 8px 12px !important;
    margin-top: 8px !important;
    flex-shrink: 0;
    width: 100%;
    overflow: hidden;
}
.time-slider-wrapper > div:first-child {
    flex-wrap: wrap;
    gap: 4px 8px;
}
.time-slider-wrapper > div:last-child {
    flex-wrap: wrap;
    gap: 2px 6px;
}
#timeSliderLabel {
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    color: var(--accent) !important;
    max-width: 100%;
    overflow-wrap: anywhere;
}

/* Tabela de precificação */
.val-table { font-size: 13px; font-variant-numeric: tabular-nums; }
.val-table th,
body.theme-light .val-table th {
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.07em;
    color: var(--text-faint);
    border-bottom: 1px solid var(--border);
    padding: 9px 10px;
}
.val-table td { padding: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.04); }
body.theme-light .val-table td { border-bottom: 1px solid rgba(9, 9, 11, 0.06); }
.val-table tbody tr { transition: background 0.12s ease; }
.val-table tbody tr:hover td { background: var(--hover-bg); }
.val-tag { border-radius: 999px; padding: 3px 10px; font-size: 11px; font-weight: 500; letter-spacing: 0.01em; }

/* Modal de tela cheia — Glass + backdrop escurecido */
.chart-box.fullscreen-card {
    top: 16px !important;
    left: 16px !important;
    right: 16px !important;
    bottom: 16px !important;
    background: var(--glass-bg) !important;
    -webkit-backdrop-filter: var(--glass-blur) saturate(150%);
    backdrop-filter: var(--glass-blur) saturate(150%);
    border: 1px solid var(--glass-border) !important;
    border-radius: 18px;
    box-shadow: var(--shadow-lg), var(--surface-highlight) !important;
    animation: glassModalIn 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}
body:has(.chart-box.fullscreen-card) { overflow: hidden; }
body:has(.chart-box.fullscreen-card) .charts-container::before {
    content: "";
    position: fixed;
    inset: 0;
    z-index: 9998;
    background: rgba(9, 9, 11, 0.55);
    -webkit-backdrop-filter: blur(6px);
    backdrop-filter: blur(6px);
    animation: glassFadeIn 0.2s ease;
}
body.theme-light:has(.chart-box.fullscreen-card) .charts-container::before { background: rgba(244, 244, 245, 0.55); }

/* Eventos societários (gaveta) */
.btn-toggle-events,
body.theme-light .btn-toggle-events {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-main);
    border-radius: 9px;
    font-weight: 500;
}
.btn-toggle-events:hover,
body.theme-light .btn-toggle-events:hover { background: var(--hover-bg); border-color: var(--border-strong); color: var(--text-main); }
.events-tab-btn { border-radius: 8px; font-weight: 500; }
.events-tab-btn.active,
body.theme-light .events-tab-btn.active { background: var(--hover-bg); border-color: var(--border); color: var(--text-main); }
.events-table { font-variant-numeric: tabular-nums; }
.events-table th,
body.theme-light .events-table th {
    background: var(--glass-bg);
    -webkit-backdrop-filter: var(--glass-blur);
    backdrop-filter: var(--glass-blur);
    color: var(--text-faint);
    font-size: 10.5px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
}
.events-table td,
body.theme-light .events-table td { border-bottom: 1px solid var(--border); }
.event-badge { border-radius: 999px; font-weight: 600; padding: 2px 8px; }

/* Heatmap */
.heatmap-header-card { padding: 20px 24px; }
.sector-group { padding: 18px 20px 20px; }
.sector-title { border-bottom: 1px solid var(--border); }
.sector-title-text { font-size: 14px; font-weight: 600; letter-spacing: -0.01em; }
.sector-count-badge,
body.theme-light .sector-count-badge {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
}
.heatmap-stock-tile { border-radius: 10px; }
.heatmap-stock-tile:hover { transform: translateY(-2px); box-shadow: 0 12px 28px -10px rgba(0, 0, 0, 0.6); }
.tile-ticker { font-weight: 700; letter-spacing: 0.02em; }
.tile-price, .tile-pl-val { font-variant-numeric: tabular-nums; }
.tile-pl-tag { border-radius: 999px; }
.legend-item { border-radius: 999px; font-weight: 500; padding: 5px 12px; }
.legend-item-all { background: transparent; border-color: var(--border); }
body.theme-light .legend-item-all { background: #ffffff; color: #18181b; }
.legend-item.active { outline: 1.5px solid rgba(250, 250, 250, 0.75); box-shadow: none; transform: none; }
body.theme-light .legend-item.active { outline: 1.5px solid #18181b; box-shadow: none; }

/* Rodapé em pílula de vidro */
footer {
    width: fit-content;
    max-width: 100%;
    margin-left: auto !important;
    margin-right: auto !important;
    padding: 8px 16px;
    border-radius: 999px;
    background: var(--card-bg);
    -webkit-backdrop-filter: var(--surface-blur);
    backdrop-filter: var(--surface-blur);
    border: 1px solid var(--border);
    box-shadow: var(--surface-highlight);
}
footer strong { font-variant-numeric: tabular-nums; }

/* =====================================================================
   RESPONSIVIDADE MOBILE (< 640px)
   ===================================================================== */
@media (max-width: 640px) {
    body { padding: 8px 6px; }
    .container { padding: 0 2px; }
    .brand { display: none; }
    .app-tab-divider { display: none; }
    .app-tab-nav {
        top: 6px;
        padding: 4px;
        gap: 4px;
        margin-bottom: 12px;
        flex-wrap: nowrap;
    }
    .app-tab-btn {
        flex: 1 1 auto;
        justify-content: center;
        padding: 7px 6px;
        font-size: 11.5px;
        gap: 5px;
        white-space: nowrap;
        min-width: 0;
    }
    .app-tab-btn .sector-count-badge {
        font-size: 9.5px;
        padding: 1px 5px;
    }
    .app-tab-theme-toggle {
        margin-left: auto;
        flex-shrink: 0;
    }
    .app-tab-theme-toggle .period-btn {
        padding: 5px 8px !important;
        font-size: 13px !important;
    }
    .header { gap: 10px; padding-bottom: 12px; margin-bottom: 12px; }
    .title-area h1 { font-size: 16.5px; }
    .earnings-badge { font-size: 11px; }
    .controls {
        display: flex;
        flex-direction: column;
        gap: 8px;
        width: 100%;
    }
    .controls > .control-group:nth-child(2) label { display: none; }
    .custom-combobox-wrapper {
        min-width: 0 !important;
        width: 100% !important;
    }
    .ibov-pe-badge {
        width: 100%;
        justify-content: flex-start;
        padding: 7px 10px;
        gap: 6px;
    }
    .ibov-pe-badge .val { font-size: 15px; }
    /* Em mobile, oculta o seletor de modo de tela (Compacto/Conforto/Expandido) pois a tela já é 1 coluna */
    .control-group:has(#btnLayoutCompact) {
        display: none;
    }
    .cards-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        margin-bottom: 14px;
    }
    .card { padding: 12px; }
    .card-value { font-size: 18px; }
    .card-label { font-size: 10px; }
    .card-sub { font-size: 10.5px; }
    /* Faz o 5º card (ROE) ocupar as 2 colunas em mobile para ficar simétrico */
    #kpiCardROE { grid-column: span 2; }
    .chart-box {
        padding: 12px;
        height: 330px;
    }
    .chart-box:has(.time-slider-wrapper) {
        height: 410px;
    }
    .chart-title { font-size: 13px; }
    .chart-mean { font-size: 10px; padding: 2px 7px; }
    .chart-slider-box {
        padding: 4px 8px;
        gap: 6px;
    }
    span[id^="sliderVal"] {
        min-width: 68px !important;
        font-size: 10px !important;
    }
    .time-slider-wrapper {
        padding: 7px 10px !important;
    }
    .time-slider-wrapper > div:first-child {
        font-size: 11px !important;
    }
    /* No celular, esconde o subtítulo longo "(Sincroniza todos os gráficos)" e a dica do meio */
    .time-slider-wrapper > div:last-child > span:nth-child(2) {
        display: none;
    }
    .val-table th, .val-table td {
        padding: 6px 4px;
        font-size: 11px;
    }
    .val-tag {
        font-size: 9.5px;
        padding: 2px 6px;
        white-space: normal;
        line-height: 1.25;
    }
    .heatmap-header-card { padding: 14px; }
    .heatmap-search-box { min-width: 0; width: 100%; }
    .sector-group { padding: 14px; }
    .sector-cards-grid {
        grid-template-columns: repeat(auto-fill, minmax(115px, 1fr));
        gap: 8px;
    }
    footer {
        border-radius: 14px;
        padding: 8px 12px;
        font-size: 11px;
    }
}
/* =====================================================================
   ABA 3: EVENTOS SOCIETÁRIOS B3 (SPLITS, INPLITS, BONIFICAÇÃO, CIS RED CAP)
   ===================================================================== */
#tabEventsContent {
    display: none;
    width: 100%;
    animation: fadeInTab 0.3s ease;
}
.color-ev-split {
    background: linear-gradient(135deg, rgba(0, 230, 118, 0.18), rgba(16, 185, 129, 0.26));
    border-color: rgba(0, 230, 118, 0.55) !important;
    color: #34d399 !important;
}
body.theme-light .color-ev-split {
    background: linear-gradient(135deg, rgba(0, 200, 83, 0.14), rgba(16, 185, 129, 0.22));
    border-color: #16a34a !important;
    color: #15803d !important;
}
.color-ev-inplit {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.20), rgba(185, 28, 28, 0.30));
    border-color: rgba(239, 68, 68, 0.60) !important;
    color: #f87171 !important;
}
body.theme-light .color-ev-inplit {
    background: linear-gradient(135deg, rgba(220, 38, 38, 0.14), rgba(185, 28, 28, 0.22));
    border-color: #dc2626 !important;
    color: #b91c1c !important;
}
.color-ev-bonus {
    background: linear-gradient(135deg, rgba(14, 165, 233, 0.18), rgba(20, 184, 166, 0.25));
    border-color: rgba(56, 189, 248, 0.55) !important;
    color: #38bdf8 !important;
}
body.theme-light .color-ev-bonus {
    background: linear-gradient(135deg, rgba(2, 132, 199, 0.13), rgba(13, 148, 136, 0.20));
    border-color: #0284c7 !important;
    color: #0369a1 !important;
}
.color-ev-cis {
    background: linear-gradient(135deg, rgba(168, 85, 247, 0.20), rgba(139, 92, 246, 0.28));
    border-color: rgba(168, 85, 247, 0.58) !important;
    color: #c084fc !important;
}
body.theme-light .color-ev-cis {
    background: linear-gradient(135deg, rgba(147, 51, 234, 0.13), rgba(126, 34, 206, 0.20));
    border-color: #9333ea !important;
    color: #7e22ce !important;
}
.color-ev-other {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.18), rgba(217, 119, 6, 0.25));
    border-color: rgba(245, 158, 11, 0.55) !important;
    color: #fbbf24 !important;
}
body.theme-light .color-ev-other {
    background: linear-gradient(135deg, rgba(217, 119, 6, 0.13), rgba(180, 83, 9, 0.20));
    border-color: #d97706 !important;
    color: #b45309 !important;
}
.events-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 10px;
}
.event-stock-tile {
    position: relative;
    padding: 11px 12px 9px 12px;
    border-radius: 10px;
    border: 1px solid;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 98px;
    text-align: left;
    user-select: none;
    overflow: hidden;
}
.event-stock-tile:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 28px -10px rgba(0, 0, 0, 0.6);
    z-index: 10;
}
body.theme-light .event-stock-tile:hover {
    box-shadow: 0 10px 22px -8px rgba(0, 0, 0, 0.15);
}
.event-tile-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
    margin-bottom: 3px;
}
.event-tile-type-pill {
    font-size: 9.5px;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 999px;
    letter-spacing: 0.04em;
    background: rgba(0, 0, 0, 0.28);
    text-transform: uppercase;
    white-space: nowrap;
}
body.theme-light .event-tile-type-pill {
    background: rgba(255, 255, 255, 0.65);
}
.event-tile-desc {
    font-size: 10.5px;
    color: var(--text-main);
    opacity: 0.88;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 6px;
    font-weight: 500;
}
.event-tile-bottom {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-top: auto;
    padding-top: 5px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    gap: 6px;
}
body.theme-light .event-tile-bottom {
    border-top: 1px solid rgba(0, 0, 0, 0.08);
}
.event-tile-ratio {
    font-family: var(--font-mono);
    font-size: 13.5px;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
}
.event-tile-date {
    font-family: var(--font-mono);
    font-size: 10.5px;
    font-weight: 600;
    color: var(--text-main);
    opacity: 0.9;
    padding: 2px 6px;
    border-radius: 6px;
    background: rgba(0, 0, 0, 0.22);
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}
body.theme-light .event-tile-date {
    background: rgba(0, 0, 0, 0.06);
}
@media (max-width: 640px) {
    .app-tab-nav {
        flex-wrap: wrap !important;
    }
    .events-cards-grid {
        grid-template-columns: repeat(auto-fill, minmax(145px, 1fr));
        gap: 8px;
    }
}
</style>

</head>

<body>



    <div class="container">


        <!-- Barra de Navegação Superior (Abas: Detalhada vs Heatmap Geral) -->
        <div class="app-tab-nav">
            <div class="brand" title="Dashboard Fundamentalista B3 / CVM"><span class="brand-mark">P/L</span><span class="brand-text"><strong>Fundamentalista</strong><small>B3 · CVM</small></span></div><span class="app-tab-divider"></span>
            <button class="app-tab-btn active" id="btnTabDetail" onclick="switchAppTab('detail')">
                📈 <span>Visão Detalhada do Ativo</span>
            </button>
            <button class="app-tab-btn" id="btnTabHeatmap" onclick="switchAppTab('heatmap')">
                🗺️ <span>Heatmap de Mercado (P/L)</span>
                <span class="sector-count-badge" id="badgeTotalStocksHeatmap">126 Ações</span>
            </button>
            <button class="app-tab-btn" id="btnTabEvents" onclick="switchAppTab('events')">
                🔄 <span>Splits, Inplits & Eventos</span>
                <span class="sector-count-badge" id="badgeTotalEventsTab">233 Eventos</span>
            </button>
            <button class="app-tab-btn" id="btnTabMacro" onclick="switchAppTab('macro')">
                🏛️ <span>Macro & Juros</span>
                <span class="sector-count-badge" id="badgeMacroSelic">--%</span>
            </button>
            <button class="app-tab-btn" id="btnTabIfr" onclick="switchAppTab('ifr')">
                ⚡ <span>Entradas &gt; IFR</span>
                <span class="sector-count-badge" id="badgeTotalAtivosIfr" style="display:inline-flex; align-items:center; gap:6px;">
                    <span class="ifr-pulse-dot"></span>
                    <span id="badgeIfrCountText">5 Ativos</span>
                </span>
            </button>

            <!-- Alternador Global de Tema (🌙 Escuro / ☀️ Claro) -->
            <div class="app-tab-theme-toggle">
                <div class="period-selector" style="padding: 2px;">
                    <button class="period-btn active" id="btnThemeObsidian" onclick="setTheme('obsidian', this)" title="Modo Escuro (Obsidian)" style="font-size: 14px; padding: 6px 12px;">🌙</button>
                    <button class="period-btn" id="btnThemeLight" onclick="setTheme('light', this)" title="Modo Claro" style="font-size: 14px; padding: 6px 12px;">☀️</button>
                </div>
            </div>
        </div>
    
        <div id="tabDetailContent">
<!-- Header -->

        <div class="header">

            <div class="title-area">

                <h1 style="display:flex; align-items:center; flex-wrap:wrap; gap:8px;"><span id="headerBrandIcon"></span><span id="headerTitleText">ITUB4 - ITAUUNIBANCO</span> <span class="badge">B3 & CVM</span></h1>

                <p id="headerSubtitle"><span class="earnings-badge" id="earningsBadgeWrapper">📅 Próximo Resultado: <strong id="earningsDateVal">--/--/----</strong> • <span id="earningsTimingVal" class="timing-badge">--</span></span></p>

            </div>

            <div class="controls">

                <!-- P/L Médio IBOV (ao lado esquerdo da seleção de ação) -->

                <div class="control-group">

                    <div class="ibov-pe-badge" title="P/L Agregado Consolidado do IBOV (Earnings Yield ponderado incluindo empresas com prejuízo - Cobertura: 99.65%)">

                        <span class="tag">P/L IBOV:</span>

                        <span class="val" id="ibovPEVal">__IBOV_PE__x</span>

                        <span class="desc">(Agreg.)</span>

                    </div>

                </div>

                <div class="control-group">
                    <label for="tickerSearchInput" style="font-size: 13px; color: var(--text-muted); white-space: nowrap;">Ação / Índice:</label>
                    <div class="custom-combobox-wrapper" id="comboboxWrapper">
                        <input type="text" id="tickerSearchInput" class="combobox-input" placeholder="Buscar ou escolher ação..." autocomplete="off" spellcheck="false">
                        <span class="combobox-arrow" id="comboboxArrow" title="Abrir lista de ações">▼</span>
                        <div class="combobox-dropdown" id="comboboxDropdown">
                            <!-- Itens gerados dinamicamente via JS -->
                        </div>
                        <select id="tickerSelect" style="display:none;" onchange="changeTicker(this.value)"></select>
                    </div>
                </div>

                <!-- Seleção de Período On Demand -->



<!-- Seletor de Modo de Visualização da Tela -->
                <div class="control-group">
                    <div class="period-selector" style="background: rgba(15, 23, 42, 0.9);">
                        <button class="period-btn" id="btnLayoutCompact" onclick="setLayoutMode('compact', this)" title="Visualização compacta para leitura rápida">📱 Compacto</button>
                        <button class="period-btn active" id="btnLayoutNormal" onclick="setLayoutMode('normal', this)" title="Visualização confortável e equilibrada">🖥️ Conforto</button>
                        <button class="period-btn" id="btnLayoutExpanded" onclick="setLayoutMode('expanded', this)" title="Aproveita a tela inteira em 3 colunas balanceadas">📐 Expandido</button>
                    </div>
                </div>

<div class="control-group">

                    <div class="period-selector">

                        <button class="period-btn" data-period-years="1" onclick="setPeriod(1, this)">1 Ano</button>

                        <button class="period-btn" data-period-years="2" onclick="setPeriod(2, this)">2 Anos</button>

                        <button class="period-btn active" data-period-years="5" onclick="setPeriod(5, this)">5 Anos</button>

                        <button class="period-btn" data-period-years="10" onclick="setPeriod(10, this)">10 Anos</button>

                    </div>

                </div>

            </div>

        </div>



        <!-- 5 Cards KPI -->

        <div class="cards-grid">

            <div class="card card-blue" id="kpiCardPrice" style="position: relative;">
                <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                    <span class="card-label">Preço Atual</span>
                    <!-- Indicador / Triângulo de Anomalia do Ativo -->
                    <a id="tickerAnomalyBadge" href="anomalias.html" title="Anomalia detectada nesta ação" style="display: none; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 6px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.45); color: #f87171; text-decoration: none; cursor: pointer; transition: all 0.25s ease;">
                        <svg id="tickerAnomalySvg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; filter: drop-shadow(0 0 5px rgba(239, 68, 68, 0.8));">
                            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                    </a>
                </div>
                <span class="card-value" id="kpiPrice">-</span>
                <span class="card-sub" id="kpiDate">-</span>
            </div>

            <div class="card card-yellow" id="kpiCardDY">

                <span class="card-label">Dividend Yield (TTM)</span>

                <span class="card-value" id="kpiDY">-</span>

                <span class="card-sub" id="kpiDYMean">Média: -</span>

            </div>

            <div class="card card-green">

                <span class="card-label">P/L (TTM)</span>

                <span class="card-value" id="kpiPL">-</span>

                <span class="card-sub" id="kpiPLMean">Média: -</span>

            </div>

            <div class="card card-orange" id="kpiCardPVP">

                <span class="card-label">P/VP Atual</span>

                <span class="card-value" id="kpiPVP">-</span>

                <span class="card-sub" id="kpiPVPMean">Média: -</span>

            </div>

            <div class="card card-red" id="kpiCardROE">

                <span class="card-label">ROE (TTM)</span>

                <span class="card-value" id="kpiROE">-</span>

                <span class="card-sub" id="kpiROEMean">Média: -</span>

            </div>

        </div>



        <!-- Gráficos -->

        <div class="charts-container">

            <div class="chart-box">

                <div class="chart-header">

                    <span class="chart-title">Preço de Fechamento (R$)</span>

                    <div style="display:flex; align-items:center; gap:8px;"><span class="chart-mean" id="badgeEMA50">EMA(50): -</span><button class="btn-fullscreen" onclick="toggleFullscreenChart(this)" title="Maximizar este gráfico em tela cheia">⛶</button></div>

                </div>

                <div class="chart-slider-box">

                    <span style="font-size: 11px; white-space: nowrap;">Eixo Y:</span>

                    <div class="dual-slider-container" id="containerPrice">

                        <div class="slider-track"></div>

                        <div class="slider-range-fill" id="fillPrice"></div>

                        <input type="range" id="sliderMinPrice" oninput="onDualSliderInput('chartPrice', 'min', 'R$ ')">

                        <input type="range" id="sliderMaxPrice" oninput="onDualSliderInput('chartPrice', 'max', 'R$ ')">

                    </div>

                    <span id="sliderValPrice" style="font-weight: 600; color: #fff; min-width: 90px; text-align: center;">Auto</span>

                    <button class="btn-reset-slider" onclick="resetDualSlider('chartPrice', 'R$ ')">Reset</button>

                </div>

                <div class="chart-canvas-wrapper">

                    <canvas id="chartPrice"></canvas>

                </div>
                <!-- Slider de Período Temporal (Controlador Global de Data) -->
                <div class="time-slider-wrapper" style="margin-top: 10px; padding: 10px 14px; background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; font-size: 12px;">
                        <span style="color: #94a3b8; display: flex; align-items: center; gap: 6px;">
                            📅 <b>Período Histórico (Sincroniza todos os gráficos):</b>
                        </span>
                        <span id="timeSliderLabel" style="font-weight: 700; color: #38bdf8; font-family: monospace; font-size: 12px;">Carregando...</span>
                    </div>
                    <div class="dual-slider-container" id="containerTime" style="height: 24px; position: relative; width: 100%;">
                        <div class="slider-track" style="height: 6px; background: #334155; border-radius: 3px; position: absolute; width: 100%; top: 9px;"></div>
                        <div class="slider-range-fill" id="fillTime" style="height: 6px; background: linear-gradient(90deg, #0284c7, #38bdf8); border-radius: 3px; position: absolute; top: 9px;"></div>
                        <input type="range" id="sliderTimeStart" min="0" max="100" value="0" oninput="onTimeSliderInput('start')" style="position: absolute; width: 100%; top: 0; pointer-events: none; -webkit-appearance: none; background: transparent; height: 24px; z-index: 3;">
                        <input type="range" id="sliderTimeEnd" min="0" max="100" value="100" oninput="onTimeSliderInput('end')" style="position: absolute; width: 100%; top: 0; pointer-events: none; -webkit-appearance: none; background: transparent; height: 24px; z-index: 4;">
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px; font-size: 10px; color: #64748b;">
                        <span id="timeSliderMinDate">-</span>
                        <span style="color: #94a3b8;">Arraste as pontas para filtrar data inicial e final</span>
                        <span id="timeSliderMaxDate">-</span>
                    </div>
                </div>

            </div>



            <div class="chart-box">

                <div class="chart-header">

                    <span class="chart-title">Preço / Lucro (P/L TTM)</span>

                    <div style="display:flex; align-items:center; gap:8px;"><span class="chart-mean" id="badgeMeanPL">Média: -</span><button class="btn-fullscreen" onclick="toggleFullscreenChart(this)" title="Maximizar este gráfico em tela cheia">⛶</button></div>

                </div>

                <div class="chart-slider-box">

                    <span style="font-size: 11px; white-space: nowrap;">Eixo Y:</span>

                    <div class="dual-slider-container" id="containerPL">

                        <div class="slider-track"></div>

                        <div class="slider-range-fill" id="fillPL"></div>

                        <input type="range" id="sliderMinPL" oninput="onDualSliderInput('chartPL', 'min', '', 'x')">

                        <input type="range" id="sliderMaxPL" oninput="onDualSliderInput('chartPL', 'max', '', 'x')">

                    </div>

                    <span id="sliderValPL" style="font-weight: 600; color: #fff; min-width: 90px; text-align: center;">Auto</span>

                    <button class="btn-reset-slider" onclick="resetDualSlider('chartPL', '', 'x')">Reset</button>

                </div>

                <div class="chart-canvas-wrapper">

                    <canvas id="chartPL"></canvas>

                </div>

            </div>



            <div class="chart-box" id="boxChartPVP">

                <div class="chart-header">

                    <span class="chart-title">Preço / Valor Patrimonial (P/VP)</span>

                    <div style="display:flex; align-items:center; gap:8px;"><span class="chart-mean" id="badgeMeanPVP">Média: -</span><button class="btn-fullscreen" onclick="toggleFullscreenChart(this)" title="Maximizar este gráfico em tela cheia">⛶</button></div>

                </div>

                <div class="chart-slider-box">

                    <span style="font-size: 11px; white-space: nowrap;">Eixo Y:</span>

                    <div class="dual-slider-container" id="containerPVP">

                        <div class="slider-track"></div>

                        <div class="slider-range-fill" id="fillPVP"></div>

                        <input type="range" id="sliderMinPVP" oninput="onDualSliderInput('chartPVP', 'min', '', 'x')">

                        <input type="range" id="sliderMaxPVP" oninput="onDualSliderInput('chartPVP', 'max', '', 'x')">

                    </div>

                    <span id="sliderValPVP" style="font-weight: 600; color: #fff; min-width: 90px; text-align: center;">Auto</span>

                    <button class="btn-reset-slider" onclick="resetDualSlider('chartPVP', '', 'x')">Reset</button>

                </div>

                <div class="chart-canvas-wrapper">

                    <canvas id="chartPVP"></canvas>

                </div>

            </div>



            <div class="chart-box" id="boxChartROE">

                <div class="chart-header">

                    <span class="chart-title">ROE Histórico (TTM %)</span>

                    <div style="display:flex; align-items:center; gap:8px;"><span class="chart-mean" id="badgeMeanROE">Média: -</span><button class="btn-fullscreen" onclick="toggleFullscreenChart(this)" title="Maximizar este gráfico em tela cheia">⛶</button></div>

                </div>

                <div class="chart-slider-box">

                    <span style="font-size: 11px; white-space: nowrap;">Eixo Y:</span>

                    <div class="dual-slider-container" id="containerROE">

                        <div class="slider-track"></div>

                        <div class="slider-range-fill" id="fillROE"></div>

                        <input type="range" id="sliderMinROE" oninput="onDualSliderInput('chartROE', 'min', '', '%')">

                        <input type="range" id="sliderMaxROE" oninput="onDualSliderInput('chartROE', 'max', '', '%')">

                    </div>

                    <span id="sliderValROE" style="font-weight: 600; color: #fff; min-width: 90px; text-align: center;">Auto</span>

                    <button class="btn-reset-slider" onclick="resetDualSlider('chartROE', '', '%')">Reset</button>

                </div>

                <div class="chart-canvas-wrapper">

                    <canvas id="chartROE"></canvas>

                </div>

            </div>



            <div class="chart-box" id="boxChartDY">

                <div class="chart-header">

                    <span class="chart-title">Dividend Yield Histórico (% 12M)</span>

                    <div style="display:flex; align-items:center; gap:8px;"><span class="chart-mean" id="badgeMeanDY">Média: -</span><button class="btn-fullscreen" onclick="toggleFullscreenChart(this)" title="Maximizar este gráfico em tela cheia">⛶</button></div>

                </div>

                <div class="chart-slider-box">

                    <span style="font-size: 11px; white-space: nowrap;">Eixo Y:</span>

                    <div class="dual-slider-container" id="containerDY">

                        <div class="slider-track"></div>

                        <div class="slider-range-fill" id="fillDY"></div>

                        <input type="range" id="sliderMinDY" oninput="onDualSliderInput('chartDY', 'min', '', '%')">

                        <input type="range" id="sliderMaxDY" oninput="onDualSliderInput('chartDY', 'max', '', '%')">

                    </div>

                    <span id="sliderValDY" style="font-weight: 600; color: #fff; min-width: 90px; text-align: center;">Auto</span>

                    <button class="btn-reset-slider" onclick="resetDualSlider('chartDY', '', '%')">Reset</button>

                </div>

                <div class="chart-canvas-wrapper">

                    <canvas id="chartDY"></canvas>

                </div>

            </div>



            <!-- Box Precificação por P/L Médio (Para Ações Individuais, IBOV e IFNC) -->

            <div class="chart-box" id="boxValuationGeneral" style="height: auto; min-height: 320px;">

                <div class="chart-header">

                    <span class="chart-title" id="valCardTitle">Precificação Justa & Zonas de Compra (P/L)</span>

                    <div style="display:flex; align-items:center; gap:8px;"><span class="chart-mean" id="badgeLPA">LPA (TTM): -</span><button class="btn-fullscreen" onclick="toggleFullscreenChart(this)" title="Maximizar esta tabela em tela cheia">⛶</button></div>

                </div>

                <div class="val-table-container" id="containerValTableSingle">

                    <table class="val-table">

                        <thead>

                            <tr>

                                <th>Cenário</th>

                                <th style="text-align: center;">Múltiplo P/L</th>

                                <th style="text-align: center;">vs P/L Médio</th>

                                <th style="text-align: right;">Preço Estimado</th>

                                <th style="text-align: right;">Distância vs Atual</th>

                            </tr>

                        </thead>

                        <tbody id="valTableBody">

                            <!-- Preenchido via renderCharts() -->

                        </tbody>

                    </table>

                </div>

                <!-- Botão e Gaveta no final do Card: Histórico de Proventos e Eventos Societários (B3) -->
                <div id="boxCorporateEventsSection" style="margin-top: 22px; border-top: 1px dashed var(--border-color, rgba(255,255,255,0.08)); padding-top: 14px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 13px; font-weight: 600; color: var(--text-muted); display: inline-flex; align-items: center; gap: 6px;">
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                                Histórico de Proventos, Splits & Grupamentos
                            </span>
                            <span id="badgeEventsCount" style="font-size: 11px; padding: 2px 8px; border-radius: 12px; background: rgba(56, 189, 248, 0.12); color: #38bdf8; font-weight: 600; display: none;"></span>
                        </div>
                        <button id="btnToggleEvents" class="btn-toggle-events" onclick="toggleCorporateEvents()" title="Consultar histórico oficial de dividendos, JCP, desdobramentos e grupamentos da B3">
                            <span id="txtToggleEvents">Ver Histórico B3</span>
                            <span id="iconToggleEvents" style="font-size: 10px; transition: transform 0.25s ease;">▼</span>
                        </button>
                    </div>

                    <!-- Gaveta Expansível -->
                    <div id="drawerCorporateEvents" style="display: none; margin-top: 16px;">
                        <!-- Abas de Navegação -->
                        <div style="display: flex; gap: 8px; border-bottom: 1px solid var(--border-color, rgba(255,255,255,0.08)); padding-bottom: 8px; margin-bottom: 12px;">
                            <button id="tabBtnDividends" class="events-tab-btn active" onclick="switchEventsTab('divs')">
                                💰 Proventos em Dinheiro (<span id="countTabDivs">0</span>)
                            </button>
                            <button id="tabBtnSplits" class="events-tab-btn" onclick="switchEventsTab('splits')">
                                🔄 Splits & Inplits (<span id="countTabSplits">0</span>)
                            </button>
                        </div>

                        <!-- Conteúdo da Aba 1: Proventos em Dinheiro -->
                        <div id="tabContentDividends" style="max-height: 320px; overflow-y: auto;">
                            <!-- Preenchido via renderEventsTable() -->
                        </div>

                        <!-- Conteúdo da Aba 2: Splits e Grupamentos -->
                        <div id="tabContentSplits" style="display: none; max-height: 320px; overflow-y: auto;">
                            <!-- Preenchido via renderEventsTable() -->
                        </div>
                    </div>
                </div>

            </div>

        </div>

        <!-- Seção Especial: 3 Cards Completos de Precificação (BBSE3, CXSE3, PSSA3) para o índice SEGUROS -->
        <div id="containerValCardsMulti" style="display: none; width: 100%; margin-top: 25px;">
            <!-- Preenchido dinamicamente quando SEGUROS estiver ativo -->
        </div>
        </div>


        <!-- Aba 2: Heatmap Completo de Mercado por Setores e Faixas de P/L -->
        <div id="tabHeatmapContent">
            <!-- Cabeçalho & Filtros do Heatmap -->
            <div class="heatmap-header-card">
                <div>
                    <h2 style="font-size: 20px; font-weight: 800; color: var(--text-main); margin-bottom: 4px; display: flex; align-items: center; gap: 8px;">
                        🗺️ Heatmap do Mercado por P/L (TTM)
                    </h2>
                    <p style="font-size: 12px; color: var(--text-muted); margin: 0;">
                        Todas as ações agrupadas por setor econômico. Clique em qualquer bloco para abrir a análise detalhada.
                    </p>
                </div>

                <div class="heatmap-filters">
                    <div class="heatmap-search-box">
                        <span class="heatmap-search-icon">🔍</span>
                        <input type="text" id="heatmapFilterInput" placeholder="Filtrar por ticker ou nome..." oninput="filterHeatmap(this.value)">
                    </div>

                    <div class="control-group" style="margin: 0;">
                        <select id="heatmapSectorFilter" onchange="filterHeatmapSector(this.value)" style="padding: 8px 14px; background: var(--card-bg); color: var(--text-main); border: 1px solid var(--border); border-radius: 6px; font-size: 13px; outline: none; cursor: pointer;">
                            <option value="ALL">🌐 Todos os Setores</option>
                        </select>
                    </div>

                    <div class="control-group" style="margin: 0;" title="Período utilizado para calcular o P/L Médio (Méd:) e o desconto/prêmio (%) de cada ação">
                        <div class="period-selector">
                            <button class="period-btn" data-period-years="1" onclick="setPeriod(1, this)">1 Ano</button>
                            <button class="period-btn" data-period-years="2" onclick="setPeriod(2, this)">2 Anos</button>
                            <button class="period-btn active" data-period-years="5" onclick="setPeriod(5, this)">5 Anos</button>
                            <button class="period-btn" data-period-years="10" onclick="setPeriod(10, this)">10 Anos</button>
                        </div>
                    </div>
                </div>

                <!-- Legenda Oficial e Filtro Interativo por Faixas de P/L -->
                <div class="heatmap-legend" style="width: 100%; padding-top: 10px; border-top: 1px solid var(--border); margin-top: 8px;">
                    <span style="color: var(--text-muted); font-weight: 600; margin-right: 4px;">Filtrar P/L:</span>
                    <span class="legend-item legend-item-all active" id="btnFilterPlAll" onclick="filterHeatmapPL('ALL', this)" title="Exibir todas as ações">🌐 Todas</span>
                    <span class="legend-item color-pl-limao" id="btnFilterPl_0_8" onclick="filterHeatmapPL('0_8', this)" title="Filtrar ações com P/L de 0 a 8x">🟢 0 a 8x</span>
                    <span class="legend-item color-pl-verde" id="btnFilterPl_8_15" onclick="filterHeatmapPL('8_15', this)" title="Filtrar ações com P/L de 8 a 15x">🟢 8 a 15x</span>
                    <span class="legend-item color-pl-claro" id="btnFilterPl_15_25" onclick="filterHeatmapPL('15_25', this)" title="Filtrar ações com P/L de 15 a 25x">🔵 15 a 25x</span>
                    <span class="legend-item color-pl-vm-claro" id="btnFilterPl_25_50" onclick="filterHeatmapPL('25_50', this)" title="Filtrar ações com P/L de 25 a 50x">🟠 25 a 50x</span>
                    <span class="legend-item color-pl-vm-forte" id="btnFilterPl_gt50" onclick="filterHeatmapPL('gt50', this)" title="Filtrar ações com P/L > 50x ou Prejuízo">🔴 > 50x / Prej.</span>
                    <span class="legend-item color-pl-nd" id="btnFilterPl_nd" onclick="filterHeatmapPL('nd', this)" title="Filtrar ações sem P/L">⚪ Sem P/L</span>
                </div>
            </div>

            <!-- Grade Dinâmica dos Setores e Ações -->
            <div class="heatmap-sectors-container" id="heatmapContainer">
                <!-- Preenchido dinamicamente via renderHeatmap() -->
            </div>
        </div>

        <!-- Aba 3: Mapa de Eventos Societários B3 (Splits, Inplits, Bonificações & Cisões) -->
        <div id="tabEventsContent">
            <div class="heatmap-header-card">
                <div>
                    <h2 style="font-size: 20px; font-weight: 800; color: var(--text-main); margin-bottom: 4px; display: flex; align-items: center; gap: 8px;">
                        🔄 Histórico de Splits, Inplits, Bonificações & Cisões (B3)
                    </h2>
                    <p style="font-size: 12px; color: var(--text-muted); margin: 0;">
                        Mapeamento oficial da B3 com data-com, data de aprovação e proporção/fator. Clique em qualquer card para abrir os gráficos da empresa.
                    </p>
                </div>

                <div class="heatmap-filters">
                    <div class="heatmap-search-box">
                        <span class="heatmap-search-icon">🔍</span>
                        <input type="text" id="eventsFilterInput" placeholder="Buscar ticker, empresa, fator ou ano..." oninput="filterEventsMap(this.value)">
                    </div>

                    <div class="control-group" style="margin: 0;">
                        <select id="eventsSectorFilter" onchange="filterEventsSector(this.value)" style="padding: 8px 14px; background: var(--card-bg); color: var(--text-main); border: 1px solid var(--border); border-radius: 6px; font-size: 13px; outline: none; cursor: pointer;">
                            <option value="ALL">🌐 Todos os Setores</option>
                        </select>
                    </div>

                    <div class="control-group" style="margin: 0;">
                        <select id="eventsYearFilter" onchange="filterEventsYear(this.value)" style="padding: 8px 14px; background: var(--card-bg); color: var(--text-main); border: 1px solid var(--border); border-radius: 6px; font-size: 13px; outline: none; cursor: pointer;">
                            <option value="ALL">📅 Todos os Períodos</option>
                            <option value="2025_2026">🔥 2025 – 2026 (Recentes)</option>
                            <option value="2020_2024">📆 2020 – 2024</option>
                            <option value="2015_2019">📆 2015 – 2019</option>
                            <option value="PRE_2015">🏛️ Antes de 2015</option>
                        </select>
                    </div>

                    <div class="control-group" style="margin: 0;">
                        <div class="period-selector" style="padding: 2px;">
                            <button class="period-btn active" id="btnEvViewTimeline" onclick="setEventsViewMode('timeline', this)" title="Ordenar do mais recente para o mais antigo">🕒 Linha do Tempo</button>
                            <button class="period-btn" id="btnEvViewSector" onclick="setEventsViewMode('sector', this)" title="Agrupar por Setor Econômico (Padrão Heatmap)">🏛️ Setores</button>
                        </div>
                    </div>
                </div>

                <!-- Legenda Oficial e Filtro Interativo por Tipo de Evento -->
                <div class="heatmap-legend" style="width: 100%; padding-top: 10px; border-top: 1px solid var(--border); margin-top: 8px;">
                    <span style="color: var(--text-muted); font-weight: 600; margin-right: 4px;">Filtrar Evento:</span>
                    <span class="legend-item legend-item-all active" id="btnFilterEvAll" onclick="filterEventsType('ALL', this)" title="Exibir todos os eventos societários">🌐 Todos (<span id="cntEvAll">0</span>)</span>
                    <span class="legend-item color-ev-split" id="btnFilterEvSplit" onclick="filterEventsType('SPLIT', this)" title="Desdobramento de Ações (Split) - Multiplica quantidade de ações">🟢 Split / Desdobramento (<span id="cntEvSplit">0</span>)</span>
                    <span class="legend-item color-ev-inplit" id="btnFilterEvInplit" onclick="filterEventsType('INPLIT', this)" title="Grupamento de Ações (Inplit) - Consolida ações">🔴 Inplit / Grupamento (<span id="cntEvInplit">0</span>)</span>
                    <span class="legend-item color-ev-bonus" id="btnFilterEvBonus" onclick="filterEventsType('BONUS', this)" title="Bonificação em Ações">🔵 Bonificação (<span id="cntEvBonus">0</span>)</span>
                    <span class="legend-item color-ev-cis" id="btnFilterEvCis" onclick="filterEventsType('CIS', this)" title="Cisão com Redução de Capital (CIS RED CAP)">🟣 CIS RED CAP (<span id="cntEvCis">0</span>)</span>
                    <span class="legend-item color-ev-other" id="btnFilterEvOther" onclick="filterEventsType('OTHER', this)" title="Incorporação, Restituição de Capital e Resgate">🟡 Incorporação / Outros (<span id="cntEvOther">0</span>)</span>
                </div>
            </div>

            <!-- Container Dinâmico dos Cards de Eventos -->
            <div class="heatmap-sectors-container" id="eventsMapContainer">
                <!-- Preenchido dinamicamente via renderEventsHeatmap() -->
            </div>
        </div>

        <!-- Aba 4: Macro & Juros (Copom, Focus, Curva de Juros Tesouro Direto, Regimes & E se?) -->
        <div id="tabMacroContent">
            <!-- Hero Macro & KPIs em Tempo Real -->
            <div class="macro-hero-card macro-section">
                <div class="macro-hero-top">
                    <div>
                        <span class="macro-kicker">POLÍTICA MONETÁRIA · EXPECTATIVAS · CENÁRIOS</span>
                        <h2 class="macro-hero-title">Macro &amp; Juros (Brasil &amp; Global)</h2>
                        <p class="macro-hero-sub">O porquê por trás do preço das ações e índices: ciclo da Selic (Copom), expectativas do Boletim Focus ao vivo, curva de juros do Tesouro Direto com inflação implícita (breakeven), regimes de risco e mapa de transmissão para o mercado brasileiro.</p>
                    </div>
                    <div class="macro-live-pill" id="mcLiveStatusPill" title="Dados pré-carregados via Supabase + atualização automática ao vivo nas APIs do Banco Central">
                        <span class="macro-live-dot"></span>
                        <span id="mcLiveStatusText">Snapshot BCB/Tesouro</span>
                    </div>
                </div>

                <div class="macro-kpi-strip">
                    <div class="macro-kpi-chip highlight">
                        <span class="lbl">Selic Meta</span>
                        <strong id="mcKpiSelic">--%</strong>
                        <small id="mcKpiSelicSrc">BCB · SGS 432</small>
                    </div>
                    <div class="macro-kpi-chip">
                        <span class="lbl">CDI Efetivo</span>
                        <strong id="mcKpiCdi">--%</strong>
                        <small id="mcKpiCdiSrc">BCB · SGS 4389</small>
                    </div>
                    <div class="macro-kpi-chip">
                        <span class="lbl">IPCA 12M</span>
                        <strong id="mcKpiIpca12">--%</strong>
                        <small id="mcKpiIpcaSrc">IBGE · SGS 13522</small>
                    </div>
                    <div class="macro-kpi-chip">
                        <span class="lbl">Juro Real Ex-Post</span>
                        <strong id="mcKpiReal">--%</strong>
                        <small>Selic descontada pelo IPCA 12M</small>
                    </div>
                    <div class="macro-kpi-chip copom">
                        <span class="lbl">Próximo Copom</span>
                        <strong id="mcKpiNextCopom">--</strong>
                        <small id="mcKpiNextCopomSub">Contagem em dias úteis B3</small>
                    </div>
                </div>

                <div class="macro-subnav">
                    <button type="button" class="macro-subnav-btn" onclick="MacroModule.scrollToSection('macroSecJuros')">🏦 Copom &amp; Focus</button>
                    <button type="button" class="macro-subnav-btn" onclick="MacroModule.scrollToSection('macroSecCurva')">📈 Vértices DI1 &amp; Curva de Juros</button>
                    <button type="button" class="macro-subnav-btn" onclick="MacroModule.scrollToSection('macroSecRegimes')">🧭 Regimes de Risco</button>
                    <button type="button" class="macro-subnav-btn" onclick="MacroModule.scrollToSection('macroSecEse')">🔀 Mapa "E se…?"</button>
                </div>
            </div>

            <!-- Bloco 1: Ciclo Copom + Boletim Focus -->
            <div id="macroSecJuros" class="macro-grid-2 macro-section">
                <div class="macro-panel">
                    <div class="macro-panel-head">
                        <div>
                            <span class="macro-kicker orange" id="mcCopomKicker">DECISÕES DO COPOM</span>
                            <h3>Trajetória da Taxa Selic</h3>
                        </div>
                        <div class="period-selector" style="padding: 2px;" id="mcCopomYearTabs">
                            <button type="button" class="period-btn active" onclick="MacroModule.setCopomYear(2026, this)">2026</button>
                            <button type="button" class="period-btn" onclick="MacroModule.setCopomYear(2027, this)">2027</button>
                        </div>
                    </div>
                    <div id="mcCopomChart" class="macro-svg-box"></div>
                    <p class="macro-note" id="mcCopomDesc">
                        Cada decisão do Copom impacta diretamente a ponta curta da curva DI, o CDI da renda fixa e o custo de capital das empresas domésticas na B3 (especialmente varejo, construção e endividadas).
                    </p>
                </div>

                <div class="macro-panel">
                    <div class="macro-panel-head">
                        <div>
                            <span class="macro-kicker">API OLINDA / BANCO CENTRAL</span>
                            <h3>Boletim Focus — Mediana do Mercado</h3>
                        </div>
                        <span class="macro-src-badge" id="mcFocusDate">carregando…</span>
                    </div>
                    <div class="macro-table-wrap">
                        <table class="macro-table">
                            <thead>
                                <tr>
                                    <th>Indicador</th>
                                    <th data-mc-focus-y="0">--</th>
                                    <th data-mc-focus-y="1">--</th>
                                    <th data-mc-focus-y="2">--</th>
                                </tr>
                            </thead>
                            <tbody id="mcFocusBody"></tbody>
                        </table>
                    </div>
                    <p class="macro-note">
                        Setas comparam com a pesquisa anterior (▲ subiu, ▼ caiu, = estável). Publicado às segundas-feiras pelo BCB reunindo projeções de mais de 100 instituições.
                    </p>
                </div>
            </div>

            <!-- Bloco 2: Vértices DI1 + Curva do Tesouro Direto & Breakeven -->
            <div id="macroSecCurva" class="macro-section">
                <div class="macro-panel" style="margin-bottom: 18px;">
                    <div class="macro-grid-12">
                        <div>
                            <span class="macro-kicker">ESTRUTURA A TERMO (DI1)</span>
                            <h3 style="margin: 4px 0 8px 0; font-size: 17px;">Como ler a curva de juros futuros</h3>
                            <p class="macro-note" style="margin-top: 0;">
                                Os contratos DI1 de janeiro são os vértices mais líquidos. A diferença entre a Selic atual e os vértices curtos mostra quanto corte (ou alta) o mercado já precifica. Vértices longos (F31, F33) refletem prêmio fiscal e inflação de prazo.
                            </p>
                            <ul style="margin: 12px 0 0 18px; padding: 0; font-size: 12px; color: var(--text-muted); line-height: 1.6;">
                                <li><strong class="macro-pos">Curva fechando</strong> (taxas caindo) ➔ alívio de valuation para bolsa, varejo e small caps.</li>
                                <li><strong class="macro-neg">Curva abrindo</strong> (taxas subindo) ➔ maior taxa de desconto, pressão nos múltiplos P/L.</li>
                                <li><strong style="color: var(--accent-orange);">Inclinação</strong> (longo − curto) ➔ termômetro de risco fiscal e prêmio de longo prazo.</li>
                            </ul>
                        </div>
                        <div>
                            <div style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                                <span class="macro-kicker" style="margin: 0;">VÉRTICES DI1 VIGENTES (CONTAGEM DU ANBIMA)</span>
                            </div>
                            <div id="mcDiVertices" class="macro-di-grid"></div>
                        </div>
                    </div>
                </div>

                <!-- Painel Curva do Tesouro Direto -->
                <div class="macro-panel" id="mcCurveWrap">
                    <div class="macro-panel-head">
                        <div>
                            <span class="macro-kicker green">CURVA PÚBLICA · TESOURO TRANSPARENTE</span>
                            <h3 id="mcCurveTitle">A curva de juros abriu ou fechou?</h3>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px; align-items: center;">
                            <div class="period-selector" style="padding: 2px;">
                                <button type="button" class="period-btn active" data-mc-ck="pre" onclick="MacroModule.setCurveKind('pre', this)">Prefixada</button>
                                <button type="button" class="period-btn" data-mc-ck="ipca" onclick="MacroModule.setCurveKind('ipca', this)">IPCA+ (real)</button>
                            </div>
                            <div class="period-selector" style="padding: 2px;">
                                <button type="button" class="period-btn active" data-mc-cc="1" onclick="MacroModule.setCurveBack(1, this)">vs ontem</button>
                                <button type="button" class="period-btn" data-mc-cc="5" onclick="MacroModule.setCurveBack(5, this)">1 sem.</button>
                                <button type="button" class="period-btn" data-mc-cc="21" onclick="MacroModule.setCurveBack(21, this)">1 mês</button>
                            </div>
                        </div>
                    </div>

                    <div class="macro-grid-8-4">
                        <div id="mcCurveChart" class="macro-svg-box"></div>
                        <div>
                            <div id="mcCurveKpis" class="macro-curve-kpis"></div>
                            <span class="macro-kicker" style="margin-bottom: 6px;">Variação por vencimento</span>
                            <div id="mcCurveBars" style="margin-bottom: 10px;"></div>
                            <p id="mcCurveRead" class="macro-note"></p>
                        </div>
                    </div>

                    <!-- Bloco Inflação Implícita (Breakeven) -->
                    <div id="mcBeWrap" style="margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--border); display: none;">
                        <div class="macro-panel-head">
                            <div>
                                <span class="macro-kicker orange">INFLAÇÃO IMPLÍCITA (BREAKEVEN)</span>
                                <h3 id="mcBeTitle">Quanta inflação o mercado está precificando?</h3>
                            </div>
                            <span class="macro-src-badge">Prefixado ÷ IPCA+ · média anual até o vencimento</span>
                        </div>
                        <div class="macro-grid-8-4">
                            <div id="mcBeBars"></div>
                            <div>
                                <div id="mcBeFocus" style="padding: 12px; border-radius: 10px; border: 1px solid var(--border); background: rgba(255,255,255,0.03); font-family: var(--font-mono); font-size: 11px;"></div>
                                <p id="mcBeRead" class="macro-note"></p>
                            </div>
                        </div>
                    </div>

                    <p class="macro-note" id="mcCurveSrc" style="font-family: var(--font-mono); font-size: 10.5px; margin-top: 14px; padding-top: 10px; border-top: 1px solid var(--border);"></p>
                </div>
            </div>

            <!-- Bloco 3: Regimes de Risco (Intermercados) -->
            <div id="macroSecRegimes" class="macro-panel macro-section">
                <div class="macro-panel-head" style="padding-bottom: 12px; border-bottom: 1px solid var(--border);">
                    <div>
                        <span class="macro-kicker">GUIA DE LEITURA · INTERMERCADOS</span>
                        <h3>Como os ativos costumam reagir em cada regime de risco</h3>
                    </div>
                    <div class="period-selector" style="padding: 2px;" id="mcRegimeBtns"></div>
                </div>
                <h4 id="mcRegimeTitle" style="margin: 12px 0 6px 0; font-size: 17px; font-weight: 700; color: var(--text-main);"></h4>
                <p id="mcRegimeDesc" class="macro-note" style="margin-top: 0;"></p>
                <div class="macro-risk-scale">
                    <div id="mcRegimeMarker" class="macro-risk-marker" style="left: 50%;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); text-transform: uppercase;">
                    <span>Aversão (dólar, ouro, Treasuries)</span>
                    <span>Neutro</span>
                    <span>Apetite (Ibovespa, emergentes)</span>
                </div>
                <div id="mcRegimeGrid" class="macro-regime-grid"></div>
                <p class="macro-note" style="font-size: 11px;">Padrões históricos frequentes, não regras absolutas. Correlações mudam em cenários eleitorais ou choques fiscais.</p>
            </div>

            <!-- Bloco 4: "E se…?" Mapa de Reações & Conexão com Ações B3 -->
            <div id="macroSecEse" class="macro-section">
                <div class="macro-panel" style="margin-bottom: 16px;">
                    <div class="macro-panel-head">
                        <div>
                            <span class="macro-kicker">E SE…? · MAPA DE TRANSMISSÃO MACRO</span>
                            <h3>Como cada choque macro chega aos ativos da B3</h3>
                        </div>
                        <span class="macro-src-badge">REAÇÃO TÍPICA EDUCACIONAL</span>
                    </div>

                    <div class="macro-grid-tx">
                        <div id="mcTxEvents" class="macro-tx-list"></div>
                        <div style="border: 1px solid var(--border); border-radius: 12px; padding: 16px; background: rgba(255,255,255,0.02);">
                            <div id="mcTxHead" style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start; gap: 10px; padding-bottom: 12px; border-bottom: 1px solid var(--border);"></div>
                            <div id="mcTxFlow"></div>
                            <div class="macro-grid-2" style="margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border);">
                                <div>
                                    <span class="macro-kicker">👁️ O QUE OBSERVAR</span>
                                    <ul id="mcTxWatch" style="margin: 6px 0 0 16px; padding: 0; font-size: 12px; color: var(--text-muted); line-height: 1.55;"></ul>
                                </div>
                                <div>
                                    <span class="macro-kicker orange">⚠️ QUANDO A REGRA FALHA</span>
                                    <p id="mcTxFail" class="macro-note" style="margin-top: 6px;"></p>
                                </div>
                            </div>
                            <div class="macro-ticker-links" id="mcTxTickerLinks"></div>
                        </div>
                    </div>
                </div>

                <div class="macro-panel">
                    <div class="macro-panel-head">
                        <div>
                            <span class="macro-kicker">TABELA-RESUMO · CLIQUE NUMA LINHA PARA SIMULAR</span>
                            <h3>Matriz Rápida de Sensibilidade</h3>
                        </div>
                        <span class="macro-src-badge">▲ sobe · ▼ cai · ● ambíguo</span>
                    </div>
                    <div class="macro-table-wrap">
                        <table class="macro-table" style="min-width: 660px;">
                            <thead id="mcTxThead"></thead>
                            <tbody id="mcTxTbody"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>


        <!-- =====================================================================
        ABA 5: Entradas > IFR (Estratégia Quantitativa & Rastreador Diário)
        ===================================================================== -->
        <div id="tabIfrContent">

            <!-- KPIs no Topo -->
            <div class="ifr-kpi-grid">
                <div class="ifr-kpi-card">
                    <div class="ifr-kpi-title">
                        <span>Taxa de Acerto</span>
                        <span>🎯</span>
                    </div>
                    <div class="ifr-kpi-val pos" id="kpiIfrWinRate">78,5%</div>
                    <div class="ifr-kpi-sub">
                        <span id="kpiIfrScoreText">(22 Gains · 6 Stops)</span>
                        <span class="tag-up">▲</span>
                    </div>
                </div>

                <div class="ifr-kpi-card">
                    <div class="ifr-kpi-title">
                        <span>Resultado Acumulado</span>
                        <span>💰</span>
                    </div>
                    <div class="ifr-kpi-val pos" id="kpiIfrTotalProfit">+R$ 14.850,00</div>
                    <div class="ifr-kpi-sub">
                        <span class="tag-up" id="kpiIfrProfitPct">(+18,4%)</span>
                        <span>sobre capital base</span>
                    </div>
                </div>

                <div class="ifr-kpi-card">
                    <div class="ifr-kpi-title">
                        <span>Capital Alocado</span>
                        <span>💼</span>
                    </div>
                    <div class="ifr-kpi-val" id="kpiIfrAllocated">R$ 23.100,00</div>
                    <div class="ifr-kpi-sub" id="kpiIfrPositionsCount">
                        (5 ativos em carteira)
                    </div>
                </div>

                <div class="ifr-kpi-card">
                    <div class="ifr-kpi-title">
                        <span>Radar Gatilho IFR &lt; 30</span>
                        <span>📡</span>
                    </div>
                    <div class="ifr-kpi-val" id="kpiIfrRadarCount" style="color: #38bdf8;">3 Ações</div>
                    <div class="ifr-kpi-sub">
                        <span>Monitoramento Diário B3</span>
                    </div>
                </div>
            </div>

            <!-- Gráfico de Evolução Patrimonial -->
            <div class="ifr-chart-card">
                <div class="ifr-chart-header">
                    <div>
                        <div class="ifr-chart-title">
                            📈 Curva de Evolução Patrimonial
                            <span class="ifr-chart-badge" id="ifrPatrimonioCurrentBadge">Patrimônio: R$ 64.850,00 (+29,7%)</span>
                        </div>
                        <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">
                            Simulação rigorosa partindo de R$ 50.000,00 com aportes fixos de R$ 3.300,00 por entrada e gestão de saídas no IFR(21).
                        </div>
                    </div>
                    <div style="font-size: 12px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;" id="ifrSyncStatusText">
                        🟢 Sincronizado com Firebase Firestore
                    </div>
                </div>
                <div class="ifr-chart-container">
                    <canvas id="chartIfrEvolucao"></canvas>
                </div>
            </div>

            <!-- Barra de Filtros e Alternador Compacto vs Conforto -->
            <div class="ifr-toolbar">
                <div class="ifr-filter-group">
                    <button class="ifr-filter-btn active" onclick="IfrModule.setFilter('TODOS', this)">🌐 Todos</button>
                    <button class="ifr-filter-btn" onclick="IfrModule.setFilter('E1', this)">🟢 Em Andamento 1/3</button>
                    <button class="ifr-filter-btn" onclick="IfrModule.setFilter('E2', this)">🟡 Preço Médio 2/3</button>
                    <button class="ifr-filter-btn" onclick="IfrModule.setFilter('E3', this)">🟠 Alerta 3/3</button>
                    <button class="ifr-filter-btn" onclick="IfrModule.setFilter('GAIN', this)">🟢 Encerrados (Gain)</button>
                    <button class="ifr-filter-btn" onclick="IfrModule.setFilter('STOP', this)">🔴 Encerrados (Stop)</button>
                </div>

                <div style="display:flex; align-items:center; gap: 12px; flex-wrap: wrap;">
                    <div style="position:relative;">
                        <input type="text" id="ifrSearchInput" placeholder="Buscar ticker..." oninput="IfrModule.onSearch(this.value)" style="padding: 7px 12px 7px 30px; border-radius: 8px; border: 1px solid var(--border); background: rgba(255,255,255,0.04); color: var(--text-main); font-size: 13px; outline: none; width: 140px;">
                        <span style="position:absolute; left:10px; top:50%; transform:translateY(-50%); font-size:12px; color:var(--text-muted);">🔍</span>
                    </div>

                    <div class="ifr-view-toggle">
                        <button class="ifr-view-btn" id="btnIfrViewCompact" onclick="IfrModule.setViewMode('compact', this)">📱 Compacto</button>
                        <button class="ifr-view-btn active" id="btnIfrViewComfort" onclick="IfrModule.setViewMode('comfort', this)">🖥️ Conforto</button>
                    </div>
                </div>
            </div>

            <!-- Lista de Cards de Operações -->
            <div class="ifr-trades-list" id="ifrTradesList">
                <!-- Renderizado dinamicamente por IfrModule -->
            </div>

        </div>

        <!-- Rodapé Minimalista com Status de Atualização -->
        <footer style="margin-top: 35px; margin-bottom: 25px; display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 14px; font-size: 12px; color: var(--text-muted); opacity: 0.95;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="display: inline-block; width: 8px; height: 8px; background-color: #22c55e; border-radius: 50%; box-shadow: 0 0 8px rgba(34, 197, 94, 0.7); animation: pulseGreen 2.2s infinite ease-in-out;"></span>
                <span>Última atualização: <strong style="color: var(--text-main); font-weight: 600;">__LAST_UPDATE_DATETIME__</strong></span>
            </div>
            <span style="color: var(--border-color, #222634); opacity: 0.7;">•</span>
            <!-- Botão / Badge Interativo de Auditoria de Anomalias -->
            <a id="anomalyFooterBadge" href="anomalias.html" title="Auditoria Contínua B3 & CVM" style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 20px; text-decoration: none; font-size: 11.5px; font-weight: 500; transition: all 0.2s ease; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.03); color: var(--text-muted);">
                <svg id="anomalySvgIcon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink: 0; transition: all 0.3s ease;">
                    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                </svg>
                <span id="anomalyStatusText">Auditoria</span>
            </a>
        </footer>

    </div>

    <style>
    @keyframes pulseGreen {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
        70% { transform: scale(1.15); box-shadow: 0 0 0 6px rgba(34, 197, 94, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
    }
    @keyframes pulseWarningGlow {
        0% { transform: scale(1); filter: drop-shadow(0 0 2px rgba(245, 158, 11, 0.6)); }
        50% { transform: scale(1.1); filter: drop-shadow(0 0 8px rgba(239, 68, 68, 0.95)); }
        100% { transform: scale(1); filter: drop-shadow(0 0 2px rgba(245, 158, 11, 0.6)); }
    }
    @keyframes pulseTickerAnomaly {
        0% { transform: scale(0.96); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.65); }
        50% { transform: scale(1.08); box-shadow: 0 0 10px rgba(239, 68, 68, 0.85); }
        100% { transform: scale(0.96); box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.65); }
    }
    @keyframes pulseTickerWarning {
        0% { transform: scale(0.96); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.65); }
        50% { transform: scale(1.08); box-shadow: 0 0 10px rgba(245, 158, 11, 0.85); }
        100% { transform: scale(0.96); box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.65); }
    }
    .badge-anomaly-active {
        background: rgba(239, 68, 68, 0.12) !important;
        border-color: rgba(239, 68, 68, 0.4) !important;
        color: #f87171 !important;
    }
    .badge-anomaly-active:hover {
        background: rgba(239, 68, 68, 0.22) !important;
        border-color: rgba(239, 68, 68, 0.7) !important;
    }
    .badge-anomaly-active svg {
        stroke: #ef4444 !important;
        animation: pulseWarningGlow 2s infinite ease-in-out;
    }
    .badge-anomaly-clean {
        background: rgba(34, 197, 94, 0.08) !important;
        border-color: rgba(34, 197, 94, 0.3) !important;
        color: #4ade80 !important;
    }
    .badge-anomaly-clean:hover {
        background: rgba(34, 197, 94, 0.16) !important;
    }
    .badge-anomaly-clean svg {
        stroke: #22c55e !important;
    }
    .ticker-anomaly-critical {
        display: inline-flex !important;
        animation: pulseTickerAnomaly 2s infinite ease-in-out;
        background: rgba(239, 68, 68, 0.18) !important;
        border-color: rgba(239, 68, 68, 0.6) !important;
        color: #ef4444 !important;
    }
    .ticker-anomaly-warning {
        display: inline-flex !important;
        animation: pulseTickerWarning 2.2s infinite ease-in-out;
        background: rgba(245, 158, 11, 0.18) !important;
        border-color: rgba(245, 158, 11, 0.6) !important;
        color: #f59e0b !important;
    }
    .ticker-anomaly-critical:hover, .ticker-anomaly-warning:hover {
        transform: scale(1.15) !important;
    }
    </style>

    <style>
    /* =====================================================================
       ABA 4: MACRO & JUROS (Copom, Focus, Curva DI / Tesouro, Regimes & E se?)
       ===================================================================== */
    #tabMacroContent {
        display: none;
        width: 100%;
        max-width: 100%;
        overflow-x: hidden;
        animation: fadeInTab 0.3s ease;
    }
    .macro-section {
        margin-bottom: 18px;
    }
    .macro-hero-card,
    .macro-panel {
        background: var(--card-bg);
        -webkit-backdrop-filter: var(--surface-blur);
        backdrop-filter: var(--surface-blur);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: var(--surface-highlight), var(--shadow-sm);
        padding: 18px 20px;
    }
    body.theme-light .macro-hero-card,
    body.theme-light .macro-panel {
        box-shadow: var(--surface-highlight), 0 1px 3px rgba(9, 9, 11, 0.05), 0 8px 24px -12px rgba(9, 9, 11, 0.08);
    }
    .macro-kicker {
        font-family: var(--font-mono);
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--accent-blue);
        display: inline-block;
        margin-bottom: 4px;
    }
    .macro-kicker.orange { color: var(--accent-orange); }
    .macro-kicker.green { color: var(--accent-green); }
    .macro-hero-top {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
    }
    .macro-hero-title {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.025em;
        color: var(--text-main);
        margin: 0 0 6px 0;
    }
    .macro-hero-sub {
        font-size: 13px;
        color: var(--text-muted);
        max-width: 780px;
        line-height: 1.5;
        margin: 0;
    }
    .macro-live-pill {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 6px 12px;
        border-radius: 999px;
        font-family: var(--font-mono);
        font-size: 11px;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #34d399;
        white-space: nowrap;
    }
    body.theme-light .macro-live-pill {
        background: rgba(21, 128, 61, 0.08);
        border-color: rgba(21, 128, 61, 0.3);
        color: #15803d;
    }
    .macro-live-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: currentColor;
        animation: pulseGreen 2.2s infinite ease-in-out;
    }
    .macro-kpi-strip {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 10px;
        margin-top: 14px;
    }
    .macro-kpi-chip {
        padding: 11px 13px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border);
        display: flex;
        flex-direction: column;
        gap: 3px;
    }
    body.theme-light .macro-kpi-chip {
        background: #f8fafc;
    }
    .macro-kpi-chip.highlight {
        border-color: rgba(56, 189, 248, 0.45);
        background: rgba(56, 189, 248, 0.08);
    }
    body.theme-light .macro-kpi-chip.highlight {
        border-color: rgba(2, 132, 199, 0.35);
        background: rgba(2, 132, 199, 0.06);
    }
    .macro-kpi-chip.copom {
        border-color: rgba(245, 158, 11, 0.45);
        background: rgba(245, 158, 11, 0.08);
    }
    .macro-kpi-chip span.lbl {
        font-family: var(--font-mono);
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        text-transform: uppercase;
    }
    .macro-kpi-chip strong {
        font-family: var(--font-mono);
        font-size: 18px;
        font-weight: 800;
        color: var(--text-main);
        font-variant-numeric: tabular-nums;
    }
    .macro-kpi-chip small {
        font-size: 10.5px;
        color: var(--text-faint, var(--text-muted));
    }
    .macro-subnav {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
        padding-top: 12px;
        border-top: 1px solid var(--border);
    }
    .macro-subnav-btn {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid var(--border);
        color: var(--text-muted);
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s ease;
    }
    .macro-subnav-btn:hover {
        border-color: var(--accent-blue);
        color: var(--text-main);
    }
    body.theme-light .macro-subnav-btn {
        background: #f1f5f9;
        color: #334155;
    }
    .macro-grid-2 {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
        align-items: start;
    }
    .macro-grid-12 {
        display: grid;
        grid-template-columns: 5fr 7fr;
        gap: 18px;
        align-items: center;
    }
    .macro-grid-8-4 {
        display: grid;
        grid-template-columns: 8fr 4fr;
        gap: 18px;
        align-items: start;
    }
    .macro-grid-tx {
        display: grid;
        grid-template-columns: 4fr 8fr;
        gap: 16px;
        align-items: start;
    }
    .macro-panel-head {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
    }
    .macro-panel-head h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 700;
        color: var(--text-main);
    }
    .macro-src-badge {
        font-family: var(--font-mono);
        font-size: 10px;
        color: var(--text-muted);
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.03);
    }
    .macro-svg-box {
        background: rgba(9, 10, 15, 0.45);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 10px;
        overflow: hidden;
    }
    body.theme-light .macro-svg-box {
        background: #f8fafc;
    }
    .macro-svg-box svg {
        width: 100%;
        height: auto;
        display: block;
    }
    .macro-note {
        font-size: 12px;
        color: var(--text-muted);
        line-height: 1.55;
        margin: 10px 0 0 0;
    }
    .macro-table-wrap {
        width: 100%;
        overflow-x: auto;
        border: 1px solid var(--border);
        border-radius: 10px;
    }
    .macro-table {
        width: 100%;
        border-collapse: collapse;
        font-family: var(--font-mono);
        font-size: 12px;
        font-variant-numeric: tabular-nums;
    }
    .macro-table th {
        text-align: left;
        padding: 10px 12px;
        font-size: 10.5px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-muted);
        background: rgba(255, 255, 255, 0.04);
        border-bottom: 1px solid var(--border);
    }
    body.theme-light .macro-table th {
        background: #f1f5f9;
    }
    .macro-table td {
        padding: 10px 12px;
        border-bottom: 1px solid var(--border);
        color: var(--text-main);
    }
    .macro-table tr:last-child td { border-bottom: none; }
    .macro-table tr.clickable-row { cursor: pointer; transition: background 0.15s ease; }
    .macro-table tr.clickable-row:hover { background: rgba(56, 189, 248, 0.08); }
    .macro-table tr.active-row { background: rgba(56, 189, 248, 0.14); }
    .macro-pos { color: #34d399; font-weight: 700; }
    .macro-neg { color: #f87171; font-weight: 700; }
    .macro-neu { color: var(--text-muted); font-weight: 600; }
    body.theme-light .macro-pos { color: #15803d; }
    body.theme-light .macro-neg { color: #b91c1c; }

    .macro-di-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 8px;
    }
    .macro-di-card {
        padding: 10px 12px;
        border-radius: 9px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border);
        font-family: var(--font-mono);
    }
    body.theme-light .macro-di-card { background: #f8fafc; }
    .macro-di-card strong { display: block; font-size: 13px; color: var(--text-main); }
    .macro-di-card span.dt { display: block; font-size: 10.5px; color: var(--text-muted); margin-top: 2px; }
    .macro-di-card span.du { display: block; font-size: 11px; font-weight: 700; color: var(--accent-blue); margin-top: 3px; }

    .macro-curve-kpis {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        margin-bottom: 12px;
    }
    .macro-curve-kpi {
        padding: 10px 12px;
        border-radius: 9px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.03);
        font-family: var(--font-mono);
    }
    body.theme-light .macro-curve-kpi { background: #f8fafc; }
    .macro-curve-kpi span.lbl { display: block; font-size: 10px; color: var(--text-muted); text-transform: uppercase; }
    .macro-curve-kpi strong { display: block; font-size: 18px; margin: 2px 0; color: var(--text-main); }
    .macro-curve-kpi small { font-size: 10.5px; color: var(--text-muted); }

    .macro-bar-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 6px;
        font-family: var(--font-mono);
        font-size: 11px;
    }
    .macro-bar-track {
        position: relative;
        flex: 1;
        height: 10px;
        border-radius: 5px;
        background: rgba(255, 255, 255, 0.06);
        overflow: hidden;
    }
    body.theme-light .macro-bar-track { background: #e2e8f0; }

    .macro-be-bar-wrap { margin-bottom: 10px; }
    .macro-be-bar-head {
        display: flex;
        justify-content: space-between;
        font-family: var(--font-mono);
        font-size: 11px;
        margin-bottom: 4px;
    }
    .macro-be-track {
        position: relative;
        height: 14px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.06);
        overflow: hidden;
    }
    body.theme-light .macro-be-track { background: #e2e8f0; }

    .macro-risk-scale {
        position: relative;
        height: 10px;
        border-radius: 999px;
        background: linear-gradient(90deg, #ef4444 0%, #f59e0b 50%, #10b981 100%);
        margin: 12px 0 6px 0;
    }
    .macro-risk-marker {
        position: absolute;
        top: -4px;
        width: 6px;
        height: 18px;
        border-radius: 3px;
        background: #ffffff;
        border: 2px solid #0f172a;
        transform: translateX(-50%);
        transition: left 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .macro-regime-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        margin-top: 14px;
    }
    .macro-tx-list {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .macro-tx-btn {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border);
        border-left: 4px solid transparent;
        text-align: left;
        cursor: pointer;
        color: var(--text-main);
        transition: all 0.15s ease;
    }
    body.theme-light .macro-tx-btn { background: #f8fafc; }
    .macro-tx-btn:hover { border-color: var(--border-strong); }
    .macro-tx-btn.active {
        background: rgba(56, 189, 248, 0.12);
        border-color: rgba(56, 189, 248, 0.45);
        border-left-color: #f59e0b;
    }
    body.theme-light .macro-tx-btn.active {
        background: #0f172a;
        color: #ffffff;
    }
    .macro-tx-btn .tx-tag {
        display: block;
        font-family: var(--font-mono);
        font-size: 9.5px;
        font-weight: 700;
        color: var(--accent-blue);
        letter-spacing: 0.05em;
    }
    .macro-tx-btn.active .tx-tag { color: #fbbf24; }
    .macro-tx-btn .tx-title {
        display: block;
        font-size: 12.5px;
        font-weight: 700;
        line-height: 1.25;
    }
    .macro-flow-steps {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 10px;
        margin-top: 12px;
    }
    .macro-flow-step {
        padding: 11px 12px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border);
    }
    body.theme-light .macro-flow-step { background: #f8fafc; }
    .macro-flow-step.first { border-left: 3px solid #f59e0b; }
    .macro-flow-chips {
        display: grid;
        grid-template-columns: repeat(7, minmax(0, 1fr));
        gap: 8px;
        margin-top: 12px;
    }
    .macro-asset-chip {
        padding: 8px 6px;
        border-radius: 8px;
        border: 1px solid var(--border);
        text-align: center;
        font-family: var(--font-mono);
    }
    .macro-asset-chip.up {
        border-color: rgba(34, 197, 94, 0.45);
        background: rgba(34, 197, 94, 0.1);
    }
    .macro-asset-chip.dn {
        border-color: rgba(239, 68, 68, 0.45);
        background: rgba(239, 68, 68, 0.1);
    }
    .macro-ticker-links {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--border);
        align-items: center;
    }
    .macro-ticker-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 5px 10px;
        border-radius: 8px;
        font-family: var(--font-mono);
        font-size: 11.5px;
        font-weight: 700;
        cursor: pointer;
        border: 1px solid rgba(56, 189, 248, 0.35);
        background: rgba(56, 189, 248, 0.1);
        color: var(--accent-blue);
        transition: all 0.15s ease;
    }
    .macro-ticker-pill:hover {
        transform: translateY(-1px);
        background: rgba(56, 189, 248, 0.22);
    }
    @media (max-width: 980px) {
        .macro-grid-2,
        .macro-grid-12,
        .macro-grid-8-4,
        .macro-grid-tx {
            grid-template-columns: 1fr;
        }
        .macro-flow-steps { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .macro-flow-chips { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    }
    @media (max-width: 640px) {
        .macro-hero-card, .macro-panel { padding: 14px 12px; }
        .macro-hero-title { font-size: 20px; }
        .macro-di-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .macro-regime-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .macro-flow-steps { grid-template-columns: 1fr; }
        .macro-flow-chips { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        .macro-tx-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }

    /* =====================================================================
       ABA 5: ENTRADAS > IFR (Estratégia Quantitativa B3 + NoSQL Firestore)
       ===================================================================== */
    @keyframes pulseIfrDot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.4; transform: scale(0.85); }
    }

    #tabIfrContent {
        display: none;
        width: 100%;
        animation: fadeInTab 0.3s ease;
    }

    /* Grid de KPIs no Topo */
    .ifr-kpi-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }

    .ifr-kpi-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 20px 22px;
        position: relative;
        overflow: hidden;
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }

    .ifr-kpi-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
    }

    .ifr-kpi-title {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .ifr-kpi-val {
        font-size: 26px;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-main);
        letter-spacing: -0.02em;
        margin-bottom: 6px;
    }

    .ifr-kpi-val.pos { color: #00e676; }
    .ifr-kpi-val.neg { color: #ff3366; }

    .ifr-kpi-sub {
        font-size: 13px;
        color: var(--text-muted);
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .ifr-kpi-sub .tag-up {
        color: #00e676;
        font-weight: 700;
    }

    /* Card do Gráfico de Evolução Patrimonial */
    .ifr-chart-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 22px 24px;
        margin-bottom: 24px;
    }

    .ifr-chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 18px;
        border-bottom: 1px solid var(--border);
        padding-bottom: 14px;
    }

    .ifr-chart-title {
        font-size: 17px;
        font-weight: 700;
        color: var(--text-main);
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .ifr-chart-badge {
        font-size: 12px;
        padding: 3px 10px;
        border-radius: 999px;
        background: rgba(0, 230, 118, 0.12);
        color: #00e676;
        border: 1px solid rgba(0, 230, 118, 0.3);
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
    }

    .ifr-chart-container {
        position: relative;
        height: 280px;
        width: 100%;
    }

    /* Barra de Filtros e Controles */
    .ifr-toolbar {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 14px 18px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 14px;
    }

    .ifr-filter-group {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }

    .ifr-filter-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 7px 14px;
        font-size: 13px;
        font-weight: 600;
        border-radius: 8px;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.03);
        color: var(--text-muted);
        cursor: pointer;
        transition: all 0.2s ease;
        user-select: none;
    }

    .ifr-filter-btn:hover {
        background: rgba(255, 255, 255, 0.07);
        color: var(--text-main);
        border-color: rgba(255, 255, 255, 0.2);
    }

    .ifr-filter-btn.active {
        background: rgba(14, 165, 233, 0.2);
        border-color: #38bdf8;
        color: #ffffff;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
    }

    body.theme-light .ifr-filter-btn {
        background: #f1f5f9;
        border-color: #e2e8f0;
        color: #475569;
    }

    body.theme-light .ifr-filter-btn:hover {
        background: #e2e8f0;
        color: #0f172a;
    }

    body.theme-light .ifr-filter-btn.active {
        background: #e0f2fe;
        border-color: #0284c7;
        color: #0369a1;
        box-shadow: 0 2px 6px rgba(14, 165, 233, 0.2);
    }

    .ifr-view-toggle {
        display: inline-flex;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 3px;
        gap: 4px;
    }

    .ifr-view-btn {
        border: none;
        background: transparent;
        color: var(--text-muted);
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 600;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .ifr-view-btn.active {
        background: #1e293b;
        color: #38bdf8;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    }

    body.theme-light .ifr-view-btn.active {
        background: #ffffff;
        color: #0284c7;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
    }

    /* Cards e Linhas de Operações */
    .ifr-trades-list {
        display: flex;
        flex-direction: column;
        gap: 14px;
    }

    .ifr-trade-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 18px 24px;
        display: grid;
        grid-template-columns: 260px 1fr 240px;
        align-items: center;
        gap: 24px;
        transition: all 0.2s ease;
    }

    .ifr-trade-card:hover {
        border-color: rgba(56, 189, 248, 0.35);
        box-shadow: 0 6px 22px rgba(0, 0, 0, 0.2);
    }

    /* Coluna Esquerda: Ativo, Preço, P/L e IFR */
    .ifr-asset-col {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }

    .ifr-asset-head {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .ifr-asset-logo {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 13px;
        color: #0f172a;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        flex-shrink: 0;
        letter-spacing: -0.02em;
    }

    .ifr-ticker-title {
        font-size: 18px;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        color: var(--text-main);
        letter-spacing: -0.01em;
    }

    .ifr-sector-badge {
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.08);
        color: var(--text-muted);
        border: 1px solid var(--border);
    }

    body.theme-light .ifr-sector-badge {
        background: #f1f5f9;
        color: #475569;
        border-color: #cbd5e1;
    }

    .ifr-asset-metrics {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 12px;
        font-size: 12px;
        color: var(--text-muted);
    }

    .ifr-metric-item strong {
        color: var(--text-main);
        font-family: 'JetBrains Mono', monospace;
    }

    .ifr-pill {
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
    }

    .ifr-pill.warn {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }

    .ifr-pill.alert {
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
        animation: pulseIfrDot 2s infinite ease-in-out;
    }

    .ifr-pill.ok {
        background: rgba(0, 230, 118, 0.15);
        color: #00e676;
        border: 1px solid rgba(0, 230, 118, 0.35);
    }

    /* Coluna Central: Visual 3-Step Progress Bar (Conforto) */
    .ifr-steps-wrap {
        display: flex;
        align-items: center;
        gap: 8px;
        width: 100%;
        position: relative;
    }

    .ifr-step-node {
        flex: 1;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 10px 14px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 4px;
        text-align: center;
        position: relative;
        transition: all 0.2s ease;
    }

    .ifr-step-node.done {
        background: rgba(0, 230, 118, 0.08);
        border: 1.5px solid #00e676;
        box-shadow: 0 0 12px rgba(0, 230, 118, 0.15);
    }

    .ifr-step-node.pending {
        background: transparent;
        border: 1.5px dashed var(--border);
        opacity: 0.6;
    }

    .ifr-step-badge {
        font-size: 12px;
        font-weight: 700;
        font-family: 'JetBrains Mono', monospace;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .ifr-step-node.done .ifr-step-badge {
        color: #00e676;
    }

    .ifr-step-sub {
        font-size: 11px;
        color: var(--text-muted);
        font-family: 'JetBrains Mono', monospace;
    }

    .ifr-step-connector {
        width: 20px;
        height: 2px;
        background: var(--border);
        flex-shrink: 0;
    }

    .ifr-step-connector.done {
        background: #00e676;
        box-shadow: 0 0 6px rgba(0, 230, 118, 0.4);
    }

    /* Modo Compacto para Linhas */
    .ifr-trade-card.compact {
        padding: 14px 20px;
        grid-template-columns: 240px 1fr 220px;
        gap: 16px;
    }

    .ifr-compact-bar-wrap {
        display: flex;
        flex-direction: column;
        gap: 6px;
        width: 100%;
    }

    .ifr-compact-track {
        height: 6px;
        border-radius: 999px;
        background: var(--slider-track);
        position: relative;
        overflow: hidden;
    }

    .ifr-compact-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #00e676, #00d2ff);
        transition: width 0.3s ease;
    }

    .ifr-compact-labels {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        color: var(--text-muted);
        font-family: 'JetBrains Mono', monospace;
    }

    /* Coluna Direita: Preço Médio, Alvos, Stop Geral & P&L % */
    .ifr-summary-col {
        display: flex;
        flex-direction: column;
        gap: 6px;
        text-align: right;
    }

    .ifr-summary-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        color: var(--text-muted);
    }

    .ifr-summary-row strong {
        color: var(--text-main);
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
    }

    .ifr-pnl-val {
        font-size: 18px;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.01em;
        margin-top: 4px;
    }

    .ifr-pnl-val.pos { color: #00e676; }
    .ifr-pnl-val.neg { color: #ff3366; }

    @media (max-width: 1100px) {
        .ifr-kpi-grid { grid-template-columns: repeat(2, 1fr); }
        .ifr-trade-card {
            grid-template-columns: 1fr;
            gap: 18px;
        }
        .ifr-summary-col { text-align: left; }
    }

    @media (max-width: 650px) {
        .ifr-kpi-grid { grid-template-columns: 1fr; }
        .ifr-toolbar { flex-direction: column; align-items: stretch; }
    }

    /* --- Alto Contraste no Modo Claro (Tema Clean) para Entradas > IFR --- */
    .ifr-pulse-dot {
        display: inline-block;
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #00e676;
        box-shadow: 0 0 8px #00e676;
        animation: pulseIfrDot 2s infinite ease-in-out;
    }

    body.theme-light .ifr-pulse-dot {
        background: #15803d !important;
        box-shadow: 0 0 6px rgba(21, 128, 61, 0.5) !important;
    }

    body.theme-light .ifr-kpi-card {
        background: #ffffff !important;
        border-color: #cbd5e1 !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05) !important;
    }

    body.theme-light .ifr-kpi-card:hover {
        border-color: #0284c7 !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08) !important;
    }

    body.theme-light .ifr-kpi-title {
        color: #475569 !important;
        font-weight: 700 !important;
    }

    body.theme-light .ifr-kpi-val {
        color: #0f172a !important;
    }

    body.theme-light .ifr-kpi-val.pos {
        color: #15803d !important; /* Verde Floresta de Alto Contraste */
    }

    body.theme-light .ifr-kpi-val.neg {
        color: #b91c1c !important; /* Vermelho Vivo Escuro */
    }

    body.theme-light .ifr-kpi-sub {
        color: #475569 !important;
    }

    body.theme-light .ifr-kpi-sub .tag-up {
        color: #15803d !important;
        font-weight: 800 !important;
    }

    body.theme-light .ifr-chart-card {
        background: #ffffff !important;
        border-color: #cbd5e1 !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05) !important;
    }

    body.theme-light .ifr-chart-badge {
        background: #dcfce7 !important;
        color: #15803d !important;
        border: 1px solid #86efac !important;
        font-weight: 700 !important;
    }

    body.theme-light .ifr-toolbar {
        background: #ffffff !important;
        border-color: #cbd5e1 !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
    }

    body.theme-light #ifrSearchInput {
        background: #f8fafc !important;
        border-color: #cbd5e1 !important;
        color: #0f172a !important;
    }

    body.theme-light .ifr-trade-card {
        background: #ffffff !important;
        border-color: #cbd5e1 !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
    }

    body.theme-light .ifr-trade-card:hover {
        border-color: #0284c7 !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
    }

    body.theme-light .ifr-ticker-title {
        color: #0f172a !important;
    }

    body.theme-light .ifr-asset-metrics {
        color: #334155 !important;
    }

    body.theme-light .ifr-metric-item strong {
        color: #0f172a !important;
    }

    body.theme-light .ifr-pill.ok {
        background: #dcfce7 !important;
        color: #15803d !important;
        border: 1px solid #86efac !important;
        font-weight: 800 !important;
    }

    body.theme-light .ifr-pill.warn {
        background: #fef3c7 !important;
        color: #92400e !important;
        border: 1px solid #fcd34d !important;
        font-weight: 800 !important;
    }

    body.theme-light .ifr-pill.alert {
        background: #fee2e2 !important;
        color: #b91c1c !important;
        border: 1px solid #fca5a5 !important;
        font-weight: 800 !important;
    }

    body.theme-light .ifr-step-node {
        background: #f8fafc !important;
        border-color: #cbd5e1 !important;
    }

    body.theme-light .ifr-step-node.done {
        background: #f0fdf4 !important;
        border: 1.5px solid #15803d !important;
        box-shadow: 0 1px 5px rgba(21, 128, 61, 0.15) !important;
    }

    body.theme-light .ifr-step-node.done .ifr-step-badge {
        color: #15803d !important;
        font-weight: 800 !important;
    }

    body.theme-light .ifr-step-connector.done {
        background: #15803d !important;
        box-shadow: none !important;
    }

    body.theme-light .ifr-step-node.pending {
        background: #f8fafc !important;
        border: 1.5px dashed #94a3b8 !important;
        opacity: 0.85 !important;
    }

    body.theme-light .ifr-step-node.pending .ifr-step-badge {
        color: #475569 !important;
    }

    body.theme-light .ifr-step-sub {
        color: #334155 !important;
        font-weight: 600 !important;
    }

    body.theme-light .ifr-step-connector {
        background: #cbd5e1 !important;
    }

    body.theme-light .ifr-summary-row {
        color: #475569 !important;
    }

    body.theme-light .ifr-summary-row strong {
        color: #0f172a !important;
    }

    body.theme-light .ifr-pnl-val.pos {
        color: #15803d !important;
        font-weight: 800 !important;
    }

    body.theme-light .ifr-pnl-val.neg {
        color: #b91c1c !important;
        font-weight: 800 !important;
    }

    body.theme-light .ifr-compact-track {
        background: #e2e8f0 !important;
    }

    body.theme-light .ifr-compact-fill {
        background: linear-gradient(90deg, #15803d, #0284c7) !important;
    }

    body.theme-light .ifr-compact-labels {
        color: #334155 !important;
        font-weight: 600 !important;
    }


    </style>

    <script>

        const DATA = __DATA_PLACEHOLDER__;
        const IFR_CACHE_DATA = __IFR_PLACEHOLDER__;
        const EARNINGS_CALENDAR = __EARNINGS_PLACEHOLDER__;
        const CORPORATE_EVENTS_MAP = __CORPORATE_EVENTS_PLACEHOLDER__;
        const EVENTS_ALL_DATA = __EVENTS_ALL_DATA_PLACEHOLDER__;
        const MACRO_DATA = __MACRO_PLACEHOLDER__;

        // Glass Pro: tipografia e tooltips flutuantes dos gráficos alinhados ao design system (zinc-900/80 + border-zinc-800)
        function applyGlassChartTheme() {
            if (typeof Chart === 'undefined') return;
            const light = document.body.classList.contains('theme-light');
            Chart.defaults.font.family = "'Inter', ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif";
            Chart.defaults.font.size = 11;
            const tt = Chart.defaults.plugins.tooltip;
            tt.backgroundColor = light ? 'rgba(255, 255, 255, 0.92)' : 'rgba(24, 24, 27, 0.88)';
            tt.borderColor = light ? '#e4e4e7' : '#27272a';
            tt.borderWidth = 1;
            tt.cornerRadius = 10;
            tt.padding = 12;
            tt.caretSize = 5;
            tt.boxPadding = 5;
            tt.usePointStyle = true;
            tt.titleColor = light ? '#09090b' : '#fafafa';
            tt.bodyColor = light ? '#3f3f46' : '#d4d4d8';
            tt.titleFont = { weight: '600', size: 12 };
            tt.bodyFont = { size: 11.5 };
            tt.titleMarginBottom = 8;
            Chart.defaults.elements.point.hoverBorderWidth = 2;
            Chart.defaults.elements.point.hoverBorderColor = light ? '#ffffff' : '#09090b';
        }
        applyGlassChartTheme();

        
        const COMPANY_DOMAINS = {
            'ABCB4': 'bancoabc.com.br', 'ABEV3': 'ambev.com.br', 'ALOS3': 'allos.co', 'ALPA4': 'alpargatas.com.br',
            'ALUP11': 'alupar.com.br', 'AMBP3': 'ambipar.com', 'ANIM3': 'animaeducacao.com.br', 'ARZZ3': 'azzas2154.com.br',
            'ASAI3': 'assai.com.br', 'AURE3': 'aurenenergia.com.br', 'AZUL4': 'voeazul.com.br', 'AZZA3': 'azzas2154.com.br',
            'B3SA3': 'b3.com.br', 'BBAS3': 'bb.com.br', 'BBDC3': 'bradesco.com.br', 'BBDC4': 'bradesco.com.br',
            'BBSE3': 'bbseguridade.com.br', 'BEEF3': 'minervafoods.com', 'BHIA3': 'casasbahia.com.br', 'BPAC11': 'btgpactual.com',
            'BPAN4': 'bancopan.com.br', 'BRAP4': 'bradespar.com', 'BRFS3': 'brf-global.com', 'BRKM5': 'braskem.com.br',
            'BRSR6': 'banrisul.com.br', 'CASH3': 'meliuz.com.br', 'CBAV3': 'cba.com.br', 'CCRO3': 'grupoccr.com.br',
            'CEAB3': 'cea.com.br', 'CIEL3': 'cielo.com.br', 'CMIG3': 'cemig.com.br', 'CMIG4': 'cemig.com.br',
            'CMIN3': 'cmin.com.br', 'COGN3': 'cogna.com.br', 'CPLE3': 'copel.com', 'CPLE6': 'copel.com',
            'CRFB3': 'carrefour.com.br', 'CSAN3': 'cosan.com.br', 'CSMG3': 'copasa.com.br', 'CSNA3': 'csn.com.br',
            'CURY3': 'cury.net', 'CVCB3': 'cvc.com.br', 'CXSE3': 'caixaseguridade.com.br', 'CYRE3': 'cyrela.com.br',
            'DASA3': 'dasa.com.br', 'DIRR3': 'direcional.com.br', 'DXCO3': 'dex.co', 'ECOR3': 'ecorodovias.com.br',
            'EGIE3': 'engie.com.br', 'ELET3': 'eletrobras.com', 'ELET6': 'eletrobras.com', 'EMBR3': 'embraer.com',
            'ENEV3': 'eneva.com.br', 'ENGI11': 'energisa.com.br', 'EQTL3': 'equatorialenergia.com.br', 'EZTC3': 'eztc.com.br',
            'FLRY3': 'fleury.com.br', 'FRAS3': 'frasle.com', 'GFSA3': 'gafisa.com.br', 'GGBR3': 'gerdau.com',
            'GGBR4': 'gerdau.com', 'GGPS3': 'gpssa.com.br', 'GMAT3': 'grupomateus.com.br', 'GOAU4': 'gerdau.com',
            'GUAR3': 'riachuelo.com.br', 'HAPV3': 'hapvida.com.br', 'HBSA3': 'hidroviasdobrasil.com', 'HYPE3': 'hypera.com.br',
            'IGTI11': 'iguatemi.com.br', 'INTB3': 'intelbras.com.br', 'IRBR3': 'irbre.com', 'ISAE4': 'isacteep.com.br',
            'ITSA3': 'itausa.com.br', 'ITSA4': 'itausa.com.br', 'ITUB3': 'itau.com.br', 'ITUB4': 'itau.com.br',
            'JBSS3': 'jbs.com.br', 'JHSF3': 'jhsf.com.br', 'JSLG3': 'jsl.com.br', 'KEPL3': 'kepler.com.br',
            'KLBN11': 'klabin.com.br', 'KLBN4': 'klabin.com.br', 'LEVE3': 'mahle.com', 'LJQQ3': 'lojasqueroquero.com.br',
            'LREN3': 'lojasrenner.com.br', 'LWSA3': 'locaweb.com.br', 'MDIA3': 'mdiasbranco.com.br', 'MGLU3': 'magazineluiza.com.br',
            'MILS3': 'mills.com.br', 'MOVI3': 'movida.com.br', 'MRFG3': 'marfrig.com.br', 'MRVE3': 'mrv.com.br',
            'MULT3': 'multiplan.com.br', 'MYPK3': 'iochpe.com.br', 'NEOE3': 'neoenergia.com', 'NTCO3': 'naturaeco.com',
            'ODPV3': 'odontoprev.com.br', 'ONCO3': 'oncoclinicas.com', 'ORVR3': 'orizonvr.com.br', 'PCAR3': 'gpabr.com',
            'PETR3': 'petrobras.com.br', 'PETR4': 'petrobras.com.br', 'PETZ3': 'petz.com.br', 'PGMN3': 'paguemenos.com.br',
            'PLPL3': 'planoeplano.com.br', 'POMO4': 'marcopolo.com.br', 'PORT3': 'wilsonsons.com.br', 'POSI3': 'meupositivo.com.br',
            'PRIO3': 'prio3.com.br', 'PSSA3': 'porto.com.br', 'QUAL3': 'qualicorp.com.br', 'RADL3': 'drogaraia.com.br',
            'RAIL3': 'rumolog.com', 'RAIZ4': 'raizen.com.br', 'RANI3': 'irani.com.br', 'RAPT4': 'rapi.com.br',
            'RDOR3': 'rededorsaoluiz.com.br', 'RECV3': 'petroreconcavo.com.br', 'RENT3': 'localiza.com', 'RRRP3': 'bravaenergia.com',
            'SANB11': 'santander.com.br', 'SANB4': 'santander.com.br', 'SAPR11': 'sanepar.com.br', 'SAPR4': 'sanepar.com.br',
            'SBFG3': 'centauro.com.br', 'SBSP3': 'sabesp.com.br', 'SIMH3': 'simpar.com.br', 'SLCE3': 'slcagricola.com.br',
            'SMFT3': 'smartfit.com.br', 'SMTO3': 'saomartinho.com.br', 'STBP3': 'santosbrasil.com.br', 'SUZB3': 'suzano.com.br',
            'TAEE11': 'taesa.com.br', 'TEND3': 'construtoratenda.com.br', 'TIMS3': 'tim.com.br', 'TOTS3': 'totvs.com',
            'TRPL4': 'isacteep.com.br', 'TTEN3': '3tentos.com.br', 'TUPY3': 'tupy.com.br', 'UGPA3': 'ultra.com.br',
            'UNIP6': 'unipar.com', 'USIM5': 'usiminas.com', 'VALE3': 'vale.com', 'VAMO3': 'vamos.com.br',
            'VBBR3': 'vibraenergia.com.br', 'VIVA3': 'vivara.com.br', 'VIVT3': 'vivo.com.br', 'VLID3': 'valid.com',
            'VULC3': 'vulcabras.com.br', 'VVEO3': 'viveo.com.br', 'WEGE3': 'weg.net', 'YDUQ3': 'yduqs.com.br'
        };

        function getHeaderBrandIconHtml(ticker, size = 38) {
            if (!ticker) return '';
            if (ticker === 'IBOV') return `<span class="header-brand-badge" style="display:inline-flex; align-items:center; justify-content:center; width:${size}px; height:${size}px; min-width:${size}px; border-radius:50%; background:rgba(56,189,248,0.15); border:1.5px solid rgba(56,189,248,0.4); font-size:18px; vertical-align:middle;">📊</span>`;
            if (ticker === 'IFNC') return `<span class="header-brand-badge" style="display:inline-flex; align-items:center; justify-content:center; width:${size}px; height:${size}px; min-width:${size}px; border-radius:50%; background:rgba(245,158,11,0.15); border:1.5px solid rgba(245,158,11,0.4); font-size:18px; vertical-align:middle;">🏦</span>`;
            if (ticker === 'SEGUROS') return `<span class="header-brand-badge" style="display:inline-flex; align-items:center; justify-content:center; width:${size}px; height:${size}px; min-width:${size}px; border-radius:50%; background:rgba(0,230,118,0.15); border:1.5px solid rgba(0,230,118,0.4); font-size:18px; vertical-align:middle;">🛡️</span>`;

            const domain = COMPANY_DOMAINS[ticker] || (ticker.toLowerCase() + '.com.br');
            const logoUrl = `https://www.google.com/s2/favicons?domain=${domain}&sz=128`;
            const fallbackUrl = `https://t3.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://${domain}&size=128`;

            return `<img src="${logoUrl}" alt="${ticker}" class="header-brand-logo-img" 
                         style="width:${size}px; height:${size}px; min-width:${size}px; border-radius:50%; object-fit:contain; background:#ffffff; padding:3px; box-shadow:0 2px 8px rgba(0,0,0,0.22); border:1.5px solid var(--border); vertical-align:middle; display:inline-block;" 
                         onerror="if(this.src!=='${fallbackUrl}') { this.src='${fallbackUrl}'; } else { this.style.display='none'; }">`;
        }

        function updateHeaderSubtitle(ticker) {
            const iconEl = document.getElementById('headerBrandIcon');
            if (iconEl) {
                iconEl.innerHTML = getHeaderBrandIconHtml(ticker);
            }

            const titleEl = document.getElementById('headerTitleText');
            if (titleEl && DATA[ticker]) {
                const compName = DATA[ticker].company || '';
                titleEl.textContent = compName ? `${ticker} - ${compName}` : ticker;
            }
            const subtitleEl = document.getElementById('headerSubtitle');
            if (!subtitleEl) return;

            if (['IBOV', 'IFNC', 'SEGUROS'].includes(ticker)) {
                subtitleEl.innerHTML = '<span style="color:var(--text-muted); font-size:13px;">Índice da B3 • Métricas ponderadas e histórico consolidado</span>';
                return;
            }

            const base = (ticker || '').substring(0, 4);
            let ev = EARNINGS_CALENDAR[ticker];
            if (!ev) {
                for (const k in EARNINGS_CALENDAR) {
                    if (k.substring(0, 4) === base) {
                        ev = EARNINGS_CALENDAR[k];
                        break;
                    }
                }
            }

            if (ev && ev.date) {
                const isBefore = (ev.timing && ev.timing.toLowerCase().includes('antes'));
                const timingClass = isBefore ? 'timing-before' : 'timing-after';
                const timingLabel = ev.timing || 'Após o fechamento';
                subtitleEl.innerHTML = `<span class="earnings-badge">📅 Próximo Resultado: <strong style="color:var(--text-main); font-weight:700;">${ev.date}</strong> • <span class="timing-badge ${timingClass}">${timingLabel}</span></span>`;
            } else {
                subtitleEl.innerHTML = '<span class="earnings-badge">📅 Próximo Resultado: <span style="color:var(--text-muted); font-style:italic;">Data a confirmar</span></span>';
            }
        }


        let charts = {};

        let currentTicker = 'ITUB4';

        let currentYears = 5;

        let chartCustomLimits = {};
        let customDateStartIndex = null;
        let customDateEndIndex = null;
        let isTimeSliderActive = false;

        function updateTimeSliderFill() {
            const startInput = document.getElementById('sliderTimeStart');
            const endInput = document.getElementById('sliderTimeEnd');
            const fill = document.getElementById('fillTime');
            if (!startInput || !endInput || !fill) return;

            const min = parseFloat(startInput.min);
            const max = parseFloat(startInput.max);
            const val1 = parseFloat(startInput.value);
            const val2 = parseFloat(endInput.value);

            const pct1 = ((val1 - min) / (max - min)) * 100;
            const pct2 = ((val2 - min) / (max - min)) * 100;

            fill.style.left = `${Math.min(pct1, pct2)}%`;
            fill.style.width = `${Math.abs(pct2 - pct1)}%`;
        }

        function onTimeSliderInput(handle) {
            const d = DATA[currentTicker];
            if (!d || !d.dates || d.dates.length === 0) return;

            const startInput = document.getElementById('sliderTimeStart');
            const endInput = document.getElementById('sliderTimeEnd');
            let val1 = parseInt(startInput.value);
            let val2 = parseInt(endInput.value);

            if (handle === 'start' && val1 > val2 - 2) {
                val1 = Math.max(0, val2 - 2);
                startInput.value = val1;
            } else if (handle === 'end' && val2 < val1 + 2) {
                val2 = Math.min(d.dates.length - 1, val1 + 2);
                endInput.value = val2;
            }

            customDateStartIndex = val1;
            customDateEndIndex = val2;
            isTimeSliderActive = true;

            // Desmarca botões de período pré-definido
            document.querySelectorAll('.period-btn[onclick^="setPeriod"]').forEach(b => b.classList.remove('active'));

            updateTimeSliderFill();
            renderCharts();
            updateHeaderSubtitle(currentTicker);
            if (typeof updateEventsDrawerForTicker === 'function') updateEventsDrawerForTicker(currentTicker);
        }

        function syncTimeSliderWithData(dates, filteredStartIndex, filteredEndIndex) {
            const startInput = document.getElementById('sliderTimeStart');
            const endInput = document.getElementById('sliderTimeEnd');
            const label = document.getElementById('timeSliderLabel');
            const minDateLabel = document.getElementById('timeSliderMinDate');
            const maxDateLabel = document.getElementById('timeSliderMaxDate');
            if (!startInput || !endInput) return;

            const total = dates.length;
            startInput.min = 0;
            startInput.max = total - 1;
            endInput.min = 0;
            endInput.max = total - 1;

            startInput.value = filteredStartIndex;
            endInput.value = filteredEndIndex;

            if (minDateLabel && dates[0]) minDateLabel.textContent = dates[0];
            if (maxDateLabel && dates[total - 1]) maxDateLabel.textContent = dates[total - 1];

            const startDate = dates[filteredStartIndex] || '-';
            const endDate = dates[filteredEndIndex] || '-';
            const totalDays = (filteredEndIndex - filteredStartIndex + 1);
            if (label) {
                label.textContent = `${startDate}  ➔  ${endDate} (${totalDays} pregões)`;
            }

            updateTimeSliderFill();
        }
 // { chartId: { min: val, max: val } }



        function updateRangeFill(chartId) {

            const suffixId = chartId.replace('chart', '');

            const minInput = document.getElementById('sliderMin' + suffixId);

            const maxInput = document.getElementById('sliderMax' + suffixId);

            const fill = document.getElementById('fill' + suffixId);

            if (!minInput || !maxInput || !fill) return;



            const total = parseFloat(minInput.max) - parseFloat(minInput.min);

            if (total <= 0) return;



            const minPercent = ((parseFloat(minInput.value) - parseFloat(minInput.min)) / total) * 100;

            const maxPercent = ((parseFloat(maxInput.value) - parseFloat(minInput.min)) / total) * 100;



            fill.style.left = `${minPercent}%`;

            fill.style.width = `${Math.max(0, maxPercent - minPercent)}%`;

        }



        function onDualSliderInput(chartId, changedThumb, prefix = '', suffix = '') {

            const suffixId = chartId.replace('chart', '');

            const minInput = document.getElementById('sliderMin' + suffixId);

            const maxInput = document.getElementById('sliderMax' + suffixId);

            const valLabel = document.getElementById('sliderVal' + suffixId);

            const chart = charts[chartId];

            if (!chart || !minInput || !maxInput) return;



            let minVal = parseFloat(minInput.value);

            let maxVal = parseFloat(maxInput.value);



            // Garante que o min não ultrapasse o max e vice-versa

            if (changedThumb === 'min' && minVal > maxVal) {

                minVal = maxVal;

                minInput.value = minVal;

            } else if (changedThumb === 'max' && maxVal < minVal) {

                maxVal = minVal;

                maxInput.value = maxVal;

            }



            if (!chartCustomLimits[chartId]) chartCustomLimits[chartId] = {};

            chartCustomLimits[chartId].min = minVal;

            chartCustomLimits[chartId].max = maxVal;



            chart.options.scales.y.min = minVal;

            chart.options.scales.y.max = maxVal;

            chart.update();



            updateRangeFill(chartId);



            if (valLabel) {

                valLabel.textContent = `${prefix}${minVal.toFixed(1)}${suffix} ~ ${prefix}${maxVal.toFixed(1)}${suffix}`;

            }

        }



        function resetDualSlider(chartId, prefix = '', suffix = '') {

            const chart = charts[chartId];

            if (!chart) return;



            delete chartCustomLimits[chartId];

            delete chart.options.scales.y.min;

            delete chart.options.scales.y.max;

            chart.update();



            const suffixId = chartId.replace('chart', '');

            const minInput = document.getElementById('sliderMin' + suffixId);

            const maxInput = document.getElementById('sliderMax' + suffixId);

            const valLabel = document.getElementById('sliderVal' + suffixId);



            if (minInput && maxInput) {

                minInput.value = minInput.min;

                maxInput.value = maxInput.max;

                updateRangeFill(chartId);

            }

            if (valLabel) valLabel.textContent = 'Auto';

        }



        function setupDualSlider(chartId, values, prefix = '', suffix = '', allowNegative = false) {

            const valid = values.filter(x => x !== null && !isNaN(x));

            if (!valid.length) return;



            const minObserved = Math.min(...valid);

            const maxObserved = Math.max(...valid);

            const suffixId = chartId.replace('chart', '');

            const minInput = document.getElementById('sliderMin' + suffixId);

            const maxInput = document.getElementById('sliderMax' + suffixId);

            const valLabel = document.getElementById('sliderVal' + suffixId);



            if (!minInput || !maxInput) return;



            const sliderMin = allowNegative ? Math.floor(minObserved * 1.1) : Math.max(0, Math.floor(minObserved * 0.9));

            const sliderMax = Math.ceil(maxObserved * 1.15) || 10;

            const step = Number(((sliderMax - sliderMin) / 100).toFixed(2)) || 0.1;



            minInput.min = sliderMin;

            minInput.max = sliderMax;

            minInput.step = step;



            maxInput.min = sliderMin;

            maxInput.max = sliderMax;

            maxInput.step = step;



            if (chartCustomLimits[chartId]) {

                minInput.value = chartCustomLimits[chartId].min;

                maxInput.value = chartCustomLimits[chartId].max;

                if (valLabel) {

                    valLabel.textContent = `${prefix}${chartCustomLimits[chartId].min.toFixed(1)}${suffix} ~ ${prefix}${chartCustomLimits[chartId].max.toFixed(1)}${suffix}`;

                }

            } else {

                minInput.value = sliderMin;

                maxInput.value = sliderMax;

                if (valLabel) valLabel.textContent = 'Auto';

            }



            updateRangeFill(chartId);

        }



        function initSelect() {

            const select = document.getElementById('tickerSelect');

            const tickers = Object.keys(DATA).sort();



            // Recupera o último ticker e período salvos no localStorage (se existirem)

            const savedTicker = localStorage.getItem('fundamentalista_ticker');

            const savedYears = parseInt(localStorage.getItem('fundamentalista_years'));



            if (savedTicker && DATA[savedTicker]) {

                currentTicker = savedTicker;

            } else if (DATA['ITUB4']) {

                currentTicker = 'ITUB4';

            } else if (tickers.length > 0) {

                currentTicker = tickers[0];

            }



            if (savedYears && [1, 2, 5, 10].includes(savedYears)) {

                currentYears = savedYears;

            }



                        // Determina a data máxima mais recente negociada no banco de dados
            let latestMarketDateStr = '2000-01-01';
            Object.values(DATA).forEach(item => {
                if (item.dates && item.dates.length > 0) {
                    const lastD = item.dates[item.dates.length - 1];
                    if (lastD > latestMarketDateStr) latestMarketDateStr = lastD;
                }
            });

            // Limite de 7 dias antes do pregão mais recente
            const maxMarketDate = new Date(latestMarketDateStr);
            const cutoffTradingDate = new Date(maxMarketDate);
            cutoffTradingDate.setDate(cutoffTradingDate.getDate() - 7);
            const cutoffDateStr = cutoffTradingDate.toISOString().split('T')[0];

            // Filtra apenas tickers ativos negociados nos últimos 7 dias (mantendo sempre o IBOV no topo)
            const activeTickers = tickers.filter(t => {
                if (t === 'IBOV') return false; // adicionado manualmente no topo
                const item = DATA[t];
                if (!item || !item.dates || item.dates.length === 0) return false;
                const lastDate = item.dates[item.dates.length - 1];
                return lastDate >= cutoffDateStr;
            });

            // Coloca os índices com destaque no topo
            const indices = ['IBOV'];
            if (DATA['IFNC']) indices.push('IFNC');
            if (DATA['SEGUROS']) indices.push('SEGUROS');
            const sortedTickers = [...indices, ...activeTickers.filter(t => !['IBOV', 'IFNC', 'SEGUROS'].includes(t)).sort()];

            // Se o ticker salvo ou selecionado não estiver na lista ativa, fallback para ITUB4
            if (!sortedTickers.includes(currentTicker)) {
                currentTicker = sortedTickers.includes('ITUB4') ? 'ITUB4' : sortedTickers[0];
            }

            // Popula tanto o select oculto quanto a lista pesquisável
            sortedTickers.forEach(t => {
                if (!DATA[t]) return;
                const opt = document.createElement('option');
                opt.value = t;
                let displayLabel = `${t} - ${DATA[t].company}`;
                if (t === 'IBOV') displayLabel = `📊 IBOV - ${DATA[t].company}`;
                else if (t === 'IFNC') displayLabel = `🏦 IFNC - ${DATA[t].company}`;
                else if (t === 'SEGUROS') displayLabel = `🛡️ SEGUROS - ${DATA[t].company}`;
                opt.textContent = displayLabel;
                if (t === currentTicker) opt.selected = true;
                select.appendChild(opt);
            });

            // Inicializa o Combobox Pesquisável
            setupCombobox(sortedTickers);



            // Atualiza botões de período para refletir o último período salvo

            document.querySelectorAll('.period-btn[onclick^="setPeriod"]').forEach(b => {

                const onclickStr = b.getAttribute('onclick') || '';

                if (onclickStr.includes(`setPeriod(${currentYears}`)) {

                    b.classList.add('active');

                } else {

                    b.classList.remove('active');

                }

            });

        }



        let allAvailableTickers = [];

        function setupCombobox(tickersList) {
            allAvailableTickers = tickersList;
            const input = document.getElementById('tickerSearchInput');
            const dropdown = document.getElementById('comboboxDropdown');
            const arrow = document.getElementById('comboboxArrow');
            const select = document.getElementById('tickerSelect');

            if (!input || !dropdown) return;

            let selectedIndex = -1;

            // Define o valor inicial do input baseado no currentTicker
            updateComboboxInputValue(currentTicker);

            function updateComboboxInputValue(ticker) {
                if (!DATA[ticker]) return;
                let label = `${ticker} - ${DATA[ticker].company}`;
                if (ticker === 'IBOV') label = `📊 IBOV - ${DATA[ticker].company}`;
                else if (ticker === 'IFNC') label = `🏦 IFNC - ${DATA[ticker].company}`;
                else if (ticker === 'SEGUROS') label = `🛡️ SEGUROS - ${DATA[ticker].company}`;
                input.value = label;
            }

            function updateActiveItem(items) {
                items.forEach((it, idx) => {
                    if (idx === selectedIndex) {
                        it.classList.add('active');
                        it.scrollIntoView({ block: 'nearest' });
                    } else {
                        it.classList.remove('active');
                    }
                });
            }

            function renderDropdownItems(filterText = '') {
                const query = filterText.trim().toLowerCase();
                dropdown.innerHTML = '';
                selectedIndex = -1;

                const matches = allAvailableTickers.filter(t => {
                    if (!DATA[t]) return false;
                    if (!query) return true; // Mostra tudo se estiver vazio
                    const tUpper = t.toLowerCase();
                    const name = (DATA[t].company || '').toLowerCase();
                    return tUpper.includes(query) || name.includes(query);
                });

                if (matches.length === 0) {
                    dropdown.innerHTML = '<div class="combobox-empty">Nenhuma ação encontrada</div>';
                    return;
                }

                matches.forEach((t, idx) => {
                    const item = document.createElement('div');
                    item.className = 'combobox-item' + (t === currentTicker ? ' active' : '');
                    if (t === currentTicker) selectedIndex = idx;
                    
                    let icon = '';
                    if (t === 'IBOV') icon = '📊 ';
                    else if (t === 'IFNC') icon = '🏦 ';
                    else if (t === 'SEGUROS') icon = '🛡️ ';

                    item.innerHTML = `
                        <div style="display:flex; align-items:center;">
                            <span class="combobox-item-ticker">${icon}${t}</span>
                            <span class="combobox-item-name">${DATA[t].company}</span>
                        </div>
                    `;

                    item.addEventListener('click', () => {
                        changeTicker(t);
                        dropdown.style.display = 'none';
                        arrow.textContent = '▼';
                    });

                    item.addEventListener('mouseenter', () => {
                        selectedIndex = idx;
                        const items = dropdown.querySelectorAll('.combobox-item');
                        items.forEach((it, i) => it.classList.toggle('active', i === selectedIndex));
                    });

                    dropdown.appendChild(item);
                });

                // Se houver itens e nenhum estiver ativo por ser currentTicker, foca o primeiro
                if (selectedIndex === -1 && matches.length > 0) {
                    selectedIndex = 0;
                    const firstIt = dropdown.querySelector('.combobox-item');
                    if (firstIt) firstIt.classList.add('active');
                }
            }

            // Ao focar/clicar no input: limpa o campo e exibe a lista completa de opções
            input.addEventListener('focus', () => {
                input.value = '';
                renderDropdownItems('');
                dropdown.style.display = 'block';
                arrow.textContent = '▲';
            });

            input.addEventListener('click', () => {
                if (input.value !== '') {
                    input.value = '';
                    renderDropdownItems('');
                }
                dropdown.style.display = 'block';
                arrow.textContent = '▲';
            });

            // Ao digitar: filtra dinamicamente
            input.addEventListener('input', () => {
                dropdown.style.display = 'block';
                arrow.textContent = '▲';
                renderDropdownItems(input.value);
            });

            // Navegação por teclado: Setas Cima/Baixo, Enter e Escape
            input.addEventListener('keydown', (e) => {
                const items = dropdown.querySelectorAll('.combobox-item');
                if (dropdown.style.display !== 'block') {
                    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                        dropdown.style.display = 'block';
                        arrow.textContent = '▲';
                        renderDropdownItems(input.value);
                        e.preventDefault();
                        return;
                    }
                }

                if (items.length > 0) {
                    if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        selectedIndex = (selectedIndex + 1) % items.length;
                        updateActiveItem(items);
                    } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        selectedIndex = (selectedIndex - 1 + items.length) % items.length;
                        updateActiveItem(items);
                    } else if (e.key === 'Enter') {
                        e.preventDefault();
                        if (selectedIndex >= 0 && selectedIndex < items.length) {
                            items[selectedIndex].click();
                        } else if (items.length > 0) {
                            items[0].click();
                        }
                        input.blur();
                    }
                }

                if (e.key === 'Escape') {
                    dropdown.style.display = 'none';
                    arrow.textContent = '▼';
                    updateComboboxInputValue(currentTicker);
                    input.blur();
                }
            });

            // Clique na setinha abre/fecha dropdown completo
            if (arrow) {
                arrow.addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (dropdown.style.display === 'block') {
                        dropdown.style.display = 'none';
                        arrow.textContent = '▼';
                    } else {
                        renderDropdownItems('');
                        dropdown.style.display = 'block';
                        arrow.textContent = '▲';
                        input.focus();
                    }
                });
            }

            // Fechar ao clicar fora
            document.addEventListener('click', (e) => {
                if (!e.target.closest('#comboboxWrapper')) {
                    if (dropdown.style.display === 'block') {
                        dropdown.style.display = 'none';
                        arrow.textContent = '▼';
                        updateComboboxInputValue(currentTicker);
                    }
                }
            });
        }

        function changeTicker(ticker) {
            isTimeSliderActive = false;
            customDateStartIndex = null;
            customDateEndIndex = null;
            currentTicker = ticker;

            localStorage.setItem('fundamentalista_ticker', ticker);

            const select = document.getElementById('tickerSelect');
            if (select) select.value = ticker;

            const input = document.getElementById('tickerSearchInput');
            if (input && DATA[ticker]) {
                let label = `${ticker} - ${DATA[ticker].company}`;
                if (ticker === 'IBOV') label = `📊 IBOV - ${DATA[ticker].company}`;
                else if (ticker === 'IFNC') label = `🏦 IFNC - ${DATA[ticker].company}`;
                else if (ticker === 'SEGUROS') label = `🛡️ SEGUROS - ${DATA[ticker].company}`;
                input.value = label;
            }

            renderCharts();
            updateHeaderSubtitle(ticker);
            updateEventsDrawerForTicker(ticker);
        }



        function setPeriod(years, btn) {
            isTimeSliderActive = false;
            customDateStartIndex = null;
            customDateEndIndex = null;
            currentYears = years;

            localStorage.setItem('fundamentalista_years', years);

            document.querySelectorAll('.period-btn[onclick^="setPeriod"]').forEach(b => {
                if (parseInt(b.getAttribute('data-period-years'), 10) === years) {
                    b.classList.add('active');
                } else {
                    b.classList.remove('active');
                }
            });

            renderCharts();
            if (typeof renderHeatmap === 'function') renderHeatmap();
            if (typeof updateEventsDrawerForTicker === 'function') updateEventsDrawerForTicker(currentTicker);
        }



        function calcMean(arr, allowNegative = false) {

            const valid = arr.filter(x => x !== null && !isNaN(x) && (allowNegative || x > 0));

            if (!valid.length) return 0;

            return valid.reduce((a, b) => a + b, 0) / valid.length;

        }



        function calcEMA(arr, period = 50) {

            const k = 2 / (period + 1);

            const ema = [];

            let prev = null;

            for (let i = 0; i < arr.length; i++) {

                const val = arr[i];

                if (val === null || val === undefined || isNaN(val)) {

                    ema.push(null);

                    continue;

                }

                if (prev === null) {

                    prev = val;

                } else {

                    prev = (val * k) + (prev * (1 - k));

                }

                ema.push(prev);

            }

            return ema;

        }



        function createOrUpdateChart(chartId, label, dates, values, color, isPercent = false, prefix = '', allowNegative = false, secondaryLine = null, secondaryLabel = null, secondaryColor = '#f59e0b', showBands = false) {

            const ctx = document.getElementById(chartId).getContext('2d');
            applyGlassChartTheme();

            const mean = calcMean(values, allowNegative);

            const meanLine = dates.map(() => mean);



            if (charts[chartId]) {

                charts[chartId].destroy();
                const canvasEl = document.getElementById(chartId);
                if (canvasEl) {
                    canvasEl.style.width = '';
                    canvasEl.style.height = '';
                    canvasEl.removeAttribute('width');
                    canvasEl.removeAttribute('height');
                }

            }



            const isMobile = window.innerWidth < 768;



            charts[chartId] = new Chart(ctx, {

                type: 'line',

                data: {

                    labels: dates,

                    datasets: (function() {

                        const ds = [

                            {

                                label: label,

                                data: values,

                                borderColor: color,

                                backgroundColor: function(c) {
                                    const area = c.chart.chartArea;
                                    if (!area) return color + '15';
                                    const g = c.chart.ctx.createLinearGradient(0, area.top, 0, area.bottom);
                                    g.addColorStop(0, color + '38');
                                    g.addColorStop(0.6, color + '0d');
                                    g.addColorStop(1, color + '00');
                                    return g;
                                },

                                borderWidth: 2,

                                pointRadius: 0,

                                pointHoverRadius: 4,

                                fill: true,

                                tension: 0.1

                            }

                        ];



                        if (secondaryLine) {

                            ds.push({

                                label: secondaryLabel || 'EMA(50)',

                                data: secondaryLine,

                                borderColor: secondaryColor,

                                borderWidth: 1.8,

                                borderDash: [4, 4],

                                pointRadius: 0,

                                pointHoverRadius: 4,

                                fill: false,

                                tension: 0.1

                            });

                        } else {

                            if (showBands) {

                                const plus50 = dates.map(() => mean * 1.50);

                                const plus25 = dates.map(() => mean * 1.25);

                                const minus25 = dates.map(() => mean * 0.75);

                                const minus50 = dates.map(() => mean * 0.50);



                                ds.push({

                                    label: `+50% (${(mean * 1.5).toFixed(2)})`,

                                    data: plus50,

                                    borderColor: 'rgba(148, 163, 184, 0.45)',

                                    borderWidth: 1.2,

                                    borderDash: [5, 5],

                                    pointRadius: 0,

                                    fill: false

                                });

                                ds.push({

                                    label: `+25% (${(mean * 1.25).toFixed(2)})`,

                                    data: plus25,

                                    borderColor: 'rgba(148, 163, 184, 0.65)',

                                    borderWidth: 1.2,

                                    borderDash: [5, 5],

                                    pointRadius: 0,

                                    fill: false

                                });

                            }



                            ds.push({

                                label: `Média (${mean.toFixed(2)}${isPercent ? '%' : ''})`,

                                data: meanLine,

                                borderColor: getComputedStyle(document.body).getPropertyValue('--mean-line').trim() || '#cbd5e1',

                                borderWidth: 1.6,

                                borderDash: [5, 5],

                                pointRadius: 0,

                                fill: false

                            });



                            if (showBands) {

                                const minus25 = dates.map(() => mean * 0.75);

                                const minus50 = dates.map(() => mean * 0.50);



                                ds.push({

                                    label: `-25% (${(mean * 0.75).toFixed(2)})`,

                                    data: minus25,

                                    borderColor: 'rgba(148, 163, 184, 0.65)',

                                    borderWidth: 1.2,

                                    borderDash: [5, 5],

                                    pointRadius: 0,

                                    fill: false

                                });

                                ds.push({

                                    label: `-50% (${(mean * 0.50).toFixed(2)})`,

                                    data: minus50,

                                    borderColor: 'rgba(148, 163, 184, 0.45)',

                                    borderWidth: 1.2,

                                    borderDash: [5, 5],

                                    pointRadius: 0,

                                    fill: false

                                });

                            }

                        }

                        return ds;

                    })()

                },

                options: {

                    responsive: true,
                    devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2.5),

                    maintainAspectRatio: false,

                    interaction: {

                        mode: 'index',

                        intersect: false

                    },

                    plugins: {

                        legend: {

                            labels: { 

                                color: getComputedStyle(document.body).getPropertyValue('--text-muted').trim() || '#94a3b8', 

                                font: { size: isMobile ? 10 : 11 },

                                boxWidth: isMobile ? 12 : 20

                            }

                        },

                        tooltip: {

                            callbacks: {

                                label: function(context) {

                                    let val = context.parsed.y;

                                    if (val === null) return '';

                                    return `${context.dataset.label}: ${prefix}${val.toFixed(2)}${isPercent ? '%' : ''}`;

                                }

                            }

                        }

                    },

                    scales: {

                        x: {

                            grid: { color: getComputedStyle(document.body).getPropertyValue('--grid-color').trim() || '#33415522' },

                            ticks: {

                                color: getComputedStyle(document.body).getPropertyValue('--text-muted').trim() || '#94a3b8',

                                font: { size: isMobile ? 9 : 11 },

                                maxTicksLimit: isMobile ? 5 : 8

                            }

                        },

                        y: {

                            grid: { color: getComputedStyle(document.body).getPropertyValue('--grid-color').trim() || '#33415522' },

                            min: chartCustomLimits[chartId] ? chartCustomLimits[chartId].min : undefined,

                            max: chartCustomLimits[chartId] ? chartCustomLimits[chartId].max : undefined,

                            ticks: {

                                color: getComputedStyle(document.body).getPropertyValue('--text-muted').trim() || '#94a3b8',

                                font: { size: isMobile ? 9 : 11 },

                                callback: function(value) {

                                    return `${prefix}${value.toFixed(1)}${isPercent ? '%' : ''}`;

                                }

                            }

                        }

                    }

                }

            });



            return mean;

        }



        function renderCharts() {

            const d = DATA[currentTicker];

            if (!d) return;



            const n = d.dates.length;

            if (n === 0) return;



            let startIdx = 0;
            let endIdx = n - 1;

            if (isTimeSliderActive && customDateStartIndex !== null && customDateEndIndex !== null) {
                startIdx = Math.max(0, Math.min(customDateStartIndex, n - 1));
                endIdx = Math.max(startIdx, Math.min(customDateEndIndex, n - 1));
            } else {
                const lastDate = new Date(d.dates[n - 1]);
                const cutoffDate = new Date(lastDate);
                cutoffDate.setFullYear(cutoffDate.getFullYear() - currentYears);
                const cutoffStr = cutoffDate.toISOString().split('T')[0];

                for (let i = 0; i < n; i++) {
                    if (d.dates[i] >= cutoffStr) {
                        startIdx = i;
                        break;
                    }
                }
            }

            let fDates = [], fPrices = [], fPL = [], fPVP = [], fROE = [], fDY = [];
            for (let i = startIdx; i <= endIdx; i++) {
                fDates.push(d.dates[i]);
                fPrices.push(d.prices[i]);
                fPL.push(d.pl[i]);
                fPVP.push(d.pvp[i]);
                fROE.push(d.roe[i]);
                fDY.push(d.dy ? d.dy[i] : null);
            }

            syncTimeSliderWithData(d.dates, startIdx, endIdx);

            const isIndex = (currentTicker === 'IBOV' || currentTicker === 'IFNC' || currentTicker === 'SEGUROS');
            const isIBOV = (currentTicker === 'IBOV');
            const isIFNC = (currentTicker === 'IFNC');
            const isSEGUROS = (currentTicker === 'SEGUROS');
            const unitPrefix = (isIBOV || isSEGUROS) ? '' : 'R$ ';
            const unitSuffix = (isIBOV || isSEGUROS) ? ' pts' : '';

            const lastIdx = n - 1;
            const curPrice = d.prices[lastIdx];
            const curPL = d.pl[lastIdx];
            const curPVP = d.pvp[lastIdx];
            const curROE = d.roe[lastIdx];
            const curDY = d.dy ? d.dy[lastIdx] : null;
            const curDate = d.dates[lastIdx];

            document.getElementById('kpiPrice').textContent = curPrice ? (isIBOV ? `${curPrice.toLocaleString('pt-BR', {maximumFractionDigits: 0})} pts` : `R$ ${curPrice.toFixed(2)}`) : '-';
            document.getElementById('kpiDate').textContent = `Pregão: ${curDate}`;
            if (typeof updateTickerAnomalyIndicator === 'function') updateTickerAnomalyIndicator(currentTicker);

            document.getElementById('kpiPL').textContent = curPL ? `${curPL.toFixed(2)}x` : '-';
            document.getElementById('kpiPVP').textContent = curPVP ? `${curPVP.toFixed(2)}x` : (isIndex ? 'N/A (Índice)' : '-');
            document.getElementById('kpiROE').textContent = curROE ? `${curROE.toFixed(1)}%` : (isIndex ? 'N/A (Índice)' : '-');
            document.getElementById('kpiDY').textContent = (curDY !== null && curDY !== undefined) ? `${curDY.toFixed(2)}%` : (isIndex ? 'N/A (Índice)' : '-');

            const ema50Full = calcEMA(d.prices, 50);
            const startIndex = n - fDates.length;
            const fEMA50 = ema50Full.slice(startIndex);
            const lastEMA50 = fEMA50[fEMA50.length - 1];
            const emaValFormatted = lastEMA50 ? (isIBOV ? `${lastEMA50.toLocaleString('pt-BR', {maximumFractionDigits: 0})} pts` : `R$ ${lastEMA50.toFixed(2)}`) : '-';
            const emaLabel = `EMA(50) (${emaValFormatted})`;

                        const isLight = document.body.classList.contains('theme-light');
            const colorPrice = isLight ? '#0284c7' : '#38bdf8';
            const colorEMA = isLight ? '#c2410c' : '#f59e0b';
            const colorPL = isLight ? '#16a34a' : '#34d399';
            const colorPVP = isLight ? '#ea580c' : '#fb923c';
            const colorROE = isLight ? '#dc2626' : '#fb7185';
            const colorDY = isLight ? '#ca8a04' : '#fbbf24';

            let priceChartTitle = 'Preço Fechamento';
            if (isIBOV) priceChartTitle = 'Pontuação Ibovespa (^BVSP)';
            else if (isIFNC) priceChartTitle = 'Cotação Índice Financeiro (FIND11)';
            else if (isSEGUROS) priceChartTitle = 'Índice Seguros (Base 100 - Pesos Iguais)';
            createOrUpdateChart('chartPrice', priceChartTitle, fDates, fPrices, colorPrice, false, unitPrefix, false, fEMA50, emaLabel, colorEMA);
            document.getElementById('badgeEMA50').textContent = `EMA(50): ${emaValFormatted}`;
            setupDualSlider('chartPrice', fPrices, unitPrefix);

            const meanPL = createOrUpdateChart('chartPL', 'P/L (TTM)', fDates, fPL, colorPL, false, '', false, null, null, colorEMA, true);

            document.getElementById('kpiPLMean').textContent = `Média: ${meanPL.toFixed(2)}x`;

            document.getElementById('badgeMeanPL').textContent = `Média: ${meanPL.toFixed(2)}x`;

            setupDualSlider('chartPL', fPL, '', 'x');



                        // Exibir ou ocultar os gráficos e KPIs de P/VP, ROE e Dividend Yield quando IBOV estiver selecionado
            const boxPVP = document.getElementById('boxChartPVP');
            const boxROE = document.getElementById('boxChartROE');
            const boxDY = document.getElementById('boxChartDY');
            const cardDY = document.getElementById('kpiCardDY');
            const cardPVP = document.getElementById('kpiCardPVP');
            const cardROE = document.getElementById('kpiCardROE');

            if (isIndex) {
                if (boxPVP) boxPVP.style.display = 'none';
                if (boxROE) boxROE.style.display = 'none';
                if (boxDY) boxDY.style.display = 'none';
                if (cardDY) cardDY.style.display = 'none';
                if (cardPVP) cardPVP.style.display = 'none';
                if (cardROE) cardROE.style.display = 'none';
            } else {
                if (boxPVP) boxPVP.style.display = '';
                if (boxROE) boxROE.style.display = '';
                if (boxDY) boxDY.style.display = '';
                if (cardDY) cardDY.style.display = '';
                if (cardPVP) cardPVP.style.display = '';
                if (cardROE) cardROE.style.display = '';

                const meanPVP = createOrUpdateChart('chartPVP', 'P/VP', fDates, fPVP, colorPVP);
                document.getElementById('kpiPVPMean').textContent = `Média: ${meanPVP.toFixed(2)}x`;
                document.getElementById('badgeMeanPVP').textContent = `Média: ${meanPVP.toFixed(2)}x`;
                setupDualSlider('chartPVP', fPVP, '', 'x');

                const meanROE = createOrUpdateChart('chartROE', 'ROE (TTM)', fDates, fROE, colorROE, true, '', true);
                document.getElementById('kpiROEMean').textContent = `Média: ${meanROE.toFixed(1)}%`;
                document.getElementById('badgeMeanROE').textContent = `Média: ${meanROE.toFixed(1)}%`;
                setupDualSlider('chartROE', fROE, '', '%', true);

                const meanDY = createOrUpdateChart('chartDY', 'Dividend Yield TTM', fDates, fDY, colorDY, true);
                document.getElementById('kpiDYMean').textContent = `Média: ${meanDY.toFixed(2)}%`;
                document.getElementById('badgeMeanDY').textContent = `Média: ${meanDY.toFixed(2)}%`;
                setupDualSlider('chartDY', fDY, '', '%');
            }



            // Atualizar Tabela de Precificação por P/L
            const isIBOVIndex = (currentTicker === 'IBOV' || currentTicker === 'IFNC' || currentTicker === 'SEGUROS');
            const lpa = (curPrice && curPL && curPL > 0) ? (curPrice / curPL) : null;
            const lpaLabel = isIBOV ? 'Lucro por Ponto (IBOV)' : (isIFNC ? 'LPA / Cota (FIND11)' : (isSEGUROS ? 'Lucro por Ponto (Índice)' : 'LPA (TTM)'));
            const formatVal = (val) => {
                if (!val) return '-';
                if (isIBOV || isSEGUROS) {
                    return `${val.toFixed(2)} pts`;
                }
                return `R$ ${val.toFixed(2)}`;
            };

            document.getElementById('badgeLPA').textContent = lpa ? `${lpaLabel}: ${formatVal(lpa)}` : `${lpaLabel}: -`;

            const boxGeneral = document.getElementById('boxValuationGeneral');
            const singleContainer = document.getElementById('containerValTableSingle');
            const multiContainer = document.getElementById('containerValCardsMulti');
            const valCardTitle = document.getElementById('valCardTitle');
            const tbody = document.getElementById('valTableBody');

            if (currentTicker === 'SEGUROS') {
                if (boxGeneral) boxGeneral.style.display = 'none';
                if (multiContainer) {
                    multiContainer.style.display = 'flex';
                    multiContainer.style.flexDirection = 'column';
                    multiContainer.style.gap = '20px';

                    if (valCardTitle) valCardTitle.textContent = '🛡️ Zonas de Compra & Precificação das Ações do Setor (P/L Real)';
                    document.getElementById('badgeLPA').textContent = 'Sub-Índice Pesos Iguais (33.3%)';

                    const insuranceTickers = [
                        { ticker: 'BBSE3', name: 'BB Seguridade', icon: '🏦' },
                        { ticker: 'CXSE3', name: 'Caixa Seguridade', icon: '🏛️' },
                        { ticker: 'PSSA3', name: 'Porto Seguro', icon: '🚗' }
                    ];

                    const isLightMode = document.body.classList.contains('theme-light');
                    const colorPos = isLightMode ? '#15803d' : '#4ade80';
                    const colorNeg = isLightMode ? '#b91c1c' : '#f87171';
                    const colorYellow = isLightMode ? '#a16207' : '#facc15';
                    const colorPurple = isLightMode ? '#7e22ce' : '#c084fc';
                    const colorCyan = isLightMode ? '#0369a1' : '#38bdf8';
                    const colorText = isLightMode ? '#0f172a' : '#ffffff';
                    const cardBg = isLightMode ? '#f8fafc' : 'rgba(15, 23, 42, 0.6)';
                    const cardBorder = isLightMode ? '#cbd5e1' : 'rgba(56, 189, 248, 0.2)';

                    let multiCardsHtml = '';

                    insuranceTickers.forEach(item => {
                        const tData = DATA[item.ticker];
                        if (!tData) return;
                        const prices = tData.prices;
                        const pls = tData.pl;
                        const validPairs = [];
                        for (let i = 0; i < prices.length; i++) {
                            if (prices[i] && pls[i] && pls[i] > 0) validPairs.push({ p: prices[i], pl: pls[i] });
                        }
                        if (!validPairs.length) return;

                        const curP = validPairs[validPairs.length - 1].p;
                        const curPl = validPairs[validPairs.length - 1].pl;
                        const allPls = validPairs.map(x => x.pl);
                        const meanPl = allPls.reduce((a, b) => a + b, 0) / allPls.length;
                        const minPl = Math.min(...allPls);
                        const maxPl = Math.max(...allPls);
                        const stockLpa = curP / curPl;

                        const priceMax = maxPl * stockLpa;
                        const priceMean = meanPl * stockLpa;
                        const priceDisc25 = (meanPl * 0.75) * stockLpa;
                        const priceDisc50 = (meanPl * 0.50) * stockLpa;
                        const priceMin = minPl * stockLpa;

                        const calcDiffMean = (peVal) => {
                            const pct = ((peVal - meanPl) / meanPl) * 100;
                            const sign = pct > 0 ? '+' : '';
                            const colorStyle = pct < 0 ? `color: ${colorPos};` : (pct > 0 ? `color: ${colorNeg};` : 'color: var(--text-muted);');
                            return `<span style="${colorStyle} font-weight: 700;">${sign}${pct.toFixed(1)}%</span>`;
                        };

                        const calcDiffCurrent = (target) => {
                            if (!curP || !target) return '-';
                            const pct = ((target - curP) / curP) * 100;
                            const sign = pct > 0 ? '+' : '';
                            const colorStyle = pct < 0 ? `color: ${colorPos};` : (pct > 0 ? `color: ${colorNeg};` : 'color: var(--text-muted);');
                            return `<span style="${colorStyle} font-weight: 700;">${sign}${pct.toFixed(1)}%</span>`;
                        };

                        multiCardsHtml += `
                            <div class="chart-box" style="height: auto; min-height: auto; margin-bottom: 16px; border: 1px solid var(--border); box-shadow: 0 4px 16px rgba(0,0,0,0.15);">
                                <div class="chart-header" style="border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <span class="chart-title" style="font-size: 16px; font-weight: 800; color: var(--accent);">${item.icon} ${item.ticker} - ${item.name}</span>
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <span class="chart-mean" style="font-size: 12px; font-weight: 600;">LPA (TTM): R$ ${stockLpa.toFixed(2)}</span>
                                        <button onclick="changeTicker('${item.ticker}')" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); color: var(--accent); border-radius: 6px; padding: 4px 10px; font-size: 11px; cursor: pointer; font-weight: 700; transition: all 0.2s;" title="Abrir análise detalhada de ${item.ticker}">Ver Ação ↗</button>
                                    </div>
                                </div>
                                <div class="val-table-container">
                                    <table class="val-table">
                                        <thead>
                                            <tr>
                                                <th>Cenário</th>
                                                <th style="text-align: center;">Múltiplo P/L</th>
                                                <th style="text-align: center;">vs P/L Médio</th>
                                                <th style="text-align: right;">Preço Estimado</th>
                                                <th style="text-align: right;">Distância vs Atual</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            <tr>
                                                <td><span class="val-tag val-tag-max">🔥 Pico Máximo Histórico</span></td>
                                                <td style="text-align: center; font-weight: 500;">${maxPl.toFixed(2)}x</td>
                                                <td style="text-align: center;">${calcDiffMean(maxPl)}</td>
                                                <td style="text-align: right; font-weight: 700; color: ${colorNeg};">R$ ${priceMax.toFixed(2)}</td>
                                                <td style="text-align: right;">${calcDiffCurrent(priceMax)}</td>
                                            </tr>
                                            <tr>
                                                <td><span class="val-tag val-tag-current">Preço Atual</span></td>
                                                <td style="text-align: center; font-weight: 500;">${curPl.toFixed(2)}x</td>
                                                <td style="text-align: center;">${calcDiffMean(curPl)}</td>
                                                <td style="text-align: right; font-weight: 700; color: ${colorText};">R$ ${curP.toFixed(2)}</td>
                                                <td style="text-align: right;">${calcDiffCurrent(curP)}</td>
                                            </tr>
                                            <tr>
                                                <td><span class="val-tag val-tag-mean">P/L Médio Histórico</span></td>
                                                <td style="text-align: center; font-weight: 500;">${meanPl.toFixed(2)}x</td>
                                                <td style="text-align: center; color: var(--text-muted); font-weight: 500;">0.0%</td>
                                                <td style="text-align: right; font-weight: 700; color: ${colorPos};">R$ ${priceMean.toFixed(2)}</td>
                                                <td style="text-align: right;">${calcDiffCurrent(priceMean)}</td>
                                            </tr>
                                            <tr>
                                                <td><span class="val-tag val-tag-discount">Desconto de 25% no P/L Médio</span></td>
                                                <td style="text-align: center; font-weight: 500;">${(meanPl * 0.75).toFixed(2)}x</td>
                                                <td style="text-align: center; color: #4ade80; font-weight: 500;">-25.0%</td>
                                                <td style="text-align: right; font-weight: 700; color: ${colorYellow};">R$ ${priceDisc25.toFixed(2)}</td>
                                                <td style="text-align: right;">${calcDiffCurrent(priceDisc25)}</td>
                                            </tr>
                                            <tr>
                                                <td><span class="val-tag val-tag-deep">Desconto de 50% no P/L Médio</span></td>
                                                <td style="text-align: center; font-weight: 500;">${(meanPl * 0.50).toFixed(2)}x</td>
                                                <td style="text-align: center; color: #4ade80; font-weight: 500;">-50.0%</td>
                                                <td style="text-align: right; font-weight: 700; color: ${colorPurple};">R$ ${priceDisc50.toFixed(2)}</td>
                                                <td style="text-align: right;">${calcDiffCurrent(priceDisc50)}</td>
                                            </tr>
                                            <tr>
                                                <td><span class="val-tag val-tag-min">🧊 Pico Mínimo Histórico</span></td>
                                                <td style="text-align: center; font-weight: 500;">${minPl.toFixed(2)}x</td>
                                                <td style="text-align: center;">${calcDiffMean(minPl)}</td>
                                                <td style="text-align: right; font-weight: 700; color: ${colorCyan};">R$ ${priceMin.toFixed(2)}</td>
                                                <td style="text-align: right;">${calcDiffCurrent(priceMin)}</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        `;
                    });

                    multiContainer.innerHTML = multiCardsHtml;
                }
            } else {
                if (boxGeneral) boxGeneral.style.display = '';
                if (singleContainer) singleContainer.style.display = '';
                if (multiContainer) multiContainer.style.display = 'none';
                if (valCardTitle) valCardTitle.textContent = 'Precificação Justa & Zonas de Compra (P/L)';

                if (tbody) {
                    if (!lpa || !meanPL || meanPL <= 0) {
                        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 20px;">Dados insuficientes para cálculo de precificação.</td></tr>`;
                    } else {
                        const validPLs = fPL.filter(x => x !== null && !isNaN(x) && x > 0);
                        const maxPL = validPLs.length ? Math.max(...validPLs) : null;
                        const minPL = validPLs.length ? Math.min(...validPLs) : null;

                        const priceMax = maxPL ? lpa * maxPL : null;
                        const priceMin = minPL ? lpa * minPL : null;
                        const priceMean = lpa * meanPL;
                        const priceDisc25 = lpa * (meanPL * 0.75);
                        const priceDisc50 = lpa * (meanPL * 0.50);

                        const isLightMode = document.body.classList.contains('theme-light');
                        const colorPos = isLightMode ? '#15803d' : '#4ade80';
                        const colorNeg = isLightMode ? '#b91c1c' : '#f87171';
                        const colorYellow = isLightMode ? '#a16207' : '#facc15';
                        const colorPurple = isLightMode ? '#7e22ce' : '#c084fc';
                        const colorCyan = isLightMode ? '#0369a1' : '#38bdf8';
                        const colorText = isLightMode ? '#0f172a' : '#ffffff';

                        const calcDiffMean = (peVal) => {
                            const pct = ((peVal - meanPL) / meanPL) * 100;
                            const sign = pct > 0 ? '+' : '';
                            const colorStyle = pct < 0 ? `color: ${colorPos};` : (pct > 0 ? `color: ${colorNeg};` : 'color: var(--text-muted);');
                            return `<span style="${colorStyle} font-weight: 700;">${sign}${pct.toFixed(1)}%</span>`;
                        };

                        const calcDiffCurrent = (target) => {
                            if (!curPrice || !target) return '-';
                            const pct = ((target - curPrice) / curPrice) * 100;
                            const sign = pct > 0 ? '+' : '';
                            const colorStyle = pct < 0 ? `color: ${colorPos};` : (pct > 0 ? `color: ${colorNeg};` : 'color: var(--text-muted);');
                            return `<span style="${colorStyle} font-weight: 700;">${sign}${pct.toFixed(1)}%</span>`;
                        };

                        tbody.innerHTML = `
                            <tr>
                                <td><span class="val-tag val-tag-max">🔥 Pico Máximo Histórico</span></td>
                                <td style="text-align: center; font-weight: 500;">${maxPL ? maxPL.toFixed(2) + 'x' : '-'}</td>
                                <td style="text-align: center;">${maxPL ? calcDiffMean(maxPL) : '-'}</td>
                                <td style="text-align: right; font-weight: 700; color: ${colorNeg}; font-weight: 700;">${formatVal(priceMax)}</td>
                                <td style="text-align: right;">${calcDiffCurrent(priceMax)}</td>
                            </tr>
                            <tr>
                                <td><span class="val-tag val-tag-current">${isIBOV ? 'Pontuação Atual' : 'Preço Atual'}</span></td>
                                <td style="text-align: center; font-weight: 500;">${curPL.toFixed(2)}x</td>
                                <td style="text-align: center;">${calcDiffMean(curPL)}</td>
                                <td style="text-align: right; font-weight: 700; color: ${colorText}; font-weight: 700;">${formatVal(curPrice)}</td>
                                <td style="text-align: right;">${calcDiffCurrent(curPrice)}</td>
                            </tr>
                            <tr>
                                <td><span class="val-tag val-tag-mean">P/L Médio Histórico</span></td>
                                <td style="text-align: center; font-weight: 500;">${meanPL.toFixed(2)}x</td>
                                <td style="text-align: center; color: var(--text-muted); font-weight: 500;">0.0%</td>
                                <td style="text-align: right; font-weight: 700; color: ${colorPos}; font-weight: 700;">${formatVal(priceMean)}</td>
                                <td style="text-align: right;">${calcDiffCurrent(priceMean)}</td>
                            </tr>
                            <tr>
                                <td><span class="val-tag val-tag-discount">Desconto de 25% no P/L Médio</span></td>
                                <td style="text-align: center; font-weight: 500;">${(meanPL * 0.75).toFixed(2)}x</td>
                                <td style="text-align: center; color: #4ade80; font-weight: 500;">-25.0%</td>
                                <td style="text-align: right; font-weight: 700; color: ${colorYellow}; font-weight: 700;">${formatVal(priceDisc25)}</td>
                                <td style="text-align: right;">${calcDiffCurrent(priceDisc25)}</td>
                            </tr>
                            <tr>
                                <td><span class="val-tag val-tag-deep">Desconto de 50% no P/L Médio</span></td>
                                <td style="text-align: center; font-weight: 500;">${(meanPL * 0.50).toFixed(2)}x</td>
                                <td style="text-align: center; color: #4ade80; font-weight: 500;">-50.0%</td>
                                <td style="text-align: right; font-weight: 700; color: ${colorPurple}; font-weight: 700;">${formatVal(priceDisc50)}</td>
                                <td style="text-align: right;">${calcDiffCurrent(priceDisc50)}</td>
                            </tr>
                            <tr>
                                <td><span class="val-tag val-tag-min">🧊 Pico Mínimo Histórico</span></td>
                                <td style="text-align: center; font-weight: 500;">${minPL ? minPL.toFixed(2) + 'x' : '-'}</td>
                                <td style="text-align: center;">${minPL ? calcDiffMean(minPL) : '-'}</td>
                                <td style="text-align: right; font-weight: 700; color: ${colorCyan}; font-weight: 700;">${formatVal(priceMin)}</td>
                                <td style="text-align: right;">${calcDiffCurrent(priceMin)}</td>
                            </tr>
                        `;
                    }
                }
            }
        }

        
        
        
        // ==========================================
        // Histórico de Proventos & Eventos Societários (B3)
        // ==========================================
        let eventsCache = {};
        let activeEventsTab = 'divs';

        // Converte data padrão brasileiro (DD/MM/AAAA) para ISO (AAAA-MM-DD)
        function parseBRDateToISO(dateStr) {
            if (!dateStr || dateStr === '-') return '';
            const parts = dateStr.trim().split('/');
            if (parts.length === 3) {
                return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
            }
            return dateStr;
        }

        // Obtém a data de corte inicial baseada no período atual (1A, 2A, 5A, 10A ou slider duplo)
        function getCurrentFilterCutoffDate() {
            const d = DATA[currentTicker];
            if (!d || !d.dates || d.dates.length === 0) return null;
            const n = d.dates.length;

            if (isTimeSliderActive && customDateStartIndex !== null) {
                const sIdx = Math.max(0, Math.min(customDateStartIndex, n - 1));
                return d.dates[sIdx];
            } else {
                const lastDate = new Date(d.dates[n - 1]);
                const cutoff = new Date(lastDate);
                cutoff.setFullYear(cutoff.getFullYear() - currentYears);
                return cutoff.toISOString().split('T')[0];
            }
        }

        // Inicializa cache em memória a partir de EVENTS_ALL_DATA embutido
        if (typeof EVENTS_ALL_DATA !== 'undefined' && EVENTS_ALL_DATA && Object.keys(EVENTS_ALL_DATA).length > 0) {
            eventsCache = Object.assign({}, EVENTS_ALL_DATA);
        }

        async function toggleCorporateEvents() {
            const drawer = document.getElementById('drawerCorporateEvents');
            const txt = document.getElementById('txtToggleEvents');
            const icon = document.getElementById('iconToggleEvents');
            if (!drawer) return;

            const isHidden = (drawer.style.display === 'none' || !drawer.style.display);
            if (isHidden) {
                drawer.style.display = 'block';
                if (txt) txt.textContent = 'Ocultar Histórico';
                if (icon) icon.style.transform = 'rotate(180deg)';
                await loadEventsForTicker(currentTicker);
            } else {
                drawer.style.display = 'none';
                if (txt) txt.textContent = 'Ver Histórico B3';
                if (icon) icon.style.transform = 'rotate(0deg)';
            }
        }

        function switchEventsTab(tab) {
            activeEventsTab = tab;
            const btnDivs = document.getElementById('tabBtnDividends');
            const btnSplits = document.getElementById('tabBtnSplits');
            const contentDivs = document.getElementById('tabContentDividends');
            const contentSplits = document.getElementById('tabContentSplits');

            if (tab === 'divs') {
                if (btnDivs) btnDivs.classList.add('active');
                if (btnSplits) btnSplits.classList.remove('active');
                if (contentDivs) contentDivs.style.display = 'block';
                if (contentSplits) contentSplits.style.display = 'none';
            } else {
                if (btnDivs) btnDivs.classList.remove('active');
                if (btnSplits) btnSplits.classList.add('active');
                if (contentDivs) contentDivs.style.display = 'none';
                if (contentSplits) contentSplits.style.display = 'block';
            }
        }

        // Função chamada sempre que o ativo muda, o período muda (1A/2A/5A/10A) ou no boot
        function updateEventsDrawerForTicker(ticker) {
            const section = document.getElementById('boxCorporateEventsSection');
            const drawer = document.getElementById('drawerCorporateEvents');
            const badgeCount = document.getElementById('badgeEventsCount');

            // Índices não possuem eventos societários corporativos individuais da B3
            if (['IBOV', 'IFNC', 'SEGUROS'].includes(ticker)) {
                if (section) section.style.display = 'none';
                if (drawer) drawer.style.display = 'none';
                if (badgeCount) badgeCount.style.display = 'none';
                return;
            }

            if (section) section.style.display = 'block';

            // Carrega e atualiza os dados do ativo selecionado com o filtro de período ativo
            loadEventsForTicker(ticker);
        }

        async function loadEventsForTicker(ticker) {
            if (!ticker || ['IBOV', 'IFNC', 'SEGUROS'].includes(ticker)) return;

            const contentDivs = document.getElementById('tabContentDividends');
            const contentSplits = document.getElementById('tabContentSplits');
            const badgeCount = document.getElementById('badgeEventsCount');

            // 1. Tenta recuperar do cache local em memória (populado via EVENTS_ALL_DATA ou requisições anteriores)
            if (eventsCache[ticker]) {
                renderEventsTable(ticker, eventsCache[ticker]);
                return;
            }

            // Exibe estado de carregamento se o drawer estiver visível
            const drawer = document.getElementById('drawerCorporateEvents');
            const isDrawerOpen = drawer && (drawer.style.display === 'block');
            if (isDrawerOpen) {
                if (contentDivs) contentDivs.innerHTML = '<div style="text-align:center; padding:18px; color:var(--text-muted); font-size:12px;">⏳ Carregando histórico da B3 para ' + ticker + '...</div>';
                if (contentSplits) contentSplits.innerHTML = '<div style="text-align:center; padding:18px; color:var(--text-muted); font-size:12px;">⏳ Carregando eventos societários da B3...</div>';
            }

            let data = null;
            // 2. Tenta carregar arquivo individual
            try {
                const resp = await fetch('events/' + ticker + '.json');
                if (resp.ok) {
                    data = await resp.json();
                }
            } catch(e) {}

            // 3. Fallback: tentar consolidado events_data.json
            if (!data) {
                try {
                    const respCons = await fetch('events_data.json');
                    if (respCons.ok) {
                        const allData = await respCons.json();
                        Object.assign(eventsCache, allData);
                        data = eventsCache[ticker] || null;
                    }
                } catch(e) {}
            }

            if (data) {
                eventsCache[ticker] = data;
                renderEventsTable(ticker, data);
            } else {
                // Fallback gracioso com objeto vazio para o ticker
                const emptyData = { ticker: ticker, company: (DATA[ticker] ? DATA[ticker].company : ticker), dividends: [], splits: [], inplits: [], bonuses: [] };
                eventsCache[ticker] = emptyData;
                renderEventsTable(ticker, emptyData);
            }
        }

        function renderEventsTable(ticker, data) {
            const contentDivs = document.getElementById('tabContentDividends');
            const contentSplits = document.getElementById('tabContentSplits');
            const countDivsEl = document.getElementById('countTabDivs');
            const countSplitsEl = document.getElementById('countTabSplits');
            const badgeCount = document.getElementById('badgeEventsCount');

            const allDivs = (data && data.dividends) ? data.dividends : [];
            const splits = (data && data.splits) ? data.splits : [];
            const inplits = (data && data.inplits) ? data.inplits : [];
            const bonuses = (data && data.bonuses) ? data.bonuses : [];
            const allCorporateActions = [...splits, ...inplits, ...bonuses];

            // Aplica filtro temporal sincronizado com o período selecionado (1A, 2A, 5A, 10A ou slider)
            const cutoffDateStr = getCurrentFilterCutoffDate();
            const divs = cutoffDateStr 
                ? allDivs.filter(d => {
                    const iso = parseBRDateToISO(d.date_com || d.date_approval || '');
                    return !iso || iso >= cutoffDateStr;
                })
                : allDivs;

            const corporateActions = cutoffDateStr
                ? allCorporateActions.filter(ev => {
                    const iso = parseBRDateToISO(ev.date_com || ev.date_approval || '');
                    return !iso || iso >= cutoffDateStr;
                })
                : allCorporateActions;

            if (countDivsEl) countDivsEl.textContent = divs.length;
            if (countSplitsEl) countSplitsEl.textContent = corporateActions.length;

            const periodLabel = isTimeSliderActive ? 'período customizado' : `${currentYears}A`;
            if (badgeCount) {
                badgeCount.style.display = 'inline-block';
                badgeCount.textContent = `${divs.length} proventos • ${corporateActions.length} eventos (${periodLabel})`;
            }

            // Renderizar Proventos
            if (contentDivs) {
                if (divs.length === 0) {
                    contentDivs.innerHTML = '<div style="text-align:center; padding:16px; color:var(--text-muted); font-size:12px;">Nenhum provento em dinheiro registrado na B3 para ' + ticker + ' no período selecionado (' + periodLabel + ').</div>';
                } else {
                    let html = '<table class="events-table"><thead><tr>';
                    html += '<th style="width: 140px;">Tipo de Provento</th>';
                    html += '<th style="text-align: right; width: 140px;">Valor por Ação (R$)</th>';
                    html += '<th style="text-align: center; width: 110px;">Data-Com</th>';
                    html += '<th style="text-align: center; width: 130px;">Data de Pagamento</th>';
                    html += '<th style="text-align: center; width: 110px;">Data Aprovação</th>';
                    html += '</tr></thead><tbody>';

                    divs.forEach(d => {
                        let badgeClass = 'badge-other';
                        const typeUpper = (d.type || '').toUpperCase();
                        if (typeUpper.includes('DIVIDENDO')) badgeClass = 'badge-div';
                        else if (typeUpper.includes('JRS') || typeUpper.includes('JCP') || typeUpper.includes('JUROS')) badgeClass = 'badge-jcp';

                        const valStr = (typeof d.value === 'number') ? 'R$ ' + d.value.toFixed(4) : (d.value || '-');
                        const pgtoStr = (d.date_payment && d.date_payment !== '-') ? `<strong style="color:var(--text-main);">${d.date_payment}</strong>` : '<span style="color:var(--text-muted); opacity:0.65;">Não informada</span>';

                        html += `<tr>
                            <td><span class="event-badge ${badgeClass}">${d.type}</span></td>
                            <td style="text-align: right; font-weight: 700; color: #22c55e;">${valStr}</td>
                            <td style="text-align: center; font-weight: 500;">${d.date_com || '-'}</td>
                            <td style="text-align: center;">${pgtoStr}</td>
                            <td style="text-align: center; color: var(--text-muted);">${d.date_approval || '-'}</td>
                        </tr>`;
                    });

                    html += '</tbody></table>';
                    contentDivs.innerHTML = html;
                }
            }

            // Renderizar Splits, Inplits e Bonificações
            if (contentSplits) {
                if (corporateActions.length === 0) {
                    contentSplits.innerHTML = '<div style="text-align:center; padding:16px; color:var(--text-muted); font-size:12px;">Nenhum evento de split, inplit ou bonificação registrado para ' + ticker + ' no período selecionado (' + periodLabel + ').</div>';
                } else {
                    let html = '<table class="events-table"><thead><tr>';
                    html += '<th style="width: 170px;">Evento Societário</th>';
                    html += '<th style="text-align: center; width: 130px;">Proporção / Fator</th>';
                    html += '<th>Efeito Prático</th>';
                    html += '<th style="text-align: center; width: 110px;">Data-Com</th>';
                    html += '<th style="text-align: center; width: 110px;">Data Aprovação</th>';
                    html += '</tr></thead><tbody>';

                    corporateActions.forEach(ev => {
                        let badgeClass = 'badge-other';
                        let labelText = ev.type || 'EVENTO';
                        const typeUpper = (ev.type || '').toUpperCase();
                        if (typeUpper.includes('DESDOBRAMENTO')) {
                            badgeClass = 'badge-split';
                            labelText = 'DESDOBRAMENTO (SPLIT)';
                        } else if (typeUpper.includes('GRUPAMENTO')) {
                            badgeClass = 'badge-inplit';
                            labelText = 'GRUPAMENTO (INPLIT)';
                        } else if (typeUpper.includes('BONIFICACAO') || typeUpper.includes('BONIFICAÇÃO')) {
                            badgeClass = 'badge-bonus';
                            labelText = 'BONIFICAÇÃO';
                        }

                        html += `<tr>
                            <td><span class="event-badge ${badgeClass}">${labelText}</span></td>
                            <td style="text-align: center; font-weight: 700; color: var(--text-main);">${ev.ratio || '-'}</td>
                            <td style="color: var(--text-muted); font-weight: 500;">${ev.description || '-'}</td>
                            <td style="text-align: center; font-weight: 600;">${ev.date_com || '-'}</td>
                            <td style="text-align: center; color: var(--text-muted);">${ev.date_approval || '-'}</td>
                        </tr>`;
                    });

                    html += '</tbody></table>';
                    contentSplits.innerHTML = html;
                }
            }
        }


        function setTheme(theme, btn) {
            document.body.classList.remove('theme-light', 'theme-obsidian', 'theme-bloomberg', 'theme-emerald');
            if (theme === 'light') {
                document.body.classList.add('theme-light');
            }

            document.querySelectorAll('#btnThemeObsidian, #btnThemeLight').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');

            localStorage.setItem('fundamentalista_theme', theme);

            setTimeout(() => {
                if (typeof renderCharts === 'function') renderCharts();
                if (typeof MacroModule !== 'undefined' && MacroModule.onThemeChange) MacroModule.onThemeChange();
                if (typeof IfrModule !== 'undefined' && IfrModule.onThemeChange) IfrModule.onThemeChange();
            }, 50);
        }

        // Inicializa o tema salvo (padrão Obsidian)
        (function initTheme() {
            const savedTheme = localStorage.getItem('fundamentalista_theme') || 'obsidian';
            if (savedTheme === 'light') {
                document.body.classList.add('theme-light');
            }

            window.addEventListener('DOMContentLoaded', () => {
                const btn = (savedTheme === 'light') ? document.getElementById('btnThemeLight') : document.getElementById('btnThemeObsidian');
                if (btn) {
                    document.querySelectorAll('#btnThemeObsidian, #btnThemeLight').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                }
            });
        })();


        function setLayoutMode(mode, btn) {
            Object.keys(charts).forEach(id => {
                if (charts[id]) {
                    try { charts[id].destroy(); } catch (e) {}
                    delete charts[id];
                }
                const c = document.getElementById(id);
                if (c) {
                    c.style.width = '';
                    c.style.height = '';
                    c.removeAttribute('width');
                    c.removeAttribute('height');
                }
            });
            document.body.classList.remove('mode-compact', 'mode-expanded');
            if (mode === 'compact') {
                document.body.classList.add('mode-compact');
            } else if (mode === 'expanded') {
                document.body.classList.add('mode-expanded');
            }

            document.querySelectorAll('#btnLayoutCompact, #btnLayoutNormal, #btnLayoutExpanded').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');

            localStorage.setItem('fundamentalista_layout_mode', mode);
            setTimeout(() => {
                if (typeof renderCharts === 'function') renderCharts();
            }, 100);
        }

        function toggleFullscreenChart(btn) {
            const card = btn.closest('.chart-box');
            if (!card) return;

            const isFullscreen = card.classList.contains('fullscreen-card');
            if (isFullscreen) {
                card.classList.remove('fullscreen-card');
                btn.textContent = '⛶';
                btn.title = 'Maximizar este gráfico em tela cheia';
            } else {
                document.querySelectorAll('.chart-box.fullscreen-card').forEach(c => c.classList.remove('fullscreen-card'));
                card.classList.add('fullscreen-card');
                btn.textContent = '✖ Fechar';
                btn.title = 'Sair da tela cheia';
            }

            setTimeout(() => {
                if (typeof renderCharts === 'function') renderCharts();
            }, 100);
        }

        // Recupera o modo de layout salvo
        (function initLayoutMode() {
            const saved = localStorage.getItem('fundamentalista_layout_mode') || 'normal';
            if (saved === 'compact') {
                document.body.classList.add('mode-compact');
            } else if (saved === 'expanded') {
                document.body.classList.add('mode-expanded');
            }
            window.addEventListener('DOMContentLoaded', () => {
                const btn = saved === 'compact' ? document.getElementById('btnLayoutCompact') :
                            saved === 'expanded' ? document.getElementById('btnLayoutExpanded') :
                            document.getElementById('btnLayoutNormal');
                if (btn) {
                    document.querySelectorAll('#btnLayoutCompact, #btnLayoutNormal, #btnLayoutExpanded').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                }
            });
        })();


        
        /* =========================================================
           MAPA SETORIAL OFICIAL E LÓGICA DO HEATMAP
           ========================================================= */
        const SECTOR_MAP = {
            // Financeiro & Seguros
            'ABCB4': 'Financeiro & Seguros', 'B3SA3': 'Financeiro & Seguros', 'BBAS3': 'Financeiro & Seguros',
            'BBDC3': 'Financeiro & Seguros', 'BBDC4': 'Financeiro & Seguros', 'BBSE3': 'Financeiro & Seguros',
            'BPAC11': 'Financeiro & Seguros', 'BRSR6': 'Financeiro & Seguros',
            'CXSE3': 'Financeiro & Seguros', 'IRBR3': 'Financeiro & Seguros',
            'ITSA3': 'Financeiro & Seguros', 'ITSA4': 'Financeiro & Seguros', 'ITUB3': 'Financeiro & Seguros',
            'ITUB4': 'Financeiro & Seguros', 'PSSA3': 'Financeiro & Seguros', 'SANB11': 'Financeiro & Seguros',
            'SANB4': 'Financeiro & Seguros',

            // Petróleo, Gás & Biocombustíveis
            'CSAN3': 'Petróleo, Gás & Combustíveis', 'PETR3': 'Petróleo, Gás & Combustíveis', 'PETR4': 'Petróleo, Gás & Combustíveis',
            'PRIO3': 'Petróleo, Gás & Combustíveis', 'RAIZ4': 'Petróleo, Gás & Combustíveis',
            'RECV3': 'Petróleo, Gás & Combustíveis', 'UGPA3': 'Petróleo, Gás & Combustíveis', 'VBBR3': 'Petróleo, Gás & Combustíveis',

            // Energia Elétrica & Saneamento
            'ALUP11': 'Energia & Saneamento', 'AURE3': 'Energia & Saneamento',
            'CMIG3': 'Energia & Saneamento', 'CMIG4': 'Energia & Saneamento', 'CPLE3': 'Energia & Saneamento',
            'CSMG3': 'Energia & Saneamento', 'EGIE3': 'Energia & Saneamento',
            'ENEV3': 'Energia & Saneamento',
            'ENGI11': 'Energia & Saneamento', 'EQTL3': 'Energia & Saneamento', 'ISAE4': 'Energia & Saneamento',
            'ORVR3': 'Energia & Saneamento', 'SAPR11': 'Energia & Saneamento',
            'SAPR4': 'Energia & Saneamento', 'SBSP3': 'Energia & Saneamento', 'TAEE11': 'Energia & Saneamento', // Mineração, Siderurgia & Papel e Celulose
            'BRAP4': 'Mineração & Siderurgia', 'CBAV3': 'Mineração & Siderurgia', 'CMIN3': 'Mineração & Siderurgia',
            'CSNA3': 'Mineração & Siderurgia', 'DXCO3': 'Mineração & Siderurgia', 'GGBR3': 'Mineração & Siderurgia',
            'GGBR4': 'Mineração & Siderurgia', 'GOAU4': 'Mineração & Siderurgia', 'KLBN11': 'Mineração & Siderurgia',
            'KLBN4': 'Mineração & Siderurgia', 'RANI3': 'Mineração & Siderurgia', 'SUZB3': 'Mineração & Siderurgia',
            'UNIP6': 'Mineração & Siderurgia', 'USIM5': 'Mineração & Siderurgia', 'VALE3': 'Mineração & Siderurgia',
            'BRKM5': 'Mineração & Siderurgia',

            // Consumo Não Cíclico & Alimentos / Agro
            'ABEV3': 'Consumo & Alimentos', 'ASAI3': 'Consumo & Alimentos', 'BEEF3': 'Consumo & Alimentos',
            'GMAT3': 'Consumo & Alimentos',
            'MDIA3': 'Consumo & Alimentos', 'PCAR3': 'Consumo & Alimentos', 'SLCE3': 'Consumo & Alimentos', 'SMTO3': 'Consumo & Alimentos',
            'TTEN3': 'Consumo & Alimentos',

            // Varejo & Consumo Cíclico
            'ALPA4': 'Varejo & Consumo Cíclico', 'AMBP3': 'Varejo & Consumo Cíclico', 'AZZA3': 'Varejo & Consumo Cíclico', 'BHIA3': 'Varejo & Consumo Cíclico', 'CEAB3': 'Varejo & Consumo Cíclico',
            'LJQQ3': 'Varejo & Consumo Cíclico', 'LREN3': 'Varejo & Consumo Cíclico',
            'MGLU3': 'Varejo & Consumo Cíclico', 'SBFG3': 'Varejo & Consumo Cíclico', 'SMFT3': 'Varejo & Consumo Cíclico', 'VIVA3': 'Varejo & Consumo Cíclico', 'VULC3': 'Varejo & Consumo Cíclico',

            // Construção Civil & Shoppings
            'ALOS3': 'Construção & Imobiliário', 'CURY3': 'Construção & Imobiliário', 'CYRE3': 'Construção & Imobiliário',
            'DIRR3': 'Construção & Imobiliário', 'EZTC3': 'Construção & Imobiliário', 'GFSA3': 'Construção & Imobiliário',
            'IGTI11': 'Construção & Imobiliário', 'JHSF3': 'Construção & Imobiliário', 'MRVE3': 'Construção & Imobiliário',
            'MULT3': 'Construção & Imobiliário', 'PLPL3': 'Construção & Imobiliário', 'TEND3': 'Construção & Imobiliário',

            // Saúde & Cuidados
            'DASA3': 'Saúde & Cuidados', 'FLRY3': 'Saúde & Cuidados', 'HAPV3': 'Saúde & Cuidados',
            'HYPE3': 'Saúde & Cuidados', 'ONCO3': 'Saúde & Cuidados',
            'PGMN3': 'Saúde & Cuidados', 'QUAL3': 'Saúde & Cuidados', 'RADL3': 'Saúde & Cuidados',
            'RDOR3': 'Saúde & Cuidados', 'VVEO3': 'Saúde & Cuidados',

            // Bens Industriais, Transporte & Logística
            'CVCB3': 'Transporte & Bens Industriais',
            'ECOR3': 'Transporte & Bens Industriais', 'FRAS3': 'Transporte & Bens Industriais',
            'GGPS3': 'Transporte & Bens Industriais', 'HBSA3': 'Transporte & Bens Industriais', 'JSLG3': 'Transporte & Bens Industriais',
            'KEPL3': 'Transporte & Bens Industriais', 'LEVE3': 'Transporte & Bens Industriais', 'MILS3': 'Transporte & Bens Industriais',
            'MOVI3': 'Transporte & Bens Industriais', 'MYPK3': 'Transporte & Bens Industriais', 'POMO4': 'Transporte & Bens Industriais',
            'RAIL3': 'Transporte & Bens Industriais', 'RAPT4': 'Transporte & Bens Industriais',
            'RENT3': 'Transporte & Bens Industriais', 'SIMH3': 'Transporte & Bens Industriais', 'TUPY3': 'Transporte & Bens Industriais', 'VAMO3': 'Transporte & Bens Industriais', 'WEGE3': 'Transporte & Bens Industriais',

            // Tecnologia & Telecomunicações
            'CASH3': 'Tecnologia & Telecom', 'INTB3': 'Tecnologia & Telecom',
            'LWSA3': 'Tecnologia & Telecom', 'POSI3': 'Tecnologia & Telecom', 'TIMS3': 'Tecnologia & Telecom',
            'TOTS3': 'Tecnologia & Telecom', 'VIVT3': 'Tecnologia & Telecom', 'VLID3': 'Tecnologia & Telecom',

            // Educação
            'ANIM3': 'Educação', 'COGN3': 'Educação', 'YDUQ3': 'Educação'
        };

        const SECTOR_ICONS = {
            'Financeiro & Seguros': '🏦',
            'Petróleo, Gás & Combustíveis': '🛢️',
            'Energia & Saneamento': '⚡',
            'Mineração & Siderurgia': '⛏️',
            'Consumo & Alimentos': '🛒',
            'Varejo & Consumo Cíclico': '🛍️',
            'Construção & Imobiliário': '🏗️',
            'Saúde & Cuidados': '🩺',
            'Transporte & Bens Industriais': '🏭',
            'Tecnologia & Telecom': '💻',
            'Educação': '🎓',
            'Outros': '📦'
        };

        let currentAppTab = 'detail';
        let heatmapSearchQuery = '';
        let heatmapSelectedSector = 'ALL';
        let heatmapSelectedPL = 'ALL';

        function getHeatmapTier(pl) {
            if (pl === null || pl === undefined || isNaN(pl)) return 'nd';
            if (pl < 0 || pl > 50) return 'gt50';
            if (pl <= 8) return '0_8';
            if (pl <= 15) return '8_15';
            if (pl <= 25) return '15_25';
            if (pl <= 50) return '25_50';
            return 'gt50';
        }

        function filterHeatmapPL(tier, el) {
            if (heatmapSelectedPL === tier && tier !== 'ALL') {
                heatmapSelectedPL = 'ALL';
            } else {
                heatmapSelectedPL = tier;
            }

            document.querySelectorAll('.heatmap-legend .legend-item').forEach(item => item.classList.remove('active'));
            if (heatmapSelectedPL === 'ALL') {
                const btnAll = document.getElementById('btnFilterPlAll');
                if (btnAll) btnAll.classList.add('active');
            } else if (el) {
                el.classList.add('active');
            }
            renderHeatmap();
        }

        function switchAppTab(tab) {
            currentAppTab = tab;
            const btnDetail = document.getElementById('btnTabDetail');
            const btnHeatmap = document.getElementById('btnTabHeatmap');
            const btnEvents = document.getElementById('btnTabEvents');
            const btnMacro = document.getElementById('btnTabMacro');
            const secDetail = document.getElementById('tabDetailContent');
            const secHeatmap = document.getElementById('tabHeatmapContent');
            const secEvents = document.getElementById('tabEventsContent');
            const secMacro = document.getElementById('tabMacroContent');
            const btnIfr = document.getElementById('btnTabIfr');
            const secIfr = document.getElementById('tabIfrContent');

            if (btnDetail) btnDetail.classList.remove('active');
            if (btnHeatmap) btnHeatmap.classList.remove('active');
            if (btnEvents) btnEvents.classList.remove('active');
            if (btnMacro) btnMacro.classList.remove('active');
            if (secDetail) secDetail.style.display = 'none';
            if (secHeatmap) secHeatmap.style.display = 'none';
            if (secEvents) secEvents.style.display = 'none';
            if (secMacro) secMacro.style.display = 'none';
            if (btnIfr) btnIfr.classList.remove('active');
            if (secIfr) secIfr.style.display = 'none';

            if (tab === 'detail') {
                if (btnDetail) btnDetail.classList.add('active');
                if (secDetail) secDetail.style.display = 'block';
                setTimeout(() => {
                    if (typeof renderCharts === 'function') renderCharts();
                }, 50);
            } else if (tab === 'events') {
                if (btnEvents) btnEvents.classList.add('active');
                if (secEvents) secEvents.style.display = 'block';
                eventsMapViewMode = 'timeline';
                const btnTl = document.getElementById('btnEvViewTimeline');
                const btnSec = document.getElementById('btnEvViewSector');
                if (btnTl) btnTl.classList.add('active');
                if (btnSec) btnSec.classList.remove('active');
                renderEventsHeatmap();
            } else if (tab === 'macro') {
                if (btnMacro) btnMacro.classList.add('active');
                if (secMacro) secMacro.style.display = 'block';
                if (typeof MacroModule !== 'undefined') MacroModule.onOpen();
            } else if (tab === 'ifr') {
                if (btnIfr) btnIfr.classList.add('active');
                if (secIfr) secIfr.style.display = 'block';
                if (typeof IfrModule !== 'undefined') IfrModule.onOpen();
            } else {
                if (btnHeatmap) btnHeatmap.classList.add('active');
                if (secHeatmap) secHeatmap.style.display = 'block';
                renderHeatmap();
            }
        }

        function getHeatmapClassForPL(pl) {
            if (pl === null || pl === undefined || isNaN(pl)) return 'color-pl-nd';
            if (pl < 0) return 'color-pl-vm-forte';
            if (pl <= 8) return 'color-pl-limao';
            if (pl <= 15) return 'color-pl-verde';
            if (pl <= 25) return 'color-pl-claro';
            if (pl <= 50) return 'color-pl-vm-claro';
            return 'color-pl-vm-forte';
        }

        function getHeatmapTagForPL(pl) {
            if (pl === null || pl === undefined || isNaN(pl)) return 'Sem P/L';
            if (pl < 0) return 'Prejuízo';
            if (pl <= 8) return '0 a 8x';
            if (pl <= 15) return '8 a 15x';
            if (pl <= 25) return '15 a 25x';
            if (pl <= 50) return '25 a 50x';
            return '> 50x';
        }

        function renderHeatmap() {
            const container = document.getElementById('heatmapContainer');
            if (!container) return;

            // Popular select de setores uma única vez se vazio
            const secSelect = document.getElementById('heatmapSectorFilter');
            if (secSelect && secSelect.options.length <= 1) {
                const uniqueSecs = Array.from(new Set(Object.values(SECTOR_MAP))).sort();
                uniqueSecs.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s;
                    opt.textContent = `${SECTOR_ICONS[s] || '📁'} ${s}`;
                    secSelect.appendChild(opt);
                });
            }

            // Agrupar ações por setor
            const sectorGroups = {};
            let totalCount = 0;

            const q = heatmapSearchQuery.trim().toLowerCase();

            Object.keys(DATA).forEach(ticker => {
                if (ticker === 'IBOV' || ticker === 'IFNC' || ticker === 'SEGUROS') return;

                const item = DATA[ticker];
                const sector = SECTOR_MAP[ticker] || 'Outros';

                if (heatmapSelectedSector !== 'ALL' && sector !== heatmapSelectedSector) return;

                const compName = (item.company || '').toLowerCase();
                if (q && !ticker.toLowerCase().includes(q) && !compName.includes(q)) return;

                const validPrices = (item.prices || []).filter(p => p !== null && !isNaN(p));
                const validPls = (item.pl || []).filter(p => p !== null && !isNaN(p));
                const curPrice = validPrices.length ? validPrices[validPrices.length - 1] : null;
                const curPl = validPls.length ? validPls[validPls.length - 1] : null;

                if (heatmapSelectedPL !== 'ALL') {
                    const itemTier = getHeatmapTier(curPl);
                    if (itemTier !== heatmapSelectedPL) return;
                }

                // Calcular a média histórica do P/L respeitando o período selecionado (currentYears: 1, 2, 5 ou 10 anos)
                const datesArr = item.dates || [];
                const plArr = item.pl || [];
                let startIdxHm = 0;
                if (datesArr.length > 0) {
                    const lastDt = new Date(datesArr[datesArr.length - 1]);
                    const cutoffDt = new Date(lastDt);
                    cutoffDt.setFullYear(cutoffDt.getFullYear() - currentYears);
                    const cutoffStrHm = cutoffDt.toISOString().split('T')[0];
                    for (let i = 0; i < datesArr.length; i++) {
                        if (datesArr[i] >= cutoffStrHm) {
                            startIdxHm = i;
                            break;
                        }
                    }
                }
                const periodPositivePls = [];
                for (let i = startIdxHm; i < plArr.length; i++) {
                    const pVal = plArr[i];
                    if (pVal !== null && !isNaN(pVal) && pVal > 0) {
                        periodPositivePls.push(pVal);
                    }
                }
                const meanPl = periodPositivePls.length ? (periodPositivePls.reduce((a, b) => a + b, 0) / periodPositivePls.length) : null;
                let diffPct = null;
                if (curPl !== null && meanPl !== null && meanPl > 0) {
                    diffPct = ((curPl - meanPl) / meanPl) * 100;
                }

                if (!sectorGroups[sector]) sectorGroups[sector] = [];
                sectorGroups[sector].push({
                    ticker: ticker,
                    name: item.company || ticker,
                    price: curPrice,
                    pl: curPl,
                    meanPl: meanPl,
                    diffPct: diffPct
                });
                totalCount++;
            });

            const badgeTotal = document.getElementById('badgeTotalStocksHeatmap');
            if (badgeTotal) badgeTotal.textContent = `${totalCount} Ações`;

            // Ordenar ações dentro de cada setor por P/L crescente
            Object.keys(sectorGroups).forEach(sec => {
                sectorGroups[sec].sort((a, b) => {
                    const plA = a.pl === null ? 999999 : a.pl;
                    const plB = b.pl === null ? 999999 : b.pl;
                    return plA - plB;
                });
            });

            // Ordem dos setores
            const sectorOrder = [
                'Financeiro & Seguros', 'Petróleo, Gás & Combustíveis', 'Energia & Saneamento',
                'Mineração & Siderurgia', 'Consumo & Alimentos', 'Varejo & Consumo Cíclico',
                'Construção & Imobiliário', 'Saúde & Cuidados', 'Transporte & Bens Industriais',
                'Tecnologia & Telecom', 'Educação', 'Outros'
            ];

            let html = '';
            sectorOrder.forEach(secName => {
                const list = sectorGroups[secName];
                if (!list || list.length === 0) return;

                const icon = SECTOR_ICONS[secName] || '📁';
                html += `
                    <div class="sector-group">
                        <div class="sector-title">
                            <div class="sector-title-text">
                                <span>${icon}</span>
                                <span>${secName}</span>
                            </div>
                            <span class="sector-count-badge">${list.length} ativos</span>
                        </div>
                        <div class="sector-cards-grid">
                `;

                list.forEach(stock => {
                    const colorClass = getHeatmapClassForPL(stock.pl);
                    const plStr = stock.pl !== null ? `${stock.pl.toFixed(1)}x` : 'N/D';
                    const priceStr = stock.price !== null ? `R$ ${stock.price.toFixed(2)}` : '-';

                    // Formatar % vs Média Histórica da Ação
                    let diffBadgeHtml = '<span class="tile-pl-tag diff-tag-neutral">N/D</span>';
                    let meanInfoStr = 'Média Histórica: N/D';
                    if (stock.diffPct !== null && !isNaN(stock.diffPct)) {
                        const sign = stock.diffPct > 0 ? '+' : '';
                        const formattedPct = `${sign}${stock.diffPct.toFixed(1)}%`;
                        meanInfoStr = `Média Histórica: ${stock.meanPl.toFixed(1)}x (${formattedPct})`;
                        if (stock.diffPct < 0) {
                            diffBadgeHtml = `<span class="tile-pl-tag diff-tag-discount" title="Desconto de ${Math.abs(stock.diffPct).toFixed(1)}% vs Média Histórica (${stock.meanPl.toFixed(1)}x)">▼ ${formattedPct}</span>`;
                        } else if (stock.diffPct > 0) {
                            diffBadgeHtml = `<span class="tile-pl-tag diff-tag-premium" title="Prêmio de +${stock.diffPct.toFixed(1)}% vs Média Histórica (${stock.meanPl.toFixed(1)}x)">▲ ${formattedPct}</span>`;
                        } else {
                            diffBadgeHtml = `<span class="tile-pl-tag diff-tag-neutral">0.0%</span>`;
                        }
                    }

                    html += `
                        <div class="heatmap-stock-tile ${colorClass}" onclick="openDetailFromHeatmap('${stock.ticker}')" title="${stock.ticker} - ${stock.name}&#10;P/L Atual: ${plStr}&#10;${meanInfoStr}&#10;Cotação: ${priceStr}&#10;Clique para ver gráficos e valuation completos">
                            <span class="tile-view-hint">↗</span>
                            <div class="tile-header">
                                <span class="tile-ticker">${stock.ticker}</span>
                                <span class="tile-price">${priceStr}</span>
                            </div>
                            <div class="tile-name" title="${stock.name}">${stock.name}</div>
                            <div class="tile-bottom">
                                <span class="tile-pl-val">${plStr}</span>
                                ${diffBadgeHtml}
                            </div>
                        </div>
                    `;
                });

                html += `
                        </div>
                    </div>
                `;
            });

            if (html === '') {
                html = `
                    <div style="text-align: center; padding: 50px 20px; color: var(--text-muted); background: var(--card-bg); border-radius: var(--radius); border: 1px solid var(--border);">
                        <p style="font-size: 16px; font-weight: 600; margin-bottom: 6px;">Nenhuma ação encontrada para o filtro atual.</p>
                        <p style="font-size: 13px;">Tente buscar por outro termo ou selecione Todos os Setores.</p>
                    </div>
                `;
            }

            container.innerHTML = html;
        }

        function filterHeatmap(q) {
            heatmapSearchQuery = q;
            renderHeatmap();
        }

        function filterHeatmapSector(sec) {
            heatmapSelectedSector = sec;
            renderHeatmap();
        }

        function openDetailFromHeatmap(ticker) {
            switchAppTab('detail');
            changeTicker(ticker);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function openDetailAndEventsFromMap(ticker) {
            switchAppTab('detail');
            changeTicker(ticker);
            const drawer = document.getElementById('drawerCorporateEvents');
            const txt = document.getElementById('txtToggleEvents');
            const icon = document.getElementById('iconToggleEvents');
            if (drawer) {
                drawer.style.display = 'block';
                if (txt) txt.textContent = 'Ocultar Histórico';
                if (icon) icon.style.transform = 'rotate(180deg)';
                switchEventsTab('splits');
                loadEventsForTicker(ticker);
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        let eventsMapSearchQuery = '';
        let eventsMapSelectedSector = 'ALL';
        let eventsMapSelectedYear = 'ALL';
        let eventsMapSelectedType = 'ALL';
        let eventsMapViewMode = 'timeline';

        function parseDateBRToISO(dtStr) {
            if (!dtStr || typeof dtStr !== 'string') return '0000-00-00';
            const parts = dtStr.trim().split('/');
            if (parts.length === 3) {
                return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
            }
            return dtStr;
        }

        function classifyCorporateEvent(rawType) {
            const t = (rawType || '').toUpperCase();
            if (t.includes('DESDOBRAMENTO')) {
                return { category: 'SPLIT', colorClass: 'color-ev-split', shortLabel: 'SPLIT', icon: '🟢', fullLabel: 'Desdobramento (Split)' };
            }
            if (t.includes('GRUPAMENTO')) {
                return { category: 'INPLIT', colorClass: 'color-ev-inplit', shortLabel: 'INPLIT', icon: '🔴', fullLabel: 'Grupamento (Inplit)' };
            }
            if (t.includes('BONIFICA')) {
                return { category: 'BONUS', colorClass: 'color-ev-bonus', shortLabel: 'BONIFICAÇÃO', icon: '🔵', fullLabel: 'Bonificação em Ações' };
            }
            if (t.includes('CIS RED CAP') || t.includes('CISAO') || t.includes('CISÃO')) {
                return { category: 'CIS', colorClass: 'color-ev-cis', shortLabel: 'CIS RED CAP', icon: '🟣', fullLabel: 'Cisão / Redução de Capital' };
            }
            return { category: 'OTHER', colorClass: 'color-ev-other', shortLabel: t || 'EVENTO', icon: '🟡', fullLabel: t || 'Evento Societário' };
        }

        function formatEventRatioAndEffect(category, rawType, ratio, desc) {
            if (category === 'CIS') {
                const r = (ratio || '').toString().replace('%', '');
                return { ratioText: `${r}%`, effectText: `Cisão / Red. Cap. (${r}%)` };
            }
            if (category === 'OTHER') {
                const r = (ratio || '').toString();
                const d = (desc && desc !== ratio) ? desc : `${rawType}: Fator ${r}`;
                return { ratioText: r.includes('%') || r.includes(':') ? r : `${r}%`, effectText: d };
            }
            return { ratioText: ratio || '-', effectText: desc || rawType || '-' };
        }

        function buildAllFlatCorporateEvents() {
            const list = [];
            Object.keys(CORPORATE_EVENTS_MAP || {}).forEach(ticker => {
                const entry = CORPORATE_EVENTS_MAP[ticker];
                if (!entry) return;
                const compName = (DATA[ticker] && DATA[ticker].company) ? DATA[ticker].company : (entry.company || ticker);
                const sector = SECTOR_MAP[ticker] || 'Outros';
                const rawEvents = [
                    ...(entry.splits || []),
                    ...(entry.inplits || []),
                    ...(entry.bonuses || [])
                ];
                rawEvents.forEach(ev => {
                    const cls = classifyCorporateEvent(ev.type);
                    const isoDate = parseDateBRToISO((ev.date_com && ev.date_com !== '-') ? ev.date_com : ev.date_approval);
                    const yearNum = parseInt(isoDate.substring(0, 4), 10) || 0;
                    const fmt = formatEventRatioAndEffect(cls.category, ev.type, ev.ratio, ev.description);
                    list.push({
                        ticker: ticker,
                        company: compName,
                        sector: sector,
                        rawType: ev.type || 'EVENTO',
                        category: cls.category,
                        colorClass: cls.colorClass,
                        shortLabel: cls.shortLabel,
                        icon: cls.icon,
                        fullLabel: cls.fullLabel,
                        ratio: fmt.ratioText,
                        description: fmt.effectText,
                        dateCom: ev.date_com || '-',
                        dateApproval: ev.date_approval || '-',
                        isoDate: isoDate,
                        year: yearNum
                    });
                });
            });
            list.sort((a, b) => b.isoDate.localeCompare(a.isoDate));
            return list;
        }

        function filterEventsType(type, el) {
            if (eventsMapSelectedType === type && type !== 'ALL') {
                eventsMapSelectedType = 'ALL';
            } else {
                eventsMapSelectedType = type;
            }
            document.querySelectorAll('#tabEventsContent .heatmap-legend .legend-item').forEach(item => item.classList.remove('active'));
            if (eventsMapSelectedType === 'ALL') {
                const btnAll = document.getElementById('btnFilterEvAll');
                if (btnAll) btnAll.classList.add('active');
            } else if (el) {
                el.classList.add('active');
            }
            renderEventsHeatmap();
        }

        function filterEventsMap(q) {
            eventsMapSearchQuery = q || '';
            renderEventsHeatmap();
        }

        function filterEventsSector(sec) {
            eventsMapSelectedSector = sec || 'ALL';
            renderEventsHeatmap();
        }

        function filterEventsYear(yr) {
            eventsMapSelectedYear = yr || 'ALL';
            renderEventsHeatmap();
        }

        function setEventsViewMode(mode, btn) {
            eventsMapViewMode = mode;
            document.querySelectorAll('#btnEvViewSector, #btnEvViewTimeline').forEach(b => b.classList.remove('active'));
            if (btn) btn.classList.add('active');
            renderEventsHeatmap();
        }

        function renderEventsHeatmap() {
            const container = document.getElementById('eventsMapContainer');
            if (!container) return;

            const secSelect = document.getElementById('eventsSectorFilter');
            if (secSelect && secSelect.options.length <= 1) {
                const uniqueSecs = Array.from(new Set(Object.values(SECTOR_MAP))).sort();
                uniqueSecs.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s;
                    opt.textContent = `${SECTOR_ICONS[s] || '📁'} ${s}`;
                    secSelect.appendChild(opt);
                });
            }

            const allEvents = buildAllFlatCorporateEvents();
            const q = eventsMapSearchQuery.trim().toLowerCase();
            const counts = { ALL: 0, SPLIT: 0, INPLIT: 0, BONUS: 0, CIS: 0, OTHER: 0 };

            const filtered = allEvents.filter(ev => {
                if (eventsMapSelectedSector !== 'ALL' && ev.sector !== eventsMapSelectedSector) return false;
                if (eventsMapSelectedYear !== 'ALL') {
                    if (eventsMapSelectedYear === '2025_2026' && (ev.year < 2025 || ev.year > 2026)) return false;
                    if (eventsMapSelectedYear === '2020_2024' && (ev.year < 2020 || ev.year > 2024)) return false;
                    if (eventsMapSelectedYear === '2015_2019' && (ev.year < 2015 || ev.year > 2019)) return false;
                    if (eventsMapSelectedYear === 'PRE_2015' && ev.year >= 2015) return false;
                }
                if (q) {
                    const hay = `${ev.ticker} ${ev.company} ${ev.rawType} ${ev.ratio} ${ev.description} ${ev.dateCom}`.toLowerCase();
                    if (!hay.includes(q)) return false;
                }
                counts.ALL++;
                counts[ev.category] = (counts[ev.category] || 0) + 1;
                if (eventsMapSelectedType !== 'ALL' && ev.category !== eventsMapSelectedType) return false;
                return true;
            });

            const setTxt = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
            setTxt('cntEvAll', counts.ALL);
            setTxt('cntEvSplit', counts.SPLIT);
            setTxt('cntEvInplit', counts.INPLIT);
            setTxt('cntEvBonus', counts.BONUS);
            setTxt('cntEvCis', counts.CIS);
            setTxt('cntEvOther', counts.OTHER);
            setTxt('badgeTotalEventsTab', `${filtered.length} Eventos`);

            const renderTile = (ev) => `
                <div class="event-stock-tile ${ev.colorClass}" onclick="openDetailAndEventsFromMap('${ev.ticker}')" title="${ev.ticker} - ${ev.company}&#10;Evento: ${ev.fullLabel}&#10;Proporção / Fator: ${ev.ratio} (${ev.description})&#10;Data-Com: ${ev.dateCom}&#10;Aprovação: ${ev.dateApproval}&#10;Clique para abrir os gráficos da ação">
                    <div class="event-tile-top">
                        <span class="tile-ticker">${ev.ticker}</span>
                        <span class="event-tile-type-pill">${ev.shortLabel}</span>
                    </div>
                    <div class="tile-name" title="${ev.company}">${ev.company}</div>
                    <div class="event-tile-desc" title="${ev.description}">${ev.description}</div>
                    <div class="event-tile-bottom">
                        <span class="event-tile-ratio" title="Proporção / Fator">${ev.ratio}</span>
                        <span class="event-tile-date" title="Data-Com na B3">📅 ${ev.dateCom}</span>
                    </div>
                </div>
            `;

            let html = '';

            if (eventsMapViewMode === 'timeline') {
                const byYear = {};
                filtered.forEach(ev => {
                    const yKey = ev.year > 0 ? String(ev.year) : 'Sem Data';
                    if (!byYear[yKey]) byYear[yKey] = [];
                    byYear[yKey].push(ev);
                });
                const yearsSorted = Object.keys(byYear).sort((a, b) => b.localeCompare(a));
                yearsSorted.forEach(yr => {
                    const list = byYear[yr];
                    html += `
                        <div class="sector-group">
                            <div class="sector-title">
                                <div class="sector-title-text">
                                    <span>🗓️</span>
                                    <span>Ano de ${yr}</span>
                                </div>
                                <span class="sector-count-badge">${list.length} eventos</span>
                            </div>
                            <div class="events-cards-grid">
                                ${list.map(renderTile).join('')}
                            </div>
                        </div>
                    `;
                });
            } else {
                const sectorGroups = {};
                filtered.forEach(ev => {
                    if (!sectorGroups[ev.sector]) sectorGroups[ev.sector] = [];
                    sectorGroups[ev.sector].push(ev);
                });
                const sectorOrder = [
                    'Financeiro & Seguros', 'Petróleo, Gás & Combustíveis', 'Energia & Saneamento',
                    'Mineração & Siderurgia', 'Consumo & Alimentos', 'Varejo & Consumo Cíclico',
                    'Construção & Imobiliário', 'Saúde & Cuidados', 'Transporte & Bens Industriais',
                    'Tecnologia & Telecom', 'Educação', 'Outros'
                ];
                sectorOrder.forEach(secName => {
                    const list = sectorGroups[secName];
                    if (!list || list.length === 0) return;
                    const icon = SECTOR_ICONS[secName] || '📁';
                    html += `
                        <div class="sector-group">
                            <div class="sector-title">
                                <div class="sector-title-text">
                                    <span>${icon}</span>
                                    <span>${secName}</span>
                                </div>
                                <span class="sector-count-badge">${list.length} eventos</span>
                            </div>
                            <div class="events-cards-grid">
                                ${list.map(renderTile).join('')}
                            </div>
                        </div>
                    `;
                });
            }

            if (html === '') {
                html = `
                    <div style="text-align: center; padding: 50px 20px; color: var(--text-muted); background: var(--card-bg); border-radius: var(--radius); border: 1px solid var(--border);">
                        <p style="font-size: 16px; font-weight: 600; margin-bottom: 6px;">Nenhum evento societário encontrado para o filtro selecionado.</p>
                        <p style="font-size: 13px;">Tente limpar a busca ou selecionar "Todos" na barra de tipos de evento.</p>
                    </div>
                `;
            }

            container.innerHTML = html;
        }
        window.addEventListener('DOMContentLoaded', () => {
            try {
                const totalEv = buildAllFlatCorporateEvents().length;
                const badge = document.getElementById('badgeTotalEventsTab');
                if (badge && totalEv > 0) badge.textContent = `${totalEv} Eventos`;
            } catch (e) {}
        });
    

        window.onload = function() {

            initSelect();

            renderCharts();
            updateHeaderSubtitle(currentTicker);
            updateEventsDrawerForTicker(currentTicker);

        };



                // Auditoria Continua: Dicionario de anomalias ativas por ticker
        var ACTIVE_ANOMALIES_BY_TICKER = {};

        function updateTickerAnomalyIndicator(ticker) {
            var badge = document.getElementById('tickerAnomalyBadge');
            var svg = document.getElementById('tickerAnomalySvg');
            if (!badge || !svg) return;

            var anomalies = ACTIVE_ANOMALIES_BY_TICKER[ticker] || [];
            if (anomalies.length > 0) {
                var hasCritical = anomalies.some(function(a) { return a.severity === 'CRITICAL'; });
                badge.className = hasCritical ? 'ticker-anomaly-critical' : 'ticker-anomaly-warning';
                var titles = anomalies.map(function(a) { return '[' + a.severity + '] ' + a.metric_name + ': ' + a.diagnosis; }).join(' | ');
                badge.title = 'Alerta: ' + anomalies.length + ' anomalia(s) detectada(s) em ' + ticker + ' — ' + titles + ' (Clique para abrir o Painel de Auditoria Detalhado)';
                badge.style.display = 'inline-flex';
                if (hasCritical) {
                    svg.style.filter = 'drop-shadow(0 0 6px rgba(239, 68, 68, 0.9))';
                    svg.setAttribute('stroke', '#ef4444');
                } else {
                    svg.style.filter = 'drop-shadow(0 0 6px rgba(245, 158, 11, 0.9))';
                    svg.setAttribute('stroke', '#f59e0b');
                }
            } else {
                badge.className = '';
                badge.style.display = 'none';
            }
        }

        (function initAnomalyBadge() {
            fetch('anomalies_data.json')
                .then(function(res) {
                    if (!res.ok) throw new Error('Status ' + res.status);
                    return res.json();
                })
                .then(function(data) {
                    ACTIVE_ANOMALIES_BY_TICKER = {};
                    if (data && data.anomalies) {
                        data.anomalies.forEach(function(a) {
                            if (!a.ticker) return;
                            if (!ACTIVE_ANOMALIES_BY_TICKER[a.ticker]) {
                                ACTIVE_ANOMALIES_BY_TICKER[a.ticker] = [];
                            }
                            ACTIVE_ANOMALIES_BY_TICKER[a.ticker].push(a);
                        });
                    }
                    if (typeof currentTicker !== 'undefined') {
                        updateTickerAnomalyIndicator(currentTicker);
                    }
                    var badge = document.getElementById('anomalyFooterBadge');
                    var textEl = document.getElementById('anomalyStatusText');
                    if (!badge || !textEl) return;
                    var total = data.total_active || 0;
                    var critical = data.critical_count || 0;
                    if (total > 0) {
                        badge.classList.add('badge-anomaly-active');
                        badge.classList.remove('badge-anomaly-clean');
                        textEl.textContent = total + (total > 1 ? ' anomalias' : ' anomalia');
                        badge.title = total + ' anomalias detectadas na auditoria. Clique para auditar.';
                    } else {
                        badge.classList.add('badge-anomaly-clean');
                        badge.classList.remove('badge-anomaly-active');
                        textEl.textContent = 'Sem anomalias ativas';
                        badge.title = 'Nenhuma anomalia ativa detectada. Base consistente.';
                    }
                })
                .catch(function(err) {
                    var badge = document.getElementById('anomalyFooterBadge');
                    var textEl = document.getElementById('anomalyStatusText');
                    if (badge && textEl) {
                        badge.classList.add('badge-anomaly-clean');
                        textEl.textContent = 'Auditoria';
                    }
                });
        })();

        const MacroModule = (function () {
            'use strict';

            let initialized = false;
            let liveLoaded = false;
            let copomYear = 2026;
            let curveKind = 'pre';
            let curveBack = 1;
            let txSelected = 0;
            let regimeSelected = 'base';

            const DEFAULT_COPOM = {
                2026: [
                    { date: '2026-01-28', rate: 15.0, label: '15,00% (manutenção)' },
                    { date: '2026-03-18', rate: 14.75, label: '14,75% (−0,25)' },
                    { date: '2026-04-29', rate: 14.5, label: '14,50% (−0,25)' },
                    { date: '2026-06-17', rate: 14.25, label: '14,25% (−0,25)' },
                    { date: '2026-08-05', rate: 14.0, label: '14,00% (−0,25)' },
                    { date: '2026-09-16', rate: 13.75, label: '13,75% (−0,25)' },
                    { date: '2026-11-04', rate: 13.75, label: '13,75% (manutenção)' },
                    { date: '2026-12-09', rate: null, label: null }
                ],
                2027: [
                    { date: '2027-01-27', rate: null, label: null },
                    { date: '2027-03-17', rate: null, label: null },
                    { date: '2027-04-28', rate: null, label: null },
                    { date: '2027-06-16', rate: null, label: null },
                    { date: '2027-08-04', rate: null, label: null },
                    { date: '2027-09-22', rate: null, label: null },
                    { date: '2027-10-27', rate: null, label: null },
                    { date: '2027-12-08', rate: null, label: null }
                ]
            };

            const DEFAULT_FOMC = [
                '2026-01-28', '2026-03-18', '2026-04-29', '2026-06-17',
                '2026-07-29', '2026-09-16', '2026-10-28', '2026-12-09',
                '2027-01-27', '2027-03-17', '2027-04-28', '2027-06-09',
                '2027-07-28', '2027-09-15', '2027-10-27', '2027-12-08'
            ];

            const state = {
                indicators: (MACRO_DATA && MACRO_DATA.indicators) ? JSON.parse(JSON.stringify(MACRO_DATA.indicators)) : {},
                copom_meetings: (MACRO_DATA && MACRO_DATA.copom_meetings) ? JSON.parse(JSON.stringify(MACRO_DATA.copom_meetings)) : JSON.parse(JSON.stringify(DEFAULT_COPOM)),
                fomc_dates: (MACRO_DATA && MACRO_DATA.fomc_dates && MACRO_DATA.fomc_dates.length) ? MACRO_DATA.fomc_dates : DEFAULT_FOMC,
                focus: (MACRO_DATA && MACRO_DATA.focus) ? JSON.parse(JSON.stringify(MACRO_DATA.focus)) : {},
                curva: (MACRO_DATA && MACRO_DATA.curva) ? MACRO_DATA.curva : { historico: {} },
                atualizado_em: (MACRO_DATA && MACRO_DATA.atualizado_em) ? MACRO_DATA.atualizado_em : ''
            };

            const MONTH_NAMES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
            const WEEKDAYS = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];
            const esc = s => String(s == null ? '' : s)
                .replaceAll('&', '&amp;')
                .replaceAll('<', '&lt;')
                .replaceAll('>', '&gt;')
                .replaceAll('"', '&quot;')
                .replaceAll("'", '&#39;');
            const pad2 = n => String(n).padStart(2, '0');
            const fmtNum = (v, d = 2) => (v == null || isNaN(v)) ? '—' : Number(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
            const fmtPct = (v, d = 2) => (v == null || isNaN(v)) ? '—' : fmtNum(v, d) + '%';
            const isLight = () => document.body.classList.contains('theme-light');

            function nowBRT() {
                try {
                    const parts = new Intl.DateTimeFormat('en-CA', {
                        timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit',
                        hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
                    }).formatToParts(new Date()).reduce((acc, p) => { acc[p.type] = p.value; return acc; }, {});
                    return new Date(+parts.year, +parts.month - 1, +parts.day, +parts.hour % 24, +parts.minute, +parts.second);
                } catch (_) {
                    return new Date();
                }
            }
            function todayBRT() {
                const n = nowBRT();
                return new Date(n.getFullYear(), n.getMonth(), n.getDate());
            }
            function parseISO(s) {
                const p = String(s || '').split('-').map(Number);
                return new Date(p[0], (p[1] || 1) - 1, p[2] || 1);
            }
            function toISO(d) { return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`; }
            function toBR(d) { return `${pad2(d.getDate())}/${pad2(d.getMonth() + 1)}/${d.getFullYear()}`; }
            function toBRShort(d) { return `${pad2(d.getDate())}/${pad2(d.getMonth() + 1)}`; }
            function addDays(d, n) { return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n); }

            const holidayCache = {};
            function easter(y) {
                const a = y % 19, b = Math.floor(y / 100), c = y % 100, d = Math.floor(b / 4), e = b % 4;
                const f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30;
                const i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7;
                const m = Math.floor((a + 11 * h + 22 * l) / 451);
                const month = Math.floor((h + l - 7 * m + 114) / 31);
                const day = ((h + l - 7 * m + 114) % 31) + 1;
                return new Date(y, month - 1, day);
            }
            function b3Holidays(y, includeYearEnd = true) {
                const cacheKey = (includeYearEnd ? 'b' : 'n') + y;
                if (holidayCache[cacheKey]) return holidayCache[cacheKey];
                const e = easter(y);
                const s = new Set([
                    toISO(new Date(y, 0, 1)), toISO(addDays(e, -48)), toISO(addDays(e, -47)),
                    toISO(addDays(e, -2)), toISO(new Date(y, 3, 21)), toISO(new Date(y, 4, 1)),
                    toISO(addDays(e, 60)), toISO(new Date(y, 8, 7)), toISO(new Date(y, 9, 12)),
                    toISO(new Date(y, 10, 2)), toISO(new Date(y, 10, 15)), toISO(new Date(y, 11, 25))
                ]);
                if (y >= 2024) s.add(toISO(new Date(y, 10, 20)));
                if (includeYearEnd) {
                    s.add(`${y}-12-24`);
                    s.add(`${y}-12-31`);
                }
                holidayCache[cacheKey] = s;
                return s;
            }
            function isBusinessDay(d, b3 = true) {
                const wd = d.getDay();
                if (wd === 0 || wd === 6) return false;
                return !b3Holidays(d.getFullYear(), b3).has(toISO(d));
            }
            function nextBusinessDay(d, b3 = true) {
                let x = new Date(d);
                while (!isBusinessDay(x, b3)) x = addDays(x, 1);
                return x;
            }
            function businessDaysBetween(from, to, b3 = false) {
                let n = 0, d = addDays(from, 1);
                while (d <= to) {
                    if (isBusinessDay(d, b3)) n++;
                    d = addDays(d, 1);
                }
                return n;
            }
            function getDiJanuaryVertices(count = 8) {
                const today = todayBRT(), out = [];
                for (let y = today.getFullYear() + 1; out.length < count; y++) {
                    const exp = nextBusinessDay(new Date(y, 0, 1), true);
                    if (exp < today) continue;
                    out.push({ code: `DI1F${String(y).slice(2)}`, expiry: exp, du: businessDaysBetween(today, exp, false) });
                }
                return out;
            }
            function allCopomDatesFlat() {
                const out = [];
                Object.keys(state.copom_meetings || {}).sort().forEach(yr => {
                    (state.copom_meetings[yr] || []).forEach(item => { if (item && item.date) out.push(item.date); });
                });
                return out;
            }

            function renderTopBadgeAndKPIs() {
                const ind = state.indicators || {};
                const selicV = ind.selic ? ind.selic.value : null;
                const cdiV = ind.cdi ? ind.cdi.value : null;
                const ipcaV = ind.ipca12m ? ind.ipca12m.value : null;
                const realV = (selicV != null && ipcaV != null) ? (((1 + selicV / 100) / (1 + ipcaV / 100) - 1) * 100) : ind.realRate;

                const topBadge = document.getElementById('badgeMacroSelic');
                if (topBadge && selicV != null) topBadge.textContent = `Selic ${fmtPct(selicV)}`;

                const setTxt = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
                setTxt('mcKpiSelic', fmtPct(selicV));
                setTxt('mcKpiSelicSrc', ind.selic ? `${ind.selic.src || 'BCB'} · ${ind.selic.date || '--'}` : 'BCB · SGS 432');
                setTxt('mcKpiCdi', fmtPct(cdiV));
                setTxt('mcKpiCdiSrc', ind.cdi ? `${ind.cdi.src || 'BCB'} · ${ind.cdi.date || '--'}` : 'BCB · SGS 4389');
                setTxt('mcKpiIpca12', fmtPct(ipcaV));
                setTxt('mcKpiIpcaSrc', ind.ipca12m ? `${ind.ipca12m.src || 'IBGE'} · ${ind.ipca12m.date || '--'}` : 'IBGE · SGS 13522');
                setTxt('mcKpiReal', fmtPct(realV));

                const td = todayBRT();
                const nextDt = allCopomDatesFlat().map(parseISO).find(d => d >= td);
                if (nextDt) {
                    const du = businessDaysBetween(td, nextDt, true);
                    setTxt('mcKpiNextCopom', `${WEEKDAYS[nextDt.getDay()]} ${toBRShort(nextDt)}`);
                    setTxt('mcKpiNextCopomSub', `${du} dias úteis até a decisão`);
                } else {
                    setTxt('mcKpiNextCopom', 'A definir');
                }
            }

            function renderCopomChart() {
                const container = document.getElementById('mcCopomChart');
                if (!container) return;

                const curYear = todayBRT().getFullYear();
                const yearsAvail = Object.keys(state.copom_meetings || {}).map(Number).filter(Boolean).sort();
                if (!yearsAvail.includes(copomYear)) copomYear = yearsAvail.includes(curYear) ? curYear : (yearsAvail[0] || 2026);

                const meetings = (state.copom_meetings[String(copomYear)] || DEFAULT_COPOM[copomYear] || []);
                const kicker = document.getElementById('mcCopomKicker');
                if (kicker) kicker.textContent = `DECISÕES DO COPOM EM ${copomYear}`;

                const done = meetings.filter(m => m.rate != null && !isNaN(m.rate)).map(m => ({ d: parseISO(m.date), v: Number(m.rate), label: m.label || '' }));
                const pending = meetings.filter(m => m.rate == null || isNaN(m.rate)).map(m => ({ d: parseISO(m.date) }));
                const n = Math.max(1, done.length + pending.length);

                const vals = done.map(p => p.v);
                const minV = vals.length ? Math.floor((Math.min(...vals) - 0.75) * 2) / 2 : 12.5;
                const maxV = vals.length ? Math.ceil((Math.max(...vals) + 0.5) * 2) / 2 : 15.5;
                const span = Math.max(1.0, maxV - minV);

                const W = 640, H = 228, L = 48, R = 14, T = 20, B = 44;
                const x = i => L + (i + 0.5) * (W - L - R) / n;
                const y = v => T + (maxV - v) / span * (H - T - B);
                const light = isLight();
                const mutedColor = light ? '#475569' : '#94a3b8';
                const barBase = light ? '#0f172a' : '#1e3a5f';
                const accentBar = light ? '#0284c7' : '#00d2ff';
                const pendingClr = light ? '#c2410c' : '#ff9100';

                let s = `<svg viewBox="0 0 ${W} ${H}" style="font-family: var(--font-mono);" role="img" aria-label="Trajetória da Selic em ${copomYear}">`;
                const step = span > 3 ? 1.0 : 0.5;
                for (let g = Math.ceil(minV / step) * step; g <= maxV + 0.001; g += step) {
                    const yy = y(g).toFixed(1);
                    s += `<line x1="${L}" x2="${W - R}" y1="${yy}" y2="${yy}" stroke="${mutedColor}" stroke-opacity="0.22" stroke-dasharray="3 3"/>`;
                    s += `<text x="4" y="${Number(yy) + 3}" font-size="9.5" fill="${mutedColor}">${fmtNum(g, 2)}%</text>`;
                }

                const bw = Math.min(44, (W - L - R) / n * 0.56);
                done.forEach((p, i) => {
                    const isLast = (i === done.length - 1);
                    const topY = y(p.v);
                    const hBar = Math.max(2, (H - B) - topY);
                    s += `<rect x="${(x(i) - bw / 2).toFixed(1)}" y="${topY.toFixed(1)}" width="${bw.toFixed(1)}" height="${hBar.toFixed(1)}" rx="4" fill="${isLast ? accentBar : barBase}" opacity="${isLast ? '0.95' : '0.82'}"><title>${toBR(p.d)} · ${esc(p.label || fmtPct(p.v))}</title></rect>`;
                    s += `<text x="${x(i).toFixed(1)}" y="${(topY - 6).toFixed(1)}" font-size="10" font-weight="700" text-anchor="middle" fill="${isLast ? accentBar : mutedColor}">${fmtNum(p.v, 2)}</text>`;
                    s += `<text x="${x(i).toFixed(1)}" y="${H - 25}" font-size="9.5" text-anchor="middle" fill="${mutedColor}">${MONTH_NAMES[p.d.getMonth()]}</text>`;
                });

                pending.forEach((p, j) => {
                    const i = done.length + j;
                    s += `<rect x="${(x(i) - bw / 2).toFixed(1)}" y="${T + 10}" width="${bw.toFixed(1)}" height="${H - B - T - 10}" rx="4" fill="none" stroke="${pendingClr}" stroke-width="1.5" stroke-dasharray="4 3"/>`;
                    s += `<text x="${x(i).toFixed(1)}" y="${((H - B + T) / 2 + 4).toFixed(1)}" font-size="11" text-anchor="middle" fill="${pendingClr}" font-weight="700">?</text>`;
                    s += `<text x="${x(i).toFixed(1)}" y="${H - 25}" font-size="9.5" text-anchor="middle" fill="${pendingClr}">${toBRShort(p.d)}</text>`;
                });

                s += `<text x="${W - R}" y="${H - 5}" font-size="9" text-anchor="end" fill="${mutedColor}">Meta Selic (% a.a.) · BCB SGS 432 · tracejado = próximas reuniões</text></svg>`;
                container.innerHTML = s;

                const descEl = document.getElementById('mcCopomDesc');
                if (descEl) {
                    if (done.length) {
                        const lastM = done[done.length - 1];
                        const firstM = done[0];
                        descEl.innerHTML = `Em <strong>${copomYear}</strong>, o Copom iniciou em <strong>${fmtPct(firstM.v)}</strong> e encontra-se em <strong>${esc(lastM.label || fmtPct(lastM.v))}</strong> (reunião de <strong>${toBR(lastM.d)}</strong>). Cortes na Selic tendem a fechar a ponta curta da curva DI e reduzir a taxa de desconto das ações domésticas na B3.`;
                    } else {
                        descEl.textContent = `Calendário oficial do Copom para ${copomYear}: todas as 8 reuniões ainda estão programadas; os valores serão preenchidos automaticamente após cada comunicado via série SGS 432.`;
                    }
                }
            }

            function renderFocusTable() {
                const tbody = document.getElementById('mcFocusBody');
                if (!tbody) return;
                const y0 = todayBRT().getFullYear();
                const years = [y0, y0 + 1, y0 + 2];
                document.querySelectorAll('[data-mc-focus-y]').forEach(th => {
                    th.textContent = years[+th.dataset.mcFocusY] || '';
                });

                const ROWS = [
                    ['IPCA', 'IPCA (%)', 2],
                    ['Selic', 'Selic fim de ano (%)', 2],
                    ['PIB Total', 'PIB (% cresc.)', 2],
                    ['Câmbio', 'Câmbio (R$/US$)', 2],
                    ['IGP-M', 'IGP-M (%)', 2]
                ];

                tbody.innerHTML = ROWS.map(([k, label, dec]) => {
                    const entry = (state.focus || {})[k];
                    const tds = years.map(yr => {
                        const yrStr = String(yr);
                        const v = entry && entry.byYear ? entry.byYear[yrStr] : null;
                        const p = entry && entry.prevByYear ? entry.prevByYear[yrStr] : null;
                        if (v == null || isNaN(v)) return `<td class="macro-neu">—</td>`;
                        let arrow = '<span class="macro-neu">=</span>';
                        if (p != null && !isNaN(p) && Math.abs(v - p) >= 1e-6) {
                            arrow = v > p ? '<span class="macro-neg" title="Subiu vs semana anterior">▲</span>' : '<span class="macro-pos" title="Caiu vs semana anterior">▼</span>';
                        }
                        return `<td>${fmtNum(v, dec)} ${arrow}</td>`;
                    }).join('');
                    return `<tr><td style="font-weight: 700;">${esc(label)}</td>${tds}</tr>`;
                }).join('');

                const dates = Object.values(state.focus || {}).map(r => r && r.date).filter(Boolean).sort();
                const dateBadge = document.getElementById('mcFocusDate');
                if (dateBadge) {
                    const latest = dates.length ? dates[dates.length - 1] : null;
                    dateBadge.textContent = latest ? `PESQUISA DE ${latest.split('-').reverse().join('/')}` : 'SNAPSHOT BCB';
                }
            }

            function renderDiVertices() {
                const el = document.getElementById('mcDiVertices');
                if (!el) return;
                el.innerHTML = getDiJanuaryVertices(8).map(v => `
                    <div class="macro-di-card">
                        <strong>${esc(v.code)}</strong>
                        <span class="dt">Vence ${toBR(v.expiry)}</span>
                        <span class="du">${v.du.toLocaleString('pt-BR')} DU</span>
                    </div>
                `).join('');
            }

            const bpStr = v => (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(Math.round(v * 100)) + ' bps';
            function interpRealRate(pts, anos) {
                if (!pts || !pts.length) return null;
                if (anos < pts[0].anos) return (pts[0].anos - anos <= 0.6) ? pts[0].taxa : null;
                if (anos > pts[pts.length - 1].anos) return (anos - pts[pts.length - 1].anos <= 0.6) ? pts[pts.length - 1].taxa : null;
                for (let i = 1; i < pts.length; i++) {
                    if (anos <= pts[i].anos) {
                        const p = pts[i - 1], q = pts[i];
                        const denom = q.anos - p.anos;
                        if (Math.abs(denom) < 1e-6) return p.taxa;
                        return p.taxa + (q.taxa - p.taxa) * (anos - p.anos) / denom;
                    }
                }
                return null;
            }
            function calcBreakeven(dateKey) {
                const hist = (state.curva && state.curva.historico) ? state.curva.historico : {};
                const foto = hist[dateKey];
                if (!foto || !(foto.pre || []).length || !(foto.ipca || []).length) return [];
                return foto.pre.map(p => {
                    const real = interpRealRate(foto.ipca, p.anos);
                    if (real == null || (1 + real / 100) <= 0) return null;
                    return { venc: p.venc, anos: p.anos, v: ((1 + p.taxa / 100) / (1 + real / 100) - 1) * 100 };
                }).filter(Boolean);
            }

            function renderCurveSection() {
                const wrap = document.getElementById('mcCurveWrap');
                const chartEl = document.getElementById('mcCurveChart');
                if (!wrap || !chartEl) return;

                const hist = (state.curva && state.curva.historico) ? state.curva.historico : {};
                const datas = Object.keys(hist).filter(d => ((hist[d] && hist[d][curveKind]) || []).length > 0).sort();
                if (!datas.length) {
                    chartEl.innerHTML = `<div style="padding: 30px; text-align: center; color: var(--text-muted); font-size: 13px;">Curva do Tesouro Direto ainda sem histórico suficiente no cache.</div>`;
                    return;
                }

                const dH = datas[datas.length - 1];
                const dA = datas[Math.max(0, datas.length - 1 - curveBack)];
                const H = hist[dH][curveKind] || [];
                const A = (dA !== dH && hist[dA]) ? (hist[dA][curveKind] || []) : [];
                const mapA = Object.fromEntries(A.map(p => [p.venc, p]));
                const pares = H.map(p => ({ ...p, ant: mapA[p.venc] ? mapA[p.venc].taxa : p.taxa }));

                document.querySelectorAll('[data-mc-cc]').forEach(btn => {
                    const ok = datas.length > +btn.dataset.mcCc;
                    btn.disabled = !ok;
                    btn.style.opacity = ok ? '1' : '0.4';
                    btn.style.cursor = ok ? 'pointer' : 'not-allowed';
                });

                const narrow = (chartEl.clientWidth || 640) < 520;
                const W = narrow ? 360 : 640, Hh = narrow ? 250 : 295, L = 44, R = 14, T = 20, B = 34;
                const selicVal = (curveKind === 'pre' && state.indicators && state.indicators.selic) ? Number(state.indicators.selic.value) : null;
                const ys = H.map(p => p.taxa).concat(A.map(p => p.taxa)).concat(selicVal ? [selicVal] : []);
                const minRaw = ys.length ? Math.min(...ys) : 5;
                const maxRaw = ys.length ? Math.max(...ys) : 15;
                const y0 = Math.floor(minRaw * 2) / 2 - 0.25;
                const y1 = Math.max(y0 + 1.0, Math.ceil(maxRaw * 2) / 2 + 0.25);
                const x1 = Math.max(1, Math.ceil(Math.max(...H.map(p => p.anos), ...(A.length ? A.map(p => p.anos) : [1]))));

                const X = a => L + (a / x1) * (W - L - R);
                const Y = v => T + ((y1 - v) / (y1 - y0)) * (Hh - T - B);
                const pathOf = pts => pts.map((p, i) => (i ? 'L' : 'M') + X(p.anos).toFixed(1) + ' ' + Y(p.taxa).toFixed(1)).join(' ');

                const light = isLight();
                const mutedClr = light ? '#64748b' : '#94a3b8';
                const gridClr = light ? 'rgba(15,23,42,0.1)' : 'rgba(255,255,255,0.08)';
                const mainLine = light ? '#0284c7' : '#00d2ff';
                const prevLine = light ? '#94a3b8' : '#64748b';
                const dotText = light ? '#0f172a' : '#f1f5f9';
                const selicClr = light ? '#c2410c' : '#ff9100';

                let grid = '';
                const step = (y1 - y0) > 3 ? 1.0 : 0.5;
                for (let v = Math.ceil(y0 / step) * step; v <= y1 + 0.001; v += step) {
                    grid += `<line x1="${L}" x2="${W - R}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}" stroke="${gridClr}" stroke-width="1"/>`;
                    grid += `<text x="${L - 6}" y="${(Y(v) + 3).toFixed(1)}" text-anchor="end" fill="${mutedClr}" font-size="10">${fmtNum(v, step < 1 ? 1 : 0)}%</text>`;
                }
                for (let a = 0; a <= x1; a += (x1 > 12 ? 5 : 1)) {
                    grid += `<text x="${X(a).toFixed(1)}" y="${Hh - B + 16}" text-anchor="middle" fill="${mutedClr}" font-size="10">${a}a</text>`;
                }

                const lbl = iso => toBRShort(parseISO(iso));
                const dots = H.map(p => {
                    const ant = mapA[p.venc];
                    const d = ant ? p.taxa - ant.taxa : 0;
                    return `<g><circle cx="${X(p.anos).toFixed(1)}" cy="${Y(p.taxa).toFixed(1)}" r="4.5" fill="${mainLine}"><title>${esc(p.titulo)} · ${fmtNum(p.taxa, 2)}% a.a.${ant ? ' · ' + bpStr(d) + ' vs ' + lbl(dA) : ''}</title></circle><text x="${X(p.anos).toFixed(1)}" y="${(Y(p.taxa) - 9).toFixed(1)}" text-anchor="middle" font-size="10" font-weight="700" fill="${dotText}">${fmtNum(p.taxa, 2)}</text></g>`;
                }).join('');

                chartEl.innerHTML = `<svg viewBox="0 0 ${W} ${Hh}" style="font-family: var(--font-mono);" role="img" aria-label="Curva de juros do Tesouro">
                    ${grid}
                    ${selicVal ? `<line x1="${L}" x2="${W - R}" y1="${Y(selicVal).toFixed(1)}" y2="${Y(selicVal).toFixed(1)}" stroke="${selicClr}" stroke-dasharray="4 4" stroke-width="1.5"/><text x="${W - R}" y="${(Y(selicVal) - 5).toFixed(1)}" text-anchor="end" fill="${selicClr}" font-size="10" font-weight="700">Selic ${fmtNum(selicVal, 2)}%</text>` : ''}
                    ${A.length ? `<path d="${pathOf(A)}" fill="none" stroke="${prevLine}" stroke-width="2" stroke-dasharray="5 4"/>` : ''}
                    <path d="${pathOf(H)}" fill="none" stroke="${mainLine}" stroke-width="2.5"/>
                    ${dots}
                    <g font-size="10" transform="translate(${L + 8},${T + 2})">
                        <line x1="0" x2="18" y1="0" y2="0" stroke="${mainLine}" stroke-width="2.5"/>
                        <text x="23" y="3" fill="${dotText}">${lbl(dH)}</text>
                        ${A.length ? `<line x1="72" x2="90" y1="0" y2="0" stroke="${prevLine}" stroke-width="2" stroke-dasharray="5 4"/><text x="95" y="3" fill="${mutedClr}">${lbl(dA)}</text>` : ''}
                    </g>
                </svg>`;

                const media = pares.reduce((acc, p) => acc + (p.taxa - p.ant), 0) / (pares.length || 1);
                const inc = H.length > 1 ? H[H.length - 1].taxa - H[0].taxa : 0;
                const incA = pares.length > 1 ? pares[pares.length - 1].ant - pares[0].ant : 0;
                const clsDelta = v => v > 0.005 ? 'macro-neg' : (v < -0.005 ? 'macro-pos' : 'macro-neu');

                const kpisEl = document.getElementById('mcCurveKpis');
                if (kpisEl) {
                    kpisEl.innerHTML = `
                        <div class="macro-curve-kpi">
                            <span class="lbl">Média</span>
                            <strong class="${clsDelta(media)}">${bpStr(media)}</strong>
                            <small>${media > 0.005 ? 'abriu' : (media < -0.005 ? 'fechou' : 'estável')} vs ${lbl(dA)}</small>
                        </div>
                        <div class="macro-curve-kpi">
                            <span class="lbl">Inclinação</span>
                            <strong>${Math.round(inc * 100)} bps</strong>
                            <small>longo − curto · ${bpStr(inc - incA)}</small>
                        </div>
                    `;
                }

                const barsEl = document.getElementById('mcCurveBars');
                if (barsEl) {
                    const mx = Math.max(0.05, ...pares.map(p => Math.abs(p.taxa - p.ant)));
                    barsEl.innerHTML = pares.map(p => {
                        const d = p.taxa - p.ant;
                        const w = Math.min(50, (Math.abs(d) / mx) * 50);
                        const barStyle = d >= 0 ? `left: 50%; width: ${w}%; background: #ef4444;` : `right: 50%; width: ${w}%; background: #22c55e;`;
                        return `<div class="macro-bar-row">
                            <span style="width: 38px; color: var(--text-muted);">${p.venc.slice(0, 4)}</span>
                            <div class="macro-bar-track">
                                <div style="position: absolute; top: 0; bottom: 0; left: 50%; width: 1px; background: var(--border-strong, #475569);"></div>
                                <div style="position: absolute; top: 0; bottom: 0; ${barStyle}"></div>
                            </div>
                            <span style="width: 58px; text-align: right;" class="${clsDelta(d)}">${bpStr(d)}</span>
                        </div>`;
                    }).join('');
                }

                const titleEl = document.getElementById('mcCurveTitle');
                if (titleEl) {
                    titleEl.textContent = Math.abs(media) < 0.02
                        ? 'Curva praticamente estável no período'
                        : (media > 0 ? `Curva abriu ${bpStr(media)} em média` : `Curva fechou ${bpStr(Math.abs(media)).replace('+', '')} em média`);
                }

                const readEl = document.getElementById('mcCurveRead');
                if (readEl) {
                    const curto = pares[0], longo = pares[pares.length - 1];
                    const dc = curto ? curto.taxa - curto.ant : 0;
                    const dl = longo ? longo.taxa - longo.ant : 0;
                    const forma = Math.abs(dl - dc) < 0.05
                        ? (media > 0.02 ? 'a curva subiu de forma paralela' : media < -0.02 ? 'a curva caiu de forma paralela' : 'a curva permaneceu estável')
                        : (dl > dc
                            ? (media > 0 ? 'os vértices longos subiram mais que os curtos (maior prêmio fiscal/inflação à frente)' : 'os curtos caíram mais que os longos (mercado precifica mais cortes de Selic)')
                            : (media > 0 ? 'os juros curtos subiram mais que os longos (curva achatou com Selic mais alta por mais tempo)' : 'os juros longos caíram mais que os curtos (alívio no prêmio de risco)'));
                    const impacto = curveKind === 'pre'
                        ? (media > 0.02 ? 'Juros maiores tendem a comprimir múltiplos P/L em ações domésticas, varejo e construção.' : media < -0.02 ? 'Juros menores tendem a aliviar o custo de capital e apoiar ações ligadas à economia local.' : '')
                        : 'A curva IPCA+ mostra o juro real livre de inflação paga pelo Tesouro.';
                    readEl.innerHTML = `<strong>Leitura:</strong> desde ${lbl(dA)}, ${forma}. ${impacto}`;
                }

                const srcEl = document.getElementById('mcCurveSrc');
                if (srcEl) {
                    srcEl.textContent = `Fonte: Tesouro Nacional / Tesouro Transparente (taxas oficiais de compra · títulos sem cupom) · Comparando ${lbl(dH)} vs ${lbl(dA)}.`;
                }

                renderBreakeven(dH, dA, lbl);
            }

            function renderBreakeven(dH, dA, lbl) {
                const wrap = document.getElementById('mcBeWrap');
                const barsEl = document.getElementById('mcBeBars');
                if (!wrap || !barsEl) return;

                const H = calcBreakeven(dH);
                const A = Object.fromEntries(calcBreakeven(dA).map(x => [x.venc, x.v]));
                if (!H.length) {
                    wrap.style.display = 'none';
                    return;
                }
                wrap.style.display = 'block';

                const maxB = Math.max(7, Math.ceil(Math.max(...H.map(x => x.v)) + 0.5));
                const pctW = v => Math.max(0, Math.min(100, (v / maxB) * 100));
                const metaClr = isLight() ? '#0f172a' : '#ffffff';

                barsEl.innerHTML = H.map(x => {
                    const prevV = A[x.venc];
                    const diff = prevV != null ? x.v - prevV : null;
                    const hot = x.v > 4.5;
                    const barClr = hot ? '#ef4444' : '#f59e0b';
                    const diffHtml = diff != null
                        ? ` <span class="${diff > 0.005 ? 'macro-neg' : (diff < -0.005 ? 'macro-pos' : 'macro-neu')}">${diff > 0 ? '+' : diff < 0 ? '−' : ''}${Math.abs(Math.round(diff * 100))} bps</span>`
                        : '';
                    return `<div class="macro-be-bar-wrap">
                        <div class="macro-be-bar-head">
                            <span style="color: var(--text-muted);">${x.venc.slice(0, 4)} <small>(${fmtNum(x.anos, 1)}a)</small></span>
                            <span><strong class="${hot ? 'macro-neg' : ''}">${fmtNum(x.v, 2)}% a.a.</strong>${diffHtml}</span>
                        </div>
                        <div class="macro-be-track">
                            <div style="position: absolute; top: 0; bottom: 0; left: ${pctW(1.5)}%; width: ${pctW(4.5) - pctW(1.5)}%; background: rgba(34,197,94,0.22);" title="Intervalo de tolerância da meta (1,5% a 4,5%)"></div>
                            <div style="position: absolute; top: 3px; bottom: 3px; left: 0; width: ${pctW(x.v)}%; background: ${barClr}; border-radius: 3px;"></div>
                            <div style="position: absolute; top: 0; bottom: 0; left: ${pctW(3.0)}%; width: 2px; background: ${metaClr};" title="Centro da meta de inflação: 3,0%"></div>
                            ${prevV != null ? `<div style="position: absolute; top: 0; bottom: 0; left: ${pctW(prevV)}%; width: 2px; background: #94a3b8;" title="${lbl(dA)}: ${fmtNum(prevV, 2)}%"></div>` : ''}
                        </div>
                    </div>`;
                }).join('') + `<div style="display: flex; flex-wrap: wrap; gap: 12px; font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); margin-top: 6px;">
                    <span><strong style="color: var(--text-main);">|</strong> Meta 3,0%</span>
                    <span><span style="display:inline-block;width:10px;height:10px;background:rgba(34,197,94,0.35);vertical-align:middle;border-radius:2px;"></span> Tolerância 1,5%–4,5%</span>
                    <span><strong style="color: #94a3b8;">|</strong> Referência ${lbl(dA)}</span>
                </div>`;

                const fx = (state.focus || {}).IPCA;
                const yrs = (fx && fx.byYear) ? Object.keys(fx.byYear).filter(y => fx.byYear[y] != null).sort().slice(0, 4) : [];
                const beFocusEl = document.getElementById('mcBeFocus');
                if (beFocusEl) {
                    beFocusEl.innerHTML = `<span class="macro-kicker" style="margin-bottom: 6px;">FOCUS · IPCA ESPERADO</span>` +
                        (yrs.length
                            ? `<div style="display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 6px; text-align: center;">${yrs.map(y => `<div><span style="display:block;font-size:10px;color:var(--text-muted);">${y}</span><strong style="font-size:13px;">${fmtNum(fx.byYear[y], 2)}%</strong></div>`).join('')}</div>`
                            : `<span style="color: var(--text-muted);">Aguardando Focus BCB…</span>`);
                }

                const mediaBe = H.reduce((acc, x) => acc + x.v, 0) / H.length;
                const fmed = yrs.length ? yrs.reduce((acc, y) => acc + Number(fx.byYear[y]), 0) / yrs.length : null;
                const beTitleEl = document.getElementById('mcBeTitle');
                if (beTitleEl) beTitleEl.textContent = `Mercado precifica ~${fmtNum(mediaBe, 1)}% de inflação média ao ano`;

                const beReadEl = document.getElementById('mcBeRead');
                if (beReadEl) {
                    const statusStr = mediaBe > 4.5
                        ? 'a inflação implícita está <strong>acima do teto da meta (4,5%)</strong>.'
                        : (mediaBe > 3.5 ? 'a inflação implícita está acima do centro de 3%, dentro do intervalo de tolerância.' : 'a inflação implícita está próxima da meta de 3% (ancoragem favorável).');
                    const focusDiff = fmed != null
                        ? ` O Focus projeta média de ~${fmtNum(fmed, 1)}% ao ano${(mediaBe - fmed > 0.4) ? ' (a diferença extra reflete prêmio de risco exigido na curva).' : ' (mercado alinhado ao consenso).'}`
                        : '';
                    beReadEl.innerHTML = `<strong>Leitura:</strong> ${statusStr}${focusDiff}`;
                }
            }

            const REGIMES = {
                base: {
                    label: 'Base / Neutro',
                    marker: '50%',
                    title: 'Regime neutro: fluxo seletivo, juros domésticos guiam a bolsa.',
                    desc: 'Sem choque global dominante, a B3 responde principalmente a Copom, inflação e agenda fiscal. Setores sensíveis a juros (varejo, construção, small caps) reagem mais ao DI do que ao exterior.',
                    grid: [['IBOV / WIN', 'Lateral / segue DI', 'macro-neu'], ['Dólar / WDO', 'Ancorado no carry', 'macro-neu'], ['DI curto', 'Segue Copom', 'macro-neu'], ['Ouro', 'Estável', 'macro-neu']]
                },
                off: {
                    label: 'Risk-off (Aversão)',
                    marker: '15%',
                    title: 'Aversão a risco: investidores fogem para dólar, Treasuries e ouro.',
                    desc: 'Choques globais (recessão, conflitos, Fed mais duro) fortalecem o DXY. Mercados emergentes sofrem saída de capital: o dólar sobe, o Ibovespa cai e os vértices longos da curva DI abrem.',
                    grid: [['IBOV / WIN', 'Queda ▼', 'macro-neg'], ['Dólar / WDO', 'Alta ▲', 'macro-pos'], ['DI longo', 'Abre ▲', 'macro-neg'], ['Ouro', 'Alta ▲', 'macro-pos']]
                },
                on: {
                    label: 'Risk-on (Apetite)',
                    marker: '85%',
                    title: 'Apetite a risco: capital estrangeiro busca retorno em emergentes.',
                    desc: 'Com juros globais em queda e dólar global fraco, o diferencial de juros atrai fluxo para a B3. A bolsa sobe puxada por bancos e commodities, o real se aprecia e a curva DI fecha.',
                    grid: [['IBOV / WIN', 'Alta ▲', 'macro-pos'], ['Dólar / WDO', 'Queda ▼', 'macro-neg'], ['Curva DI', 'Fecha ▼', 'macro-pos'], ['Commodities', 'Alta ▲', 'macro-pos']]
                }
            };

            function setRegime(key) {
                regimeSelected = REGIMES[key] ? key : 'base';
                const btnsEl = document.getElementById('mcRegimeBtns');
                if (btnsEl) {
                    btnsEl.innerHTML = Object.entries(REGIMES).map(([k, v]) =>
                        `<button type="button" class="period-btn ${k === regimeSelected ? 'active' : ''}" onclick="MacroModule.setRegime('${k}')">${esc(v.label)}</button>`
                    ).join('');
                }
                const r = REGIMES[regimeSelected];
                const marker = document.getElementById('mcRegimeMarker');
                if (marker) marker.style.left = r.marker;
                const titleEl = document.getElementById('mcRegimeTitle');
                if (titleEl) titleEl.textContent = r.title;
                const descEl = document.getElementById('mcRegimeDesc');
                if (descEl) descEl.textContent = r.desc;
                const gridEl = document.getElementById('mcRegimeGrid');
                if (gridEl) {
                    gridEl.innerHTML = r.grid.map(([a, val, cls]) =>
                        `<div class="macro-di-card"><span style="font-size:10px;color:var(--text-muted);text-transform:uppercase;">${esc(a)}</span><strong class="${cls}" style="margin-top:4px;font-size:13.5px;">${esc(val)}</strong></div>`
                    ).join('');
                }
            }

            const TX_ASSETS = [
                ['WIN', 'IBOV / WIN'], ['WDO', 'Dólar'], ['DIc', 'DI curto'],
                ['DIl', 'DI longo'], ['VAR', 'Varejo'], ['BAN', 'Bancos'], ['CMD', 'VALE · PETR']
            ];
            const txNextOf = list => {
                const tISO = toISO(todayBRT());
                const found = (list || []).find(x => x >= tISO);
                return found ? parseISO(found) : null;
            };
            const txFirstWeekday = (wd) => {
                const t = todayBRT();
                for (let k = 0; k < 2; k++) {
                    const d = new Date(t.getFullYear(), t.getMonth() + k, 1);
                    while (d.getDay() !== wd) d.setDate(d.getDate() + 1);
                    if (d >= t) return d;
                }
                return null;
            };
            const txNextIPCA = () => {
                const t = todayBRT();
                let d = new Date(t.getFullYear(), t.getMonth(), 10);
                if (d < t) d = new Date(t.getFullYear(), t.getMonth() + 1, 10);
                return d;
            };

            const TX_SCENARIOS = [
                {
                    icon: '✂️', tag: 'COPOM', title: 'Copom corta mais que o esperado', short: 'Copom mais brando',
                    when: () => ['Próximo Copom', txNextOf(allCopomDatesFlat())],
                    steps: [
                        ['Gatilho', 'Corte maior que o consenso ou sinalização dovish'],
                        ['Juros', 'DI curto fecha forte; CDI futuro recua'],
                        ['Câmbio', 'Diferencial de juros encolhe e pressiona o dólar'],
                        ['Bolsa', 'Custo de capital cai: domésticas e varejo ganham']
                    ],
                    m: { WIN: 1, WDO: 1, DIc: -2, DIl: -1, VAR: 1, BAN: 0, CMD: 0 },
                    watch: ['Reação dos vértices DI1F27/F28 logo após o comunicado (18h30)', 'Se dólar sobe junto por perda de carry ou cai por entrada de fluxo', 'Tom sobre ancoragem de expectativas de inflação'],
                    fail: 'Se o mercado interpretar o corte como precipitado diante de inflação alta, o DI longo abre, o dólar dispara e a bolsa devolve a alta.',
                    tickers: ['IBOV', 'IFNC', 'MGLU3', 'CYRE3', 'ITUB4']
                },
                {
                    icon: '🛑', tag: 'COPOM', title: 'Copom mais duro que o esperado', short: 'Copom mais duro',
                    when: () => ['Próximo Copom', txNextOf(allCopomDatesFlat())],
                    steps: [
                        ['Gatilho', 'Pausa nos cortes, alta da Selic ou comunicado duro'],
                        ['Juros', 'DI curto abre; ponta longa pode achatar por credibilidade'],
                        ['Câmbio', 'Carry mais atrativo fortalece o real (dólar recua)'],
                        ['Bolsa', 'Taxa de desconto sobe: múltiplos P/L sofrem pressão']
                    ],
                    m: { WIN: -1, WDO: -1, DIc: 2, DIl: 0, VAR: -1, BAN: 0, CMD: 0 },
                    watch: ['Inclinação da curva (curto subindo e longo caindo = credibilidade)', 'Desempenho de varejo e construtoras na abertura seguinte', 'Revisões de Selic terminal no Boletim Focus'],
                    fail: 'Se o aperto for visto como insuficiente para conter o fiscal/inflação, o DI longo abre junto e o dólar também sobe.',
                    tickers: ['IBOV', 'IFNC', 'MGLU3', 'LREN3', 'BBAS3']
                },
                {
                    icon: '🔥', tag: 'INFLAÇÃO', title: 'IPCA acima do consenso', short: 'IPCA acima',
                    when: () => ['Próximo IPCA (≈ dia 10)', txNextIPCA()],
                    steps: [
                        ['Gatilho', 'Inflação mensal acima das projeções de mercado'],
                        ['Expectativa', 'Menor espaço para cortes ou maior risco de alta na Selic'],
                        ['Juros', 'DI curto e intermediário abrem às 9h'],
                        ['Bolsa', 'Setores sensíveis a juros perdem tração']
                    ],
                    m: { WIN: -1, WDO: 0, DIc: 1, DIl: 1, VAR: -1, BAN: 0, CMD: 0 },
                    watch: ['Qualidade da surpresa: núcleo e inflação de serviços pesam mais', 'Magnitude da surpresa (> 0,10 p.p. costuma movimentar o pregão)', 'Reação inicial do DI curto antes da abertura da bolsa'],
                    fail: 'Quando a alta decorre de itens voláteis (alimentos in natura, energia) com núcleos comportados, o efeito se dissipa rápido.',
                    tickers: ['IBOV', 'MGLU3', 'CYRE3', 'RADL3']
                },
                {
                    icon: '❄️', tag: 'INFLAÇÃO', title: 'IPCA abaixo do consenso', short: 'IPCA abaixo',
                    when: () => ['Próximo IPCA (≈ dia 10)', txNextIPCA()],
                    steps: [
                        ['Gatilho', 'Inflação mensal abaixo das projeções'],
                        ['Expectativa', 'Abre espaço para alívio monetário'],
                        ['Juros', 'Curva DI fecha em toda a estrutura'],
                        ['Bolsa', 'Varejo, construção e cíclicos domésticos ganham']
                    ],
                    m: { WIN: 1, WDO: 0, DIc: -1, DIl: -1, VAR: 1, BAN: 0, CMD: 0 },
                    watch: ['Desaceleração em serviços subjacentes', 'Se a bolsa acompanha o fechamento do DI ou é travada pelo exterior'],
                    fail: 'Inflação muito baixa decorrente de recessão forte assusta quanto à revisão de lucros corporativos.',
                    tickers: ['IBOV', 'IFNC', 'MGLU3', 'CYRE3', 'WEGE3']
                },
                {
                    icon: '🦅', tag: 'EUA', title: 'Fed duro / payroll forte', short: 'Fed duro',
                    when: () => ['Próximo FOMC', txNextOf(state.fomc_dates), 'Payroll (1ª sexta)', txFirstWeekday(5)],
                    steps: [
                        ['Gatilho', 'Juros dos EUA altos por mais tempo ou emprego forte'],
                        ['Global', 'Treasuries (US10Y) e dólar global (DXY) sobem'],
                        ['Fluxo', 'Redução de alocação estrangeira em emergentes'],
                        ['Brasil', 'Dólar sobe, DI longo abre e Ibovespa recua']
                    ],
                    m: { WIN: -1, WDO: 1, DIc: 0, DIl: 1, VAR: -1, BAN: 0, CMD: -1 },
                    watch: ['US10Y e DXY no minuto da divulgação (9h30 ou 10h30 BRT)', 'S&P 500 futuro e moedas pares (MXN/BRL)'],
                    fail: 'Emprego forte com inflação comportada pode sinalizar pouso suave, impulsionando o S&P 500 e anulando a queda local.',
                    tickers: ['IBOV', 'VALE3', 'PETR4', 'WEGE3']
                },
                {
                    icon: '🕊️', tag: 'EUA', title: 'Fed brando / payroll fraco', short: 'Fed brando',
                    when: () => ['Próximo FOMC', txNextOf(state.fomc_dates), 'Payroll (1ª sexta)', txFirstWeekday(5)],
                    steps: [
                        ['Gatilho', 'Fed sinaliza cortes ou desaceleração controlada nos EUA'],
                        ['Global', 'US10Y e DXY recuam; apetite global a risco cresce'],
                        ['Fluxo', 'Capital externo retorna a emergentes e commodities'],
                        ['Brasil', 'Dólar recua, DI longo fecha e bolsa avança']
                    ],
                    m: { WIN: 1, WDO: -1, DIc: 0, DIl: -1, VAR: 1, BAN: 0, CMD: 1 },
                    watch: ['Enfraquecimento amplo do DXY', 'Fluxo estrangeiro na B3 e avanço de commodities'],
                    fail: 'Payroll fraco demais pode acender temores de recessão global, disparando aversão a risco (risk-off).',
                    tickers: ['IBOV', 'VALE3', 'PETR4', 'ITUB4', 'BBAS3']
                },
                {
                    icon: '⚠️', tag: 'FISCAL', title: 'Risco fiscal no Brasil', short: 'Risco fiscal',
                    when: () => ['Sem data fixa', null],
                    steps: [
                        ['Gatilho', 'Expansão de gastos ou afrouxamento da meta fiscal'],
                        ['Prêmio', 'Investidores exigem maior prêmio de risco país'],
                        ['Juros & Câmbio', 'DI longo abre forte e dólar dispara simultaneamente'],
                        ['Bolsa', 'Estatais, bancos e varejo sofrem compressão de múltiplos']
                    ],
                    m: { WIN: -1, WDO: 2, DIc: 1, DIl: 2, VAR: -1, BAN: -1, CMD: 0 },
                    watch: ['DI longo (DI1F31+) e dólar subindo juntos', 'Resiliência relativa de exportadoras com receita em dólar'],
                    fail: 'Ambiente externo extremamente benigno (dólar global desabando) pode mascarar o ruído fiscal temporariamente.',
                    tickers: ['IBOV', 'IFNC', 'PETR4', 'BBAS3', 'WEGE3']
                },
                {
                    icon: '🏭', tag: 'CHINA', title: 'China anuncia estímulos', short: 'China estimula',
                    when: () => ['Sem data fixa', null],
                    steps: [
                        ['Gatilho', 'Pacote de crédito, infraestrutura ou juros na China'],
                        ['Commodities', 'Minério de ferro, aço e petróleo aceleram alta'],
                        ['Brasil', 'Mineradoras, siderúrgicas e óleo puxam o Ibovespa'],
                        ['Câmbio', 'Saldo comercial mais forte valoriza o real']
                    ],
                    m: { WIN: 1, WDO: -1, DIc: 0, DIl: 0, VAR: 0, BAN: 0, CMD: 2 },
                    watch: ['Cotação do minério em Dalian/Singapura durante a madrugada', 'Participação de VALE3 e siderúrgicas no fluxo comprador'],
                    fail: 'Pacotes abaixo da expectativa sem medidas fiscais concretas costumam devolver a alta já na abertura da B3.',
                    tickers: ['IBOV', 'VALE3', 'GGBR4', 'CSNA3', 'PRIO3']
                }
            ];

            function txArrow(v) {
                if (v === 2) return '<span class="macro-pos">▲▲</span>';
                if (v === 1) return '<span class="macro-pos">▲</span>';
                if (v === -1) return '<span class="macro-neg">▼</span>';
                if (v === -2) return '<span class="macro-neg">▼▼</span>';
                return '<span class="macro-neu">●</span>';
            }

            function renderTxScenario(scrollHead = false) {
                const listEl = document.getElementById('mcTxEvents');
                const headEl = document.getElementById('mcTxHead');
                const flowEl = document.getElementById('mcTxFlow');
                const watchEl = document.getElementById('mcTxWatch');
                const failEl = document.getElementById('mcTxFail');
                const linksEl = document.getElementById('mcTxTickerLinks');
                const theadEl = document.getElementById('mcTxThead');
                const tbodyEl = document.getElementById('mcTxTbody');
                if (!listEl || !headEl || !flowEl) return;

                const e = TX_SCENARIOS[txSelected] || TX_SCENARIOS[0];
                listEl.innerHTML = TX_SCENARIOS.map((x, idx) => `
                    <button type="button" class="macro-tx-btn ${idx === txSelected ? 'active' : ''}" onclick="MacroModule.pickTx(${idx})">
                        <span style="font-size: 18px; flex-shrink: 0;">${x.icon}</span>
                        <span>
                            <span class="tx-tag">${esc(x.tag)}</span>
                            <span class="tx-title">${esc(x.title)}</span>
                        </span>
                    </button>
                `).join('');

                const w = e.when();
                const dateChips = [];
                for (let k = 0; k < w.length; k += 2) {
                    const dt = w[k + 1];
                    dateChips.push(`<span class="macro-src-badge">📅 ${esc(w[k])}${dt ? `: <strong style="color:var(--text-main);">${WEEKDAYS[dt.getDay()]} ${toBRShort(dt)}</strong>` : ''}</span>`);
                }
                headEl.innerHTML = `
                    <div>
                        <span class="macro-kicker orange" style="margin-bottom:2px;">CENÁRIO SELECIONADO</span>
                        <h3 style="margin:0; font-size:17px; color:var(--text-main);">${e.icon} ${esc(e.title)}?</h3>
                    </div>
                    <div style="display:flex; flex-wrap:wrap; gap:6px;">${dateChips.join('')}</div>
                `;

                const stepsHtml = `<div class="macro-flow-steps">${e.steps.map(([stTitle, stDesc], idx) => `
                    <div class="macro-flow-step ${idx === 0 ? 'first' : ''}">
                        <span class="macro-kicker" style="font-size:9.5px;">${idx + 1}. ${esc(stTitle)}</span>
                        <p style="margin: 4px 0 0 0; font-size: 12px; color: var(--text-main); line-height: 1.4;">${esc(stDesc)}</p>
                    </div>
                `).join('')}</div>`;

                const chipsHtml = `<div style="margin-top: 14px;">
                    <span class="macro-kicker" style="margin-bottom: 4px;">📊 IMPACTO TÍPICO NOS ATIVOS</span>
                    <div class="macro-flow-chips">${TX_ASSETS.map(([k, lbl]) => {
                        const v = e.m[k];
                        const cls = v > 0 ? 'up' : (v < 0 ? 'dn' : '');
                        return `<div class="macro-asset-chip ${cls}"><span style="display:block;font-size:10px;color:var(--text-muted);">${esc(lbl)}</span><span style="font-size:14px;">${txArrow(v)}</span></div>`;
                    }).join('')}</div>
                </div>`;

                flowEl.innerHTML = stepsHtml + chipsHtml;
                if (watchEl) watchEl.innerHTML = e.watch.map(wItem => `<li>${esc(wItem)}</li>`).join('');
                if (failEl) failEl.textContent = e.fail;

                if (linksEl) {
                    const available = (e.tickers || []).filter(tk => typeof DATA !== 'undefined' && DATA[tk]);
                    linksEl.innerHTML = available.length
                        ? `<span style="font-size:11px;color:var(--text-muted);font-weight:600;">Ver no Dashboard:</span>` +
                          available.map(tk => `<button type="button" class="macro-ticker-pill" onclick="MacroModule.openTicker('${tk}')">${esc(tk)} ↗</button>`).join('')
                        : '';
                }

                if (theadEl) {
                    theadEl.innerHTML = `<tr><th>Evento</th>${TX_ASSETS.map(a => `<th style="text-align:center;">${esc(a[1])}</th>`).join('')}</tr>`;
                }
                if (tbodyEl) {
                    tbodyEl.innerHTML = TX_SCENARIOS.map((x, idx) => `
                        <tr class="clickable-row ${idx === txSelected ? 'active-row' : ''}" onclick="MacroModule.pickTx(${idx}, true)">
                            <td style="font-family: inherit; font-weight: 600; white-space: nowrap;">${x.icon} ${esc(x.short)}</td>
                            ${TX_ASSETS.map(a => `<td style="text-align: center;">${txArrow(x.m[a[0]])}</td>`).join('')}
                        </tr>
                    `).join('');
                }

                if (scrollHead) headEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }

            async function getJSONWithTimeout(url, ms = 9000) {
                const ctl = new AbortController();
                const timer = setTimeout(() => ctl.abort(), ms);
                try {
                    const resp = await fetch(url, { signal: ctl.signal, cache: 'no-store' });
                    if (!resp.ok) throw new Error('HTTP ' + resp.status);
                    return await resp.json();
                } finally {
                    clearTimeout(timer);
                }
            }

            async function refreshLiveFromBCB() {
                const statusEl = document.getElementById('mcLiveStatusText');
                const CACHE_KEY = 'fundamentalista_macro_live_v1';
                try {
                    const cachedRaw = localStorage.getItem(CACHE_KEY);
                    if (cachedRaw) {
                        const cached = JSON.parse(cachedRaw);
                        if (cached && cached.ts && (Date.now() - cached.ts) < 15 * 60 * 1000) {
                            if (cached.indicators) Object.assign(state.indicators, cached.indicators);
                            if (cached.focus && Object.keys(cached.focus).length) state.focus = cached.focus;
                            if (cached.copom_meetings) state.copom_meetings = cached.copom_meetings;
                            renderAll();
                            if (statusEl) statusEl.textContent = 'Dados Oficiais BCB (cache 15m)';
                            return;
                        }
                    }
                } catch (_) {}

                if (statusEl) statusEl.textContent = 'Sincronizando APIs BCB…';

                const td = todayBRT();
                const endDt = addDays(td, 2);
                const endBR = `${pad2(endDt.getDate())}/${pad2(endDt.getMonth() + 1)}/${endDt.getFullYear()}`;
                let anyOk = false;

                try {
                    const selicRows = await getJSONWithTimeout(
                        `https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados?formato=json&dataInicial=01/01/2026&dataFinal=${endBR}`,
                        9000
                    );
                    if (Array.isArray(selicRows) && selicRows.length) {
                        const map432 = {};
                        const validToday = [];
                        selicRows.forEach(item => {
                            const val = parseFloat(String(item.valor).replace(',', '.'));
                            map432[item.data] = val;
                            const parts = item.data.split('/');
                            const dObj = new Date(+parts[2], +parts[1] - 1, +parts[0]);
                            if (dObj <= td) validToday.push({ d: dObj, v: val });
                        });
                        if (validToday.length) {
                            validToday.sort((a, b) => a.d - b.d);
                            const last = validToday[validToday.length - 1];
                            state.indicators.selic = { value: last.v, date: toBR(last.d), src: 'BCB · SGS 432' };
                        }
                        // Atualiza dinamicamente decisões do Copom passadas
                        Object.keys(state.copom_meetings || {}).forEach(yr => {
                            state.copom_meetings[yr] = (state.copom_meetings[yr] || []).map(m => {
                                const mDt = parseISO(m.date);
                                if (mDt > td) return { date: m.date, rate: null, label: null };
                                const dAfter = toBR(addDays(mDt, 1));
                                const dSame = toBR(mDt);
                                if (map432[dAfter] != null) {
                                    const rAfter = map432[dAfter];
                                    const rBefore = map432[dSame];
                                    let lbl = fmtPct(rAfter);
                                    if (rBefore != null) {
                                        const diff = Math.round((rAfter - rBefore) * 100) / 100;
                                        lbl = Math.abs(diff) < 1e-6
                                            ? `${fmtPct(rAfter)} (manutenção)`
                                            : `${fmtPct(rAfter)} (${diff > 0 ? '+' : '−'}${fmtNum(Math.abs(diff), 2)})`;
                                    }
                                    return { date: m.date, rate: rAfter, label: lbl };
                                }
                                return m;
                            });
                        });
                        anyOk = true;
                    }
                } catch (_) {}

                const sgsJobs = [
                    [4389, 'cdi', false, 'BCB · SGS 4389'],
                    [13522, 'ipca12m', true, 'IBGE via BCB · SGS 13522'],
                    [433, 'ipcaMes', true, 'IBGE via BCB · SGS 433']
                ].map(async ([code, key, monthly, src]) => {
                    const rows = await getJSONWithTimeout(`https://api.bcb.gov.br/dados/serie/bcdata.sgs.${code}/dados/ultimos/1?formato=json`, 8000);
                    if (Array.isArray(rows) && rows[0]) {
                        const val = parseFloat(String(rows[0].valor).replace(',', '.'));
                        const dStr = monthly ? String(rows[0].data).slice(3) : rows[0].data;
                        state.indicators[key] = { value: val, date: dStr, src: src };
                        anyOk = true;
                    }
                });

                const yrsFocus = [td.getFullYear(), td.getFullYear() + 1, td.getFullYear() + 2, td.getFullYear() + 3];
                const focusJobs = ['IPCA', 'Selic', 'PIB Total', 'Câmbio', 'IGP-M'].map(async ind => {
                    const flt = encodeURIComponent(`Indicador eq '${ind}' and baseCalculo eq 0`);
                    const url = `https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais?$top=50&$filter=${flt}&$orderby=Data%20desc&$format=json&$select=Indicador,IndicadorDetalhe,Data,DataReferencia,Mediana`;
                    const j = await getJSONWithTimeout(url, 11000);
                    const rows = (j.value || []).filter(r => !r.IndicadorDetalhe || r.IndicadorDetalhe === 'null');
                    if (rows.length) {
                        const entry = { date: rows[0].Data, byYear: {}, prevByYear: {} };
                        yrsFocus.forEach(y => {
                            const ys = String(y);
                            const sameY = rows.filter(r => String(r.DataReferencia) === ys);
                            if (sameY[0]) entry.byYear[ys] = Number(sameY[0].Mediana);
                            const prev = sameY.find(r => r.Data < (sameY[0] && sameY[0].Data));
                            if (prev) entry.prevByYear[ys] = Number(prev.Mediana);
                        });
                        state.focus[ind] = entry;
                        anyOk = true;
                    }
                });

                await Promise.allSettled([...sgsJobs, ...focusJobs]);

                if (anyOk) {
                    try {
                        localStorage.setItem(CACHE_KEY, JSON.stringify({
                            ts: Date.now(),
                            indicators: state.indicators,
                            copom_meetings: state.copom_meetings,
                            focus: state.focus
                        }));
                    } catch (_) {}
                    if (statusEl) statusEl.textContent = 'BCB Ao Vivo Conectado';
                } else if (statusEl) {
                    statusEl.textContent = 'Snapshot Consolidado (BCB/Tesouro)';
                }
                renderAll();
            }

            function renderAll() {
                renderTopBadgeAndKPIs();
                renderCopomChart();
                renderFocusTable();
                renderDiVertices();
                renderCurveSection();
                setRegime(regimeSelected);
                renderTxScenario(false);
            }

            return {
                initBadgeOnly: function () {
                    renderTopBadgeAndKPIs();
                },
                onOpen: function () {
                    if (!initialized) {
                        initialized = true;
                        renderAll();
                    } else {
                        renderCopomChart();
                        renderCurveSection();
                    }
                    if (!liveLoaded) {
                        liveLoaded = true;
                        refreshLiveFromBCB();
                    }
                },
                onThemeChange: function () {
                    if (initialized) {
                        renderCopomChart();
                        renderCurveSection();
                        renderTxScenario(false);
                    }
                },
                onResize: function () {
                    if (initialized && typeof currentAppTab !== 'undefined' && currentAppTab === 'macro') {
                        renderCurveSection();
                    }
                },
                setCopomYear: function (yr, btn) {
                    copomYear = yr;
                    document.querySelectorAll('#mcCopomYearTabs .period-btn').forEach(b => b.classList.remove('active'));
                    if (btn) btn.classList.add('active');
                    renderCopomChart();
                },
                setCurveKind: function (kind, btn) {
                    curveKind = kind;
                    document.querySelectorAll('[data-mc-ck]').forEach(b => b.classList.remove('active'));
                    if (btn) btn.classList.add('active');
                    renderCurveSection();
                },
                setCurveBack: function (days, btn) {
                    curveBack = days;
                    document.querySelectorAll('[data-mc-cc]').forEach(b => b.classList.remove('active'));
                    if (btn) btn.classList.add('active');
                    renderCurveSection();
                },
                setRegime: setRegime,
                pickTx: function (idx, scrollHead = false) {
                    txSelected = idx;
                    renderTxScenario(scrollHead);
                },
                scrollToSection: function (id) {
                    const el = document.getElementById(id);
                    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                },
                openTicker: function (ticker) {
                    if (typeof DATA !== 'undefined' && DATA[ticker] && typeof openDetailFromHeatmap === 'function') {
                        openDetailFromHeatmap(ticker);
                    }
                }
            };
        })();

        window.addEventListener('DOMContentLoaded', () => {
            if (typeof MacroModule !== 'undefined') MacroModule.initBadgeOnly();
        });

        let macroResizeTimer = null;
        window.addEventListener('resize', () => {
            clearTimeout(macroResizeTimer);
            macroResizeTimer = setTimeout(() => {
                if (typeof MacroModule !== 'undefined') MacroModule.onResize();
            }, 150);
        });

        window.onresize = function() {

            renderCharts();

        };


        /* =====================================================================
           MÓDULO: IfrModule (Entradas > IFR)
           Lógica do Frontend, Integração Firestore e Renderização de Gráficos
           ===================================================================== */
        const IfrModule = (function () {
            'use strict';

            let currentFilter = 'TODOS';
            let currentViewMode = 'comfort'; // 'comfort' ou 'compact'
            let searchQuery = '';
            let chartInstance = null;
            let firestoreDb = null;

            // Dados em memória carregados do cache ou Firestore
            let ifrData = {
                config: {
                    capital_inicial: 50000,
                    caixa_livre: 41750,
                    capital_alocado_atual: 23100,
                    lucro_realizado_acumulado: 14850,
                    total_trades_finalizados: 28,
                    total_gains: 22,
                    total_stops: 6,
                    taxa_acerto_pct: 78.5,
                    quantidade_ativos_posicionados: 5
                },
                ativos: {},
                trades: {},
                evolucao: []
            };

            const LOGO_COLORS = {
                'ITUB4': { bg: '#ec7000', color: '#ffffff', text: 'itau' },
                'PETR4': { bg: '#008542', color: '#ffcc00', text: 'BR' },
                'VALE3': { bg: '#007e7a', color: '#ffffff', text: 'VALE' },
                'WEGE3': { bg: '#005792', color: '#ffffff', text: 'WEG' },
                'BBAS3': { bg: '#ffed00', color: '#003882', text: 'BB' },
                'BBDC4': { bg: '#cc092f', color: '#ffffff', text: 'BBDC' },
                'PRIO3': { bg: '#111319', color: '#00e676', text: 'PRIO' }
            };

            function initData() {
                if (typeof IFR_CACHE_DATA !== 'undefined' && IFR_CACHE_DATA && IFR_CACHE_DATA.config) {
                    ifrData = IFR_CACHE_DATA;
                }
            }

            window.FIREBASE_CONFIG = {
                apiKey: "AIzaSyAHUDyH4qRLfi_M7Lzw7hnwUoW14UL1dqI",
                authDomain: "dashboard-b3-estrategia-448bd.firebaseapp.com",
                projectId: "dashboard-b3-estrategia-448bd",
                storageBucket: "dashboard-b3-estrategia-448bd.firebasestorage.app",
                messagingSenderId: "314996311829",
                appId: "1:314996311829:web:a0890814ec08b94b1f8b1c"
            };

            function initFirebaseClient() {
                try {
                    if (window.FIREBASE_CONFIG && typeof firebase !== 'undefined' && !firebase.apps.length) {
                        firebase.initializeApp(window.FIREBASE_CONFIG);
                        firestoreDb = firebase.firestore();
                        console.log('⚡ Firebase Firestore conectado no cliente web!');

                        // Listeners em tempo real
                        firestoreDb.collection('configuracao_ifr').doc('estado_global').onSnapshot(doc => {
                            if (doc.exists) {
                                ifrData.config = doc.data();
                                renderKPIs();
                            }
                        });

                        firestoreDb.collection('evolucao_patrimonial').orderBy('data', 'asc').onSnapshot(snap => {
                            const evo = [];
                            snap.forEach(d => evo.push(d.data()));
                            if (evo.length > 0) {
                                ifrData.evolucao = evo;
                                renderChart();
                            }
                        });

                        firestoreDb.collection('trades_ifr').onSnapshot(snap => {
                            const trs = {};
                            snap.forEach(d => { trs[d.id] = d.data(); });
                            ifrData.trades = trs;
                            renderTrades();
                        });
                    }
                } catch (e) {
                    console.warn('Aviso Firebase Web:', e.message);
                }
            }

            function formatMoney(val) {
                if (val === null || val === undefined || isNaN(val)) return 'R$ --';
                return 'R$ ' + Number(val).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            }

            function renderKPIs() {
                const cfg = ifrData.config || {};
                const kpiWin = document.getElementById('kpiIfrWinRate');
                const kpiScore = document.getElementById('kpiIfrScoreText');
                const kpiProfit = document.getElementById('kpiIfrTotalProfit');
                const kpiProfitPct = document.getElementById('kpiIfrProfitPct');
                const kpiAlloc = document.getElementById('kpiIfrAllocated');
                const kpiPositions = document.getElementById('kpiIfrPositionsCount');
                const kpiRadar = document.getElementById('kpiIfrRadarCount');
                const badgeCount = document.getElementById('badgeIfrCountText');

                if (kpiWin) kpiWin.innerText = (cfg.taxa_acerto_pct || 78.5).toFixed(1).replace('.', ',') + '%';
                if (kpiScore) kpiScore.innerText = `(${cfg.total_gains || 22} Gains · ${cfg.total_stops || 6} Stops)`;

                const profit = cfg.lucro_realizado_acumulado || 14850;
                const profitSign = profit >= 0 ? '+' : '';
                if (kpiProfit) {
                    kpiProfit.innerText = `${profitSign}${formatMoney(profit)}`;
                    kpiProfit.className = 'ifr-kpi-val ' + (profit >= 0 ? 'pos' : 'neg');
                }

                const profitPct = ((profit / (cfg.capital_inicial || 50000)) * 100).toFixed(1).replace('.', ',');
                if (kpiProfitPct) kpiProfitPct.innerText = `(${profitSign}${profitPct}%)`;

                const alloc = cfg.capital_alocado_atual || 23100;
                if (kpiAlloc) kpiAlloc.innerText = formatMoney(alloc);

                const activeCount = Object.values(ifrData.trades || {}).filter(t => t.status === 'ABERTO').length || cfg.quantidade_ativos_posicionados || 5;
                if (kpiPositions) kpiPositions.innerText = `(${activeCount} ativos em carteira)`;
                if (badgeCount) badgeCount.innerText = `${activeCount} Ativos`;

                // Contar ativos no radar IFR < 30
                const radarCount = Object.values(ifrData.ativos || {}).filter(a => a.ifr_21 && a.ifr_21 < 30).length || 3;
                if (kpiRadar) kpiRadar.innerText = `${radarCount} Ações`;
            }

            function renderChart() {
                const ctx = document.getElementById('chartIfrEvolucao');
                if (!ctx) return;

                const evoList = ifrData.evolucao || [];
                if (evoList.length === 0) return;

                const labels = evoList.map(p => {
                    const parts = p.data.split('-');
                    return parts.length === 3 ? `${parts[2]}/${parts[1]}/${parts[0].slice(2)}` : p.data;
                });
                const dataValues = evoList.map(p => p.patrimonio_total);
                const lastPoint = evoList[evoList.length - 1];

                const currentBadge = document.getElementById('ifrPatrimonioCurrentBadge');
                if (currentBadge && lastPoint) {
                    const varPct = lastPoint.variacao_pct_total || 0;
                    currentBadge.innerText = `Patrimônio: ${formatMoney(lastPoint.patrimonio_total)} (${varPct >= 0 ? '+' : ''}${varPct.toFixed(1)}%)`;
                }

                if (chartInstance) {
                    chartInstance.destroy();
                }

                const isLight = document.body.classList.contains('theme-light');
                // Alto Contraste: Verde Floresta #15803d no modo claro (idêntico à Visão Detalhada)
                const lineColor = isLight ? '#15803d' : '#00e676';
                const gridColor = isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.06)';
                const textColor = isLight ? '#1e293b' : '#8492a6';

                const canvasCtx = ctx.getContext('2d');
                const gradient = canvasCtx.createLinearGradient(0, 0, 0, 260);
                if (isLight) {
                    gradient.addColorStop(0, 'rgba(21, 128, 61, 0.22)');
                    gradient.addColorStop(1, 'rgba(21, 128, 61, 0.00)');
                } else {
                    gradient.addColorStop(0, 'rgba(0, 230, 118, 0.28)');
                    gradient.addColorStop(1, 'rgba(0, 230, 118, 0.00)');
                }

                chartInstance = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Patrimônio Total (R$)',
                            data: dataValues,
                            borderColor: lineColor,
                            borderWidth: 2.5,
                            fill: true,
                            backgroundColor: gradient,
                            tension: 0.25,
                            pointRadius: 3,
                            pointHoverRadius: 6,
                            pointBackgroundColor: lineColor,
                            pointBorderColor: '#ffffff',
                            pointBorderWidth: 1.5
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: {
                            intersect: false,
                            mode: 'index'
                        },
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: isLight ? 'rgba(255, 255, 255, 0.96)' : 'rgba(17, 19, 25, 0.95)',
                                titleColor: isLight ? '#0f172a' : '#f1f5f9',
                                bodyColor: isLight ? '#334155' : '#8492a6',
                                borderColor: isLight ? '#cbd5e1' : '#222634',
                                borderWidth: 1,
                                padding: 12,
                                displayColors: false,
                                callbacks: {
                                    label: function (context) {
                                        const idx = context.dataIndex;
                                        const pt = evoList[idx] || {};
                                        return [
                                            `Patrimônio: ${formatMoney(context.raw)}`,
                                            `Variação: ${pt.variacao_pct_total >= 0 ? '+' : ''}${pt.variacao_pct_total}%`,
                                            `Caixa Livre: ${formatMoney(pt.caixa_livre)}`,
                                            `Capital Alocado: ${formatMoney(pt.capital_alocado)}`
                                        ];
                                    }
                                }
                            }
                        },
                        scales: {
                            x: {
                                grid: { color: gridColor },
                                ticks: { color: textColor, font: { size: 11, family: "'JetBrains Mono', monospace" } }
                            },
                            y: {
                                grid: { color: gridColor },
                                ticks: {
                                    color: textColor,
                                    font: { size: 11, family: "'JetBrains Mono', monospace" },
                                    callback: function (val) {
                                        return 'R$ ' + (val / 1000).toFixed(0) + 'k';
                                    }
                                }
                            }
                        }
                    }
                });
            }

            function renderTrades() {
                const listEl = document.getElementById('ifrTradesList');
                if (!listEl) return;

                const allTrades = Object.values(ifrData.trades || {});
                const ativosMap = ifrData.ativos || {};

                // Filtrar conforme o filtro selecionado
                let filtered = allTrades.filter(t => {
                    if (currentFilter === 'TODOS') return true;
                    if (currentFilter === 'E1') return t.status === 'ABERTO' && t.etapa_atual === 1;
                    if (currentFilter === 'E2') return t.status === 'ABERTO' && t.etapa_atual === 2;
                    if (currentFilter === 'E3') return t.status === 'ABERTO' && t.etapa_atual === 3;
                    if (currentFilter === 'GAIN') return t.status === 'FINALIZADO_GAIN';
                    if (currentFilter === 'STOP') return t.status === 'FINALIZADO_STOP';
                    return true;
                });

                if (searchQuery.trim()) {
                    const q = searchQuery.trim().toUpperCase();
                    filtered = filtered.filter(t => t.ticker.includes(q) || (t.empresa && t.empresa.toUpperCase().includes(q)));
                }

                if (filtered.length === 0) {
                    listEl.innerHTML = `
                        <div style="background:var(--card-bg); border:1px solid var(--border); border-radius:var(--radius); padding:40px; text-align:center; color:var(--text-muted);">
                            <div style="font-size:32px; margin-bottom:10px;">🔍</div>
                            <div style="font-size:16px; font-weight:600; color:var(--text-main);">Nenhuma operação encontrada</div>
                            <div style="font-size:13px; margin-top:4px;">Ajuste os filtros ou aguarde os próximos pregões monitorados.</div>
                        </div>
                    `;
                    return;
                }

                let html = '';
                for (const t of filtered) {
                    const ativo = ativosMap[t.ticker] || {};
                    const logo = LOGO_COLORS[t.ticker] || { bg: '#ffffff', color: '#0f172a', text: t.ticker.slice(0, 4) };

                    const currentPrice = t.preco_fechamento_atual || ativo.ultimo_preco || t.preco_medio_atual;
                    const ifr = ativo.ifr_21 !== undefined ? ativo.ifr_21 : 45.0;
                    const ifrClass = ifr < 30 ? 'alert' : (ifr > 70 ? 'ok' : 'warn');

                    const pnlPct = t.status === 'ABERTO'
                        ? (t.resultado_nao_realizado_pct || 0)
                        : (t.resultado_realizado_pct || 0);
                    const pnlClass = pnlPct >= 0 ? 'pos' : 'neg';
                    const pnlSign = pnlPct >= 0 ? '+' : '';

                    const e1 = (t.entradas && t.entradas[0]) || { preco: currentPrice, data: t.data_abertura || '--' };
                    const e2 = (t.entradas && t.entradas[1]) || null;
                    const e3 = (t.entradas && t.entradas[2]) || null;

                    const pm = t.preco_medio_atual || currentPrice;
                    const stopPrice = t.stop_geral_preco || Number((pm * 0.50).toFixed(2));
                    const alvoDesc = t.alvo_saida_desc || 'IFR > 70';

                    // Formatar data abreviada (DD/MM)
                    function fmtDate(dStr) {
                        if (!dStr || dStr === '--') return '--';
                        const p = dStr.split('-');
                        return p.length === 3 ? `${p[2]}/${p[1]}` : dStr;
                    }

                    if (currentViewMode === 'comfort') {
                        // Modo Conforto
                        const isFinalizado = (t.status === 'FINALIZADO_GAIN' || t.status === 'FINALIZADO_STOP');
                        const isGain = (t.status === 'FINALIZADO_GAIN');
                        const e1Done = true;
                        const e2Done = Boolean(e2 && (t.etapa_atual >= 2));
                        const e3Done = Boolean(e3 && (t.etapa_atual >= 3));

                        const nextE2Price = Number((e1.preco * 0.90).toFixed(2));
                        const nextE3Price = e2 ? Number((e2.preco * 0.90).toFixed(2)) : Number((e1.preco * 0.81).toFixed(2));

                        let statusBadgeHtml = '';
                        if (isFinalizado) {
                            statusBadgeHtml = isGain 
                                ? '<span style="font-size:11px; font-weight:700; padding:2px 8px; border-radius:999px; background:#dcfce7; color:#15803d; border:1px solid #86efac;">ENCERRADO (GAIN) 🎯</span>'
                                : '<span style="font-size:11px; font-weight:700; padding:2px 8px; border-radius:999px; background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5;">ENCERRADO (STOP) 🚨</span>';
                        }

                        // Textos descritivos das etapas
                        let e2SubText = 'Aguardando ' + formatMoney(nextE2Price);
                        if (e2Done && e2) {
                            e2SubText = `${fmtDate(e2.data)} ${formatMoney(e2.preco)}`;
                        } else if (isFinalizado) {
                            e2SubText = 'Não necessária';
                        }

                        let e3SubText = 'Aguardando ' + formatMoney(nextE3Price);
                        if (e3Done && e3) {
                            e3SubText = `${fmtDate(e3.data)} ${formatMoney(e3.preco)}`;
                        } else if (isFinalizado) {
                            e3SubText = 'Não necessária';
                        }

                        // Coluna da Direita adaptada para abertos vs encerrados
                        let col3Html = '';
                        if (isFinalizado) {
                            const resRealizadoRs = t.resultado_realizado_rs !== null && t.resultado_realizado_rs !== undefined
                                ? t.resultado_realizado_rs
                                : (t.valor_mercado_atual - t.capital_total_alocado);
                            const resSign = resRealizadoRs >= 0 ? '+' : '';

                            col3Html = `
                                <div class="ifr-summary-row">
                                    <span>Preço Entrada (PM)</span>
                                    <span>Saída em ${fmtDate(t.data_encerramento)}</span>
                                </div>
                                <div class="ifr-summary-row">
                                    <strong>${formatMoney(pm)}</strong>
                                    <strong style="color:${isGain ? 'var(--accent-green)' : 'var(--accent-red)'};">${formatMoney(t.preco_saida || currentPrice)}</strong>
                                </div>
                                <div class="ifr-summary-row" style="margin-top:6px;">
                                    <span>Motivo Saída:</span>
                                    <span style="font-size:11px; font-weight:600; color:${isGain ? 'var(--accent-green)' : 'var(--accent-red)'};">${t.motivo_encerramento || alvoDesc}</span>
                                </div>
                                <div class="ifr-pnl-val ${pnlClass}">
                                    Resultado: ${resSign}${formatMoney(resRealizadoRs)} (${pnlSign}${pnlPct.toFixed(1).replace('.', ',')}%)
                                </div>
                            `;
                        } else {
                            col3Html = `
                                <div class="ifr-summary-row">
                                    <span>Preço Médio Atual</span>
                                    <span>Stop Geral (-50%)</span>
                                </div>
                                <div class="ifr-summary-row">
                                    <strong>${formatMoney(pm)}</strong>
                                    <strong style="color:var(--accent-red);">${formatMoney(stopPrice)}</strong>
                                </div>
                                <div class="ifr-summary-row" style="margin-top:6px;">
                                    <span>Alvo de Saída:</span>
                                    <span style="font-size:11px; font-weight:600; color:#38bdf8;">${alvoDesc}</span>
                                </div>
                                <div class="ifr-pnl-val ${pnlClass}">
                                    P&amp;L: ${pnlSign}${pnlPct.toFixed(1).replace('.', ',')}%
                                </div>
                            `;
                        }

                        html += `
                        <div class="ifr-trade-card">
                            <!-- Coluna 1: Ativo, Preço, P/L e IFR -->
                            <div class="ifr-asset-col">
                                <div class="ifr-asset-head">
                                    ${getHeaderBrandIconHtml(t.ticker, 36)}
                                    <div>
                                        <div style="display:flex; align-items:center; gap:8px;">
                                            <span class="ifr-ticker-title">${t.ticker}</span>
                                            <span class="ifr-sector-badge">${t.setor || 'Geral'}</span>
                                            ${statusBadgeHtml}
                                        </div>
                                    </div>
                                </div>
                                <div class="ifr-asset-metrics">
                                    <span class="ifr-metric-item">Preço: <strong>${formatMoney(currentPrice)}</strong></span>
                                    <span class="ifr-metric-item">P/L: <strong>${ativo.ultimo_pl ? ativo.ultimo_pl + 'x' : '--'}</strong> vs Méd 2A: <strong>${(ativo.pl_medio_historico_2a || ativo.pl_medio_historico) ? (ativo.pl_medio_historico_2a || ativo.pl_medio_historico) + 'x' : '--'}</strong></span>
                                    <span class="ifr-pill ${ifrClass}">IFR: ${ifr.toFixed(1)}</span>
                                </div>
                            </div>

                            <!-- Coluna 2: Progressão das 3 Entradas (E1, E2, E3) -->
                            <div class="ifr-steps-wrap">
                                <!-- E1 -->
                                <div class="ifr-step-node done">
                                    <div class="ifr-step-badge">✓ E1 R$ 3.300</div>
                                    <div class="ifr-step-sub">${fmtDate(e1.data)} ${formatMoney(e1.preco)}</div>
                                </div>

                                <div class="ifr-step-connector ${e2Done ? 'done' : ''}"></div>

                                <!-- E2 -->
                                <div class="ifr-step-node ${e2Done ? 'done' : 'pending'}">
                                    <div class="ifr-step-badge">${e2Done ? '✓ ' : ''}E2 R$ 3.300</div>
                                    <div class="ifr-step-sub">${e2SubText}</div>
                                </div>

                                <div class="ifr-step-connector ${e3Done ? 'done' : ''}"></div>

                                <!-- E3 -->
                                <div class="ifr-step-node ${e3Done ? 'done' : 'pending'}">
                                    <div class="ifr-step-badge">${e3Done ? '✓ ' : ''}E3 R$ 3.300</div>
                                    <div class="ifr-step-sub">${e3SubText}</div>
                                </div>
                            </div>

                            <!-- Coluna 3: Métricas de Fechamento ou Posição Aberta -->
                            <div class="ifr-summary-col">
                                ${col3Html}
                            </div>
                        </div>
                        `;
                    } else {
                        // Modo Compacto
                        const progressPct = t.etapa_atual === 1 ? 33 : (t.etapa_atual === 2 ? 66 : 100);

                        html += `
                        <div class="ifr-trade-card compact">
                            <div class="ifr-asset-col">
                                <div class="ifr-asset-head">
                                    ${getHeaderBrandIconHtml(t.ticker, 28)}
                                    <span class="ifr-ticker-title" style="font-size:15px;">${t.ticker}</span>
                                    <span class="ifr-sector-badge">${t.setor || 'Geral'}</span>
                                </div>
                                <div class="ifr-asset-metrics">
                                    <span>${formatMoney(currentPrice)}</span>
                                    <span class="ifr-pill ${ifrClass}" style="padding:1px 6px; font-size:10px;">IFR ${ifr.toFixed(1)}</span>
                                </div>
                            </div>

                            <div class="ifr-compact-bar-wrap">
                                <div class="ifr-compact-track">
                                    <div class="ifr-compact-fill" style="width: ${progressPct}%;"></div>
                                </div>
                                <div class="ifr-compact-labels">
                                    <span>E1 (${fmtDate(e1.data)})</span>
                                    <span>${e2 ? 'E2 (' + fmtDate(e2.data) + ')' : 'E2 (-10%)'}</span>
                                    <span>${e3 ? 'E3 (' + fmtDate(e3.data) + ')' : 'E3 (-10%)'}</span>
                                </div>
                            </div>

                            <div class="ifr-summary-col">
                                <div class="ifr-summary-row">
                                    <span>PM: <strong>${formatMoney(pm)}</strong></span>
                                    <span class="ifr-pnl-val ${pnlClass}" style="font-size:15px; margin:0;">
                                        ${pnlSign}${pnlPct.toFixed(1).replace('.', ',')}%
                                    </span>
                                </div>
                            </div>
                        </div>
                        `;
                    }
                }

                listEl.innerHTML = html;
            }

            return {
                init: function () {
                    initData();
                    initFirebaseClient();
                },
                onThemeChange: function () {
                    renderChart();
                    renderTrades();
                },
                onOpen: function () {
                    initData();
                    renderKPIs();
                    renderChart();
                    renderTrades();
                },
                onResize: function () {
                    if (chartInstance) chartInstance.resize();
                },
                setFilter: function (filter, btnEl) {
                    currentFilter = filter;
                    document.querySelectorAll('.ifr-filter-btn').forEach(b => b.classList.remove('active'));
                    if (btnEl) btnEl.classList.add('active');
                    renderTrades();
                },
                setViewMode: function (mode, btnEl) {
                    currentViewMode = mode;
                    document.querySelectorAll('.ifr-view-btn').forEach(b => b.classList.remove('active'));
                    if (btnEl) btnEl.classList.add('active');
                    renderTrades();
                },
                onSearch: function (val) {
                    searchQuery = val || '';
                    renderTrades();
                }
            };
        })();

        // Inicializar IfrModule no carregamento
        document.addEventListener('DOMContentLoaded', () => {
            if (typeof IfrModule !== 'undefined') IfrModule.init();
        });
        
    </script>

</body>

</html>

"""



from datetime import datetime

html_final = template.replace("__DATA_PLACEHOLDER__", raw_data)
html_final = html_final.replace("__EARNINGS_PLACEHOLDER__", json.dumps(earnings_data, ensure_ascii=False))
html_final = html_final.replace("__CORPORATE_EVENTS_PLACEHOLDER__", json.dumps(corporate_events_summary, ensure_ascii=False))
html_final = html_final.replace("__EVENTS_ALL_DATA_PLACEHOLDER__", json.dumps(corporate_events_full, ensure_ascii=False))
html_final = html_final.replace("__MACRO_PLACEHOLDER__", json.dumps(macro_snapshot, ensure_ascii=False))
html_final = html_final.replace("__IFR_PLACEHOLDER__", json.dumps(ifr_cache, ensure_ascii=False))

ibov_val = ibov_info.get("aggregated_pe_all") or ibov_info.get("weighted_pe", 10.16)
html_final = html_final.replace("__IBOV_PE__", f"{float(ibov_val):.2f}")

now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
html_final = html_final.replace("__LAST_UPDATE_DATETIME__", now_str)



with open("dashboard.html", "w", encoding="utf-8") as f:

    f.write(html_final)



print("dashboard.html atualizado com layout 100% responsivo (Mobile, Tablet, Desktop)!")

