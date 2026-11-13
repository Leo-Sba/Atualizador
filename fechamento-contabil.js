/**
 * ============================================================================
 * FECHAMENTO CONTÁBIL DIÁRIO — Orquestração (Supabase leitura + Firestore)
 * ============================================================================
 * Modo incremental (job diário):
 *   1. Lê todos os fechamentos já gravados e confere a cadeia de hashes.
 *   2. Reprocessa o histórico usando as MESMAS entradas gravadas em cada dia
 *      (preços, IBOV, proventos, eventos) e exige hashes idênticos — qualquer
 *      alteração retroativa em trades ou dados interrompe o job.
 *   3. Fecha somente os pregões novos com dados do Supabase.
 *   4. Só grava se TODAS as validações dos novos fechamentos passarem.
 *
 * Modo reconstrução (migração única): recalcula tudo a partir do Supabase.
 * ============================================================================
 */
'use strict';

const C = require('./contabil-ifr');
const { carregarDadosMercado } = require('./dados-mercado-ifr');

const DATA_INICIO = '2026-01-02';

class ErroContabil extends Error {}

async function lerFechamentosGravados(db) {
  const snap = await db.collection('fechamentos_ifr').get();
  const lista = [];
  snap.forEach(d => lista.push(d.data()));
  lista.sort((a, b) => a.data.localeCompare(b.data));
  return lista;
}

/** Proventos publicados no Supabase para datas-ex já fechadas e ainda não reconhecidos */
function detectarProventosRetroativos({ gravados, proventosSupabase, calendario, dataNova }) {
  const reconhecidos = new Set();
  gravados.forEach(f => {
    const e = f.entradas_utilizadas || {};
    (e.proventos || []).forEach(p => reconhecidos.add(`${f.data}|${p.ticker}|${p.tipo}|${p.valor_por_acao}`));
    (e.proventos_retroativos || []).forEach(p => reconhecidos.add(`${C.mapearPregao(p.data_ex, calendario)}|${p.ticker}|${p.tipo}|${p.valor_por_acao}`));
  });
  const ultimo = gravados.length ? gravados[gravados.length - 1].data : null;
  const retro = [];
  for (const p of proventosSupabase) {
    const d = C.mapearPregao(p.data_ex, calendario);
    if (!d || !ultimo || d > ultimo) continue;
    if (reconhecidos.has(`${d}|${p.ticker}|${p.tipo}|${p.valor_por_acao}`)) continue;
    const idx = gravados.findIndex(f => f.data === d);
    const anterior = idx > 0 ? gravados[idx - 1] : null;
    if (!anterior) continue;
    anterior.investido.posicoes.filter(pos => pos.ticker === p.ticker && pos.quantidade > 0).forEach(pos => {
      retro.push({ ticker: p.ticker, trade_id: pos.trade_id, quantidade: pos.quantidade, valor_por_acao: p.valor_por_acao, tipo: p.tipo, data_ex: d, data: dataNova });
    });
  }
  return retro;
}

/**
 * Calcula (sem gravar) os fechamentos contábeis.
 * @returns {{ fechamentos, ledger, novos, novosLancamentos, estado, gravados }}
 */
async function calcularFechamentos({ db, pool, trades, modo = 'incremental', dataInicio = DATA_INICIO }) {
  const listaTrades = Object.values(trades);
  const tickers = listaTrades.map(t => t.ticker);
  const dados = await carregarDadosMercado(pool, { tickers: tickers.length ? tickers : ['BOVA11'], dataInicio });

  if (modo === 'reconstruir') {
    const r = C.reprocessarHistorico({ trades: listaTrades, calendario: dados.calendario, precos: dados.precos, ibov: dados.ibov, proventos: dados.proventos, eventos: dados.eventos });
    return { ...r, novos: r.fechamentos, novosLancamentos: r.ledger, gravados: [] };
  }

  const gravados = await lerFechamentosGravados(db);
  if (!gravados.length) throw new ErroContabil('Nenhum fechamento gravado. Execute a migração (migrar-contabilidade.js --gravar) primeiro.');
  const problemasCadeia = C.verificarCadeia(gravados);
  if (problemasCadeia.length) throw new ErroContabil('Cadeia de fechamentos adulterada: ' + problemasCadeia.join(' | '));

  const ultimo = gravados[gravados.length - 1].data;
  const diasNovos = dados.calendario.filter(d => d > ultimo);
  const calendario = [...gravados.map(f => f.data), ...diasNovos];

  const entradasPorDia = {};
  gravados.forEach(f => { entradasPorDia[f.data] = f.entradas_utilizadas; });

  const proventosRetroativosPorDia = {};
  if (diasNovos.length) {
    const retro = detectarProventosRetroativos({ gravados, proventosSupabase: dados.proventos, calendario, dataNova: diasNovos[0] });
    if (retro.length) proventosRetroativosPorDia[diasNovos[0]] = retro;
  }

  const r = C.reprocessarHistorico({
    trades: listaTrades, calendario, precos: dados.precos, ibov: dados.ibov,
    proventos: dados.proventos.filter(p => C.mapearPregao(p.data_ex, calendario) > ultimo),
    eventos: dados.eventos.filter(e => C.mapearPregao(e.data, calendario) > ultimo),
    entradasPorDia, proventosRetroativosPorDia
  });

  // Imutabilidade: o passado recalculado precisa ser idêntico ao gravado
  for (let i = 0; i < gravados.length; i++) {
    if (r.fechamentos[i].hash !== gravados[i].hash) {
      throw new ErroContabil(`Divergência no fechamento já gravado de ${gravados[i].data}: algum trade ou lançamento passado foi alterado. Correções devem ser feitas por estorno, nunca reescrevendo o histórico.`);
    }
  }

  const novos = r.fechamentos.slice(gravados.length);
  const novosLancamentos = r.ledger.filter(l => l.data > ultimo);
  return { ...r, novos, novosLancamentos, gravados };
}

function exigirConciliacao(novos) {
  const falhas = novos.filter(f => !f.conciliado);
  if (falhas.length) {
    const det = falhas.slice(0, 5).map(f => `${f.data}: ` + Object.entries(f.validacoes).filter(([, v]) => !v.ok).map(([k, v]) => `${k} (${v.detalhe})`).join('; '));
    throw new ErroContabil(`${falhas.length} fechamento(s) NÃO conciliado(s):\n  ` + det.join('\n  '));
  }
}

async function commitEmLotes(db, ops) {
  for (let i = 0; i < ops.length; i += 400) {
    const batch = db.batch();
    ops.slice(i, i + 400).forEach(fn => fn(batch));
    await batch.commit();
  }
}

/**
 * Grava ledger (create), fechamentos (create), resumo do gráfico e estado global.
 * create() falha se o documento já existir — garantia de imutabilidade.
 */
async function gravarFechamentos(db, { novos, novosLancamentos, fechamentos, estado }) {
  exigirConciliacao(novos);

  // Lançamentos já existentes precisam ter o mesmo hash (idempotência)
  const ledgerOps = [];
  for (const l of novosLancamentos) {
    const ref = db.collection('ledger_ifr').doc(l.id);
    const atual = await ref.get();
    if (atual.exists) {
      if (atual.data().hash !== l.hash) throw new ErroContabil(`Lançamento ${l.id} já existe com conteúdo diferente`);
      continue;
    }
    ledgerOps.push(b => b.create(ref, l));
  }
  await commitEmLotes(db, ledgerOps);
  await commitEmLotes(db, novos.map(f => b => b.create(db.collection('fechamentos_ifr').doc(f.data), f)));

  // Resumo do gráfico por ano (derivado; pode ser regravado)
  const porAno = {};
  fechamentos.forEach(f => (porAno[f.data.slice(0, 4)] = porAno[f.data.slice(0, 4)] || []).push(C.resumoParaGrafico(f)));
  const anosAfetados = [...new Set(novos.map(f => f.data.slice(0, 4)))];
  for (const ano of anosAfetados) {
    await db.collection('fechamentos_resumo').doc(ano).set({ ano, serie: porAno[ano], atualizado_em: new Date().toISOString() });
  }

  const ult = fechamentos[fechamentos.length - 1];
  await db.collection('configuracao_ifr').doc('estado_global').set(estadoGlobalDe(ult), { merge: true });
  return { gravados: novos.length, lancamentos: ledgerOps.length };
}

/** Campos do estado global derivados SEMPRE do último fechamento contábil */
function estadoGlobalDe(f) {
  return {
    capital_inicial: f.patrimonio.nav_inicial,
    caixa_livre: f.caixa.saldo,
    capital_alocado_atual: f.investido.custo_aquisicao,
    valor_mercado_posicoes: f.investido.valor_mercado,
    patrimonio_total: f.patrimonio.nav,
    lucro_realizado_acumulado: f.resultados.realizado_acum,
    lucro_nao_realizado: f.resultados.nao_realizado,
    proventos_acumulados: f.resultados.proventos_acum,
    aportes_acumulados: f.resultados.aportes_acum,
    rentabilidade_acumulada_pct: f.rentabilidade.rent_acum,
    total_trades_encerrados: f.eficiencia.operacoes_encerradas,
    trades_vencedores: f.eficiencia.vencedoras,
    trades_perdedores: f.eficiencia.perdedoras,
    taxa_acerto_pct: f.eficiencia.taxa_acerto,
    quantidade_ativos_posicionados: f.investido.n_posicoes,
    ultimo_fechamento_contabil: f.data,
    ultimo_fechamento_hash: f.hash,
    ultimo_fechamento_conciliado: f.conciliado
  };
}

/** Bloco a ser embutido no entradas_ifr_cache.json (fallback offline do dashboard) */
function blocoCache({ fechamentos, ledger }) {
  const ult = fechamentos[fechamentos.length - 1];
  return {
    fechamentos_resumo: fechamentos.map(C.resumoParaGrafico),
    ultimo_fechamento: ult,
    ledger,
    evolucao: fechamentos.map(f => ({
      data: f.data,
      patrimonio_total: f.patrimonio.nav,
      caixa_livre: f.caixa.saldo,
      valor_mercado_posicoes: f.investido.valor_mercado,
      capital_alocado: f.investido.custo_aquisicao,
      lucro_realizado_acumulado: f.resultados.realizado_acum,
      variacao_pct_total: Number(f.rentabilidade.rent_acum.toFixed(2)),
      quantidade_ativos_posicionados: f.investido.n_posicoes
    }))
  };
}

module.exports = { DATA_INICIO, ErroContabil, calcularFechamentos, gravarFechamentos, exigirConciliacao, estadoGlobalDe, blocoCache, lerFechamentosGravados };
