/**
 * sync-fiscal-firestore.js
 *
 * Lê `macro_fiscal_cache.json` gerado por `fetch_fiscal_data.py` e grava no Cloud Firestore
 * (Projeto: dashboard-b3-estrategia-448bd) na coleção `macro_fiscal`, documento `governo_central_historico`.
 *
 * Executado diariamente às 03:00 AM BRT no GitHub Actions.
 */

try {
  require('dotenv').config();
} catch (_) {
  // dotenv opcional caso variáveis já estejam no ambiente (GitHub Actions)
}

const fs = require('fs');
const path = require('path');

async function main() {
  const cachePath = path.resolve(__dirname, 'macro_fiscal_cache.json');
  if (!fs.existsSync(cachePath)) {
    throw new Error('Arquivo macro_fiscal_cache.json não encontrado em ' + cachePath);
  }

  const raw = fs.readFileSync(cachePath, 'utf8');
  const payload = JSON.parse(raw);

  if (!payload || !Array.isArray(payload.series) || payload.series.length === 0) {
    throw new Error('Payload de macro_fiscal_cache.json inválido ou vazio.');
  }

  let saKey = process.env.FIREBASE_SERVICE_ACCOUNT_KEY;
  if (!saKey) {
    const defaultSaPath = 'C:/Users/Leo/Downloads/dashboard-b3-estrategia-448bd-firebase-adminsdk-fbsvc-6b53b074cb.json';
    if (fs.existsSync(defaultSaPath)) {
      saKey = defaultSaPath;
    }
  }

  if (!saKey) {
    console.log('ℹ️ FIREBASE_SERVICE_ACCOUNT_KEY não definida no ambiente local. Cache macro_fiscal_cache.json pronto; sincronização com Firestore ocorrerá via GitHub Actions.');
    process.exit(0);
  }

  const admin = require('firebase-admin');
  if (admin.apps.length === 0) {
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
    console.log('✅ Firebase Admin SDK conectado (Projeto: ' + serviceAccount.project_id + ')');
  }

  const db = admin.firestore();
  const docRef = db.collection('macro_fiscal').doc('governo_central_historico');

  await docRef.set({
    updated_at: payload.updated_at,
    schedule_info: payload.schedule_info || 'Atualizado diariamente às 03:00 BRT via GitHub Actions',
    reference_month: payload.reference_month,
    source: payload.source,
    ipca_deflator_factor: payload.ipca_deflator_factor,
    kpis: payload.kpis,
    series: payload.series,
    synced_at_iso: new Date().toISOString()
  }, { merge: true });

  console.log(
    `🔥 Firestore atualizado com sucesso: macro_fiscal/governo_central_historico ` +
    `(${payload.series.length} meses, último: ${payload.reference_month})`
  );
  process.exit(0);
}

main().catch(err => {
  console.error('❌ Erro ao sincronizar macro_fiscal no Firestore:', err.message);
  process.exit(1);
});
