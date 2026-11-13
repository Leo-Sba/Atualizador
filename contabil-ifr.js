/**
 * ============================================================================
 * MOTOR CONTÁBIL — Carteira "Entradas > IFR"
 * ============================================================================
 * Módulo de funções puras (sem I/O) responsável por:
 *   1. Gerar o livro-razão (ledger) imutável a partir dos trades, aportes,
 *      proventos e eventos societários.
 *   2. Reprocessar o histórico pregão a pregão e produzir um FECHAMENTO
 *      CONTÁBIL DIÁRIO completo (patrimônio, caixa, investido, resultados,
 *      rentabilidade por cotas, eficiência e auditoria).
 *   3. Validar automaticamente cada fechamento:
 *        NAV = Caixa + Valor de Mercado
 *        ΔNAV = ΔPnL não realizado + Realizado + Proventos − Custos − Impostos
 *               + Aportes − Retiradas + Eventos societários   (resíduo < R$ 0,01)
 *      Além de reconstruir caixa e quantidades diretamente do ledger
 *      (verificação independente do estado incremental).
 *   4. Encadear os fechamentos por hash SHA-256 (histórico imutável).
 *
 * Premissas definidas pelo usuário (13/11/2026):
 *   - Sem taxas, corretagem ou impostos.
 *   - Liquidação imediata (D+0): vendas e proventos entram no caixa no dia.
 *   - Aporte de R$ 500,00 no primeiro pregão de cada mês (após o mês inicial).
 *   - Compra fracionária: quantidade = floor(3300 / preço).
 *   - Proventos: direito de quem detinha a ação no fechamento anterior à data-ex;
 *     como a base não informa data de pagamento, o crédito ocorre na data-ex.
 * ============================================================================
 */
'use strict';

const crypto = require('crypto');

const CAPITAL_INICIAL = 50000;
const APORTE_MENSAL = 500;
const APORTE_POR_ENTRADA = 3300;
const TOLERANCIA = 0.01;

// Ordem de processamento dos lançamentos dentro de um mesmo pregão
const ORDEM_TIPO = {
  APORTE_INICIAL: 0, APORTE: 1, RETIRADA: 2, EVENTO_SOCIETARIO: 3,
  PROVENTO: 4, VENDA: 5, COMPRA: 6, ESTORNO: 7
};

// ---------------------------------------------------------------------------
// Utilitários
// ---------------------------------------------------------------------------
const r2 = v => Math.round((Number(v) + Number.EPSILON) * 100) / 100;
const r6 = v => Math.round((Number(v) + Number.EPSILON) * 1e6) / 1e6;
const r8 = v => Math.round((Number(v) + Number.EPSILON) * 1e8) / 1e8;
const pct = (a, b) => (b ? r6((a / b - 1) * 100) : 0);

/** JSON canônico (chaves ordenadas) para hashing determinístico */
function canonico(obj) {
  if (obj === null || typeof obj !== 'object') return JSON.stringify(obj);
  if (Array.isArray(obj)) return '[' + obj.map(canonico).join(',') + ']';
  return '{' + Object.keys(obj).sort()
    .filter(k => obj[k] !== undefined)
    .map(k => JSON.stringify(k) + ':' + canonico(obj[k])).join(',') + '}';
}

function sha256(obj) {
  return crypto.createHash('sha256').update(canonico(obj)).digest('hex');
}

function semHash(obj) {
  const { hash, ...resto } = obj;
  return resto;
}

/** Primeiro pregão do calendário >= data informada */
function mapearPregao(data, calendario) {
  if (!data) return null;
  for (const d of calendario) if (d >= data) return d;
  return null;
}

// ---------------------------------------------------------------------------
// 1. Lançamentos-base (aportes + ordens dos trades)
// ---------------------------------------------------------------------------
function criarLancamento(campos) {
  const l = {
    id: campos.id,
    data: campos.data,
    tipo: campos.tipo,
    ticker: campos.ticker || null,
    trade_id: campos.trade_id || null,
    nivel: campos.nivel || null,
    quantidade: campos.quantidade || 0,
    preco: campos.preco || 0,
    valor_caixa: r2(campos.valor_caixa || 0),
    descricao: campos.descricao || '',
    data_original: campos.data_original || campos.data,
    motivo: campos.motivo || null
  };
  l.hash = sha256(l);
  return l;
}

/**
 * Gera os lançamentos que não dependem do estado da carteira:
 * aporte inicial, aportes mensais e ordens de compra/venda dos trades.
 * Datas que não são pregão são deslocadas para o próximo pregão.
 */
function gerarLancamentosBase({ trades, calendario, capitalInicial = CAPITAL_INICIAL, aporteMensal = APORTE_MENSAL }) {
  const lancs = [];
  const inconsistencias = [];
  if (!calendario.length) return { lancamentos: lancs, inconsistencias };

  const inicio = calendario[0];
  lancs.push(criarLancamento({
    id: `${inicio}_APORTE_INICIAL`, data: inicio, tipo: 'APORTE_INICIAL',
    valor_caixa: capitalInicial, descricao: 'Capital inicial da carteira'
  }));

  // Aporte mensal: primeiro pregão de cada mês posterior ao mês inicial
  let mesAnterior = inicio.slice(0, 7);
  for (const d of calendario) {
    const mes = d.slice(0, 7);
    if (mes !== mesAnterior) {
      mesAnterior = mes;
      if (aporteMensal > 0) {
        lancs.push(criarLancamento({
          id: `${d}_APORTE`, data: d, tipo: 'APORTE', valor_caixa: aporteMensal,
          descricao: `Aporte mensal ${mes}`
        }));
      }
    }
  }

  for (const t of trades) {
    (t.entradas || []).forEach(e => {
      const d = mapearPregao(e.data, calendario);
      if (!d) { inconsistencias.push(`Entrada E${e.nivel} de ${t.id} em ${e.data} fora do calendário`); return; }
      const qtd = Number(e.quantidade);
      const preco = Number(e.preco);
      lancs.push(criarLancamento({
        id: `${d}_COMPRA_${t.id}_E${e.nivel}`, data: d, data_original: e.data, tipo: 'COMPRA',
        ticker: t.ticker, trade_id: t.id, nivel: e.nivel, quantidade: qtd, preco,
        valor_caixa: -r2(qtd * preco), descricao: `Compra E${e.nivel} ${t.ticker}`
      }));
    });
    if (t.status !== 'ABERTO' && t.data_encerramento) {
      const d = mapearPregao(t.data_encerramento, calendario);
      if (!d) { inconsistencias.push(`Saída de ${t.id} em ${t.data_encerramento} fora do calendário`); continue; }
      const qtd = (t.entradas || []).reduce((s, e) => s + Number(e.quantidade), 0);
      const preco = Number(t.preco_saida);
      lancs.push(criarLancamento({
        id: `${d}_VENDA_${t.id}`, data: d, data_original: t.data_encerramento, tipo: 'VENDA',
        ticker: t.ticker, trade_id: t.id, quantidade: qtd, preco,
        valor_caixa: r2(qtd * preco), descricao: `Venda ${t.ticker} (${t.motivo_encerramento || t.status})`,
        motivo: t.motivo_encerramento || t.status
      }));
    }
  }

  lancs.sort((a, b) => a.data.localeCompare(b.data) || ORDEM_TIPO[a.tipo] - ORDEM_TIPO[b.tipo] || a.id.localeCompare(b.id));
  return { lancamentos: lancs, inconsistencias };
}

// ---------------------------------------------------------------------------
// 2. Estado e fechamento diário
// ---------------------------------------------------------------------------
function estadoInicial(capitalInicial = CAPITAL_INICIAL) {
  return {
    data: null,
    capital_inicial: capitalInicial,
    caixa: 0,
    posicoes: {},              // trade_id -> { ticker, trade_id, quantidade, custo }
    realizado_acum: 0,
    proventos_acum: 0,
    aportes_acum: 0,           // aportes posteriores ao capital inicial
    retiradas_acum: 0,
    custos_acum: 0,
    impostos_acum: 0,
    eventos_acum: 0,
    nav: 0, vm: 0, custo_total: 0, nao_realizado: 0,
    cotas: 0, cota: 1, cota_max: 1,
    max_drawdown: 0, max_drawdown_data: null,
    ibov_base: null, ibov: null,
    cota_inicio_mes: 1, cota_inicio_ano: 1, ibov_inicio_mes: null, ibov_inicio_ano: null,
    ultimo_preco: {},
    custo_por_trade: {},       // trade_id -> custo total comprado
    realizado_por_trade: {},   // trade_id -> realizado acumulado
    trades_encerrados: [],     // { trade_id, ticker, realizado, custo, data }
    n_compras: 0, n_vendas: 0, n_proventos: 0,
    hash: null
  };
}

function clonar(o) { return JSON.parse(JSON.stringify(o)); }

/**
 * Processa um pregão e gera o fechamento contábil.
 * @param {object} p
 *   estadoAnterior, data, lancamentosBase (do dia), precos {ticker: close},
 *   ibov (number|null), proventos [{ticker, valor_por_acao, tipo}],
 *   eventos [{ticker, multiplicador, descricao}], ledgerAcumulado (lançamentos até o dia anterior)
 */
function fecharDia({ estadoAnterior, data, lancamentosBase = [], precos = {}, ibov = null, proventos = [], eventos = [], proventosRetroativos = [], ledgerAcumulado = [] }) {
  const prev = estadoAnterior;
  const s = clonar(prev);
  const primeiroDia = prev.data === null;
  const erros = [];
  const avisos = [];
  const lancDia = [];

  // Viradas de mês/ano para rentabilidade mensal e anual
  if (!primeiroDia) {
    if (data.slice(0, 7) !== prev.data.slice(0, 7)) { s.cota_inicio_mes = prev.cota; s.ibov_inicio_mes = prev.ibov; }
    if (data.slice(0, 4) !== prev.data.slice(0, 4)) { s.cota_inicio_ano = prev.cota; s.ibov_inicio_ano = prev.ibov; }
  }

  // Preços do dia (carrega último preço conhecido quando não houver cotação)
  Object.entries(precos).forEach(([t, p]) => { if (p > 0) s.ultimo_preco[t] = Number(p); });

  // 2a. Eventos societários (desdobramento/grupamento/bonificação): altera quantidade, mantém custo
  let eventosDia = 0;
  for (const ev of eventos) {
    Object.values(s.posicoes).filter(p => p.ticker === ev.ticker).forEach(pos => {
      const novaQtd = Math.floor(pos.quantidade * ev.multiplicador);
      const delta = novaQtd - pos.quantidade;
      pos.quantidade = novaQtd;
      lancDia.push(criarLancamento({
        id: `${data}_EVENTO_SOCIETARIO_${pos.trade_id}`, data, tipo: 'EVENTO_SOCIETARIO',
        ticker: ev.ticker, trade_id: pos.trade_id, quantidade: delta, preco: 0, valor_caixa: 0,
        descricao: ev.descricao || `Evento societário ${ev.ticker} (fator ${ev.multiplicador})`
      }));
    });
  }

  // 2b. Proventos: direito sobre a posição do fechamento anterior (antes das ordens do dia)
  let proventosDia = 0;
  for (const pv of proventos) {
    Object.values(prev.posicoes).filter(p => p.ticker === pv.ticker && p.quantidade > 0).forEach(pos => {
      const valor = r2(pos.quantidade * Number(pv.valor_por_acao));
      if (valor <= 0) return;
      lancDia.push(criarLancamento({
        id: `${data}_PROVENTO_${pos.trade_id}_${pv.tipo || 'DIVIDEND'}`, data, tipo: 'PROVENTO',
        ticker: pv.ticker, trade_id: pos.trade_id, quantidade: pos.quantidade, preco: Number(pv.valor_por_acao),
        valor_caixa: valor, descricao: `${pv.tipo === 'JCP' ? 'JCP' : 'Dividendo'} ${pv.ticker} (R$ ${Number(pv.valor_por_acao).toFixed(6)}/ação)`
      }));
    });
  }

  // 2b'. Proventos retroativos: data-ex já fechada, mas o provento só foi publicado depois.
  //      Reconhecido hoje sobre a quantidade detida no fechamento anterior à data-ex original.
  for (const pr of proventosRetroativos) {
    const valor = r2(Number(pr.quantidade) * Number(pr.valor_por_acao));
    if (valor <= 0) continue;
    lancDia.push(criarLancamento({
      id: `${data}_PROVENTO_${pr.trade_id}_${pr.tipo || 'DIVIDEND'}_RETRO_${pr.data_ex}`, data, data_original: pr.data_ex, tipo: 'PROVENTO',
      ticker: pr.ticker, trade_id: pr.trade_id, quantidade: Number(pr.quantidade), preco: Number(pr.valor_por_acao),
      valor_caixa: valor, descricao: `Provento retroativo ${pr.ticker} (data-ex ${pr.data_ex}, publicado após o fechamento)`
    }));
    avisos.push(`Provento retroativo de ${pr.ticker} (data-ex ${pr.data_ex}) reconhecido em ${data}`);
  }

  const todos = [...lancDia, ...lancamentosBase]
    .sort((a, b) => ORDEM_TIPO[a.tipo] - ORDEM_TIPO[b.tipo] || a.id.localeCompare(b.id));

  // 2c. Aplicação dos lançamentos
  let aportesDia = 0, retiradasDia = 0, realizadoDia = 0, entradasCaixa = 0, saidasCaixa = 0;
  const vendasDia = [];
  for (const l of todos) {
    if (l.valor_caixa > 0) entradasCaixa = r2(entradasCaixa + l.valor_caixa);
    if (l.valor_caixa < 0) saidasCaixa = r2(saidasCaixa - l.valor_caixa);

    switch (l.tipo) {
      case 'APORTE_INICIAL':
        s.caixa = r2(s.caixa + l.valor_caixa);
        aportesDia = r2(aportesDia + l.valor_caixa);
        break;
      case 'APORTE':
        s.caixa = r2(s.caixa + l.valor_caixa);
        s.aportes_acum = r2(s.aportes_acum + l.valor_caixa);
        aportesDia = r2(aportesDia + l.valor_caixa);
        break;
      case 'RETIRADA':
        s.caixa = r2(s.caixa + l.valor_caixa); // valor negativo
        s.retiradas_acum = r2(s.retiradas_acum - l.valor_caixa);
        retiradasDia = r2(retiradasDia - l.valor_caixa);
        break;
      case 'EVENTO_SOCIETARIO':
        eventosDia = r2(eventosDia + l.valor_caixa);
        break;
      case 'PROVENTO':
        s.caixa = r2(s.caixa + l.valor_caixa);
        s.proventos_acum = r2(s.proventos_acum + l.valor_caixa);
        proventosDia = r2(proventosDia + l.valor_caixa);
        s.n_proventos++;
        break;
      case 'VENDA': {
        const pos = s.posicoes[l.trade_id];
        if (!pos || pos.quantidade < l.quantidade) {
          erros.push(`Venda ${l.id}: posição inexistente ou insuficiente (${pos ? pos.quantidade : 0} < ${l.quantidade})`);
          break;
        }
        const custoVendido = r2(pos.custo * (l.quantidade / pos.quantidade));
        const realizado = r2(l.valor_caixa - custoVendido);
        pos.quantidade -= l.quantidade;
        pos.custo = r2(pos.custo - custoVendido);
        s.caixa = r2(s.caixa + l.valor_caixa);
        s.realizado_acum = r2(s.realizado_acum + realizado);
        realizadoDia = r2(realizadoDia + realizado);
        s.realizado_por_trade[l.trade_id] = r2((s.realizado_por_trade[l.trade_id] || 0) + realizado);
        s.n_vendas++;
        vendasDia.push({ id: l.id, realizado, custo: custoVendido });
        if (pos.quantidade === 0) {
          const custoTrade = s.custo_por_trade[l.trade_id] || custoVendido;
          s.trades_encerrados.push({
            trade_id: l.trade_id, ticker: l.ticker, data,
            realizado: s.realizado_por_trade[l.trade_id], custo: custoTrade,
            retorno_pct: custoTrade ? r6(s.realizado_por_trade[l.trade_id] / custoTrade * 100) : 0,
            motivo: l.motivo
          });
          delete s.posicoes[l.trade_id];
        }
        break;
      }
      case 'COMPRA': {
        const custo = -l.valor_caixa;
        if (s.caixa + TOLERANCIA < custo) {
          erros.push(`Compra ${l.id}: caixa insuficiente (R$ ${s.caixa.toFixed(2)} < R$ ${custo.toFixed(2)})`);
        } else if (s.caixa + TOLERANCIA < APORTE_POR_ENTRADA) {
          avisos.push(`Compra ${l.id}: executada com caixa abaixo da trava de R$ ${APORTE_POR_ENTRADA} (R$ ${s.caixa.toFixed(2)})`);
        }
        const pos = s.posicoes[l.trade_id] || { ticker: l.ticker, trade_id: l.trade_id, quantidade: 0, custo: 0 };
        pos.quantidade += l.quantidade;
        pos.custo = r2(pos.custo + custo);
        s.posicoes[l.trade_id] = pos;
        s.caixa = r2(s.caixa + l.valor_caixa);
        s.custo_por_trade[l.trade_id] = r2((s.custo_por_trade[l.trade_id] || 0) + custo);
        s.n_compras++;
        break;
      }
      default:
        erros.push(`Tipo de lançamento desconhecido: ${l.tipo}`);
    }
  }

  // 2d. Marcação a mercado
  const posicoes = [];
  let vm = 0, custoTotal = 0;
  for (const pos of Object.values(s.posicoes)) {
    const preco = s.ultimo_preco[pos.ticker];
    if (!(preco > 0)) erros.push(`Sem cotação para ${pos.ticker} em ${data}`);
    const vmPos = r2(pos.quantidade * (preco || 0));
    vm = r2(vm + vmPos);
    custoTotal = r2(custoTotal + pos.custo);
    posicoes.push({
      ticker: pos.ticker, trade_id: pos.trade_id, quantidade: pos.quantidade,
      preco_medio: pos.quantidade ? r6(pos.custo / pos.quantidade) : 0,
      custo: pos.custo, preco: preco || 0, valor_mercado: vmPos,
      nao_realizado: r2(vmPos - pos.custo),
      nao_realizado_pct: pos.custo ? r6((vmPos / pos.custo - 1) * 100) : 0,
      cotacao_do_dia: precos[pos.ticker] > 0
    });
  }
  const nav = r2(s.caixa + vm);
  posicoes.forEach(p => { p.pct_nav = nav ? r6(p.valor_mercado / nav * 100) : 0; });
  posicoes.sort((a, b) => b.valor_mercado - a.valor_mercado);
  posicoes.filter(p => !p.cotacao_do_dia).forEach(p => avisos.push(`${p.ticker}: sem cotação em ${data}, usado último preço conhecido`));

  s.vm = vm; s.custo_total = custoTotal; s.nao_realizado = r2(vm - custoTotal); s.nav = nav;

  // 2e. Sistema de cotas (TWR) — aportes não distorcem a rentabilidade
  const fluxo = r2(aportesDia - retiradasDia);
  if (primeiroDia || prev.cotas === 0) {
    s.cota = 1;
    s.cotas = r6(nav / 1);
  } else {
    s.cota = r8((nav - fluxo) / prev.cotas);
    s.cotas = r6(prev.cotas + fluxo / s.cota);
  }
  s.cota_max = Math.max(prev.cota_max || 1, s.cota);
  const drawdown = r6((s.cota / s.cota_max - 1) * 100);
  if (drawdown < s.max_drawdown) { s.max_drawdown = drawdown; s.max_drawdown_data = data; }

  // IBOV
  s.ibov = ibov || prev.ibov;
  if (s.ibov_base === null && s.ibov) { s.ibov_base = s.ibov; s.ibov_inicio_mes = s.ibov; s.ibov_inicio_ano = s.ibov; }

  // 2f. Conciliação da variação do patrimônio
  const deltaNav = r2(nav - (prev.nav || 0));
  const deltaNaoRealizado = r2(s.nao_realizado - (prev.nao_realizado || 0));
  const componentes = {
    pnl_nao_realizado: deltaNaoRealizado,
    resultado_realizado: realizadoDia,
    proventos: proventosDia,
    custos: 0,
    impostos: 0,
    aportes: aportesDia,
    retiradas: -retiradasDia,
    eventos_societarios: eventosDia
  };
  const somaComponentes = r2(Object.values(componentes).reduce((a, b) => a + b, 0));
  const residuo = r2(deltaNav - somaComponentes);

  // 2g. Verificação independente: reconstrói caixa e quantidades a partir do ledger
  const ledgerAteHoje = [...ledgerAcumulado, ...todos];
  const caixaLedger = r2(ledgerAteHoje.reduce((a, l) => a + l.valor_caixa, 0));
  const qtdLedger = {};
  ledgerAteHoje.forEach(l => {
    if (!l.trade_id) return;
    if (l.tipo === 'COMPRA' || l.tipo === 'EVENTO_SOCIETARIO') qtdLedger[l.trade_id] = (qtdLedger[l.trade_id] || 0) + l.quantidade;
    if (l.tipo === 'VENDA') qtdLedger[l.trade_id] = (qtdLedger[l.trade_id] || 0) - l.quantidade;
  });
  const divergQtd = [];
  Object.entries(qtdLedger).forEach(([tid, q]) => {
    const qPos = s.posicoes[tid] ? s.posicoes[tid].quantidade : 0;
    if (q !== qPos) divergQtd.push(`${tid}: ledger ${q} vs posição ${qPos}`);
  });
  Object.keys(s.posicoes).forEach(tid => { if (!(tid in qtdLedger)) divergQtd.push(`${tid}: posição sem lançamento`); });
  const vmRecalc = r2(posicoes.reduce((a, p) => a + p.valor_mercado, 0));

  const validacoes = {
    nav_igual_caixa_mais_vm: { ok: Math.abs(nav - r2(s.caixa + vmRecalc)) < TOLERANCIA, detalhe: `NAV ${nav} = Caixa ${s.caixa} + VM ${vmRecalc}` },
    variacao_explicada: { ok: Math.abs(residuo) < TOLERANCIA, detalhe: `ΔNAV ${deltaNav} − componentes ${somaComponentes} = resíduo ${residuo}` },
    caixa_confere_ledger: { ok: Math.abs(caixaLedger - s.caixa) < TOLERANCIA, detalhe: `Caixa pelo ledger ${caixaLedger} vs estado ${s.caixa}` },
    quantidades_conferem_ledger: { ok: divergQtd.length === 0, detalhe: divergQtd.length ? divergQtd.join('; ') : 'Todas as posições conferem com o ledger' },
    caixa_nao_negativo: { ok: s.caixa >= -TOLERANCIA, detalhe: `Caixa ${s.caixa}` },
    ordens_consistentes: { ok: erros.length === 0, detalhe: erros.length ? erros.join('; ') : 'Sem erros de execução' },
    encadeamento_hash: { ok: primeiroDia ? true : Boolean(prev.hash), detalhe: primeiroDia ? 'Primeiro fechamento (gênese)' : `Encadeado a ${prev.data}` }
  };
  const conciliado = Object.values(validacoes).every(v => v.ok);

  // 2h. Eficiência da estratégia
  const enc = s.trades_encerrados;
  const vencedoras = enc.filter(t => t.realizado > 0);
  const perdedoras = enc.filter(t => t.realizado <= 0);
  const somaGanhos = r2(vencedoras.reduce((a, t) => a + t.realizado, 0));
  const somaPerdas = r2(perdedoras.reduce((a, t) => a + t.realizado, 0));

  // Eventos do dia (alimentam as bolinhas do gráfico)
  const eventosGrafico = todos.map(l => {
    const ev = { tipo: l.tipo, ticker: l.ticker, trade_id: l.trade_id, nivel: l.nivel, quantidade: l.quantidade, preco: l.preco, valor: l.valor_caixa };
    if (l.tipo === 'VENDA') {
      const v = vendasDia.find(x => x.id === l.id);
      ev.realizado = v ? v.realizado : 0;
      ev.resultado_pct = v && v.custo ? r6(v.realizado / v.custo * 100) : 0;
      ev.motivo = l.motivo;
      ev.classe = (l.motivo || '').includes('STOP') ? 'STOP' : (ev.realizado >= 0 ? 'GAIN' : 'LOSS');
    }
    return ev;
  });

  const ibovAcum = s.ibov_base && s.ibov ? pct(s.ibov, s.ibov_base) : null;
  const rentAcum = r6((s.cota - 1) * 100);

  const fechamento = {
    data,
    patrimonio: {
      nav,
      nav_inicial: s.capital_inicial,
      variacao_total: r2(nav - s.capital_inicial),
      variacao_por_aportes: r2(s.aportes_acum - s.retiradas_acum),
      variacao_por_resultado: r2(s.realizado_acum + s.nao_realizado + s.proventos_acum - s.custos_acum - s.impostos_acum),
      nav_anterior: prev.nav || 0,
      variacao_dia: deltaNav
    },
    caixa: {
      saldo: s.caixa,
      livre: s.caixa,
      comprometido: 0,
      a_receber_vendas: 0,
      a_receber_proventos: 0,
      entradas_dia: entradasCaixa,
      saidas_dia: saidasCaixa,
      entradas_possiveis: Math.floor(s.caixa / APORTE_POR_ENTRADA),
      nota: 'Liquidação imediata (D+0): vendas e proventos entram no caixa no próprio dia.'
    },
    investido: {
      valor_mercado: vm,
      custo_aquisicao: custoTotal,
      pct_investido: nav ? r6(vm / nav * 100) : 0,
      n_posicoes: posicoes.length,
      posicoes
    },
    resultados: {
      realizado_acum: s.realizado_acum,
      realizado_dia: realizadoDia,
      nao_realizado: s.nao_realizado,
      nao_realizado_dia: deltaNaoRealizado,
      proventos_acum: s.proventos_acum,
      proventos_dia: proventosDia,
      custos_acum: s.custos_acum,
      impostos_acum: s.impostos_acum,
      resultado_liquido: r2(s.realizado_acum + s.nao_realizado + s.proventos_acum - s.custos_acum - s.impostos_acum),
      resultado_dia: r2(deltaNaoRealizado + realizadoDia + proventosDia),
      aportes_acum: s.aportes_acum,
      retiradas_acum: s.retiradas_acum
    },
    rentabilidade: {
      cota: s.cota,
      cotas: s.cotas,
      rent_dia: primeiroDia ? 0 : pct(s.cota, prev.cota),
      rent_mes: pct(s.cota, s.cota_inicio_mes),
      rent_ano: pct(s.cota, s.cota_inicio_ano),
      rent_acum: rentAcum,
      ibov: s.ibov,
      ibov_dia: (!primeiroDia && prev.ibov && s.ibov) ? pct(s.ibov, prev.ibov) : 0,
      ibov_mes: s.ibov_inicio_mes && s.ibov ? pct(s.ibov, s.ibov_inicio_mes) : null,
      ibov_ano: s.ibov_inicio_ano && s.ibov ? pct(s.ibov, s.ibov_inicio_ano) : null,
      ibov_acum: ibovAcum,
      supera_ibov: ibovAcum === null ? null : rentAcum > ibovAcum,
      alpha_acum: ibovAcum === null ? null : r6(rentAcum - ibovAcum),
      drawdown_atual: drawdown,
      max_drawdown: s.max_drawdown,
      max_drawdown_data: s.max_drawdown_data
    },
    eficiencia: {
      operacoes_encerradas: enc.length,
      operacoes_abertas: posicoes.length,
      ordens_executadas: s.n_compras + s.n_vendas,
      vencedoras: vencedoras.length,
      perdedoras: perdedoras.length,
      taxa_acerto: enc.length ? r6(vencedoras.length / enc.length * 100) : 0,
      lucro_medio: vencedoras.length ? r2(somaGanhos / vencedoras.length) : 0,
      prejuizo_medio: perdedoras.length ? r2(somaPerdas / perdedoras.length) : 0,
      resultado_medio: enc.length ? r2((somaGanhos + somaPerdas) / enc.length) : 0,
      profit_factor: somaPerdas < 0 ? r6(somaGanhos / Math.abs(somaPerdas)) : null,
      retorno_medio_capital_pct: enc.length ? r6(enc.reduce((a, t) => a + t.retorno_pct, 0) / enc.length) : 0
    },
    conciliacao: { delta_nav: deltaNav, componentes, soma_componentes: somaComponentes, residuo },
    validacoes,
    conciliado,
    avisos,
    eventos: eventosGrafico,
    lancamentos: todos.map(l => l.id),
    entradas_utilizadas: {
      precos: Object.fromEntries(Object.entries(precos).filter(([, p]) => p > 0).map(([t, p]) => [t, Number(p)])),
      ibov: ibov || null,
      proventos: proventos.map(p => ({ ticker: p.ticker, valor_por_acao: Number(p.valor_por_acao), tipo: p.tipo || 'DIVIDEND' })),
      proventos_retroativos: proventosRetroativos.map(p => ({ ticker: p.ticker, trade_id: p.trade_id, quantidade: Number(p.quantidade), valor_por_acao: Number(p.valor_por_acao), tipo: p.tipo || 'DIVIDEND', data_ex: p.data_ex })),
      eventos_societarios: eventos.map(e => ({ ticker: e.ticker, multiplicador: e.multiplicador, descricao: e.descricao || '' }))
    },
    hash_anterior: prev.hash || null
  };
  fechamento.hash = sha256(fechamento);

  s.data = data;
  s.hash = fechamento.hash;
  return { estado: s, fechamento, lancamentos: todos };
}

// ---------------------------------------------------------------------------
// 3. Reprocessamento completo do histórico
// ---------------------------------------------------------------------------
/**
 * @param {object} p
 *   trades[], calendario[] (pregões ordenados), precos { data: { ticker: close } },
 *   ibov { data: valor }, proventos [{ticker, data_ex, valor_por_acao, tipo}],
 *   eventos [{ticker, data, multiplicador, descricao}]
 */
function reprocessarHistorico({ trades, calendario, precos = {}, ibov = {}, proventos = [], eventos = [], entradasPorDia = {}, proventosRetroativosPorDia = {}, capitalInicial = CAPITAL_INICIAL, aporteMensal = APORTE_MENSAL }) {
  const { lancamentos: base, inconsistencias } = gerarLancamentosBase({ trades, calendario, capitalInicial, aporteMensal });
  const basePorDia = {};
  base.forEach(l => (basePorDia[l.data] = basePorDia[l.data] || []).push(l));

  const provPorDia = {};
  proventos.forEach(p => {
    const d = mapearPregao(p.data_ex, calendario);
    if (d) (provPorDia[d] = provPorDia[d] || []).push(p);
  });
  const evPorDia = {};
  eventos.forEach(e => {
    const d = mapearPregao(e.data, calendario);
    if (d) (evPorDia[d] = evPorDia[d] || []).push(e);
  });

  let estado = estadoInicial(capitalInicial);
  const ledger = [];
  const fechamentos = [];
  let ultimoIbov = null;
  for (const data of calendario) {
    // Dias já fechados usam exatamente as entradas gravadas no fechamento (reprodutibilidade)
    const fixo = entradasPorDia[data];
    const ibovDia = fixo ? fixo.ibov : (ibov[data] || ultimoIbov);
    if (ibovDia) ultimoIbov = ibovDia;
    const r = fecharDia({
      estadoAnterior: estado, data,
      lancamentosBase: basePorDia[data] || [],
      precos: fixo ? fixo.precos : (precos[data] || {}),
      ibov: ibovDia,
      proventos: fixo ? fixo.proventos : (provPorDia[data] || []),
      eventos: fixo ? (fixo.eventos_societarios || []) : (evPorDia[data] || []),
      proventosRetroativos: fixo ? (fixo.proventos_retroativos || []) : (proventosRetroativosPorDia[data] || []),
      ledgerAcumulado: ledger
    });
    estado = r.estado;
    ledger.push(...r.lancamentos);
    fechamentos.push(r.fechamento);
  }
  return { fechamentos, ledger, estado, inconsistencias };
}

/** Verifica a integridade da cadeia de hashes de uma lista de fechamentos */
function verificarCadeia(fechamentos) {
  const problemas = [];
  let anterior = null;
  for (const f of fechamentos) {
    if (sha256(semHash(f)) !== f.hash) problemas.push(`${f.data}: hash não confere com o conteúdo`);
    if ((f.hash_anterior || null) !== (anterior ? anterior.hash : null)) problemas.push(`${f.data}: hash_anterior quebrado`);
    anterior = f;
  }
  return problemas;
}

/** Série compacta para o gráfico (documento fechamentos_resumo/{ano}) */
function resumoParaGrafico(f) {
  return {
    d: f.data,
    nav: f.patrimonio.nav,
    caixa: f.caixa.saldo,
    vm: f.investido.valor_mercado,
    custo: f.investido.custo_aquisicao,
    real: f.resultados.realizado_acum,
    nreal: f.resultados.nao_realizado,
    prov: f.resultados.proventos_acum,
    apt: f.resultados.aportes_acum,
    res_dia: f.resultados.resultado_dia,
    cota: f.rentabilidade.cota,
    r_dia: f.rentabilidade.rent_dia,
    r_acum: f.rentabilidade.rent_acum,
    ibov_acum: f.rentabilidade.ibov_acum,
    dd: f.rentabilidade.drawdown_atual,
    ok: f.conciliado,
    res: f.conciliacao.residuo,
    ev: f.eventos.map(e => {
      const c = { t: e.tipo, tk: e.ticker, id: e.trade_id, n: e.nivel, q: e.quantidade, p: e.preco, v: e.valor };
      if (e.tipo === 'VENDA') { c.rl = e.realizado; c.rp = e.resultado_pct; c.cl = e.classe; c.m = e.motivo; }
      return c;
    })
  };
}

module.exports = {
  CAPITAL_INICIAL, APORTE_MENSAL, APORTE_POR_ENTRADA, TOLERANCIA,
  r2, r6, sha256, canonico, semHash, mapearPregao,
  criarLancamento, gerarLancamentosBase, estadoInicial, fecharDia,
  reprocessarHistorico, verificarCadeia, resumoParaGrafico
};
