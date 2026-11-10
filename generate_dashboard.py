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
if os.path.exists("events_data.json"):
    try:
        with open("events_data.json", "r", encoding="utf-8") as f:
            raw_events = json.load(f)
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
    gap: 6px;
    padding: 6px;
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
    gap: 10px;
    padding: 2px 10px 2px 4px;
    user-select: none;
}
.brand-mark {
    width: 30px;
    height: 30px;
    border-radius: 9px;
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
.brand-text strong { font-size: 13.5px; font-weight: 700; letter-spacing: -0.01em; color: var(--text-main); }
.brand-text small { font-size: 10.5px; font-weight: 500; color: var(--text-faint); letter-spacing: 0.04em; }
.app-tab-divider { width: 1px; height: 22px; background: var(--border); margin: 0 4px; }
.app-tab-btn {
    padding: 8px 14px;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-muted);
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
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
    font-size: 10.5px;
    font-weight: 600;
    padding: 1px 7px;
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

                <h1><span id="headerTitleText">ITUB4 - ITAUUNIBANCO</span> <span class="badge">B3 & CVM</span></h1>

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

    <script>

        const DATA = __DATA_PLACEHOLDER__;
        const EARNINGS_CALENDAR = __EARNINGS_PLACEHOLDER__;
        const CORPORATE_EVENTS_MAP = __CORPORATE_EVENTS_PLACEHOLDER__;

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

        function updateHeaderSubtitle(ticker) {
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

        async function loadEventsForTicker(ticker) {
            if (!ticker || ['IBOV', 'IFNC', 'SEGUROS'].includes(ticker)) return;

            const contentDivs = document.getElementById('tabContentDividends');
            const contentSplits = document.getElementById('tabContentSplits');
            const badgeCount = document.getElementById('badgeEventsCount');

            if (eventsCache[ticker]) {
                renderEventsTable(ticker, eventsCache[ticker]);
                return;
            }

            if (contentDivs) contentDivs.innerHTML = '<div style="text-align:center; padding:18px; color:var(--text-muted); font-size:12px;">⏳ Carregando histórico da B3 para ' + ticker + '...</div>';
            if (contentSplits) contentSplits.innerHTML = '<div style="text-align:center; padding:18px; color:var(--text-muted); font-size:12px;">⏳ Carregando eventos societários da B3...</div>';

            let data = null;
            // 1. Tenta carregar individual
            try {
                const resp = await fetch('events/' + ticker + '.json');
                if (resp.ok) {
                    data = await resp.json();
                }
            } catch(e) {}

            // 2. Fallback: tentar consolidado
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
                const errMsg = '<div style="text-align:center; padding:18px; color:var(--text-muted); font-size:12px;">⚠️ Dados detalhados da B3 disponíveis online via Vercel ou servidor HTTP local.</div>';
                if (contentDivs) contentDivs.innerHTML = errMsg;
                if (contentSplits) contentSplits.innerHTML = errMsg;
            }
        }

        function renderEventsTable(ticker, data) {
            const contentDivs = document.getElementById('tabContentDividends');
            const contentSplits = document.getElementById('tabContentSplits');
            const countDivsEl = document.getElementById('countTabDivs');
            const countSplitsEl = document.getElementById('countTabSplits');
            const badgeCount = document.getElementById('badgeEventsCount');

            const divs = (data && data.dividends) ? data.dividends : [];
            const splits = (data && data.splits) ? data.splits : [];
            const inplits = (data && data.inplits) ? data.inplits : [];
            const bonuses = (data && data.bonuses) ? data.bonuses : [];
            const allCorporateActions = [...splits, ...inplits, ...bonuses];

            if (countDivsEl) countDivsEl.textContent = divs.length;
            if (countSplitsEl) countSplitsEl.textContent = allCorporateActions.length;

            if (badgeCount) {
                badgeCount.style.display = 'inline-block';
                badgeCount.textContent = `${divs.length} proventos • ${allCorporateActions.length} eventos`;
            }

            // Renderizar Proventos
            if (contentDivs) {
                if (divs.length === 0) {
                    contentDivs.innerHTML = '<div style="text-align:center; padding:16px; color:var(--text-muted); font-size:12px;">Nenhum provento em dinheiro recente registrado na B3 para ' + ticker + '.</div>';
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
                if (allCorporateActions.length === 0) {
                    contentSplits.innerHTML = '<div style="text-align:center; padding:16px; color:var(--text-muted); font-size:12px;">Nenhum evento de split, inplit ou bonificação registrado para ' + ticker + '.</div>';
                } else {
                    let html = '<table class="events-table"><thead><tr>';
                    html += '<th style="width: 170px;">Evento Societário</th>';
                    html += '<th style="text-align: center; width: 130px;">Proporção / Fator</th>';
                    html += '<th>Efeito Prático</th>';
                    html += '<th style="text-align: center; width: 110px;">Data-Com</th>';
                    html += '<th style="text-align: center; width: 110px;">Data Aprovação</th>';
                    html += '</tr></thead><tbody>';

                    allCorporateActions.forEach(ev => {
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
            const secDetail = document.getElementById('tabDetailContent');
            const secHeatmap = document.getElementById('tabHeatmapContent');
            const secEvents = document.getElementById('tabEventsContent');

            if (btnDetail) btnDetail.classList.remove('active');
            if (btnHeatmap) btnHeatmap.classList.remove('active');
            if (btnEvents) btnEvents.classList.remove('active');
            if (secDetail) secDetail.style.display = 'none';
            if (secHeatmap) secHeatmap.style.display = 'none';
            if (secEvents) secEvents.style.display = 'none';

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

        window.onresize = function() {

            renderCharts();

        };

    </script>

</body>

</html>

"""



from datetime import datetime

html_final = template.replace("__DATA_PLACEHOLDER__", raw_data)
html_final = html_final.replace("__EARNINGS_PLACEHOLDER__", json.dumps(earnings_data, ensure_ascii=False))
html_final = html_final.replace("__CORPORATE_EVENTS_PLACEHOLDER__", json.dumps(corporate_events_summary, ensure_ascii=False))

ibov_val = ibov_info.get("aggregated_pe_all") or ibov_info.get("weighted_pe", 10.16)
html_final = html_final.replace("__IBOV_PE__", f"{float(ibov_val):.2f}")

now_str = datetime.now().strftime("%d/%m/%Y às %H:%M")
html_final = html_final.replace("__LAST_UPDATE_DATETIME__", now_str)



with open("dashboard.html", "w", encoding="utf-8") as f:

    f.write(html_final)



print("dashboard.html atualizado com layout 100% responsivo (Mobile, Tablet, Desktop)!")

