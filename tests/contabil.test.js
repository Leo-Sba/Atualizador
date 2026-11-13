// Testes do motor contábil (node --test tests/)
'use strict';
const test = require('node:test');
const assert = require('node:assert');
const C = require('../contabil-ifr');

const cal = ['2026-01-02', '2026-01-05', '2026-01-06', '2026-02-02', '2026-02-03'];
const px = (o) => Object.fromEntries(cal.map(d => [d, o[d] || {}]));

function rodar(trades, precos, extras = {}) {
  return C.reprocessarHistorico({ trades, calendario: cal, precos: px(precos), capitalInicial: 10000, aporteMensal: 500, ...extras });
}

function todosConciliados(fs) {
  fs.forEach(f => assert.ok(f.conciliado, `${f.data} não conciliado: ${JSON.stringify(f.validacoes)}`));
}

test('carteira vazia: só caixa e aporte mensal, cota estável', () => {
  const { fechamentos } = rodar([], {});
  todosConciliados(fechamentos);
  const ult = fechamentos.at(-1);
  assert.strictEqual(ult.patrimonio.nav, 10500);
  assert.strictEqual(ult.resultados.aportes_acum, 500);
  assert.strictEqual(ult.rentabilidade.rent_acum, 0, 'aporte não pode gerar rentabilidade');
});

test('compra, marcação a mercado e venda com lucro', () => {
  const trades = [{
    id: 'X_1', ticker: 'XXXX3', status: 'FINALIZADO_GAIN', data_encerramento: '2026-01-06', preco_saida: 12,
    motivo_encerramento: 'GAIN_IFR70', entradas: [{ nivel: 1, data: '2026-01-05', preco: 10, quantidade: 100 }]
  }];
  const { fechamentos } = rodar(trades, {
    '2026-01-05': { XXXX3: 10.5 }, '2026-01-06': { XXXX3: 12 }
  });
  todosConciliados(fechamentos);
  const d5 = fechamentos[1];
  assert.strictEqual(d5.caixa.saldo, 9000);
  assert.strictEqual(d5.investido.valor_mercado, 1050);
  assert.strictEqual(d5.resultados.nao_realizado, 50);
  const d6 = fechamentos[2];
  assert.strictEqual(d6.resultados.realizado_acum, 200);
  assert.strictEqual(d6.resultados.nao_realizado, 0);
  assert.strictEqual(d6.patrimonio.nav, 10200);
  assert.strictEqual(d6.conciliacao.componentes.pnl_nao_realizado, -50);
  assert.strictEqual(d6.conciliacao.componentes.resultado_realizado, 200);
  assert.strictEqual(d6.eficiencia.vencedoras, 1);
  assert.strictEqual(d6.eficiencia.taxa_acerto, 100);
  const ult = fechamentos.at(-1);
  assert.ok(Math.abs(ult.rentabilidade.rent_acum - 2) < 1e-6, 'rentabilidade 2% mesmo após aporte');
});

test('preço médio com E2 e stop com prejuízo', () => {
  const trades = [{
    id: 'Y_1', ticker: 'YYYY3', status: 'FINALIZADO_STOP', data_encerramento: '2026-02-03', preco_saida: 4,
    motivo_encerramento: 'STOP_PERDA_50PCT', entradas: [
      { nivel: 1, data: '2026-01-05', preco: 10, quantidade: 100 },
      { nivel: 2, data: '2026-01-06', preco: 8, quantidade: 100 }
    ]
  }];
  const { fechamentos } = rodar(trades, {
    '2026-01-05': { YYYY3: 10 }, '2026-01-06': { YYYY3: 8 }, '2026-02-02': { YYYY3: 5 }, '2026-02-03': { YYYY3: 4 }
  });
  todosConciliados(fechamentos);
  assert.strictEqual(fechamentos[2].investido.posicoes[0].preco_medio, 9);
  const ult = fechamentos.at(-1);
  assert.strictEqual(ult.resultados.realizado_acum, -1000);
  assert.strictEqual(ult.eficiencia.perdedoras, 1);
  assert.strictEqual(ult.eventos.find(e => e.tipo === 'VENDA').classe, 'STOP');
  assert.ok(ult.rentabilidade.max_drawdown < 0);
});

test('provento usa posição do dia anterior e entra no resultado', () => {
  const trades = [{ id: 'Z_1', ticker: 'ZZZZ3', status: 'ABERTO', entradas: [{ nivel: 1, data: '2026-01-05', preco: 10, quantidade: 100 }] }];
  const { fechamentos } = rodar(trades, { '2026-01-05': { ZZZZ3: 10 }, '2026-01-06': { ZZZZ3: 10 } },
    { proventos: [{ ticker: 'ZZZZ3', data_ex: '2026-01-05', valor_por_acao: 1 }, { ticker: 'ZZZZ3', data_ex: '2026-01-06', valor_por_acao: 0.5 }] });
  todosConciliados(fechamentos);
  assert.strictEqual(fechamentos[1].resultados.proventos_dia, 0, 'comprou na data-ex: sem direito');
  assert.strictEqual(fechamentos[2].resultados.proventos_dia, 50);
  assert.strictEqual(fechamentos[2].caixa.saldo, 9050);
});

test('desdobramento altera quantidade e mantém custo e NAV conciliado', () => {
  const trades = [{ id: 'S_1', ticker: 'SSSS3', status: 'ABERTO', entradas: [{ nivel: 1, data: '2026-01-05', preco: 10, quantidade: 100 }] }];
  const { fechamentos } = rodar(trades, { '2026-01-05': { SSSS3: 10 }, '2026-01-06': { SSSS3: 5 } },
    { eventos: [{ ticker: 'SSSS3', data: '2026-01-06', multiplicador: 2 }] });
  todosConciliados(fechamentos);
  const p = fechamentos[2].investido.posicoes[0];
  assert.strictEqual(p.quantidade, 200);
  assert.strictEqual(p.custo, 1000);
  assert.strictEqual(fechamentos[2].resultados.nao_realizado, 0);
});

test('compra sem caixa e venda sem posição são reprovadas', () => {
  const trades = [{ id: 'W_1', ticker: 'WWWW3', status: 'ABERTO', entradas: [{ nivel: 1, data: '2026-01-05', preco: 200, quantidade: 100 }] }];
  const { fechamentos } = rodar(trades, { '2026-01-05': { WWWW3: 200 } });
  assert.strictEqual(fechamentos[1].conciliado, false);
  assert.strictEqual(fechamentos[1].validacoes.ordens_consistentes.ok, false);
});

test('cadeia de hash detecta adulteração', () => {
  const { fechamentos } = rodar([], {});
  assert.deepStrictEqual(C.verificarCadeia(fechamentos), []);
  const adulterado = JSON.parse(JSON.stringify(fechamentos));
  adulterado[2].patrimonio.nav = 999999;
  assert.ok(C.verificarCadeia(adulterado).length > 0);
});

test('reprocessamento é determinístico (mesmos hashes)', () => {
  const a = rodar([], {}).fechamentos.map(f => f.hash);
  const b = rodar([], {}).fechamentos.map(f => f.hash);
  assert.deepStrictEqual(a, b);
});
