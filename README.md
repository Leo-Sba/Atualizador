# Atualizador Fundamentalista B3 & CVM

Pipeline automatizado via **GitHub Actions** para atualização contínua de dados de mercado da B3 e métricas fundamentalistas no PostgreSQL (Supabase).

---

## ⚡ Rotina Executada

O workflow roda automaticamente de **segunda a sexta-feira às 19:30 (horário de Brasília)** ou manualmente via **Run Workflow**:

1. **`clean_duplicates.py`**: Limpeza e garantia de unicidade dos ativos.
2. **`import_prices.py`**: Importação dos últimos pregões da B3 via Yahoo Finance.
3. **`fetch_ibov_composition.py`**: Composição oficial da carteira teórica do IBOV e cálculo do P/L médio ponderado.
4. **`import_distributions.py`**: Proventos (dividendos e JCP) e eventos societários (splits).
5. **`calculate_metrics.py`**: Recálculo diário de P/L, P/VP, ROE, LPA e VPA.
6. **`calculate_dividend_yield.py`**: Recálculo do Dividend Yield móvel de 12 meses.

---

## 🔐 Configuração dos Secrets no GitHub

Para que o GitHub Actions se conecte ao Supabase, cadastre os seguintes Secrets em:
`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`:

- `DB_HOST`: Host do banco de dados PostgreSQL (Supabase)
- `DB_PORT`: Porta (geralmente `5432`)
- `DB_NAME`: Nome da base (`postgres`)
- `DB_USER`: Usuário (`postgres.xxxx`)
- `DB_PASSWORD`: Senha do banco
