# Atualizador Fundamentalista B3 & CVM

Pipeline automatizado em cascata via **GitHub Actions** para atualização contínua de dados de mercado da B3, métricas fundamentalistas, índices e auditoria contínua no PostgreSQL (Supabase).

---

## ⚡ Arquitetura em Cascata (4 Estágios Sequenciais)

O workflow [`daily_update.yml`](.github/workflows/daily_update.yml) roda de **segunda a sexta-feira às 19:30 (horário de Brasília)** com trava global de concorrência (`concurrency: b3-supabase-pipeline`) e execução encadeada via `needs:`:

1. **Estágio 1 — Ingestão de Mercado (`--stage 1`)**:
   - `clean_duplicates.py`: Limpeza preventiva e garantia de unicidade dos ativos.
   - `import_prices.py`: Download das cotações dos últimos 15 dias da B3 via Yahoo Finance.
   - `import_distributions.py`: Atualização de proventos (dividendos/JCP) e eventos societários (splits).
2. **Estágio 2 — Motor de Cálculo Fundamentalista (`--stage 2`)**:
   - `calculate_metrics.py`: Recálculo diário de P/L, P/VP, ROE, LPA, VPA e aplicação de `UNIT_SHARES_RATIO`.
   - `calculate_dividend_yield.py`: Recálculo do Dividend Yield móvel de 12 meses.
3. **Estágio 3 — Consolidação de Índices e Calendário (`--stage 3`)**:
   - `fetch_ibov_composition.py`: Carteira teórica do IBOV e cálculo do P/L consolidado (utilizando os múltiplos recém-calculados no Estágio 2).
   - `fetch_ifnc_composition.py`: Carteira teórica e métricas do IFNC (`FIND11`).
   - `fetch_earnings_calendar.py`: Atualização do calendário de divulgação de resultados.
4. **Estágio 4 — Auto-Cura e Auditoria Contínua (`--stage 4`)**:
   - `auto_heal_anomalies.py`: Motor de Auto-Cura em 3 camadas (SQL determinístico, recálculo seletivo e fallback externo).
   - `detect_anomalies.py`: Auditoria estatística (Z-score) e contábil com persistência em `audit_anomaly_logs`.

---

## 🔐 Configuração dos Secrets no GitHub

Para que o GitHub Actions se conecte ao Supabase, cadastre os seguintes Secrets em:
`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`:

- `DB_HOST`: Host do banco de dados PostgreSQL (Supabase)
- `DB_PORT`: Porta (geralmente `5432`)
- `DB_NAME`: Nome da base (`postgres`)
- `DB_USER`: Usuário (`postgres.xxxx`)
- `DB_PASSWORD`: Senha do banco
