/**
 * processar-ifr.js
 * 
 * Script diário do Rastreador e Máquina de Estados da Estratégia "Entradas > IFR".
 * Executado de segunda a sexta às 18h30 (horário de Brasília) via GitHub Actions.
 * 
 * Regras & Travas Anti-Bugs:
 * 1. Idempotência: Checa se o pregão (marketDate) já foi processado hoje.
 * 2. Consulta Única no Supabase: Recupera fechamento, P/L de hoje e P/L Médio dos últimos 2 anos (> 0) em 1 segundo.
 * 3. Cálculo de IFR(21) de Wilder com suavização exponencial mantendo memória.
 * 4. Máquina de Estados com Ordem de Prioridade Rígida:
 *    - Prioridade 1: Stop Geral (-50% do Preço Médio)
 *    - Prioridade 2: Alvos de Saída (Gain):
 *      * E1: IFR > 70
 *      * E2: IFR >= 50 E Preço > Preço Médio
 *      * E3: Preço >= E3 + 10%
 *    - Prioridade 3: Preço Médio (Novas Entradas):
 *      * E2: Preço <= E1 * 0.90 (-10%) com trava de caixa >= R$ 3.300
 *      * E3: Preço <= E2 * 0.90 (-10%) com trava de caixa >= R$ 3.300
 *    - Nova Entrada 1: IFR < 30 E P/L Atual < P/L Médio (2 Anos) com ambos > 0, sem trade aberto e caixa >= R$ 3.300.
 * 5. Gravação em Batch no Cloud Firestore (projeto dashboard-b3-estrategia-448bd).
 */

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');
const admin = require('firebase-admin');
const C = require('./contabil-ifr');
const F = require('./fechamento-contabil');

function createPgPool() {
  return new Pool({
    connectionString: process.env.DATABASE_URL,
    host: process.env.DB_HOST,
    port: Number(process.env.DB_PORT || 5432),
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    ssl: { rejectUnauthorized: false },
    connectionTimeoutMillis: 15000
  });
}

function initFirebase() {
  if (admin.apps.length > 0) {
    return admin.firestore();
  }

  let saKey = process.env.FIREBASE_SERVICE_ACCOUNT_KEY;
  if (!saKey) {
    const defaultSaPath = 'C:/Users/Leo/Downloads/dashboard-b3-estrategia-448bd-firebase-adminsdk-fbsvc-6b53b074cb.json';
    if (fs.existsSync(defaultSaPath)) {
      saKey = defaultSaPath;
    }
  }

  if (saKey) {
    let serviceAccount;
    try {
      serviceAccount = JSON.parse(saKey);
    } catch (err) {
      if (fs.existsSync(saKey)) {
        serviceAccount = require(path.resolve(saKey));
      } else {
        throw new Error('Não foi possível ler as credenciais do Firebase: ' + err.message);
      }
    }
    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount)
    });
    console.log('✅ Firebase Admin SDK conectado com sucesso (Projeto: ' + serviceAccount.project_id + ')!');
  } else {
    admin.initializeApp({
      credential: admin.credential.applicationDefault()
    });
    console.log('✅ Firebase Admin SDK conectado via Application Default Credentials!');
  }

  return admin.firestore();
}

/**
 * Consulta pontual consolidada no Supabase (executada em ~1s).
 * Retorna { marketDate, quotes } com preço de fechamento, P/L atual e P/L Médio dos últimos 2 anos.
 */
async function fetchLatestMarketQuotes() {
  console.log('📡 Buscando cotações de fechamento, P/L e P/L Médio (2 anos) no Supabase...');
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    host: process.env.DB_HOST,
    port: Number(process.env.DB_PORT || 5432),
    database: process.env.DB_NAME || 'postgres',
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    ssl: { rejectUnauthorized: false },
    connectionTimeoutMillis: 15000
  });

  const query = `
    WITH data_recente AS (
        SELECT MAX(reference_date) AS max_date FROM daily_metrics
    ),
    media_pl_2a AS (
        SELECT 
            dm.security_id,
            AVG(dm.price_earnings) AS pl_medio_2a
        FROM daily_metrics dm, data_recente dr
        WHERE dm.reference_date >= (dr.max_date - INTERVAL '2 years')
          AND dm.price_earnings > 0 
          AND dm.price_earnings < 150
        GROUP BY dm.security_id
        HAVING AVG(dm.price_earnings) > 0
    )
    SELECT 
        s.ticker, 
        c.trading_name,
        c.sector,
        dm.reference_date::text AS ref_date,
        dm.close_price::float   AS close_price, 
        dm.price_earnings::float AS price_earnings,
        ROUND(m.pl_medio_2a::numeric, 2)::float AS pl_medio_2a
    FROM daily_metrics dm
    JOIN data_recente dr ON dm.reference_date = dr.max_date
    JOIN securities s ON dm.security_id = s.id
    JOIN companies c ON s.company_id = c.id
    LEFT JOIN media_pl_2a m ON dm.security_id = m.security_id
    WHERE dm.close_price > 0
    ORDER BY s.ticker ASC;
  `;

  const res = await pool.query(query);
  await pool.end();

  if (!res.rows || res.rows.length === 0) {
    throw new Error('Nenhuma cotação retornada pelo Supabase para o pregão de hoje.');
  }

  const marketDate = res.rows[0].ref_date;
  console.log(`📅 Pregão mais recente processado: ${marketDate} (${res.rows.length} ativos)`);

  const quotes = {};
  for (const row of res.rows) {
    if (row.close_price && !isNaN(row.close_price) && row.close_price > 0) {
      quotes[row.ticker] = {
        ticker: row.ticker,
        company: row.trading_name,
        sector: row.sector,
        close: Number(row.close_price.toFixed(2)),
        pe: (row.price_earnings && row.price_earnings > 0) ? Number(row.price_earnings.toFixed(2)) : null,
        plMedio2a: (row.pl_medio_2a && row.pl_medio_2a > 0) ? Number(row.pl_medio_2a.toFixed(2)) : null
      };
    }
  }

  return { marketDate, quotes };
}

/**
 * Atualização incremental da suavização de Wilder para o IFR(21)
 */
function updateWilderRSI(prevAvgGain, prevAvgLoss, prevClose, currentClose, period = 21) {
  const change = currentClose - prevClose;
  const gain = change > 0 ? change : 0;
  const loss = change < 0 ? Math.abs(change) : 0;

  const newAvgGain = (prevAvgGain * (period - 1) + gain) / period;
  const newAvgLoss = (prevAvgLoss * (period - 1) + loss) / period;

  let rsi = 50.0;
  if (newAvgLoss === 0 && newAvgGain === 0) {
    rsi = 50.0;
  } else if (newAvgLoss === 0) {
    rsi = 100.0;
  } else if (newAvgGain === 0) {
    rsi = 0.0;
  } else {
    const rs = newAvgGain / newAvgLoss;
    rsi = 100 - (100 / (1 + rs));
  }

  return {
    rsi: Number(rsi.toFixed(2)),
    avgGain: Number(newAvgGain.toFixed(6)),
    avgLoss: Number(newAvgLoss.toFixed(6))
  };
}

async function processarEstrategiaIFR() {
  console.log('⚡ Iniciando Execução Diária: Rastreador & Máquina de Estados (Entradas > IFR)...');
  const firestoreDb = initFirebase();
  const cachePath = path.resolve(__dirname, 'entradas_ifr_cache.json');

  // 1. Carregar Estado Atual do Firestore
  console.log('📥 Lendo estado atual do Cloud Firestore...');
  const configDoc = await firestoreDb.collection('configuracao_ifr').doc('estado_global').get();
  if (!configDoc.exists) {
    throw new Error('Estado global não encontrado no Firestore. Execute seed-historico.js primeiro.');
  }
  const config = configDoc.data();

  const ativos = {};
  const ativosSnap = await firestoreDb.collection('ativos_ifr').get();
  ativosSnap.forEach(doc => { ativos[doc.id] = doc.data(); });

  const trades = {};
  const tradesSnap = await firestoreDb.collection('trades_ifr').get();
  tradesSnap.forEach(doc => { trades[doc.id] = doc.data(); });

  let evolucao = [];
  const evoSnap = await firestoreDb.collection('evolucao_patrimonial').orderBy('data', 'asc').get();
  evoSnap.forEach(doc => { evolucao.push(doc.data()); });

  // 2. Buscar dados de mercado de hoje no Supabase
  const { marketDate, quotes } = await fetchLatestMarketQuotes();

  // TRAVA ANTI-BUG: IDEMPOTÊNCIA
  if (config.ultima_data_processada === marketDate) {
    console.log(`🛡️ [IDEMPOTÊNCIA] O pregão de ${marketDate} já foi processado anteriormente.`);
    console.log(`Abortando execução sem duplicar entradas ou registros na evolução patrimonial.`);
    return { status: 'ALREADY_PROCESSED', marketDate };
  }

  console.log(`🔄 Processando pregão de ${marketDate}...`);
  console.log(`💰 Saldo em Caixa Livre: R$ ${config.caixa_livre.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`);

  const APORTE_FIXO = 3300.00;
  const CAP_INICIAL = 50000.00;

  // 3. Atualizar IFR de cada ativo com o fechamento de hoje
  for (const [ticker, q] of Object.entries(quotes)) {
    let ativo = ativos[ticker];
    if (!ativo) continue;

    const currentClose = q.close;
    const currentPe = q.pe;
    const currentPl2a = q.plMedio2a;

    if (!currentClose || isNaN(currentClose) || currentClose <= 0) continue;

    const hist = ativo.historico_fechamentos || [];
    const lastHistEntry = hist[hist.length - 1];

    let newRsi = ativo.ifr_21 || 50.0;
    let newAvgGain = ativo.avg_gain_wilder || 0;
    let newAvgLoss = ativo.avg_loss_wilder || 0;

    if (lastHistEntry && lastHistEntry.data !== marketDate) {
      const prevClose = lastHistEntry.preco;
      const updated = updateWilderRSI(newAvgGain, newAvgLoss, prevClose, currentClose, 21);
      newRsi = updated.rsi;
      newAvgGain = updated.avgGain;
      newAvgLoss = updated.avgLoss;

      hist.push({ data: marketDate, preco: currentClose });
      while (hist.length > 35) {
        hist.shift();
      }
    }

    ativo.ultimo_preco = currentClose;
    ativo.ultimo_pl = currentPe;
    if (currentPl2a !== undefined) ativo.pl_medio_historico_2a = currentPl2a;
    ativo.ifr_21 = newRsi;
    ativo.avg_gain_wilder = newAvgGain;
    ativo.avg_loss_wilder = newAvgLoss;
    ativo.historico_fechamentos = hist;
    ativo.ultima_atualizacao = new Date().toISOString();
  }

  // 4. MÁQUINA DE ESTADOS: Gestão de Trades Abertos (Ordem Estrita de Prioridade)
  const openTrades = Object.values(trades).filter(t => t.status === 'ABERTO');
  console.log(`🔍 Trades abertos em monitoramento: ${openTrades.length}`);

  for (const trade of openTrades) {
    const ticker = trade.ticker;
    const ativo = ativos[ticker];
    if (!ativo) continue;

    const currentClose = ativo.ultimo_preco;
    const ifr = ativo.ifr_21;
    const pm = trade.preco_medio_atual;
    const e1 = trade.entradas[0];
    const e2 = trade.entradas[1];
    const e3 = trade.entradas[2];

    // PRIORIDADE 1 — STOP GERAL (-50% do Preço Médio Atual)
    const stopPrice = Number((pm * 0.50).toFixed(2));
    if (currentClose <= stopPrice) {
      console.log(`🚨 [STOP -50%] Ativo: ${ticker} | Preço: R$ ${currentClose} <= Stop: R$ ${stopPrice}`);
      const valorVenda = Number((trade.quantidade_total * currentClose).toFixed(2));
      const resultadoRs = Number((valorVenda - trade.capital_total_alocado).toFixed(2));
      const resultadoPct = Number(((valorVenda / trade.capital_total_alocado - 1) * 100).toFixed(2));

      config.caixa_livre = Number((config.caixa_livre + valorVenda).toFixed(2));
      config.lucro_realizado_acumulado = Number((config.lucro_realizado_acumulado + resultadoRs).toFixed(2));
      config.total_stops = (config.total_stops || 0) + 1;

      trade.status = 'FINALIZADO_STOP';
      trade.data_encerramento = marketDate;
      trade.preco_saida = currentClose;
      trade.resultado_realizado_rs = resultadoRs;
      trade.resultado_realizado_pct = resultadoPct;
      trade.motivo_encerramento = 'STOP_PERDA_50PCT';

      ativo.status_trade = 'SEM_OPERACAO';
      ativo.trade_ativo_id = null;
      continue;
    }

    // PRIORIDADE 2 — ALVOS DE SAÍDA (GAIN)
    let deuGain = false;
    let motivoGain = '';

    if (trade.etapa_atual === 1) {
      // E1: IFR > 70
      if (ifr > 70.0) {
        deuGain = true;
        motivoGain = 'GAIN_IFR70';
      }
    } else if (trade.etapa_atual === 2) {
      // E2: IFR >= 50 E Preço > Preço Médio Atual
      if (ifr >= 50.0 && currentClose > pm) {
        deuGain = true;
        motivoGain = 'GAIN_IFR50_PM';
      }
    } else if (trade.etapa_atual === 3) {
      // E3: Preço >= E3 + 10%
      const alvoE3 = Number((e3.preco * 1.10).toFixed(2));
      if (currentClose >= alvoE3) {
        deuGain = true;
        motivoGain = 'GAIN_E3_10PCT';
      }
    }

    if (deuGain) {
      console.log(`🎯 [GAIN] Ativo: ${ticker} (${trade.etapa_atual}/3) | Motivo: ${motivoGain} | Preço: R$ ${currentClose}`);
      const valorVenda = Number((trade.quantidade_total * currentClose).toFixed(2));
      const resultadoRs = Number((valorVenda - trade.capital_total_alocado).toFixed(2));
      const resultadoPct = Number(((valorVenda / trade.capital_total_alocado - 1) * 100).toFixed(2));

      config.caixa_livre = Number((config.caixa_livre + valorVenda).toFixed(2));
      config.lucro_realizado_acumulado = Number((config.lucro_realizado_acumulado + resultadoRs).toFixed(2));
      config.total_gains = (config.total_gains || 0) + 1;

      trade.status = 'FINALIZADO_GAIN';
      trade.data_encerramento = marketDate;
      trade.preco_saida = currentClose;
      trade.resultado_realizado_rs = resultadoRs;
      trade.resultado_realizado_pct = resultadoPct;
      trade.motivo_encerramento = motivoGain;

      ativo.status_trade = 'SEM_OPERACAO';
      ativo.trade_ativo_id = null;
      continue;
    }

    // PRIORIDADE 3 — NOVAS ENTRADAS (PREÇO MÉDIO)
    if (trade.etapa_atual === 1 && currentClose <= Number((e1.preco * 0.90).toFixed(2))) {
      // Gatilho E2: Preço <= E1 * 0.90 (-10%)
      if (config.caixa_livre >= APORTE_FIXO) {
        const qtdE2 = Math.floor(APORTE_FIXO / currentClose);
        if (qtdE2 > 0) {
          const custoE2 = Number((qtdE2 * currentClose).toFixed(2));
          config.caixa_livre = Number((config.caixa_livre - custoE2).toFixed(2));

          trade.entradas.push({
            nivel: 2,
            data: marketDate,
            preco: currentClose,
            quantidade: qtdE2,
            aporte_real: custoE2
          });
          trade.quantidade_total += qtdE2;
          trade.capital_total_alocado = Number((trade.capital_total_alocado + custoE2).toFixed(2));
          trade.preco_medio_atual = Number((trade.capital_total_alocado / trade.quantidade_total).toFixed(2));
          trade.stop_geral_preco = Number((trade.preco_medio_atual * 0.50).toFixed(2));
          trade.etapa_atual = 2;
          trade.alvo_saida_desc = 'IFR >= 50 e Preço > PM';

          ativo.status_trade = 'ABERTO_E2';
          console.log(`📥 [ENTRADA 2] ${ticker}: ${qtdE2} ações a R$ ${currentClose} | Novo PM: R$ ${trade.preco_medio_atual}`);
        }
      } else {
        console.log(`⚠️ Trava de caixa: saldo insuficiente para E2 em ${ticker} (Caixa: R$ ${config.caixa_livre})`);
      }
    } else if (trade.etapa_atual === 2 && currentClose <= Number((e2.preco * 0.90).toFixed(2))) {
      // Gatilho E3: Preço <= E2 * 0.90 (-10%)
      if (config.caixa_livre >= APORTE_FIXO) {
        const qtdE3 = Math.floor(APORTE_FIXO / currentClose);
        if (qtdE3 > 0) {
          const custoE3 = Number((qtdE3 * currentClose).toFixed(2));
          config.caixa_livre = Number((config.caixa_livre - custoE3).toFixed(2));

          trade.entradas.push({
            nivel: 3,
            data: marketDate,
            preco: currentClose,
            quantidade: qtdE3,
            aporte_real: custoE3
          });
          trade.quantidade_total += qtdE3;
          trade.capital_total_alocado = Number((trade.capital_total_alocado + custoE3).toFixed(2));
          trade.preco_medio_atual = Number((trade.capital_total_alocado / trade.quantidade_total).toFixed(2));
          trade.stop_geral_preco = Number((trade.preco_medio_atual * 0.50).toFixed(2));
          trade.etapa_atual = 3;
          const precoAlvoE3 = Number((currentClose * 1.10).toFixed(2));
          trade.alvo_saida_desc = `+10% da E3 (R$ ${precoAlvoE3})`;
          trade.preco_gatilho_alvo = precoAlvoE3;

          ativo.status_trade = 'ABERTO_E3';
          console.log(`📥 [ENTRADA 3] ${ticker}: ${qtdE3} ações a R$ ${currentClose} | Novo PM: R$ ${trade.preco_medio_atual}`);
        }
      } else {
        console.log(`⚠️ Trava de caixa: saldo insuficiente para E3 em ${ticker} (Caixa: R$ ${config.caixa_livre})`);
      }
    }

    // Trade continua aberto: recalcular valuation não realizado
    trade.preco_fechamento_atual = currentClose;
    trade.valor_mercado_atual = Number((trade.quantidade_total * currentClose).toFixed(2));
    trade.resultado_nao_realizado_rs = Number((trade.valor_mercado_atual - trade.capital_total_alocado).toFixed(2));
    trade.resultado_nao_realizado_pct = Number(((trade.valor_mercado_atual / trade.capital_total_alocado - 1) * 100).toFixed(2));
  }

  // 5. GATILHO DE ENTRADA 1 (Abertura de Novo Trade)
  for (const [ticker, ativo] of Object.entries(ativos)) {
    if (ativo.status_trade && ativo.status_trade !== 'SEM_OPERACAO') continue;
    if (ativo.trade_ativo_id) continue;

    const currentClose = ativo.ultimo_preco;
    const currentPe = ativo.ultimo_pl;
    const pl2a = ativo.pl_medio_historico_2a;
    const ifr = ativo.ifr_21;

    // Regra: IFR_21 < 30 E PL_Atual < PL_Medio_2A (ambos > 0)
    const ifrGatilho = (ifr < 30.0);
    const plGatilho = (currentPe !== null && pl2a !== null && currentPe > 0 && pl2a > 0 && currentPe < pl2a);

    if (ifrGatilho && plGatilho) {
      if (config.caixa_livre >= APORTE_FIXO) {
        const qtdE1 = Math.floor(APORTE_FIXO / currentClose);
        if (qtdE1 > 0) {
          const custoE1 = Number((qtdE1 * currentClose).toFixed(2));
          config.caixa_livre = Number((config.caixa_livre - custoE1).toFixed(2));

          const tradeId = `${ticker}_${marketDate.replace(/-/g, '')}`;
          const novoTrade = {
            id: tradeId,
            ticker,
            empresa: ativo.empresa || ticker,
            setor: ativo.setor || 'Geral',
            status: 'ABERTO',
            etapa_atual: 1,
            entradas: [{
              nivel: 1,
              data: marketDate,
              preco: currentClose,
              quantidade: qtdE1,
              aporte_real: custoE1
            }],
            quantidade_total: qtdE1,
            capital_total_alocado: custoE1,
            preco_medio_atual: currentClose,
            preco_fechamento_atual: currentClose,
            valor_mercado_atual: custoE1,
            resultado_nao_realizado_rs: 0.00,
            resultado_nao_realizado_pct: 0.00,
            stop_geral_preco: Number((currentClose * 0.50).toFixed(2)),
            alvo_saida_desc: 'IFR > 70',
            preco_gatilho_alvo: null,
            data_abertura: marketDate,
            data_encerramento: null,
            motivo_encerramento: null,
            preco_saida: null,
            resultado_realizado_rs: null,
            resultado_realizado_pct: null
          };

          trades[tradeId] = novoTrade;
          ativo.status_trade = 'ABERTO_E1';
          ativo.trade_ativo_id = tradeId;

          console.log(`🌟 [NOVA ENTRADA 1] ${ticker} | IFR: ${ifr} | P/L: ${currentPe}x vs Méd 2A: ${pl2a}x | Qtd: ${qtdE1} ações a R$ ${currentClose}`);
        }
      } else {
        console.log(`⚠️ Radar detectou entrada em ${ticker}, mas saldo em caixa (R$ ${config.caixa_livre}) é menor que R$ 3.300.`);
      }
    }
  }

  // 6. FECHAMENTO CONTÁBIL DIÁRIO E VALIDAÇÃO AUTOMÁTICA
  console.log('📒 Executando fechamento contábil diário...');
  const poolContabil = createPgPool();
  let resContabil;
  try {
    resContabil = await F.calcularFechamentos({
      db: firestoreDb,
      pool: poolContabil,
      trades,
      modo: 'incremental'
    });
  } finally {
    await poolContabil.end();
  }

  // Aborta com erro não-zero se qualquer regra de conciliação falhar (nada foi gravado ainda)
  F.exigirConciliacao(resContabil.novos);

  const ultFechamento = resContabil.fechamentos[resContabil.fechamentos.length - 1];
  Object.assign(config, F.estadoGlobalDe(ultFechamento));
  config.ultima_data_processada = marketDate;
  config.ultima_atualizacao = new Date().toISOString();

  const cacheBlock = F.blocoCache(resContabil);
  evolucao = cacheBlock.evolucao;

  console.log('---------------------------------------------------------');
  console.log(`📈 Resumo Diário Conciliado (${ultFechamento.data}):`);
  console.log(`   Patrimônio (NAV): R$ ${ultFechamento.patrimonio.nav.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} (Cota: ${ultFechamento.rentabilidade.rent_acum >= 0 ? '+' : ''}${ultFechamento.rentabilidade.rent_acum.toFixed(2)}%)`);
  console.log(`   Caixa Livre:      R$ ${ultFechamento.caixa.livre.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`);
  console.log(`   Capital Invest.:  R$ ${ultFechamento.investido.valor_mercado.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} (${ultFechamento.investido.n_posicoes} ativos)`);
  console.log(`   Taxa de Acerto:   ${ultFechamento.eficiencia.taxa_acerto.toFixed(1)}% (${ultFechamento.eficiencia.vencedoras} Gains · ${ultFechamento.eficiencia.perdedoras} Stops)`);
  console.log(`   Conciliação:      ${ultFechamento.conciliado ? '✅ CONCILIADO' : '❌ DIVERGÊNCIA'}`);
  console.log('---------------------------------------------------------');

  // 7. GRAVAÇÃO NO FIRESTORE (Fechamentos Imutáveis + Trades + Ativos + Estado Global)
  console.log('💾 Gravando atualizações no Cloud Firestore...');

  // Batch 1: Trades
  let bTrades = firestoreDb.batch();
  let tCount = 0;
  for (const [tId, tData] of Object.entries(trades)) {
    bTrades.set(firestoreDb.collection('trades_ifr').doc(tId), tData);
    tCount++;
    if (tCount >= 450) {
      await bTrades.commit();
      bTrades = firestoreDb.batch();
      tCount = 0;
    }
  }
  if (tCount > 0) await bTrades.commit();

  // Batch 2: Ativos
  let bAtivos = firestoreDb.batch();
  let aCount = 0;
  for (const [ticker, aData] of Object.entries(ativos)) {
    bAtivos.set(firestoreDb.collection('ativos_ifr').doc(ticker), aData);
    aCount++;
    if (aCount >= 450) {
      await bAtivos.commit();
      bAtivos = firestoreDb.batch();
      aCount = 0;
    }
  }
  if (aCount > 0) await bAtivos.commit();

  // Fechamentos imutáveis (create), Ledger, Resumos anuais e Estado Global
  const gravadosInfo = await F.gravarFechamentos(firestoreDb, {
    novos: resContabil.novos,
    novosLancamentos: resContabil.novosLancamentos,
    fechamentos: resContabil.fechamentos,
    estado: resContabil.estado
  });
  await firestoreDb.collection('configuracao_ifr').doc('estado_global').set(config);
  console.log(`🎉 Firestore atualizado (${gravadosInfo.gravados} novos fechamentos, ${gravadosInfo.lancamentos} lançamentos).`);

  // 8. Salvar Cache Local Sincronizado
  const cacheData = {
    config,
    ativos,
    trades,
    ...cacheBlock
  };
  fs.writeFileSync(cachePath, JSON.stringify(cacheData, null, 2), 'utf-8');
  console.log('💾 entradas_ifr_cache.json atualizado.');

  return {
    status: 'SUCCESS',
    marketDate,
    patrimonioTotal: ultFechamento.patrimonio.nav,
    taxaAcertoPct: ultFechamento.eficiencia.taxa_acerto
  };
}

if (require.main === module) {
  processarEstrategiaIFR().catch(err => {
    console.error('❌ Erro fatal no processamento diário IFR:', err);
    process.exit(1);
  });
}

module.exports = {
  processarEstrategiaIFR,
  updateWilderRSI,
  fetchLatestMarketQuotes
};
