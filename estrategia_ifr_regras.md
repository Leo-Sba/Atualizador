# Regras da Estratégia IFR — Bloco de Notas Editável

> **Origem atual no código:** `processar-ifr.js`
> Edite os valores e regras abaixo livremente. Quando quiser aplicar as alterações ao motor de simulação/produção, basta abrir um novo chat e pedir para sincronizar este arquivo com o `processar-ifr.js`.

---

## 1. Capital, Aportes e Custos
- **Capital Inicial:** `R$ 50.000,00`
- **Aporte Mensal:** `R$ 500,00`
- **Valor Fixo por Entrada (E1, E2, E3):** `R$ 3.300,00`
- **Lote / Quantidade:** Compra fracionada — `Math.floor(3300 / close)`
- **Liquidação:** `D+0`
- **Taxas / Corretagem:** Sem taxas (`0`)
- **Trava de Caixa:** Só executa E1, E2 ou E3 se `caixa >= R$ 3.300,00`

---

## 2. Indicadores Utilizados
- **IFR (RSI):** Wilder `IFR(21)`
- **P/L Médio 2 Anos:** Média dos valores válidos onde `price_earnings > 0 && price_earnings < 150`

---

## 3. Ordem de Prioridade Diária (State Machine)
Para cada ativo/dia, o motor avalia nesta ordem exata:

### Prioridade 1 — Stop Loss
- **Condição:** `currentClose <= Number((pm * 0.50).toFixed(2))` (queda de 50% sobre o preço médio `pm`)
- **Motivo registrado:** `STOP_PERDA_50PCT`

### Prioridade 2 — Saída no Lucro (Gain)
- **Se estiver na Etapa 1 (E1):** `ifr > 70.0` → `GAIN_IFR70`
- **Se estiver na Etapa 2 (E2):** `ifr >= 50.0 && currentClose > pm` → `GAIN_IFR50_PM`
- **Se estiver na Etapa 3 (E3):** `currentClose >= Number((e3.preco * 1.10).toFixed(2))` (+10% sobre o preço da E3) → `GAIN_E3_10PCT`

### Prioridade 3 — Preço Médio (E2 e E3)
- **Entrada 2 (E2):** `etapa_atual === 1 && currentClose <= Number((e1.preco * 0.90).toFixed(2))` (queda de 10% sobre E1, com trava `caixa >= 3300`)
- **Entrada 3 (E3):** `etapa_atual === 2 && currentClose <= Number((e2.preco * 0.90).toFixed(2))` (queda de 10% sobre E2, com trava `caixa >= 3300`)

### Prioridade 4 — Nova Entrada 1 (E1)
- **Condição:** Sem trade ativo no ticker, `caixa >= 3300`, `ifr < 30.0`, `currentPe > 0`, `pl2a > 0` e `currentPe < pl2a`
- **Filtro Anti-Grupamento (Inplit):** Bloqueio estrito de compra se a ação sofreu inplit ou grupamento (`REVERSE_SPLIT` ou `share_multiplier < 1.0`) nos últimos 2 anos.

---

## 4. Filtros de Carteira e Restrições de Compra
- **Filtro Anti-Grupamento / Inplit (Últimos 2 Anos):** Ações que sofreram inplit ou grupamento de ações (`REVERSE_SPLIT` ou fator multiplicador `< 1.0`) em qualquer momento dentro da janela móvel dos últimos 2 anos estão **terminantemente proibidas de entrar na seleção de compra (E1)**.
- **Máximo de Ativos Simultâneos:** `<!-- ex: 10 ativos -->`
- **Máximo de Ativos por Setor:** `<!-- ex: 2 ativos por setor -->`
- **Critério de Desempate (se houver mais sinais que vagas):** `<!-- ex: menor IFR(21) primeiro -->`
