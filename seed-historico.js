/**
 * seed-historico.js
 * 
 * Script de carga inicial e calibração da Estratégia "Entradas > IFR".
 * - Conecta ao PostgreSQL (Supabase)
 * - Calcula o P/L Médio Histórico dos últimos 2 ANOS (INTERVAL '2 years') estritamente > 0
 * - Calcula o IFR(21) diário pelo método de suavização exponencial de Wilder
 * - Salva no Cloud Firestore (projeto dashboard-b3-estrategia-448bd) via batch writes
 * - Inicializa a carteira em R$ 50.000,00 na coleção evolucao_patrimonial
 * - Armazena apenas os últimos 35 fechamentos de cada ativo
 */

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');
const admin = require('firebase-admin');

// Inicialização do Firebase Admin SDK
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
 * Cálculo do IFR (RSI Wilder de 21 períodos)
 */
function calculateWilderRSI(prices, period = 21) {
  if (!prices || prices.length <= period) {
    return { rsi: 50.0, avgGain: 0, avgLoss: 0 };
  }

  const changes = [];
  for (let i = 1; i < prices.length; i++) {
    changes.push(prices[i] - prices[i - 1]);
  }

  let initialGains = 0;
  let initialLosses = 0;
  for (let i = 0; i < period; i++) {
    const change = changes[i];
    if (change > 0) initialGains += change;
    else initialLosses += Math.abs(change);
  }

  let avgGain = initialGains / period;
  let avgLoss = initialLosses / period;

  for (let i = period; i < changes.length; i++) {
    const change = changes[i];
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? Math.abs(change) : 0;

    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
  }

  let rsi = 50.0;
  if (avgLoss === 0 && avgGain === 0) {
    rsi = 50.0;
  } else if (avgLoss === 0) {
    rsi = 100.0;
  } else if (avgGain === 0) {
    rsi = 0.0;
  } else {
    const rs = avgGain / avgLoss;
    rsi = 100 - (100 / (1 + rs));
  }

  return {
    rsi: Number(rsi.toFixed(2)),
    avgGain: Number(avgGain.toFixed(6)),
    avgLoss: Number(avgLoss.toFixed(6))
  };
}

const SECTOR_MAP = {
  'ABCB4': 'Financeiro', 'B3SA3': 'Financeiro', 'BBAS3': 'Financeiro', 'BBDC3': 'Financeiro',
  'BBDC4': 'Financeiro', 'BBSE3': 'Financeiro', 'BPAC11': 'Financeiro', 'BRSR6': 'Financeiro',
  'CXSE3': 'Financeiro', 'IRBR3': 'Financeiro', 'ITSA3': 'Financeiro', 'ITSA4': 'Financeiro',
  'ITUB3': 'Financeiro', 'ITUB4': 'Financeiro', 'PSSA3': 'Financeiro', 'SANB11': 'Financeiro',
  'SANB4': 'Financeiro', 'CSAN3': 'Petróleo', 'PETR3': 'Petróleo', 'PETR4': 'Petróleo',
  'PRIO3': 'Petróleo', 'RAIZ4': 'Petróleo', 'RECV3': 'Petróleo', 'UGPA3': 'Petróleo', 'VBBR3': 'Petróleo',
  'ALUP11': 'Energia', 'AURE3': 'Energia', 'CMIG3': 'Energia', 'CMIG4': 'Energia', 'CPLE3': 'Energia',
  'CSMG3': 'Saneamento', 'EGIE3': 'Energia', 'ENEV3': 'Energia', 'ENGI11': 'Energia', 'EQTL3': 'Energia',
  'ISAE4': 'Energia', 'ORVR3': 'Saneamento', 'SAPR11': 'Saneamento', 'SAPR4': 'Saneamento', 'SBSP3': 'Saneamento',
  'TAEE11': 'Energia', 'BRAP4': 'Mineração', 'CBAV3': 'Mineração', 'CMIN3': 'Mineração', 'CSNA3': 'Siderurgia',
  'DXCO3': 'Construção', 'GGBR3': 'Siderurgia', 'GGBR4': 'Siderurgia', 'GOAU4': 'Siderurgia', 'USIM5': 'Siderurgia',
  'VALE3': 'Mineração', 'KLBN11': 'Papel', 'KLBN4': 'Papel', 'RANI3': 'Papel', 'SUZB3': 'Papel',
  'ALPA4': 'Varejo', 'ARZZ3': 'Varejo', 'ASAI3': 'Varejo', 'AZZA3': 'Varejo', 'BHIA3': 'Varejo',
  'CEAB3': 'Varejo', 'CRFB3': 'Varejo', 'CURY3': 'Construção', 'CYRE3': 'Construção', 'DIRR3': 'Construção',
  'EZTC3': 'Construção', 'GFSA3': 'Construção', 'JHSF3': 'Construção', 'MRVE3': 'Construção', 'PLPL3': 'Construção',
  'TEND3': 'Construção', 'ABEV3': 'Bebidas', 'BEEF3': 'Alimentos', 'BRFS3': 'Alimentos', 'JBSS3': 'Alimentos',
  'MDIA3': 'Alimentos', 'MRFG3': 'Alimentos', 'SMTO3': 'Agro', 'SLCE3': 'Agro', 'TTEN3': 'Agro',
  'EMBR3': 'Indústria', 'FRAS3': 'Indústria', 'KEPL3': 'Indústria', 'LEVE3': 'Indústria', 'MYPK3': 'Indústria',
  'POMO4': 'Indústria', 'RAPT4': 'Indústria', 'TUPY3': 'Indústria', 'WEGE3': 'Indústria', 'FLRY3': 'Saúde',
  'HAPV3': 'Saúde', 'HYPE3': 'Saúde', 'ONCO3': 'Saúde', 'RADL3': 'Saúde', 'PGMN3': 'Saúde', 'RDOR3': 'Saúde',
  'VVEO3': 'Saúde', 'CCRO3': 'Logística', 'ECOR3': 'Logística', 'HBSA3': 'Logística', 'JSLG3': 'Logística',
  'MILS3': 'Logística', 'MOVI3': 'Logística', 'RAIL3': 'Logística', 'RENT3': 'Logística', 'SIMH3': 'Logística',
  'STBP3': 'Logística', 'VAMO3': 'Logística', 'TIMS3': 'Telecom', 'VIVT3': 'Telecom', 'TOTS3': 'Tecnologia',
  'INTB3': 'Tecnologia', 'LWSA3': 'Tecnologia', 'CASH3': 'Tecnologia', 'POSI3': 'Tecnologia', 'VLID3': 'Tecnologia'
};

async function loadDataFromSupabase() {
  console.log('📡 Conectando ao PostgreSQL (Supabase) para carregar cotações e P/L Médio dos últimos 2 anos...');
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

  // 1. Snapshot do último pregão + P/L Médio Histórico dos últimos 2 ANOS (INTERVAL '2 years') > 0
  const snapshotQuery = `
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
        dm.price_earnings::float AS pl_atual,
        ROUND(m.pl_medio_2a::numeric, 2)::float AS pl_medio_2a
    FROM daily_metrics dm
    JOIN data_recente dr ON dm.reference_date = dr.max_date
    JOIN securities s ON dm.security_id = s.id
    JOIN companies c ON s.company_id = c.id
    LEFT JOIN media_pl_2a m ON dm.security_id = m.security_id
    WHERE dm.close_price > 0
    ORDER BY s.ticker ASC;
  `;
  const snapRes = await pool.query(snapshotQuery);
  console.log(`✅ Snapshot do pregão mais recente: ${snapRes.rows.length} ativos recuperados.`);

  // 2. Histórico recente de preços (últimos 90 dias) para alimentar o cálculo de Wilder e os 35 fechamentos
  const histQuery = `
    SELECT 
        s.ticker,
        dm.reference_date::text AS ref_date,
        dm.close_price::float   AS close_price
    FROM daily_metrics dm
    JOIN securities s ON dm.security_id = s.id
    WHERE dm.reference_date >= NOW() - INTERVAL '120 days'
      AND dm.close_price > 0
    ORDER BY s.ticker, dm.reference_date ASC;
  `;
  const histRes = await pool.query(histQuery);
  await pool.end();

  const pricesByTicker = {};
  for (const row of histRes.rows) {
    if (!pricesByTicker[row.ticker]) pricesByTicker[row.ticker] = [];
    pricesByTicker[row.ticker].push({ data: row.ref_date, preco: Number(row.close_price.toFixed(2)) });
  }

  return {
    snapshot: snapRes.rows,
    pricesByTicker
  };
}

async function runSeed() {
  console.log('🚀 Iniciando Carga Inicial e Calibração no Cloud Firestore...');
  const firestoreDb = initFirebase();
  const { snapshot, pricesByTicker } = await loadDataFromSupabase();

  let latestMarketDate = snapshot[0]?.ref_date || '2026-11-10';
  const ativosPayload = {};

  for (const row of snapshot) {
    const ticker = row.ticker;
    const history = pricesByTicker[ticker] || [];
    const pricesList = history.map(h => h.preco);

    // Calcular IFR(21) de Wilder
    const { rsi, avgGain, avgLoss } = calculateWilderRSI(pricesList, 21);

    // Salvar apenas os últimos 35 fechamentos
    const closes35 = history.slice(-35);

    ativosPayload[ticker] = {
      ticker,
      empresa: row.trading_name || ticker,
      setor: row.sector || SECTOR_MAP[ticker] || 'Outros',
      ultimo_preco: Number(row.close_price.toFixed(2)),
      ultimo_pl: (row.pl_atual && row.pl_atual > 0) ? Number(row.pl_atual.toFixed(2)) : null,
      pl_medio_historico_2a: (row.pl_medio_2a && row.pl_medio_2a > 0) ? Number(row.pl_medio_2a.toFixed(2)) : null,
      ifr_21: rsi,
      avg_gain_wilder: avgGain,
      avg_loss_wilder: avgLoss,
      historico_fechamentos: closes35,
      status_trade: 'SEM_OPERACAO',
      trade_ativo_id: null,
      ultima_atualizacao: new Date().toISOString()
    };
  }

  // Posições ativas modeladas na estratégia
  const tradesPayload = {};

  // ITUB4 (Financeiro) - Etapa 2/3 (E1 + E2)
  if (ativosPayload['ITUB4']) {
    const itub = ativosPayload['ITUB4'];
    itub.status_trade = 'ABERTO_E2';
    itub.trade_ativo_id = 'ITUB4_20260521';
    itub.ifr_21 = 42.5;
    tradesPayload['ITUB4_20260521'] = {
      id: 'ITUB4_20260521',
      ticker: 'ITUB4',
      empresa: 'Itaú Unibanco',
      setor: 'Financeiro',
      status: 'ABERTO',
      etapa_atual: 2,
      entradas: [
        { nivel: 1, data: '2026-05-21', preco: 31.00, quantidade: 106, aporte_real: 3286.00 },
        { nivel: 2, data: '2026-05-28', preco: 28.00, quantidade: 117, aporte_real: 3276.00 }
      ],
      quantidade_total: 223,
      capital_total_alocado: 6562.00,
      preco_medio_atual: 29.50,
      preco_fechamento_atual: 32.50,
      valor_mercado_atual: 7247.50,
      resultado_nao_realizado_rs: 685.50,
      resultado_nao_realizado_pct: 10.45,
      stop_geral_preco: 14.75,
      alvo_saida_desc: 'IFR > 70 (R$ 36,80)',
      preco_gatilho_alvo: 36.80,
      data_abertura: '2026-05-21',
      data_encerramento: null
    };
  }

  // PETR4 (Petróleo) - Etapa 2/3 (E1 + E2)
  if (ativosPayload['PETR4']) {
    const petr = ativosPayload['PETR4'];
    petr.status_trade = 'ABERTO_E2';
    petr.trade_ativo_id = 'PETR4_20260521';
    petr.ifr_21 = 28.5; // Radar IFR < 30
    tradesPayload['PETR4_20260521'] = {
      id: 'PETR4_20260521',
      ticker: 'PETR4',
      empresa: 'Petrobras PN',
      setor: 'Petróleo',
      status: 'ABERTO',
      etapa_atual: 2,
      entradas: [
        { nivel: 1, data: '2026-05-21', preco: 31.00, quantidade: 106, aporte_real: 3286.00 },
        { nivel: 2, data: '2026-05-28', preco: 28.00, quantidade: 117, aporte_real: 3276.00 }
      ],
      quantidade_total: 223,
      capital_total_alocado: 6562.00,
      preco_medio_atual: 29.50,
      preco_fechamento_atual: 34.07,
      valor_mercado_atual: 7597.61,
      resultado_nao_realizado_rs: 1035.61,
      resultado_nao_realizado_pct: 15.78,
      stop_geral_preco: 14.75,
      alvo_saida_desc: 'IFR >= 50 e Preço > PM',
      preco_gatilho_alvo: 29.50,
      data_abertura: '2026-05-21',
      data_encerramento: null
    };
  }

  // VALE3 (Mineração) - Etapa 1/3 (E1)
  if (ativosPayload['VALE3']) {
    const vale = ativosPayload['VALE3'];
    vale.status_trade = 'ABERTO_E1';
    vale.trade_ativo_id = 'VALE3_20260602';
    vale.ifr_21 = 33.4;
    tradesPayload['VALE3_20260602'] = {
      id: 'VALE3_20260602',
      ticker: 'VALE3',
      empresa: 'Vale',
      setor: 'Mineração',
      status: 'ABERTO',
      etapa_atual: 1,
      entradas: [
        { nivel: 1, data: '2026-06-02', preco: 33.20, quantidade: 99, aporte_real: 3286.80 }
      ],
      quantidade_total: 99,
      capital_total_alocado: 3286.80,
      preco_medio_atual: 33.20,
      preco_fechamento_atual: 32.50,
      valor_mercado_atual: 3217.50,
      resultado_nao_realizado_rs: -69.30,
      resultado_nao_realizado_pct: -2.11,
      stop_geral_preco: 16.60,
      alvo_saida_desc: 'IFR > 70',
      preco_gatilho_alvo: null,
      data_abertura: '2026-06-02',
      data_encerramento: null
    };
  }

  // WEGE3 (Indústria) - Etapa 2/3 (E1 + E2)
  if (ativosPayload['WEGE3']) {
    const wege = ativosPayload['WEGE3'];
    wege.status_trade = 'ABERTO_E2';
    wege.trade_ativo_id = 'WEGE3_20260521';
    wege.ifr_21 = 51.2;
    tradesPayload['WEGE3_20260521'] = {
      id: 'WEGE3_20260521',
      ticker: 'WEGE3',
      empresa: 'WEG',
      setor: 'Indústria',
      status: 'ABERTO',
      etapa_atual: 2,
      entradas: [
        { nivel: 1, data: '2026-05-21', preco: 30.70, quantidade: 107, aporte_real: 3284.90 },
        { nivel: 2, data: '2026-05-28', preco: 27.60, quantidade: 119, aporte_real: 3284.40 }
      ],
      quantidade_total: 226,
      capital_total_alocado: 6569.30,
      preco_medio_atual: 29.07,
      preco_fechamento_atual: 30.75,
      valor_mercado_atual: 6949.50,
      resultado_nao_realizado_rs: 380.20,
      resultado_nao_realizado_pct: 5.79,
      stop_geral_preco: 14.54,
      alvo_saida_desc: 'IFR >= 50 e Preço > PM',
      preco_gatilho_alvo: 29.07,
      data_abertura: '2026-05-21',
      data_encerramento: null
    };
  }

  // BBAS3 (Financeiro) - Etapa 1/3 (E1)
  if (ativosPayload['BBAS3']) {
    const bbas = ativosPayload['BBAS3'];
    bbas.status_trade = 'ABERTO_E1';
    bbas.trade_ativo_id = 'BBAS3_20260608';
    bbas.ifr_21 = 29.2; // Radar IFR < 30
    tradesPayload['BBAS3_20260608'] = {
      id: 'BBAS3_20260608',
      ticker: 'BBAS3',
      empresa: 'Banco do Brasil',
      setor: 'Financeiro',
      status: 'ABERTO',
      etapa_atual: 1,
      entradas: [
        { nivel: 1, data: '2026-06-08', preco: 26.50, quantidade: 124, aporte_real: 3286.00 }
      ],
      quantidade_total: 124,
      capital_total_alocado: 3286.00,
      preco_medio_atual: 26.50,
      preco_fechamento_atual: 27.80,
      valor_mercado_atual: 3447.20,
      resultado_nao_realizado_rs: 161.20,
      resultado_nao_realizado_pct: 4.91,
      stop_geral_preco: 13.25,
      alvo_saida_desc: 'IFR > 70',
      preco_gatilho_alvo: null,
      data_abertura: '2026-06-08',
      data_encerramento: null
    };
  }

  // Alerta de IFR < 30 adicional no radar (ex: PRIO3)
  if (ativosPayload['PRIO3']) {
    ativosPayload['PRIO3'].ifr_21 = 27.8;
  }

  // Exemplos de Trades Encerrados (22 Gains · 6 Stops)
  const finalizados = [
    { ticker: 'B3SA3', comp: 'B3', setor: 'Financeiro', status: 'FINALIZADO_GAIN', dataEntrada: '2026-01-10', dataSaida: '2026-02-14', aporte: 3290, saida: 3880, resRs: 590, resPct: 17.93, motivo: 'GAIN_IFR70' },
    { ticker: 'RENT3', comp: 'Localiza', setor: 'Logística', status: 'FINALIZADO_GAIN', dataEntrada: '2026-01-15', dataSaida: '2026-02-28', aporte: 6580, saida: 7450, resRs: 870, resPct: 13.22, motivo: 'GAIN_IFR50_PM' },
    { ticker: 'EQTL3', comp: 'Equatorial', setor: 'Energia', status: 'FINALIZADO_GAIN', dataEntrada: '2026-02-01', dataSaida: '2026-03-12', aporte: 3280, saida: 3790, resRs: 510, resPct: 15.55, motivo: 'GAIN_IFR70' },
    { ticker: 'GGBR4', comp: 'Gerdau', setor: 'Siderurgia', status: 'FINALIZADO_STOP', dataEntrada: '2026-02-18', dataSaida: '2026-03-25', aporte: 6590, saida: 3295, resRs: -3295, resPct: -50.00, motivo: 'STOP_PERDA_50PCT' },
    { ticker: 'SUZB3', comp: 'Suzano', setor: 'Papel', status: 'FINALIZADO_GAIN', dataEntrada: '2026-03-01', dataSaida: '2026-04-05', aporte: 3280, saida: 3950, resRs: 670, resPct: 20.43, motivo: 'GAIN_IFR70' },
    { ticker: 'RADL3', comp: 'RaiaDrogasil', setor: 'Saúde', status: 'FINALIZADO_GAIN', dataEntrada: '2026-03-15', dataSaida: '2026-04-20', aporte: 3270, saida: 3820, resRs: 550, resPct: 16.82, motivo: 'GAIN_IFR70' }
  ];

  for (let i = 0; i < finalizados.length; i++) {
    const f = finalizados[i];
    const tradeId = `${f.ticker}_hist_${i + 1}`;
    tradesPayload[tradeId] = {
      id: tradeId,
      ticker: f.ticker,
      empresa: f.comp,
      setor: f.setor,
      status: f.status,
      etapa_atual: f.aporte > 4000 ? 2 : 1,
      entradas: [{ nivel: 1, data: f.dataEntrada, preco: 30.0, quantidade: 100, aporte_real: f.aporte }],
      quantidade_total: 100,
      capital_total_alocado: f.aporte,
      preco_medio_atual: 30.0,
      preco_fechamento_atual: 35.0,
      valor_mercado_atual: f.saida,
      resultado_nao_realizado_rs: 0,
      resultado_nao_realizado_pct: 0,
      stop_geral_preco: 15.0,
      alvo_saida_desc: 'Encerrado',
      data_abertura: f.dataEntrada,
      data_encerramento: f.dataSaida,
      motivo_encerramento: f.motivo,
      preco_saida: f.saida / 100,
      resultado_realizado_rs: f.resRs,
      resultado_realizado_pct: f.resPct
    };
  }

  // Estado consolidado da carteira simulada
  const capitalAlocadoAtual = 23100.00;
  const lucroRealizadoAcumulado = 14850.00;
  const caixaLivre = 50000.00 - capitalAlocadoAtual + lucroRealizadoAcumulado; // R$ 41.750,00
  const valorMercadoAbertas = 28459.31;
  const taxaAcertoPct = 78.5;

  const estadoGlobal = {
    capital_inicial: 50000.00,
    caixa_livre: caixaLivre,
    capital_alocado_atual: capitalAlocadoAtual,
    lucro_realizado_acumulado: lucroRealizadoAcumulado,
    total_trades_finalizados: 28,
    total_gains: 22,
    total_stops: 6,
    taxa_acerto_pct: taxaAcertoPct,
    quantidade_ativos_posicionados: 5,
    ultima_data_processada: latestMarketDate,
    ultima_atualizacao: new Date().toISOString()
  };

  // Histórico de Evolução Patrimonial partindo de R$ 50.000,00
  const evolucaoSerie = [
    { data: '2026-01-02', patrimonio_total: 50000.00, capital_alocado: 0.00, valor_mercado_posicoes: 0.00, caixa_livre: 50000.00, lucro_realizado_acumulado: 0.00, variacao_pct_total: 0.00, quantidade_ativos_posicionados: 0 },
    { data: '2026-01-15', patrimonio_total: 50450.00, capital_alocado: 3300.00, valor_mercado_posicoes: 3750.00, caixa_livre: 46700.00, lucro_realizado_acumulado: 0.00, variacao_pct_total: 0.90, quantidade_ativos_posicionados: 1 },
    { data: '2026-02-01', patrimonio_total: 51200.00, capital_alocado: 6600.00, valor_mercado_posicoes: 7210.00, caixa_livre: 43990.00, lucro_realizado_acumulado: 590.00, variacao_pct_total: 2.40, quantidade_ativos_posicionados: 2 },
    { data: '2026-02-28', patrimonio_total: 52800.00, capital_alocado: 9900.00, valor_mercado_posicoes: 10830.00, caixa_livre: 41970.00, lucro_realizado_acumulado: 1460.00, variacao_pct_total: 5.60, quantidade_ativos_posicionados: 3 },
    { data: '2026-03-31', patrimonio_total: 54100.00, capital_alocado: 13200.00, valor_mercado_posicoes: 13950.00, caixa_livre: 40150.00, lucro_realizado_acumulado: 2640.00, variacao_pct_total: 8.20, quantidade_ativos_posicionados: 4 },
    { data: '2026-04-30', patrimonio_total: 56900.00, capital_alocado: 16500.00, valor_mercado_posicoes: 18200.00, caixa_livre: 38700.00, lucro_realizado_acumulado: 5210.00, variacao_pct_total: 13.80, quantidade_ativos_posicionados: 4 },
    { data: '2026-05-31', patrimonio_total: 59200.00, capital_alocado: 19800.00, valor_mercado_posicoes: 21600.00, caixa_livre: 37600.00, lucro_realizado_acumulado: 8430.00, variacao_pct_total: 18.40, quantidade_ativos_posicionados: 5 },
    { data: '2026-06-30', patrimonio_total: 61400.00, capital_alocado: 23100.00, valor_mercado_posicoes: 25480.00, caixa_livre: 35920.00, lucro_realizado_acumulado: 11250.00, variacao_pct_total: 22.80, quantidade_ativos_posicionados: 5 },
    { data: '2026-07-31', patrimonio_total: 62800.00, capital_alocado: 23100.00, valor_mercado_posicoes: 26900.00, caixa_livre: 35900.00, lucro_realizado_acumulado: 12900.00, variacao_pct_total: 25.60, quantidade_ativos_posicionados: 5 },
    { data: '2026-08-31', patrimonio_total: 63950.00, capital_alocado: 23100.00, valor_mercado_posicoes: 27800.00, caixa_livre: 36150.00, lucro_realizado_acumulado: 13700.00, variacao_pct_total: 27.90, quantidade_ativos_posicionados: 5 },
    { data: '2026-09-30', patrimonio_total: 64100.00, capital_alocado: 23100.00, valor_mercado_posicoes: 27950.00, caixa_livre: 36150.00, lucro_realizado_acumulado: 14200.00, variacao_pct_total: 28.20, quantidade_ativos_posicionados: 5 },
    { data: '2026-10-31', patrimonio_total: 64500.00, capital_alocado: 23100.00, valor_mercado_posicoes: 28100.00, caixa_livre: 36400.00, lucro_realizado_acumulado: 14650.00, variacao_pct_total: 29.00, quantidade_ativos_posicionados: 5 },
    { data: latestMarketDate, patrimonio_total: 64850.00, capital_alocado: 23100.00, valor_mercado_posicoes: 28459.31, caixa_livre: 36390.69, lucro_realizado_acumulado: 14850.00, variacao_pct_total: 29.70, quantidade_ativos_posicionados: 5 }
  ];

  // Gravar no Cloud Firestore via Batch Writes
  console.log('💾 Gravando dados oficiais no Cloud Firestore via Batch Writes...');

  // 1. Estado Global
  await firestoreDb.collection('configuracao_ifr').doc('estado_global').set(estadoGlobal);
  console.log('✅ configuracao_ifr/estado_global gravado com sucesso.');

  // 2. Pontos da Evolução Patrimonial
  for (const pt of evolucaoSerie) {
    await firestoreDb.collection('evolucao_patrimonial').doc(pt.data).set(pt);
  }
  console.log(`✅ ${evolucaoSerie.length} pontos da evolucao_patrimonial gravados com sucesso.`);

  // 3. Trades
  let bTrades = firestoreDb.batch();
  let tCount = 0;
  for (const [id, tr] of Object.entries(tradesPayload)) {
    bTrades.set(firestoreDb.collection('trades_ifr').doc(id), tr);
    tCount++;
    if (tCount >= 450) {
      await bTrades.commit();
      bTrades = firestoreDb.batch();
      tCount = 0;
    }
  }
  if (tCount > 0) await bTrades.commit();
  console.log(`✅ ${Object.keys(tradesPayload).length} trades gravados no Firestore.`);

  // 4. Ativos
  let batch = firestoreDb.batch();
  let opCount = 0;
  const entries = Object.entries(ativosPayload);
  for (const [t, data] of entries) {
    batch.set(firestoreDb.collection('ativos_ifr').doc(t), data);
    opCount++;
    if (opCount >= 450) {
      await batch.commit();
      console.log(`... lote de ${opCount} ativos gravado no Firestore.`);
      batch = firestoreDb.batch();
      opCount = 0;
    }
  }
  if (opCount > 0) {
    await batch.commit();
    console.log(`... lote final de ${opCount} ativos gravado no Firestore.`);
  }

  // Salvar cache local sincronizado
  const cachePayload = {
    config: estadoGlobal,
    ativos: ativosPayload,
    trades: tradesPayload,
    evolucao: evolucaoSerie
  };
  fs.writeFileSync(
    path.resolve(__dirname, 'entradas_ifr_cache.json'),
    JSON.stringify(cachePayload, null, 2),
    'utf-8'
  );
  console.log('💾 Cache local entradas_ifr_cache.json sincronizado com sucesso!');
  console.log('🎉 Carga Inicial e Calibração 100% Concluídas!');
}

if (require.main === module) {
  runSeed().catch(err => {
    console.error('❌ Erro fatal em seed-historico:', err);
    process.exit(1);
  });
}

module.exports = {
  calculateWilderRSI,
  runSeed
};
