import { JsonComponent, escapeHtml, lcIcon } from './lightning-components.js';

const colors = ['#0176d3', '#9050e9', '#2e844a', '#fe9339', '#0b827c'];

function compactCurrency(value, currency = 'EUR') {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
    notation: 'compact',
    maximumFractionDigits: 2,
  }).format(Number(value) || 0);
}

function polyline(values, width, height, padding = 4) {
  const numeric = values.filter(value => value != null).map(Number);
  const min = Math.min(...numeric, 0);
  const max = Math.max(...numeric, 1);
  const range = Math.max(1, max - min);
  return values.map((value, index) => value == null ? null : `${padding + index * ((width - padding * 2) / Math.max(1, values.length - 1))},${height - padding - ((Number(value) - min) / range) * (height - padding * 2)}`);
}

class LcDashboardHeader extends JsonComponent {
  render() {
    const data = this.data;
    const actions = (data.actions || []).map(action => `<button class="lc-button ${action.primary ? 'lc-button--brand' : ''}" type="button" data-dashboard-action="${escapeHtml(action.action)}">${escapeHtml(action.label)}</button>`).join('');
    this.innerHTML = `<section class="lc-dashboard-header" aria-labelledby="dashboard-page-title"><div class="lc-dashboard-header__icon">${lcIcon('trend')}</div><div><span>${escapeHtml(data.eyebrow || 'Analytics')}</span><h1 id="dashboard-page-title">${escapeHtml(data.title || 'Executive Dashboard')}</h1><p>${escapeHtml(data.subtitle || '')}</p></div><div class="lc-dashboard-header__actions"><small>${escapeHtml(data.updated || '')}</small>${actions}</div></section>`;
    this.querySelectorAll('[data-dashboard-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.dashboardAction)));
  }
}

class LcMetricSparklines extends JsonComponent {
  render() {
    const data = this.data;
    const cards = (data.items || []).map(item => {
      const points = polyline(item.values || [], 150, 42, 3).filter(Boolean).join(' ');
      const directionClass = item.direction === 'down' ? 'is-down' : 'is-up';
      return `<article class="lc-spark-kpi"><span class="lc-spark-kpi__label">${escapeHtml(item.label)}</span><div><strong>${escapeHtml(item.value)}</strong><span class="lc-spark-kpi__change ${directionClass}">${item.direction === 'down' ? '↓' : '↑'} ${escapeHtml(item.change)}</span></div><span class="lc-spark-kpi__context">${escapeHtml(item.context || '')}</span><svg viewBox="0 0 150 42" role="img" aria-label="${escapeHtml(`${item.label} trend`)}"><polyline points="${points}" fill="none" stroke="${item.direction === 'down' ? '#fe9339' : '#0176d3'}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg></article>`;
    }).join('');
    this.innerHTML = `<section aria-label="${escapeHtml(data.title || 'Key metrics')}"><h2 class="lc-sr-only">${escapeHtml(data.title || 'Key metrics')}</h2><div class="lc-spark-kpis">${cards}</div></section>`;
  }
}

class LcRevenueTrend extends JsonComponent {
  render() {
    const data = this.data;
    const allValues = [...(data.target || []), ...(data.series || []).flatMap(series => series.values || [])].filter(value => value != null).map(Number);
    const max = Math.max(...allValues, 1) * 1.08;
    const labels = data.labels || [];
    const x = index => 55 + index * (670 / Math.max(1, labels.length - 1));
    const y = value => 245 - Number(value) / max * 195;
    const targetPoints = (data.target || []).map((value, index) => `${x(index)},${y(value)}`).join(' ');
    const seriesLines = (data.series || []).map((series, seriesIndex) => {
      const segments = [];
      let active = [];
      (series.values || []).forEach((value, index) => {
        if (value == null) {
          if (active.length) segments.push(active);
          active = [];
        } else active.push(`${x(index)},${y(value)}`);
      });
      if (active.length) segments.push(active);
      return segments.map(segment => `<polyline points="${segment.join(' ')}" fill="none" stroke="${escapeHtml(series.color || colors[seriesIndex])}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>`).join('');
    }).join('');
    const xLabels = labels.map((label, index) => `<text x="${x(index)}" y="274" text-anchor="middle">${escapeHtml(label)}</text>`).join('');
    const yGrid = [0, .25, .5, .75, 1].map(ratio => `<path d="M55 ${245 - ratio * 195}H725"/><text x="45" y="${249 - ratio * 195}" text-anchor="end">${Math.round(max * ratio)}${escapeHtml(data.currency || '')}</text>`).join('');
    const legend = [`<span><i style="background:#747474"></i>Target</span>`, ...(data.series || []).map((series, index) => `<span><i style="background:${escapeHtml(series.color || colors[index])}"></i>${escapeHtml(series.label)}</span>`)].join('');
    this.innerHTML = panel(data, `<div class="lc-revenue-trend" role="img" aria-label="${escapeHtml(data.title || 'Revenue trend')}"><svg viewBox="0 0 780 295"><g class="grid">${yGrid}</g><polyline points="${targetPoints}" fill="none" stroke="#747474" stroke-width="2" stroke-dasharray="7 6"/>${seriesLines}<g class="axis-labels">${xLabels}</g></svg><div class="lc-chart-legend">${legend}</div></div>`);
  }
}

class LcSalesFunnel extends JsonComponent {
  render() {
    const data = this.data;
    const stages = data.stages || [];
    const max = Math.max(1, ...stages.map(stage => Number(stage.amount)));
    const markup = stages.map((stage, index) => {
      const width = 48 + Number(stage.amount) / max * 52;
      return `<button class="lc-funnel-stage" type="button" style="width:${width}%;--funnel-color:${colors[index % colors.length]}" data-funnel-stage="${index}"><span><strong>${escapeHtml(stage.label)}</strong><small>${escapeHtml(stage.count)} opportunities</small></span><strong>${compactCurrency(stage.amount, data.currency || 'EUR')}</strong><span>${escapeHtml(stage.conversion)}%</span></button>`;
    }).join('');
    this.innerHTML = panel(data, `<div class="lc-sales-funnel">${markup}</div>`);
    this.querySelectorAll('[data-funnel-stage]').forEach(button => button.addEventListener('click', () => this.emitAction('funnel-stage-select', { index: Number(button.dataset.funnelStage), stage: stages[Number(button.dataset.funnelStage)] })));
  }
}

class LcTeamAttainment extends JsonComponent {
  render() {
    const data = this.data;
    const teams = data.teams || [];
    const rows = teams.map((team, index) => `<button class="lc-attainment-row" type="button" data-team="${index}"><span class="lc-avatar lc-avatar--small">${escapeHtml(team.initials)}</span><span><strong>${escapeHtml(team.name)}</strong><small>${escapeHtml(team.region)}</small></span><span class="lc-attainment-track"><i style="width:${Math.min(100, Number(team.attainment))}%"></i><b style="left:100%"></b></span><strong>${escapeHtml(team.attainment)}%</strong><span><small>Commit</small><strong>${compactCurrency(team.commit)}</strong></span></button>`).join('');
    this.innerHTML = panel(data, `<div class="lc-team-attainment">${rows}</div>`);
    this.querySelectorAll('[data-team]').forEach(button => button.addEventListener('click', () => this.emitAction('dashboard-team-select', { index: Number(button.dataset.team), team: teams[Number(button.dataset.team)] })));
  }
}

class LcPipelineVelocity extends JsonComponent {
  render() {
    const data = this.data;
    const max = Math.max(1, ...((data.stages || []).flatMap(stage => [Number(stage.days), Number(stage.benchmark)]))) * 1.18;
    const rows = (data.stages || []).map(stage => `<div class="lc-velocity-row"><span>${escapeHtml(stage.label)}</span><div><i style="width:${Number(stage.days) / max * 100}%"></i><b style="left:${Number(stage.benchmark) / max * 100}%" title="Benchmark: ${escapeHtml(stage.benchmark)} days"></b></div><strong class="${Number(stage.days) > Number(stage.benchmark) ? 'is-risk' : ''}">${escapeHtml(stage.days)}d</strong></div>`).join('');
    const summary = data.summary || {};
    this.innerHTML = panel(data, `<div class="lc-velocity"><div class="lc-velocity__summary"><strong>${escapeHtml(summary.value)}</strong><span>${escapeHtml(summary.label)}</span><small>${escapeHtml(summary.change)}</small></div><div>${rows}<div class="lc-velocity-legend"><span><i></i>Actual</span><span><b></b>Benchmark</span></div></div></div>`);
  }
}

class LcWinRateHeatmap extends JsonComponent {
  render() {
    const data = this.data;
    const columns = data.columns || [];
    const header = columns.map(column => `<span>${escapeHtml(column)}</span>`).join('');
    const rows = (data.rows || []).map((row, rowIndex) => `<div class="lc-heatmap-row"><strong>${escapeHtml(row.label)}</strong>${(row.values || []).map((value, columnIndex) => `<button type="button" style="--heat:${Math.min(1, Number(value) / 50)}" data-heatmap="${rowIndex}:${columnIndex}" aria-label="${escapeHtml(`${row.label}, ${columns[columnIndex]}: ${value}% win rate`)}">${escapeHtml(value)}%</button>`).join('')}</div>`).join('');
    this.innerHTML = panel(data, `<div class="lc-heatmap"><div class="lc-heatmap-header"><span></span>${header}</div>${rows}<div class="lc-heatmap-scale"><span>Lower</span><i></i><i></i><i></i><i></i><i></i><span>Higher</span></div></div>`);
    this.querySelectorAll('[data-heatmap]').forEach(button => button.addEventListener('click', () => this.emitAction('heatmap-select', { cell: button.dataset.heatmap, label: button.getAttribute('aria-label') })));
  }
}

class LcRevenueWaterfall extends JsonComponent {
  render() {
    const data = this.data;
    const items = data.items || [];
    let running = 0;
    const states = items.map(item => {
      const before = running;
      if (item.type === 'total') running = Number(item.value);
      else running += Number(item.value);
      return { ...item, before, after: running };
    });
    const max = Math.max(1, ...states.flatMap(item => [item.before, item.after]));
    const chartHeight = 190;
    const barWidth = 68;
    const gap = 28;
    const baseY = 220;
    const y = value => baseY - Number(value) / max * chartHeight;
    const bars = states.map((item, index) => {
      const x = 38 + index * (barWidth + gap);
      const start = item.type === 'total' ? 0 : Math.min(item.before, item.after);
      const end = item.type === 'total' ? item.after : Math.max(item.before, item.after);
      const top = y(end);
      const height = Math.max(4, y(start) - top);
      const tone = item.type === 'total' ? 'total' : Number(item.value) >= 0 ? 'positive' : 'negative';
      const value = `${Number(item.value) > 0 && item.type !== 'total' ? '+' : ''}${item.value}${escapeHtml(data.currency || '')}`;
      const connector = index < states.length - 1 ? `<path d="M${x + barWidth} ${y(item.after)}H${x + barWidth + gap}"/>` : '';
      return `${connector}<rect class="${tone}" x="${x}" y="${top}" width="${barWidth}" height="${height}" rx="3"/><text class="value" x="${x + barWidth / 2}" y="${Math.max(14, top - 7)}" text-anchor="middle">${value}</text><text class="label" x="${x + barWidth / 2}" y="245" text-anchor="middle">${escapeHtml(item.label)}</text>`;
    }).join('');
    this.innerHTML = panel(data, `<div class="lc-waterfall" role="img" aria-label="${escapeHtml(data.title || 'Revenue waterfall')}"><svg viewBox="0 0 ${Math.max(710, states.length * (barWidth + gap) + 40)} 265"><g class="connectors">${bars}</g></svg><div class="lc-waterfall-legend"><span><i class="positive"></i>Increase</span><span><i class="negative"></i>Decrease</span><span><i class="total"></i>Total</span></div></div>`);
  }
}

class LcRiskDealTable extends JsonComponent {
  render() {
    const data = this.data;
    const deals = data.deals || [];
    const rows = deals.map((deal, index) => `<tr><td><button class="lc-risk-deal-name" type="button" data-risk-deal="${index}"><strong>${escapeHtml(deal.name)}</strong><small>${escapeHtml(deal.account)}</small></button></td><td>${escapeHtml(deal.owner)}</td><td><strong>${compactCurrency(deal.amount)}</strong></td><td>${escapeHtml(deal.stage)}</td><td><span class="lc-deal-score lc-deal-score--small ${Number(deal.score) < 75 ? 'is-risk' : ''}">${escapeHtml(deal.score)}</span></td><td><span class="lc-risk-reason">${escapeHtml(deal.risk)}</span></td><td>${escapeHtml(deal.closeDate)}</td></tr>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Deals Requiring Attention')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><button class="lc-button" type="button" data-view-risk>View All</button></div><div class="lc-table-wrap"><table class="lc-table lc-risk-table"><thead><tr><th scope="col">Opportunity</th><th scope="col">Owner</th><th scope="col">Amount</th><th scope="col">Stage</th><th scope="col">Score</th><th scope="col">Primary Risk</th><th scope="col">Close Date</th></tr></thead><tbody>${rows}</tbody></table></div></section>`;
    this.querySelectorAll('[data-risk-deal]').forEach(button => button.addEventListener('click', () => this.emitAction('risk-deal-select', { index: Number(button.dataset.riskDeal), deal: deals[Number(button.dataset.riskDeal)] })));
    this.querySelector('[data-view-risk]').addEventListener('click', () => this.emitAction('risk-deals-view-all'));
  }
}

function panel(data, content) {
  return `<section class="lc-panel lc-chart-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Analytics')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><div class="lc-chart-panel__body">${content}</div></section>`;
}

const definitions = {
  'lc-dashboard-header': LcDashboardHeader,
  'lc-metric-sparklines': LcMetricSparklines,
  'lc-revenue-trend': LcRevenueTrend,
  'lc-sales-funnel': LcSalesFunnel,
  'lc-team-attainment': LcTeamAttainment,
  'lc-pipeline-velocity': LcPipelineVelocity,
  'lc-win-rate-heatmap': LcWinRateHeatmap,
  'lc-revenue-waterfall': LcRevenueWaterfall,
  'lc-risk-deal-table': LcRiskDealTable,
};

for (const [name, constructor] of Object.entries(definitions)) {
  if (!customElements.get(name)) customElements.define(name, constructor);
}
