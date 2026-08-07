import { JsonComponent, escapeHtml, lcIcon } from './lightning-components.js';

const salesPalette = {
  success: '#2e844a',
  brand: '#0176d3',
  purple: '#9050e9',
  warning: '#fe9339',
  neutral: '#747474',
};

function formatCurrency(value, currency = 'EUR', compact = false) {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
    notation: compact ? 'compact' : 'standard',
    maximumFractionDigits: compact ? 2 : 0,
  }).format(Number(value) || 0);
}

function salesStatusClass(status = '') {
  const value = status.toLowerCase();
  if (value.includes('approved') || value.includes('won') || value === 'low') return 'success';
  if (value.includes('pending') || value.includes('risk') || value.includes('review')) return 'warning';
  if (value.includes('rejected') || value.includes('blocked')) return 'error';
  return 'brand';
}

class LcSalesOverview extends JsonComponent {
  render() {
    const data = this.data;
    const metrics = (data.metrics || []).map(metric => `<div><span>${escapeHtml(metric.label)}</span><strong>${escapeHtml(metric.value)}</strong></div>`).join('');
    const actions = (data.actions || []).map(action => `<button class="lc-button ${action.primary ? 'lc-button--brand' : ''}" type="button" data-sales-action="${escapeHtml(action.action)}">${escapeHtml(action.label)}</button>`).join('');
    this.innerHTML = `<section class="lc-sales-overview" aria-labelledby="sales-overview-title"><div class="lc-sales-overview__top"><div class="lc-sales-overview__identity"><span class="lc-object-icon lc-object-icon--forecast">${lcIcon('trend')}</span><div><span class="lc-sales-overview__eyebrow">Forecast</span><h1 id="sales-overview-title">${escapeHtml(data.title || 'Revenue Command Center')}</h1><p>${escapeHtml(data.subtitle || '')}</p></div></div><div class="lc-sales-overview__actions"><span class="lc-badge lc-badge--success">${escapeHtml(data.status || '')}</span>${actions}</div></div><div class="lc-sales-overview__metrics">${metrics}</div></section>`;
    this.querySelectorAll('[data-sales-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.salesAction)));
  }
}

class LcForecastSummary extends JsonComponent {
  render() {
    const data = this.data;
    const quota = Math.max(1, Number(data.quota));
    const closedPercent = Math.min(100, Number(data.closed) / quota * 100);
    const commitPercent = Math.min(100, Number(data.commit) / quota * 100);
    const bestPercent = Math.min(100, Number(data.bestCase) / quota * 100);
    const gap = Number(data.quota) - Number(data.commit);
    this.innerHTML = `<section class="lc-panel lc-forecast-summary"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Forecast Summary')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><span class="lc-badge ${gap <= 0 ? 'lc-badge--success' : 'lc-badge--warning'}">${gap <= 0 ? 'On target' : `${formatCurrency(gap, data.currency, true)} gap`}</span></div><div class="lc-forecast-summary__body"><div class="lc-forecast-ring" style="--forecast-progress:${commitPercent}"><div><strong>${Math.round(commitPercent)}%</strong><span>of quota</span></div></div><div class="lc-forecast-summary__details"><div><span>Quota</span><strong>${formatCurrency(data.quota, data.currency, true)}</strong></div><div><span>Closed Won</span><strong>${formatCurrency(data.closed, data.currency, true)}</strong></div><div><span>Commit</span><strong>${formatCurrency(data.commit, data.currency, true)}</strong></div><div><span>Best Case</span><strong>${formatCurrency(data.bestCase, data.currency, true)}</strong></div><div><span>Pipeline Coverage</span><strong>${(Number(data.pipeline) / quota).toFixed(2)}×</strong></div></div></div><div class="lc-forecast-range" aria-label="Forecast range"><span style="width:${closedPercent}%" class="closed"></span><span style="width:${Math.max(0, commitPercent - closedPercent)}%" class="commit"></span><span style="width:${Math.max(0, bestPercent - commitPercent)}%" class="best"></span><i style="left:100%"><b>Quota</b></i></div></section>`;
  }
}

class LcForecastCategories extends JsonComponent {
  render() {
    const data = this.data;
    const categories = data.categories || [];
    const total = Math.max(1, ...categories.map(category => Number(category.amount)));
    const rows = categories.map((category, index) => `<button class="lc-forecast-category" type="button" data-category="${index}"><i style="background:${salesPalette[category.tone] || salesPalette.brand}"></i><span><strong>${escapeHtml(category.label)}</strong><small>${escapeHtml(category.count)} opportunities</small></span><span class="lc-forecast-category__bar"><b style="width:${Number(category.amount) / total * 100}%;background:${salesPalette[category.tone] || salesPalette.brand}"></b></span><strong>${formatCurrency(category.amount, data.currency || 'EUR', true)}</strong></button>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Forecast by Category')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><div class="lc-forecast-categories">${rows}</div></section>`;
    this.querySelectorAll('[data-category]').forEach(button => button.addEventListener('click', () => {
      const index = Number(button.dataset.category);
      this.querySelectorAll('[data-category]').forEach(item => item.classList.toggle('is-selected', item === button));
      this.emitAction('forecast-category-select', { index, category: categories[index] });
    }));
  }
}

class LcForecastHierarchy extends JsonComponent {
  render() {
    const data = this.data;
    const rows = (data.rows || []).map((row, index) => `<tr><td><button type="button" class="lc-forecast-person" style="--hierarchy-level:${Number(row.level || 0)}" data-forecast-row="${index}"><span class="lc-avatar lc-avatar--small">${escapeHtml(row.initials)}</span><span><strong>${escapeHtml(row.name)}</strong><small>${escapeHtml(row.role)}</small></span></button></td><td>${formatCurrency(row.quota, data.currency || 'EUR', true)}</td><td>${formatCurrency(row.closed, data.currency || 'EUR', true)}</td><td>${formatCurrency(row.commit, data.currency || 'EUR', true)}</td><td>${formatCurrency(row.bestCase, data.currency || 'EUR', true)}</td><td><span class="lc-badge ${Number.parseFloat(row.coverage) >= 2 ? 'lc-badge--success' : 'lc-badge--warning'}">${escapeHtml(row.coverage)}</span></td></tr>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Forecast Hierarchy')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><button class="lc-button" type="button" data-hierarchy-action>Expand All</button></div><div class="lc-table-wrap"><table class="lc-table lc-forecast-table"><thead><tr><th scope="col">Forecast Owner</th><th scope="col">Quota</th><th scope="col">Closed</th><th scope="col">Commit</th><th scope="col">Best Case</th><th scope="col">Coverage</th></tr></thead><tbody>${rows}</tbody></table></div></section>`;
    this.querySelectorAll('[data-forecast-row]').forEach(button => button.addEventListener('click', () => this.emitAction('forecast-owner-select', { index: Number(button.dataset.forecastRow), owner: data.rows[Number(button.dataset.forecastRow)] })));
    this.querySelector('[data-hierarchy-action]').addEventListener('click', () => this.emitAction('forecast-expand'));
  }
}

class LcPipelineBoard extends JsonComponent {
  render() {
    const data = this.data;
    const stages = (data.stages || []).map((stage, stageIndex) => {
      const cards = (stage.opportunities || []).map((opportunity, opportunityIndex) => `<button class="lc-pipeline-card" type="button" data-opportunity="${stageIndex}:${opportunityIndex}"><span class="lc-pipeline-card__account">${escapeHtml(opportunity.account)}</span><strong>${escapeHtml(opportunity.name)}</strong><span class="lc-pipeline-card__amount">${formatCurrency(opportunity.amount, data.currency || 'EUR', true)}</span><span class="lc-pipeline-card__meta">${escapeHtml(opportunity.closeDate)} · ${escapeHtml(opportunity.probability)}%</span>${opportunity.risk ? `<span class="lc-deal-risk">! ${escapeHtml(opportunity.risk)}</span>` : ''}<span class="lc-pipeline-card__owner">${escapeHtml(opportunity.owner)}</span></button>`).join('');
      return `<section class="lc-pipeline-stage"><header><span>${escapeHtml(stage.name)}</span><strong>${formatCurrency(stage.amount, data.currency || 'EUR', true)}</strong></header><div>${cards}</div><button class="lc-pipeline-add" type="button" data-add-stage="${stageIndex}">+ Add opportunity</button></section>`;
    }).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Opportunity Pipeline')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><div class="lc-panel__actions"><button class="lc-button" type="button" data-pipeline-action="filter">Filters</button><button class="lc-button lc-button--brand" type="button" data-pipeline-action="new-opportunity">New Opportunity</button></div></div><div class="lc-pipeline-board">${stages}</div></section>`;
    this.querySelectorAll('[data-opportunity]').forEach(button => button.addEventListener('click', () => {
      const [stageIndex, opportunityIndex] = button.dataset.opportunity.split(':').map(Number);
      this.querySelectorAll('[data-opportunity]').forEach(item => item.classList.toggle('is-selected', item === button));
      this.emitAction('opportunity-select', { stageIndex, opportunityIndex, opportunity: data.stages[stageIndex].opportunities[opportunityIndex] });
    }));
    this.querySelectorAll('[data-add-stage]').forEach(button => button.addEventListener('click', () => this.emitAction('new-opportunity', { stageIndex: Number(button.dataset.addStage) })));
    this.querySelectorAll('[data-pipeline-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.pipelineAction)));
  }
}

class LcDealInspection extends JsonComponent {
  render() {
    const data = this.data;
    const deals = (data.deals || []).map((deal, index) => `<button class="lc-deal-card" type="button" data-deal="${index}"><span class="lc-deal-score ${deal.score < 75 ? 'is-risk' : ''}">${escapeHtml(deal.score)}</span><span class="lc-deal-card__identity"><strong>${escapeHtml(deal.name)}</strong><small>${escapeHtml(deal.stage)} · ${escapeHtml(deal.amount)}</small></span><span class="lc-deal-card__risk ${String(deal.risk).toLowerCase() === 'low' ? 'is-low' : ''}"><small>Risk</small><strong>${escapeHtml(deal.risk)}</strong></span><span class="lc-deal-card__next"><small>Next best action</small><strong>${escapeHtml(deal.nextStep)}</strong></span><span aria-hidden="true">›</span></button>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Deal Inspection')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><span class="lc-badge">${lcIcon('spark')} Einstein</span></div><div class="lc-deal-list">${deals}</div></section>`;
    this.querySelectorAll('[data-deal]').forEach(button => button.addEventListener('click', () => this.emitAction('deal-inspect', { index: Number(button.dataset.deal), deal: data.deals[Number(button.dataset.deal)] })));
  }
}

class LcQuoteBuilder extends JsonComponent {
  render() {
    const data = this.data;
    const rows = (data.items || []).map((item, index) => `<tr><td><strong>${escapeHtml(item.product)}</strong><small>${escapeHtml(item.code)}</small></td><td><input class="lc-input lc-quote-number" type="number" min="1" value="${Number(item.quantity)}" aria-label="Quantity for ${escapeHtml(item.product)}" data-quote-quantity="${index}"></td><td><input class="lc-input lc-quote-number" type="number" min="0" step="0.01" value="${Number(item.unitPrice)}" aria-label="Unit price for ${escapeHtml(item.product)}" data-quote-price="${index}"></td><td>${escapeHtml(item.term)} months</td><td data-quote-line-total="${index}"></td><td><button class="lc-icon-button" type="button" aria-label="Remove ${escapeHtml(item.product)}" data-remove-line="${index}">×</button></td></tr>`).join('');
    this.innerHTML = `<section class="lc-panel lc-quote"><div class="lc-panel__header"><div class="lc-panel__heading"><span class="lc-object-icon lc-object-icon--quote">€</span><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Quote')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><div class="lc-panel__actions"><button class="lc-button" type="button" data-quote-action="preview-quote">Preview</button><button class="lc-button lc-button--brand" type="button" data-quote-action="send-quote">Send Quote</button></div></div><div class="lc-quote__meta"><div><span>Valid Until</span><strong>${escapeHtml(data.validUntil || '')}</strong></div><label><span>Discount</span><span class="lc-quote-percent"><input class="lc-input" type="number" min="0" max="100" value="${Number(data.discount || 0)}" data-quote-discount aria-label="Discount percentage"><b>%</b></span></label><div><span>Currency</span><strong>${escapeHtml(data.currency || 'EUR')}</strong></div></div><div class="lc-table-wrap"><table class="lc-table lc-quote-table"><thead><tr><th scope="col">Product</th><th scope="col">Qty</th><th scope="col">Unit Price</th><th scope="col">Term</th><th scope="col">Net Total</th><th scope="col"><span class="lc-sr-only">Actions</span></th></tr></thead><tbody>${rows}</tbody></table></div><button class="lc-quote-add" type="button" data-quote-action="add-product">+ Add Product</button><div class="lc-quote-totals"><div><span>Subtotal</span><strong data-quote-subtotal></strong></div><div><span>Discount</span><strong data-quote-discount-total></strong></div><div><span>Estimated Tax (${Number(data.taxRate || 0)}%)</span><strong data-quote-tax></strong></div><div class="total"><span>Grand Total</span><strong data-quote-total></strong></div></div></section>`;
    this.recalculate();
    this.querySelectorAll('[data-quote-quantity], [data-quote-price], [data-quote-discount]').forEach(input => input.addEventListener('input', () => this.recalculate(true)));
    this.querySelectorAll('[data-quote-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.quoteAction, { totals: this.totals })));
    this.querySelectorAll('[data-remove-line]').forEach(button => button.addEventListener('click', () => {
      const index = Number(button.dataset.removeLine);
      data.items.splice(index, 1);
      this.emitAction('quote-line-remove', { index });
      this.render();
    }));
  }

  recalculate(emit = false) {
    const currency = this.data.currency || 'EUR';
    let subtotal = 0;
    (this.data.items || []).forEach((item, index) => {
      item.quantity = Number(this.querySelector(`[data-quote-quantity="${index}"]`)?.value || item.quantity);
      item.unitPrice = Number(this.querySelector(`[data-quote-price="${index}"]`)?.value || item.unitPrice);
      const lineTotal = item.quantity * item.unitPrice;
      subtotal += lineTotal;
      this.querySelector(`[data-quote-line-total="${index}"]`).textContent = formatCurrency(lineTotal, currency);
    });
    this.data.discount = Number(this.querySelector('[data-quote-discount]')?.value || 0);
    const discount = subtotal * this.data.discount / 100;
    const net = subtotal - discount;
    const tax = net * Number(this.data.taxRate || 0) / 100;
    this.totals = { subtotal, discount, tax, total: net + tax };
    this.querySelector('[data-quote-subtotal]').textContent = formatCurrency(subtotal, currency);
    this.querySelector('[data-quote-discount-total]').textContent = `− ${formatCurrency(discount, currency)}`;
    this.querySelector('[data-quote-tax]').textContent = formatCurrency(tax, currency);
    this.querySelector('[data-quote-total]').textContent = formatCurrency(net + tax, currency);
    if (emit) this.emitAction('quote-recalculate', { totals: this.totals });
  }
}

class LcQuoteApproval extends JsonComponent {
  render() {
    const data = this.data;
    const current = Number(data.current || 0);
    const steps = (data.steps || []).map((step, index) => `<li class="${index < current ? 'is-complete' : index === current ? 'is-current' : ''}"><span class="lc-approval-node">${index < current ? '✓' : index + 1}</span><span><strong>${escapeHtml(step.label)}</strong><small>${escapeHtml(step.owner)}</small></span><span><span class="lc-badge lc-badge--${salesStatusClass(step.status)}">${escapeHtml(step.status)}</span><small>${escapeHtml(step.time)}</small></span></li>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Approval Journey')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><button class="lc-button" type="button" data-remind-approver>Send Reminder</button></div><ol class="lc-approval-journey">${steps}</ol></section>`;
    this.querySelector('[data-remind-approver]').addEventListener('click', () => this.emitAction('approval-reminder', { step: data.steps[current] }));
  }
}

class LcSalesActivity extends JsonComponent {
  render() {
    const data = this.data;
    const items = (data.items || []).map(item => `<li><span class="lc-sales-activity__icon">${escapeHtml(item.icon)}</span><span><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.detail)}</small></span><time>${escapeHtml(item.time)}</time></li>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Recent Deal Activity')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><ol class="lc-sales-activity">${items}</ol></section>`;
  }
}

const definitions = {
  'lc-sales-overview': LcSalesOverview,
  'lc-forecast-summary': LcForecastSummary,
  'lc-forecast-categories': LcForecastCategories,
  'lc-forecast-hierarchy': LcForecastHierarchy,
  'lc-pipeline-board': LcPipelineBoard,
  'lc-deal-inspection': LcDealInspection,
  'lc-quote-builder': LcQuoteBuilder,
  'lc-quote-approval': LcQuoteApproval,
  'lc-sales-activity': LcSalesActivity,
};

for (const [name, constructor] of Object.entries(definitions)) {
  if (!customElements.get(name)) customElements.define(name, constructor);
}
