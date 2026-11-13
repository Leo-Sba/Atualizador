/**
 * Carregador de dados de mercado para o motor contábil (somente leitura no Supabase).
 * Consultas leves e filtradas: apenas os tickers que a carteira operou e apenas
 * o intervalo de datas necessário.
 */
'use strict';

const isoDate = v => (v instanceof Date ? new Date(v.getTime() - v.getTimezoneOffset() * 60000).toISOString().slice(0, 10) : String(v).slice(0, 10));

/**
 * @returns {Promise<{calendario:string[], precos:Object, ibov:Object, proventos:Array, eventos:Array}>}
 */
async function carregarDadosMercado(pool, { tickers, dataInicio, dataFim = null }) {
  const lista = [...new Set(tickers)];
  const params = [lista, dataInicio];
  const filtroFim = dataFim ? 'AND p.price_date <= $3' : '';
  if (dataFim) params.push(dataFim);

  const rPrecos = await pool.query(`
    SELECT s.ticker, p.price_date, p.close_price
    FROM daily_prices p JOIN securities s ON s.id = p.security_id
    WHERE s.ticker = ANY($1) AND p.price_date >= $2 ${filtroFim} AND p.close_price > 0
    ORDER BY p.price_date`, params);

  const precos = {};
  rPrecos.rows.forEach(r => {
    const d = isoDate(r.price_date);
    (precos[d] = precos[d] || {})[r.ticker] = Number(r.close_price);
  });

  // Calendário de pregões: datas com cotação; se a carteira ainda não tiver tickers, usa o IBOV
  const rIbov = await pool.query(`
    SELECT reference_date, ibov_close FROM ibov_daily_consolidated
    WHERE reference_date >= $1 ${dataFim ? 'AND reference_date <= $2' : ''} AND ibov_close > 0
    ORDER BY reference_date`, dataFim ? [dataInicio, dataFim] : [dataInicio]);
  const ibov = {};
  rIbov.rows.forEach(r => { ibov[isoDate(r.reference_date)] = Number(r.ibov_close); });

  const calendario = [...new Set([...Object.keys(precos)])].sort();

  const rProv = await pool.query(`
    SELECT s.ticker, d.ex_date, d.payment_date, d.distribution_type, d.gross_amount_per_share
    FROM shareholder_distributions d JOIN securities s ON s.id = d.security_id
    WHERE s.ticker = ANY($1) AND d.ex_date >= $2 ${dataFim ? 'AND d.ex_date <= $3' : ''}
      AND d.gross_amount_per_share > 0
    ORDER BY d.ex_date`, params);
  const proventos = rProv.rows.map(r => ({
    ticker: r.ticker,
    data_ex: isoDate(r.ex_date),
    data_pagamento: r.payment_date ? isoDate(r.payment_date) : null,
    tipo: /JCP|INTEREST/i.test(r.distribution_type || '') ? 'JCP' : 'DIVIDEND',
    valor_por_acao: Number(r.gross_amount_per_share)
  }));

  const rEv = await pool.query(`
    SELECT s.ticker, c.effective_date, c.share_multiplier, c.event_type, c.description, c.status
    FROM corporate_actions c JOIN securities s ON s.id = c.security_id
    WHERE s.ticker = ANY($1) AND c.effective_date >= $2 ${dataFim ? 'AND c.effective_date <= $3' : ''}
      AND c.share_multiplier IS NOT NULL AND c.share_multiplier > 0 AND c.share_multiplier <> 1
      AND COALESCE(UPPER(c.status), '') NOT IN ('CANCELLED', 'CANCELADO', 'REJECTED')
    ORDER BY c.effective_date`, params);
  const eventos = rEv.rows.map(r => ({
    ticker: r.ticker,
    data: isoDate(r.effective_date),
    multiplicador: Number(r.share_multiplier),
    descricao: `${r.event_type || 'Evento'} ${r.ticker} (fator ${Number(r.share_multiplier)})${r.description ? ' - ' + r.description : ''}`
  }));

  return { calendario, precos, ibov, proventos, eventos };
}

module.exports = { carregarDadosMercado, isoDate };
