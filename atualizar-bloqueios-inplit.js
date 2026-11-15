/**
 * atualizar-bloqueios-inplit.js
 *
 * Rotina semanal (executada todo sábado à tarde via GitHub Actions no Atualizador)
 * que sincroniza a coleção `bloqueios_inplit_ifr` no Cloud Firestore.
 *
 * Regra:
 * - Consulta no Supabase eventos de inplit / grupamento de ações (`corporate_actions`
 *   e `b3_corporate_events_cache`).
 * - Calcula a última data de inplit por ticker e a data de desbloqueio (+2 anos).
 * - Mantém em `bloqueios_inplit_ifr/{ticker}` todas as empresas ainda dentro do
 *   período de restrição (`bloqueado_ate >= refDate`) e remove as já liberadas.
 * - Atualiza `teve_inplit_2a` e `bloqueado_inplit_ate` em `ativos_ifr` e no cache local.
 */

require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { Pool } = require('pg');
const admin = require('firebase-admin');

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
    const candidatePaths = [
      'C:/Users/Leo/Downloads/dashboard-b3-estrategia-448bd-firebase-adminsdk-fbsvc-5bb3e42123.json',
      'C:/Users/Leo/Downloads/dashboard-b3-estrategia-448bd-firebase-adminsdk-fbsvc-6b53b074cb.json'
    ];
    saKey = candidatePaths.find(p => fs.existsSync(p));
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
 * Soma exatos 2 anos a uma data ISO ('YYYY-MM-DD'), ajustando 29/02 para 28/02 em anos não bissextos.
 */
function addTwoYears(isoDate) {
  const [yStr, mStr, dStr] = isoDate.split('-');
  const year = Number(yStr) + 2;
  let day = Number(dStr);
  if (mStr === '02' && day === 29) {
    const isLeap = (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
    if (!isLeap) day = 28;
  }
  return `${String(year).padStart(4, '0')}-${mStr}-${String(day).padStart(2, '0')}`;
}

/**
 * Converte data 'DD/MM/YYYY' para 'YYYY-MM-DD'.
 */
function brDateToIso(brDate) {
  if (!brDate || typeof brDate !== 'string') return null;
  const parts = brDate.trim().split('/');
  if (parts.length !== 3) return null;
  const [dd, mm, yyyy] = parts;
  if (!dd || !mm || !yyyy || yyyy.length !== 4) return null;
  return `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;
}

/**
 * Converte string de proporção (ex: '20:1' ou '1:80') para fator multiplicador numérico.
 */
function parseRatioFactor(ratioStr) {
  if (!ratioStr || typeof ratioStr !== 'string') return null;
  const parts = ratioStr.split(':').map(p => Number(p.trim().replace(',', '.')));
  if (parts.length !== 2 || !parts[0] || !parts[1] || isNaN(parts[0]) || isNaN(parts[1])) {
    return null;
  }
  return parts[1] / parts[0];
}

/**
 * Formata fator multiplicador (< 1) para proporção legível (ex: 0.5 -> '2:1', 0.0667 -> '15:1').
 */
function formatMultiplierToRatio(mult) {
  if (!mult || mult <= 0 || mult >= 1) return null;
  const inv = Math.round(1 / mult);
  if (Math.abs(1 / inv - mult) < 0.002) {
    return `${inv}:1`;
  }
  return `${Number((1 / mult).toFixed(2))}:1`;
}

async function fetchActiveInplits() {
  console.log('📡 Consultando eventos de inplit/grupamento no Supabase...');
  const pool = createPgPool();

  try {
    const refRes = await pool.query(`
      SELECT COALESCE(MAX(reference_date), CURRENT_DATE)::text AS ref_date
      FROM daily_metrics;
    `);
    const refDate = refRes.rows[0]?.ref_date || new Date().toISOString().slice(0, 10);

    // 1. Eventos confirmados em corporate_actions
    const caRes = await pool.query(`
      SELECT
        s.ticker,
        comp.trading_name,
        c.effective_date::text AS effective_date,
        c.share_multiplier::float AS share_multiplier,
        c.description
      FROM corporate_actions c
      JOIN securities s ON s.id = c.security_id
      LEFT JOIN companies comp ON s.company_id = comp.id
      WHERE (c.share_multiplier < 1.0 OR c.event_type = 'REVERSE_SPLIT')
        AND COALESCE(UPPER(c.status), '') NOT IN ('CANCELLED', 'CANCELADO', 'REJECTED')
      ORDER BY c.effective_date ASC;
    `);

    // 2. Complemento via b3_corporate_events_cache (captura ativos como GFSA3 sem linha em corporate_actions)
    const cacheRes = await pool.query(`
      SELECT
        b.ticker,
        comp.trading_name,
        b.inplits,
        b.splits
      FROM b3_corporate_events_cache b
      LEFT JOIN securities s ON s.ticker = b.ticker
      LEFT JOIN companies comp ON s.company_id = comp.id
      WHERE b.inplits IS NOT NULL
        AND jsonb_array_length(b.inplits) > 0;
    `);

    const latestByTicker = {};

    const registerCandidate = ({ ticker, empresa, dataInplit, fator, proporcao, descricao, source }) => {
      if (!ticker || !dataInplit) return;
      const existing = latestByTicker[ticker];
      if (!existing) {
        latestByTicker[ticker] = {
          ticker,
          empresa: empresa || ticker,
          dataUltimoInplit: dataInplit,
          fatorMultiplicador: fator,
          proporcao: proporcao || formatMultiplierToRatio(fator) || '',
          descricao: descricao || '',
          source
        };
        return;
      }

      // Se for data estritamente mais recente (incluindo effective_date 1-5 dias após date_com do mesmo evento),
      // preserva os metadados mais ricos quando disponível
      if (dataInplit > existing.dataUltimoInplit) {
        latestByTicker[ticker] = {
          ticker,
          empresa: empresa || existing.empresa || ticker,
          dataUltimoInplit: dataInplit,
          fatorMultiplicador: fator || existing.fatorMultiplicador,
          proporcao: proporcao || existing.proporcao || formatMultiplierToRatio(fator) || '',
          descricao: descricao || existing.descricao || '',
          source
        };
      } else if (dataInplit === existing.dataUltimoInplit) {
        if (!existing.empresa || existing.empresa === ticker) {
          existing.empresa = empresa || existing.empresa;
        }
        if (!existing.proporcao && proporcao) {
          existing.proporcao = proporcao;
        }
      }
    };

    for (const row of caRes.rows) {
      const fator = row.share_multiplier ? Number(Number(row.share_multiplier).toFixed(6)) : null;
      registerCandidate({
        ticker: row.ticker,
        empresa: row.trading_name,
        dataInplit: row.effective_date,
        fator,
        proporcao: formatMultiplierToRatio(fator),
        descricao: row.description || `Grupamento ${formatMultiplierToRatio(fator) || ''}`.trim(),
        source: 'corporate_actions'
      });
    }

    for (const row of cacheRes.rows) {
      const inplits = Array.isArray(row.inplits) ? row.inplits : [];
      const splits = Array.isArray(row.splits) ? row.splits : [];

      for (const inp of inplits) {
        const tipo = String(inp?.type || 'GRUPAMENTO').toUpperCase();
        if (tipo !== 'GRUPAMENTO') continue;

        const isoDate = brDateToIso(inp.date_com);
        if (!isoDate) continue;

        const inpFactor = parseRatioFactor(inp.ratio);
        // Ignora operações simultâneas neutras ou com efeito líquido de split (ex: VIVT3 40:1 + 1:80; TIMS3 100:1 + 1:100)
        const sameDaySplits = splits.filter(sp => brDateToIso(sp?.date_com) === isoDate);
        let netFactor = inpFactor;
        if (netFactor !== null && sameDaySplits.length > 0) {
          for (const sp of sameDaySplits) {
            const spFactor = parseRatioFactor(sp?.ratio);
            if (spFactor !== null) {
              netFactor *= spFactor;
            }
          }
          if (netFactor >= 1.0) {
            continue;
          }
        }

        // Evita sobrescrever com date_com um evento recente já registrado por effective_date em corporate_actions
        const existing = latestByTicker[row.ticker];
        if (existing && existing.source === 'corporate_actions') {
          const diffDays = Math.abs(
            (new Date(existing.dataUltimoInplit + 'T00:00:00Z') - new Date(isoDate + 'T00:00:00Z')) / 86400000
          );
          if (diffDays <= 10) {
            if (!existing.proporcao && inp.ratio) existing.proporcao = inp.ratio;
            if (!existing.empresa && row.trading_name) existing.empresa = row.trading_name;
            continue;
          }
        }

        const effectiveFator = netFactor !== null ? Number(netFactor.toFixed(6)) : inpFactor;
        registerCandidate({
          ticker: row.ticker,
          empresa: row.trading_name,
          dataInplit: isoDate,
          fator: effectiveFator,
          proporcao: inp.ratio || formatMultiplierToRatio(effectiveFator),
          descricao: inp.description || `Grupamento ${inp.ratio || ''}`.trim(),
          source: 'b3_corporate_events_cache'
        });
      }
    }

    const bloqueiosVigentes = {};
    for (const [ticker, info] of Object.entries(latestByTicker)) {
      const bloqueadoAte = addTwoYears(info.dataUltimoInplit);
      if (bloqueadoAte >= refDate) {
        bloqueiosVigentes[ticker] = {
          ticker,
          empresa: info.empresa || ticker,
          dataUltimoInplit: info.dataUltimoInplit,
          bloqueadoAte,
          fatorMultiplicador: info.fatorMultiplicador,
          proporcao: info.proporcao,
          descricao: info.descricao
        };
      }
    }

    return { refDate, bloqueiosVigentes };
  } finally {
    await pool.end();
  }
}

async function atualizarBloqueiosInplit() {
  console.log('🛡️ Iniciando sincronização semanal de bloqueios por Inplit/Grupamento (IFR)...');
  const firestoreDb = initFirebase();
  const { refDate, bloqueiosVigentes } = await fetchActiveInplits();

  console.log(`📅 Data de referência do mercado: ${refDate}`);
  const vigentesList = Object.values(bloqueiosVigentes).sort((a, b) =>
    a.bloqueadoAte.localeCompare(b.bloqueadoAte)
  );
  console.log(`⛔ Empresas com bloqueio vigente (${vigentesList.length}):`);
  for (const b of vigentesList) {
    console.log(`   - ${b.ticker} (${b.empresa}): último inplit em ${b.dataUltimoInplit} (${b.proporcao}) → bloqueada até ${b.bloqueadoAte}`);
  }

  // Ler estado atual da coleção bloqueios_inplit_ifr e ativos_ifr no Firestore
  const bloqSnap = await firestoreDb.collection('bloqueios_inplit_ifr').get();
  const ativosSnap = await firestoreDb.collection('ativos_ifr').get();

  const existingBloqIds = new Set();
  bloqSnap.forEach(doc => existingBloqIds.add(doc.id));

  const ops = [];
  const nowIso = new Date().toISOString();

  // Gravar/atualizar bloqueios vigentes
  for (const info of vigentesList) {
    const docRef = firestoreDb.collection('bloqueios_inplit_ifr').doc(info.ticker);
    ops.push(batch => batch.set(docRef, {
      ticker: info.ticker,
      empresa: info.empresa,
      data_ultimo_inplit: info.dataUltimoInplit,
      bloqueado_ate: info.bloqueadoAte,
      fator_multiplicador: info.fatorMultiplicador,
      proporcao: info.proporcao,
      descricao: info.descricao,
      ativo: true,
      updated_at: nowIso
    }));
  }

  // Remover bloqueios expirados ou inexistentes no mapa vigente
  let removidosCount = 0;
  for (const id of existingBloqIds) {
    if (!bloqueiosVigentes[id]) {
      const docRef = firestoreDb.collection('bloqueios_inplit_ifr').doc(id);
      ops.push(batch => batch.delete(docRef));
      removidosCount++;
      console.log(`🔓 Liberado de bloqueio (expirado/removido): ${id}`);
    }
  }

  // Sincronizar flags nos documentos existentes de ativos_ifr
  ativosSnap.forEach(doc => {
    const data = doc.data();
    const bloq = bloqueiosVigentes[doc.id];
    const deveBloquear = Boolean(bloq);
    const ateAlvo = bloq ? bloq.bloqueadoAte : null;

    if (Boolean(data.teve_inplit_2a) !== deveBloquear || (data.bloqueado_inplit_ate || null) !== ateAlvo) {
      ops.push(batch => batch.update(doc.ref, {
        teve_inplit_2a: deveBloquear,
        bloqueado_inplit_ate: ateAlvo
      }));
    }
  });

  // Executar batches no Firestore respeitando limite de 450 operações por batch
  let batch = firestoreDb.batch();
  let count = 0;
  for (const applyOp of ops) {
    applyOp(batch);
    count++;
    if (count >= 450) {
      await batch.commit();
      batch = firestoreDb.batch();
      count = 0;
    }
  }
  if (count > 0) {
    await batch.commit();
  }

  console.log(`✅ Firestore sincronizado: ${vigentesList.length} bloqueio(s) ativo(s), ${removidosCount} removido(s).`);

  // Atualizar cache local entradas_ifr_cache.json se existir
  const cachePath = path.resolve(__dirname, 'entradas_ifr_cache.json');
  if (fs.existsSync(cachePath)) {
    const cache = JSON.parse(fs.readFileSync(cachePath, 'utf-8'));
    const bloqueiosMap = {};
    for (const info of vigentesList) {
      bloqueiosMap[info.ticker] = {
        ticker: info.ticker,
        empresa: info.empresa,
        data_ultimo_inplit: info.dataUltimoInplit,
        bloqueado_ate: info.bloqueadoAte,
        proporcao: info.proporcao
      };
    }
    cache.bloqueios_inplit = bloqueiosMap;

    if (cache.ativos && typeof cache.ativos === 'object') {
      for (const [ticker, ativo] of Object.entries(cache.ativos)) {
        const bloq = bloqueiosVigentes[ticker];
        ativo.teve_inplit_2a = Boolean(bloq);
        ativo.bloqueado_inplit_ate = bloq ? bloq.bloqueadoAte : null;
      }
    }

    fs.writeFileSync(cachePath, JSON.stringify(cache, null, 2), 'utf-8');
    console.log('💾 entradas_ifr_cache.json atualizado com bloqueios_inplit e flags de ativos.');
  }

  return { refDate, bloqueiosVigentes, removidosCount };
}

if (require.main === module) {
  atualizarBloqueiosInplit().catch(err => {
    console.error('❌ Erro fatal na sincronização semanal de bloqueios por inplit:', err);
    process.exit(1);
  });
}

module.exports = {
  atualizarBloqueiosInplit,
  fetchActiveInplits,
  addTwoYears
};
