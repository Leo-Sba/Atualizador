/**
 * ============================================================================
 * MIGRAÇÃO CONTÁBIL (execução única)
 * ============================================================================
 * 1. Lê os trades atuais do Firestore.
 * 2. Reprecifica cada ordem pelo FECHAMENTO REAL do pregão (Supabase), pois
 *    vários preços históricos foram digitados manualmente e não existiram no
 *    mercado. Datas que não são pregão vão para o próximo pregão.
 *    Os sinais (ticker, datas, níveis E1/E2/E3, saídas) NÃO são re-simulados.
 * 3. Reconstrói o ledger e todos os fechamentos diários desde 02/01/2026.
 * 4. Sem --gravar: apenas relatório (dry-run). Com --gravar: substitui a curva
 *    sintética antiga (evolucao_patrimonial) pelos fechamentos contábeis.
 *
 * Uso: node migrar-contabilidade.js [--gravar]
 * ============================================================================
 */
'use strict';
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');
const admin = require('firebase-admin');
const C = require('./contabil-ifr');
const F = require('./fechamento-contabil');
const { carregarDadosMercado } = require('./dados-mercado-ifr');

const GRAVAR = process.argv.includes('--gravar');
const USAR_CACHE = process.argv.includes('--cache');
const ATUALIZAR_CACHE = process.argv.includes('--atualizar-cache');

function chaveFirebaseDisponivel() {
  let sa = process.env.FIREBASE_SERVICE_ACCOUNT_KEY;
  if (sa) {
    try { JSON.parse(sa); return true; } catch { if (fs.existsSync(path.resolve(sa))) return true; }
  }
  const local = 'C:/Users/Leo/Downloads/dashboard-b3-estrategia-448bd-firebase-adminsdk-fbsvc-6b53b074cb.json';
  return fs.existsSync(local);
}

function initFirebase() {
  if (admin.apps.length) return admin.firestore();
  let sa = process.env.FIREBASE_SERVICE_ACCOUNT_KEY;
  const local = 'C:/Users/Leo/Downloads/dashboard-b3-estrategia-448bd-firebase-adminsdk-fbsvc-6b53b074cb.json';
  if ((!sa || !fs.existsSync(path.resolve(sa))) && fs.existsSync(local)) sa = local;
  let cred;
  try { cred = JSON.parse(sa); } catch { cred = require(path.resolve(sa)); }
  admin.initializeApp({ credential: admin.credential.cert(cred) });
  return admin.firestore();
}

function novoPool() {
  return new Pool({
    connectionString: process.env.DATABASE_URL, host: process.env.DB_HOST,
    port: Number(process.env.DB_PORT || 5432), database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER, password: process.env.DB_PASSWORD,
    ssl: { rejectUnauthorized: false }, connectionTimeoutMillis: 15000
  });
}

/** Reprecifica as ordens de um trade pelo fechamento real do pregão */
function reprecificarTrade(t, calendario, precos, ultimoPregao) {
  const out = JSON.parse(JSON.stringify(t));
  const log = [];
  const precoEm = (d) => (precos[d] || {})[t.ticker];

  out.entradas = (t.entradas || []).map(e => {
    const d = C.mapearPregao(e.data, calendario);
    const p = precoEm(d);
    if (!p) throw new Error(`Sem cotação de ${t.ticker} em ${d}`);
    const qtd = Math.floor(C.APORTE_POR_ENTRADA / p);
    log.push(`  E${e.nivel} ${e.data}${d !== e.data ? '→' + d : ''}: R$ ${Number(e.preco).toFixed(2)} × ${e.quantidade}  ⇒  R$ ${p.toFixed(2)} × ${qtd}`);
    return { ...e, data: d, data_sinal_original: e.data, preco: C.r2(p), preco_original_manual: e.preco, quantidade: qtd, aporte_real: C.r2(qtd * C.r2(p)) };
  });

  const qtdTotal = out.entradas.reduce((s, e) => s + e.quantidade, 0);
  const custo = C.r2(out.entradas.reduce((s, e) => s + e.aporte_real, 0));
  const pm = C.r6(custo / qtdTotal);
  out.quantidade_total = qtdTotal;
  out.capital_total_alocado = custo;
  out.preco_medio_atual = C.r2(pm);
  out.stop_geral_preco = C.r2(pm * 0.5);
  out.data_abertura = out.entradas[0].data;

  if (t.status !== 'ABERTO' && t.data_encerramento) {
    const d = C.mapearPregao(t.data_encerramento, calendario);
    const p = C.r2(precoEm(d));
    const venda = C.r2(qtdTotal * p);
    const res = C.r2(venda - custo);
    log.push(`  Saída ${t.data_encerramento}${d !== t.data_encerramento ? '→' + d : ''}: R$ ${Number(t.preco_saida).toFixed(2)}  ⇒  R$ ${p.toFixed(2)}  | resultado R$ ${(t.resultado_realizado_rs || 0).toFixed(2)} ⇒ R$ ${res.toFixed(2)}`);
    Object.assign(out, {
      data_encerramento: d, data_encerramento_sinal_original: t.data_encerramento,
      preco_saida: p, preco_saida_original_manual: t.preco_saida, preco_fechamento_atual: p,
      valor_mercado_atual: venda, resultado_realizado_rs: res,
      resultado_realizado_pct: C.r2(res / custo * 100),
      resultado_nao_realizado_rs: 0, resultado_nao_realizado_pct: 0
    });
  } else {
    const p = C.r2(precoEm(ultimoPregao));
    const vm = C.r2(qtdTotal * p);
    Object.assign(out, {
      preco_fechamento_atual: p, valor_mercado_atual: vm,
      resultado_nao_realizado_rs: C.r2(vm - custo),
      resultado_nao_realizado_pct: C.r2((vm / custo - 1) * 100)
    });
    const e3 = out.entradas.find(e => e.nivel === 3);
    if (e3) { out.preco_gatilho_alvo = C.r2(e3.preco * 1.10); out.alvo_saida_desc = `+10% da E3 (R$ ${out.preco_gatilho_alvo.toFixed(2).replace('.', ',')})`; }
  }
  out.reprecificado_em = new Date().toISOString();
  return { trade: out, log };
}

async function apagarColecao(db, nome) {
  const snap = await db.collection(nome).get();
  for (let i = 0; i < snap.docs.length; i += 400) {
    const b = db.batch();
    snap.docs.slice(i, i + 400).forEach(d => b.delete(d.ref));
    await b.commit();
  }
  return snap.size;
}

(async () => {
  const temChave = chaveFirebaseDisponivel();
  if (GRAVAR && !temChave) {
    throw new Error('FIREBASE_SERVICE_ACCOUNT_KEY ausente para --gravar.');
  }
  const lerDoCache = USAR_CACHE || (!GRAVAR && !temChave);
  const db = lerDoCache ? null : initFirebase();
  const pool = novoPool();
  try {
    const tradesOrig = {};
    if (lerDoCache) {
      const cachePath = path.resolve(__dirname, 'entradas_ifr_cache.json');
      const cache = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
      const rawTrades = cache.trades || {};
      if (Array.isArray(rawTrades)) rawTrades.forEach(t => { tradesOrig[t.id] = t; });
      else Object.entries(rawTrades).forEach(([id, t]) => { tradesOrig[id] = { id, ...t }; });
      console.log(`📥 ${Object.keys(tradesOrig).length} trades lidos de entradas_ifr_cache.json (${USAR_CACHE ? '--cache' : 'fallback dry-run sem chave Firebase'})`);
    } else {
      const snap = await db.collection('trades_ifr').get();
      snap.forEach(d => { tradesOrig[d.id] = { id: d.id, ...d.data() }; });
      console.log(`📥 ${Object.keys(tradesOrig).length} trades lidos do Firestore`);
    }

    const dados = await carregarDadosMercado(pool, { tickers: Object.values(tradesOrig).map(t => t.ticker), dataInicio: F.DATA_INICIO });
    const ultimoPregao = dados.calendario[dados.calendario.length - 1];
    console.log(`📅 ${dados.calendario.length} pregões (${dados.calendario[0]} a ${ultimoPregao}) | ${dados.proventos.length} proventos | ${dados.eventos.length} eventos societários`);

    console.log('\n💲 Reprecificação pelo fechamento real do pregão:');
    const trades = {};
    for (const t of Object.values(tradesOrig).sort((a, b) => a.data_abertura.localeCompare(b.data_abertura))) {
      const { trade, log } = reprecificarTrade(t, dados.calendario, dados.precos, ultimoPregao);
      trades[t.id] = trade;
      console.log(`${t.id} (${t.status})`); log.forEach(l => console.log(l));
    }

    const r = C.reprocessarHistorico({ trades: Object.values(trades), calendario: dados.calendario, precos: dados.precos, ibov: dados.ibov, proventos: dados.proventos, eventos: dados.eventos });
    if (r.inconsistencias.length) console.log('\n⚠️ Inconsistências:', r.inconsistencias);

    const falhas = r.fechamentos.filter(f => !f.conciliado);
    const avisos = r.fechamentos.flatMap(f => f.avisos.map(a => `${f.data}: ${a}`));
    const ult = r.fechamentos[r.fechamentos.length - 1];

    console.log('\n================ RELATÓRIO CONTÁBIL ================');
    console.log(`Fechamentos: ${r.fechamentos.length} | Conciliados: ${r.fechamentos.length - falhas.length} | Falhas: ${falhas.length}`);
    falhas.slice(0, 10).forEach(f => console.log(`  ❌ ${f.data}: ` + Object.entries(f.validacoes).filter(([, v]) => !v.ok).map(([k, v]) => `${k} → ${v.detalhe}`).join(' | ')));
    console.log(`Avisos: ${avisos.length}`); avisos.slice(0, 15).forEach(a => console.log('  ⚠️ ' + a));
    console.log(`Lançamentos no ledger: ${r.ledger.length} (` + Object.entries(r.ledger.reduce((m, l) => (m[l.tipo] = (m[l.tipo] || 0) + 1, m), {})).map(([k, v]) => `${k}:${v}`).join(', ') + ')');
    console.log(`\nÚltimo fechamento ${ult.data}:`);
    console.log(JSON.stringify({ patrimonio: ult.patrimonio, caixa: ult.caixa, investido: { ...ult.investido, posicoes: ult.investido.posicoes.map(p => `${p.ticker} ${p.quantidade}@${p.preco_medio.toFixed(2)} → ${p.preco} (${p.nao_realizado_pct.toFixed(1)}%)`) }, resultados: ult.resultados, rentabilidade: ult.rentabilidade, eficiencia: ult.eficiencia }, null, 2));

    if (!GRAVAR) {
      if (ATUALIZAR_CACHE) {
        F.exigirConciliacao(r.fechamentos);
        const cachePath = path.resolve(__dirname, 'entradas_ifr_cache.json');
        const cache = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
        cache.trades = trades;
        cache.config = { ...(cache.config || {}), ...F.estadoGlobalDe(ult) };
        Object.assign(cache, F.blocoCache(r));
        fs.writeFileSync(cachePath, JSON.stringify(cache, null, 2));
        console.log('\n💾 --atualizar-cache: entradas_ifr_cache.json atualizado com fechamentos conciliados (Firestore não alterado).');
      } else {
        console.log('\n🧪 DRY-RUN: nada foi gravado. Use --gravar para aplicar.');
      }
      return;
    }
    F.exigirConciliacao(r.fechamentos);

    console.log('\n💾 Gravando no Firestore...');
    for (const nome of ['fechamentos_ifr', 'ledger_ifr', 'fechamentos_resumo', 'evolucao_patrimonial']) {
      console.log(`  🗑️ ${nome}: ${await apagarColecao(db, nome)} documentos removidos`);
    }
    const bt = db.batch();
    Object.values(trades).forEach(t => bt.set(db.collection('trades_ifr').doc(t.id), t));
    await bt.commit();
    const g = await F.gravarFechamentos(db, { novos: r.fechamentos, novosLancamentos: r.ledger, fechamentos: r.fechamentos, estado: r.estado });
    console.log(`  ✅ ${g.gravados} fechamentos e ${g.lancamentos} lançamentos gravados; trades reprecificados.`);

    const cachePath = path.resolve(__dirname, 'entradas_ifr_cache.json');
    const cache = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
    cache.trades = trades;
    cache.config = { ...(cache.config || {}), ...F.estadoGlobalDe(ult) };
    Object.assign(cache, F.blocoCache(r));
    fs.writeFileSync(cachePath, JSON.stringify(cache, null, 2));
    console.log('  ✅ entradas_ifr_cache.json atualizado.');
  } finally {
    await pool.end();
  }
})().catch(e => { console.error('❌', e.message); process.exit(1); });
