# Diretrizes e Arquitetura do Projeto: Preco_Lucro (Dashboard Fundamentalista B3)

Este repositório contém a inteligência e o pipeline de geração do **Dashboard Fundamentalista & Múltiplos Históricos (B3 / CVM)**.

## 📌 Visão Geral do Sistema e Repositórios
1. **Workspace Local Principal:** `c:\Users\Leo\Documents\Antigravity\Preco_Lucro`
   - Onde residem o banco de dados local consolidado (`dashboard_data.json`), scripts de cálculo e o gerador de interface (`generate_dashboard.py`).
2. **Repositório de Atualização Automática (GitHub Actions):** `Leo-Sba/Atualizador` (`c:\Users\Leo\Documents\Antigravity\Atualizador`)
   - Executa diariamente às 19:30 (horário de Brasília) para buscar cotações na B3, demonstrativos na CVM, calcular métricas e alimentar o Supabase.
3. **Deploy Web em Produção (Vercel):** `c:\Users\Leo\Documents\Antigravity\Dashboard_Deploy`
   - URL de Produção: `https://dashboard-ibov-preco-lucro.vercel.app`
   - Qualquer atualização no dashboard deve ser feita em `generate_dashboard.py`, depois copiada para `Dashboard_Deploy/index.html` e feito o deploy via `npx vercel --prod --yes`.

---

## 🏗️ Estrutura de Ativos e Índices
O dashboard suporta ações individuais e 3 índices especiais no topo do seletor:
1. **📊 IBOV (Ibovespa):**
   - Utiliza pontuação real em pontos (`pts`).
   - P/L Agregado Consolidado oficial incluindo empresas com prejuízo (`aggregated_pe_all = 10.16x`, cobertura 99.65%).
   - Gráficos operacionais de P/VP, ROE e Dividend Yield são ocultados dinamicamente para o IBOV.
2. **🏦 IFNC (Índice Financeiro B3):**
   - Cotação oficial em **R$** baseada no ETF **FIND11** (histórico 2017–2026 de R$ 61 a R$ 164).
   - Carteira oficial ponderada com teto de 20% por ativo (redistribuição proporcional iterativa).
3. **🛡️ SEGUROS (Sub-Índice de Seguridade com Pesos Iguais):**
   - Composto por: **BBSE3 (33,33%)**, **CXSE3 (33,33%)** e **PSSA3 (33,33%)**.
   - Cotação Sintética Base 100 iniciando no IPO da CXSE3 (2021).
   - **Comportamento Especial:** Não usa o card de precificação consolidado; exibe **3 cards completos e independentes**, um para cada empresa, com tabela de 6 cenários de valuation, Preço Justo em R$ e botão `Ver Ação ↗`.

---

## 🎨 Design System e Layout (Single Page Application)
- **Modos de Tema:** Minimalista com 2 opções no topo:
  - 🌙 **Modo Escuro (Obsidian):** Fundo escuro slate com acentos neon.
  - ☀️ **Modo Claro (Clean):** Alto contraste, fundo branco e cards limpos.
- **Modos de Exibição:** Compacto, Conforto e Expandido (3 colunas balanceadas para telas ultrawide).
- **Fullscreen Individual:** Botão `⛶` em cada card para expansão em tela cheia.
- **Seletor de Ações (Combobox Inteligente):**
  - Permite digitação livre com busca instantânea por ticker ou razão social.
  - Navegação 100% por teclado: setas `↓` e `↑` para navegar, `Enter` para selecionar e `Esc` para fechar.
  - Quando em branco ou ao focar, lista todos os ativos negociados nos últimos 7 dias.
- **Slider Temporal Duplo (Histórico Sincronizado):**
  - Localizado logo abaixo do gráfico de Preço; sincroniza em tempo real a data de início e fim em todos os gráficos e tabelas.
- **Rodapé:**
  - Bolinha verde pulsante com efeito glow: `🟢 Última atualização: DD/MM/AAAA às HH:MM`.

---

## 🚀 Fluxo de Trabalho e Deploy
O pipeline possui automação ponta a ponta via GitHub Actions e também suporte a deploy manual local:

### 1. Automação Diária em Produção (GitHub Actions - 6 Estágios + Intraday Macro)
- O repositório `Leo-Sba/Atualizador` executa diariamente às 19:30 (horário de Brasília) em 6 estágios sequenciais:
  1. Ingestão de Mercado (limpeza, cotações e proventos/splits)
  2. Motor de Cálculo Fundamentalista (P/L, P/VP, ROE, LPA, VPA e DY)
  3. Consolidação de Índices (IBOV, IFNC) e Calendário
  4. Auto-Cura e Auditoria Contínua
  5. **Macro & Curva de Juros (`fetch_macro_data.py`)** *(fim da fila de dados: BCB SGS/Focus + Curva Tesouro Transparente)*
  6. **Compilação do Dashboard (`export_dashboard_data.py`) & Deploy Automático na Vercel** (`npx vercel --prod`)
- Adicionalmente, [`macro_intraday.yml`](../Atualizador/.github/workflows/macro_intraday.yml) atualiza o módulo **Macro & Juros** em janelas intradiárias (10h23, 13h23, 16h23 e 18h45 BRT) compartilhando a mesma fila de concorrência (`b3-supabase-pipeline`), publicando apenas quando houver alteração de dados.
- Para habilitar o deploy automático pela Vercel no GitHub Actions, basta configurar o secret `VERCEL_TOKEN` nas configurações do repositório `Leo-Sba/Atualizador`.

### 2. Deploy Local Manual (Desenvolvimento ou Ajustes Imediatos)
Sempre que fizer alterações locais no código do dashboard ou quiser forçar uma publicação imediata:
```powershell
cd "c:\Users\Leo\Documents\Antigravity\Preco_Lucro"
# 1. Exportar dados com garantia automática de inclusão dos 3 índices (IBOV, IFNC, SEGUROS):
python export_dashboard_data.py
# 2. Copiar dashboard gerado para a pasta de deploy:
Copy-Item -Path "c:\Users\Leo\Documents\Antigravity\Preco_Lucro\dashboard.html" -Destination "c:\Users\Leo\Documents\Antigravity\Dashboard_Deploy\index.html" -Force
# 3. Fazer o deploy em produção na Vercel:
cd "c:\Users\Leo\Documents\Antigravity\Dashboard_Deploy"
npx vercel --prod --yes
```

> [!IMPORTANT]
> **Regra Mandatória de Índices no Agente:**
> Toda e qualquer exportação de `dashboard_data.json` **DEVE SEMPRE** incluir os 3 índices fundamentais no topo (`IBOV`, `IFNC` e `SEGUROS`). O script `export_dashboard_data.py` é o ponto único da verdade que consolida as ações individuais do Supabase junto com `ibov_daily_consolidated`, `ifnc_daily_consolidated` e a síntese ponderada de `SEGUROS` (BBSE3, CXSE3, PSSA3). Nunca sobrescreva `dashboard_data.json` sem esses 3 índices.

---

## ⚖️ Regra Mandatória: Tratamento de Units e LPA/VPA (P/L e P/VP)
Units (ações com final `11`, ex: `BPAC11`, `KLBN11`, `SANB11`, `TAEE11`, etc.) são certificados de depósito de ações compostos por mais de uma ação ordinária (ON) e/ou preferencial (PN).

1. **Causa Raiz de Distorção:**
   - As demonstrações financeiras da CVM reportam o Lucro Líquido total e a quantidade total de ações (`total_shares = ON + PN`).
   - O LPA básico da empresa (`net_income / total_shares`) representa o lucro por **uma ação simples unitária**, e NÃO pelo pacote da Unit.
   - Para Units, **o LPA e o VPA DEVEM ser multiplicados pelo fator de ações por Unit** (`sec_lpa = base_lpa * unit_ratio`, `sec_vpa = base_vpa * unit_ratio`). Se essa multiplicação for omitida, o P/L de uma Unit fica multiplicado artificialmente pelo fator (ex: BPAC11 ficava ~35x em vez de ~11.8x).
2. **Tabela de Proporções Oficiais de Units B3:**
   - **`BPAC11`**: 3.0 (1 ON + 2 PN)
   - **`KLBN11`**: 5.0 (1 ON + 4 PN)
   - **`SANB11`**: 2.0 (1 ON + 1 PN)
   - **`TAEE11`**: 3.0 (1 ON + 2 PN)
   - **`ALUP11`**: 3.0 (1 ON + 2 PN)
   - **`ENGI11`**: 5.0 (1 ON + 4 PN)
   - **`SAPR11`**: 5.0 (1 ON + 4 PN)
   - **`IGTI11`**: 3.0 (1 ON + 2 PN)
3. **Aplicação Obrigatória nos Scripts:**
   - Tanto `calculate_metrics.py` quanto `adjust_splits.py` (ou qualquer script de métricas) devem conter e aplicar rigorosamente o dicionário `UNIT_SHARES_RATIO` ao calcular LPA, VPA e quantidade efetiva de Units em circulação (`total_shares / unit_ratio`).
   - Nas consultas a `financial_facts`, utilizar sempre `period_start` e `period_end` específicos do fato contábil (`f.period_start`, `f.period_end`), garantindo a soma correta dos últimos 4 trimestres (TTM) sem sobreposições de acumulados.

---

## 🔒 Regras de Segurança e Privacidade
- O código analítico e de interface permanece 100% privado no workspace local e na distribuição estática na Vercel.
- O repositório público `Leo-Sba/Atualizador` contém apenas o orquestrador do GitHub Actions.
- Credenciais do Supabase ficam restritas ao arquivo `.env` e secrets do GitHub Actions.

---

## 🏛️ Regra Mandatória: Gráfico Fiscal & Dívida/PIB (Aba Macro & Juros)
O bloco `#macroSecFiscal` (**Receitas e Despesas do Governo Central vs. Dívida/PIB (%)**, canvas `#chartMacroFiscal`) é parte obrigatória da aba **Macro & Juros**, alimentado por `macro_fiscal_cache.json` (`__MACRO_FISCAL_PLACEHOLDER__`) e sincronizado em tempo real via Firestore (`macro_fiscal/governo_central_historico`).

1. **Escala Dinâmica Obrigatória do Eixo Y Esquerdo (`R$ bilhões – deflacionado`) conforme o Período:**
   - **`5A` (`fiscalYearsRange === 5`):** `min = 45`, `max = 80`, `stepSize = 5` (`45 bi` a `80 bi`).
   - **`10A` (`fiscalYearsRange === 10`):** `min = 40`, `max = 80`, `stepSize = 5` (`40 bi` a `80 bi`).
   - **`20A` (`fiscalYearsRange === 20`) e `MÁX` (`0`):** `min = 20`, `max = 80`, `stepSize = 10` (`20 bi` a `80 bi`).
2. **Eixo Y Direito (`Dívida / PIB (%)`):** Fixo de `0%` a `100%` (`stepSize = 20`).
3. **Preservação em Refactors:** Nunca remover `#macroSecFiscal`, `renderFiscalSection()`, `setFiscalRange()` ou a regra de escala dinâmica do eixo Y esquerdo ao editar `generate_dashboard.py`.

---

## 📒 Regras de Contabilidade IFR, Rotas Limpas e Sincronização de Deploy
1. **Sincronização Obrigatória com `Leo-Sba/Atualizador`:**
   - O `daily_update.yml` (Estágio 6) compila o `dashboard.html` em produção usando o `generate_dashboard.py` de dentro do repositório `Atualizador`. Sempre que editar `generate_dashboard.py` ou os scripts de IFR (`contabil-ifr.js`, `dados-mercado-ifr.js`, `fechamento-contabil.js`, `processar-ifr.js`), copie e faça `git push` para `Atualizador` além de atualizar `Preco_Lucro` e `Dashboard_Deploy\index.html`.
2. **Cache Fiscal no Build:**
   - Garantir que `macro_fiscal_cache.json` esteja no diretório de execução ao rodar `python generate_dashboard.py`, evitando `MACRO_FISCAL_DATA = {}`.
3. **Contabilidade Diária (`Entradas > IFR`):**
   - `NAV = Caixa + Valor de Mercado dos Ativos` validado diariamente (`contabil-ifr.js` + `fechamento-contabil.js`); `processar-ifr.js` deve abortar com erro não-zero antes de gravar se a conciliação falhar.
   - No frontend (`generate_dashboard.py`), `fechamentos_resumo` usa os campos compactos (`ev`, `caixa`, `vm`, `r_acum`, `apt`, `ok`) e `ledger_ifr` usa `valor_caixa` (com saldo progressivo calculado cronologicamente).
4. **Rotas Limpas por Aba:**
   - `switchAppTab` mantém URLs limpas (`/detalhes`, `/heatmap`, `/eventos`, `/macro`, `/ifr`) via `history.pushState`, `resolveTabFromUrl()` e rewrite no `vercel.json`.
5. **Sincronização Obrigatória da Estratégia IFR (`estrategia_ifr_regras.md` ↔ `processar-ifr.js`):**
   - O arquivo `estrategia_ifr_regras.md` é o documento de referência das regras do trade system IFR. Sempre que houver qualquer alteração em `estrategia_ifr_regras.md`, o agente **DEVE** sincronizar o motor em `processar-ifr.js` (e vice-versa: se alterar parâmetros de estratégia em `processar-ifr.js`, atualizar `estrategia_ifr_regras.md`).
6. **UI/UX das Abas, Tema e Overflow Horizontal:**
   - **Botão Único de Tema:** O alternador de modo Claro/Escuro deve ser **sempre um único botão** (toggle `☀️` / `🌙`), nunca dois botões separados.
   - **Abas sem Scrollbar Visível:** As abas principais e sub-abas não devem exibir barra de rolagem horizontal visível; em telas menores, manter `overflow-x: auto` com `scrollbar-width: none` / `::-webkit-scrollbar { display: none; }` e evitar estouro horizontal (`overflow-x`) nas seções do dashboard.
7. **Ícones B3 & Content Security Policy (`vercel.json`):**
   - Os ícones das ações usam `thefintz/icones-b3` (`icones/<TICKER>.png` com fallback para `icones/<RAIZ4>.png`, depois favicon do domínio e monograma).
   - Sempre que adicionar uma nova origem externa (imagens, scripts, mapas ou APIs) no frontend, atualizar também as diretivas `img-src` / `connect-src` do `Content-Security-Policy` em `Dashboard_Deploy\vercel.json`.
8. **Configuração de CI/CD GitHub Actions & Secrets (Rastreador IFR):**
   - **Node.js 24 Nativo:** Os workflows do GitHub Actions (`rastreador-ifr.yml`) devem usar `actions/checkout@v7` e `actions/setup-node@v7` para evitar avisos de depreciação do Node.js 20.
   - **Secrets Obrigatórios em Ambientes de CI (`Fundamentalista` e `Atualizador`):**
     - `FIREBASE_SERVICE_ACCOUNT_KEY`: JSON puro e completo das credenciais do Firebase Admin SDK do projeto `dashboard-b3-estrategia-448bd` (deve ser colado estritamente como JSON iniciando em { e terminando em }, sem aspas externas ou caracteres extras que provoquem `Unexpected non-whitespace character after JSON`), necessário para ler/gravar em `configuracao_ifr`, `ativos_ifr`, `trades_ifr` e `fechamentos_ifr`).
     - `DATABASE_URL`: Connection string PostgreSQL direta para o pooler do Supabase (`postgresql://postgres.[ref]:[senha]@[pooler-host]:5432/postgres`), necessária para `pg-pool` carregar cotações, proventos e eventos societários sem tentar conexão padrão em `localhost:5432`.
   - **Execução do Workflow:** No disparo manual via `workflow_dispatch`, deixar `run_migration` e `force_run` desmarcados por padrão, a menos que haja necessidade explícita de reconstrução do histórico contábil.
9. **Visualização Mobile do Gráfico de Evolução IFR (`#chartIfrEvolucao`):**
   - **Legenda no Mobile (`<= 768px`):** Somente o botão de **Gain** (`data-ev-type="GAIN"`) inicia ativo por padrão. Todos os outros 5 botões de legenda (`COMPRA`, `STOP`, `PROVENTO`, `APORTE`, `EVENTO_SOCIETARIO`) devem iniciar com a classe `inactive` (`visibleEventTypes = false`) para evitar poluição visual e acúmulo de bolas grandes no gráfico em telas compactas.
   - Os raios dos pontos no mobile são reduzidos para `4.5px` (hover `7px`), permitindo ao usuário reativar qualquer evento com um toque na legenda.
