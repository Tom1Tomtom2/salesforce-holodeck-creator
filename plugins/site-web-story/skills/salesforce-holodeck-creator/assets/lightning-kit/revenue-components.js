import { JsonComponent, escapeHtml } from './lightning-components.js';

function revenueMoney(value, currency = 'EUR', digits = 0) {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(Number(value) || 0);
}

function revenueTone(value = '') {
  const normalized = String(value).toLowerCase();
  if (normalized.includes('approved') || normalized.includes('approuv') || normalized.includes('valid')) return 'success';
  if (normalized.includes('reject') || normalized.includes('rejet') || normalized.includes('block')) return 'error';
  if (normalized.includes('pending') || normalized.includes('attente') || normalized.includes('review') || normalized.includes('révision')) return 'warning';
  return 'brand';
}

class LcRevenueProductConfigurator extends JsonComponent {
  render() {
    const data = this.data;
    const activeCategory = Number(data.activeCategory || 0);
    const categories = (data.categories || []).map((category, index) => `<button class="lc-revenue-category ${index === activeCategory ? 'is-active' : ''}" type="button" aria-pressed="${index === activeCategory}" data-revenue-category="${index}">${escapeHtml(category.label)}<span>${escapeHtml(category.count)}</span></button>`).join('');
    const products = (data.products || []).map((product, index) => `<article class="lc-revenue-product ${product.selected ? 'is-selected' : ''}"><label><input type="checkbox" data-revenue-product="${index}" ${product.selected ? 'checked' : ''}><span class="lc-revenue-product__visual" aria-hidden="true">${escapeHtml(product.visual || '▣')}</span><span><strong>${escapeHtml(product.name)}</strong><small>${escapeHtml(product.description)}</small><b>${revenueMoney(product.price, data.currency || 'EUR')}</b></span></label><div><label><span class="lc-sr-only">Quantité pour ${escapeHtml(product.name)}</span><input class="lc-input" type="number" min="1" value="${Number(product.quantity || 1)}" data-revenue-product-quantity="${index}"></label><button class="lc-button" type="button" data-revenue-configure="${index}">${escapeHtml(product.configurable ? 'Configurer' : 'Ajouter')}</button></div></article>`).join('');
    const attributes = (data.attributes || []).map((attribute, index) => `<label><span>${escapeHtml(attribute.label)}</span><select class="lc-select" data-revenue-attribute="${index}">${(attribute.options || []).map(option => `<option ${option === attribute.value ? 'selected' : ''}>${escapeHtml(option)}</option>`).join('')}</select></label>`).join('');
    const summary = (data.summary || []).map(item => `<li><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.value)}</strong></li>`).join('');
    this.innerHTML = `<section class="lc-panel lc-revenue-configurator" aria-labelledby="${this.id || 'revenue-configurator'}-title"><div class="lc-panel__header"><div class="lc-panel__heading"><span class="lc-object-icon lc-object-icon--revenue" aria-hidden="true">▦</span><div><h2 class="lc-panel__title" id="${this.id || 'revenue-configurator'}-title">${escapeHtml(data.title || 'Configurer les produits')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><div class="lc-panel__actions"><button class="lc-button" type="button" data-revenue-action="validate-configuration">Valider</button><button class="lc-button lc-button--brand" type="button" data-revenue-action="return-to-quote">Retour au devis</button></div></div><div class="lc-revenue-configurator__body"><nav class="lc-revenue-categories" aria-label="Catégories de produits"><strong>Catégories</strong>${categories}<div class="lc-revenue-filters"><strong>Filtres</strong><label><span>Modèle de tarification</span><select class="lc-select"><option>Tout</option><option>Abonnement</option><option>Usage</option><option>Unique</option></select></label><label><span>Disponibilité</span><select class="lc-select"><option>Disponible</option><option>Tout</option></select></label></div></nav><div class="lc-revenue-products"><label class="lc-revenue-search"><span class="lc-sr-only">Rechercher des produits</span><input class="lc-input" type="search" placeholder="Rechercher des produits" data-revenue-search></label><div data-revenue-products>${products}</div></div><aside class="lc-revenue-configuration"><h3>${escapeHtml(data.configurationTitle || 'Configuration du bundle')}</h3><p>${escapeHtml(data.configurationDescription || '')}</p><div class="lc-revenue-attributes">${attributes}</div><h3>Résumé</h3><ul>${summary}</ul><div class="lc-revenue-config-total" aria-live="polite"><span>Total ponctuel</span><strong data-revenue-config-total>${revenueMoney(data.total, data.currency || 'EUR')}</strong></div></aside></div></section>`;
    this.querySelectorAll('[data-revenue-category]').forEach(button => button.addEventListener('click', () => {
      this.querySelectorAll('[data-revenue-category]').forEach(item => {
        const active = item === button;
        item.classList.toggle('is-active', active);
        item.setAttribute('aria-pressed', String(active));
      });
      this.emitAction('product-category-select', { index: Number(button.dataset.revenueCategory) });
    }));
    this.querySelectorAll('[data-revenue-product]').forEach(input => input.addEventListener('change', () => {
      const product = data.products[Number(input.dataset.revenueProduct)];
      product.selected = input.checked;
      input.closest('.lc-revenue-product').classList.toggle('is-selected', input.checked);
      this.recalculateTotal();
      this.emitAction('product-toggle', { product, selected: input.checked });
    }));
    this.querySelectorAll('[data-revenue-product-quantity]').forEach(input => input.addEventListener('input', () => {
      const product = data.products[Number(input.dataset.revenueProductQuantity)];
      product.quantity = Math.max(1, Number(input.value) || 1);
      this.recalculateTotal();
      this.emitAction('product-quantity-change', { product, quantity: product.quantity });
    }));
    this.querySelectorAll('[data-revenue-configure]').forEach(button => button.addEventListener('click', () => this.emitAction('product-configure', { index: Number(button.dataset.revenueConfigure), product: data.products[Number(button.dataset.revenueConfigure)] })));
    this.querySelectorAll('[data-revenue-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.revenueAction)));
    this.querySelector('[data-revenue-search]').addEventListener('input', event => {
      const query = event.currentTarget.value.toLowerCase();
      this.querySelectorAll('.lc-revenue-product').forEach((card, index) => { card.hidden = !String(data.products[index].name).toLowerCase().includes(query); });
    });
  }

  recalculateTotal() {
    const total = (this.data.products || []).reduce((sum, product) => {
      return product.selected ? sum + Number(product.price || 0) * Number(product.quantity || 1) : sum;
    }, 0);
    this.data.total = total;
    this.querySelector('[data-revenue-config-total]').textContent = revenueMoney(total, this.data.currency || 'EUR');
  }
}

class LcRevenueQuotePricing extends JsonComponent {
  render() {
    const data = this.data;
    const currencies = data.currencies || [{ code: data.currency || 'EUR', rate: 1 }];
    const currencyOptions = currencies.map(item => `<option value="${escapeHtml(item.code)}" ${item.code === (data.currency || currencies[0].code) ? 'selected' : ''}>${escapeHtml(item.code)} · ${escapeHtml(item.label || item.code)}</option>`).join('');
    const rows = (data.items || []).map((item, index) => `<tr><td><strong>${escapeHtml(item.product)}</strong><small>${escapeHtml(item.code)} · ${escapeHtml(item.pricingModel || '')}</small></td><td><input class="lc-input lc-revenue-number" type="number" min="1" value="${Number(item.quantity || 1)}" aria-label="Quantité pour ${escapeHtml(item.product)}" data-revenue-quantity="${index}"></td><td data-revenue-list="${index}"></td><td><label class="lc-revenue-discount"><span class="lc-sr-only">Remise pour ${escapeHtml(item.product)}</span><input class="lc-input" type="number" min="0" max="100" step="0.1" value="${Number(item.discount || 0)}" data-revenue-discount="${index}"><span>%</span></label></td><td data-revenue-net="${index}"></td><td data-revenue-cost="${index}"></td><td><span class="lc-revenue-margin" data-revenue-margin="${index}"></span></td><td><button class="lc-icon-button" type="button" aria-label="Actions pour ${escapeHtml(item.product)}" data-revenue-line="${index}">⋮</button></td></tr>`).join('');
    this.innerHTML = `<section class="lc-panel lc-revenue-quote" aria-labelledby="${this.id || 'revenue-quote'}-title"><div class="lc-panel__header"><div class="lc-panel__heading"><span class="lc-object-icon lc-object-icon--revenue" aria-hidden="true">€</span><div><h2 class="lc-panel__title" id="${this.id || 'revenue-quote'}-title">${escapeHtml(data.title || 'Atelier de tarification')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><div class="lc-panel__actions"><span class="lc-badge lc-badge--${revenueTone(data.status)}">${escapeHtml(data.status || 'Brouillon')}</span><button class="lc-button" type="button" data-revenue-quote-action="reprice">Recalculer</button><button class="lc-button lc-button--brand" type="button" data-revenue-quote-action="submit-approval">Soumettre pour approbation</button></div></div><div class="lc-revenue-quote__context"><div><span>Compte</span><strong>${escapeHtml(data.account || '')}</strong></div><div><span>Catalogue tarifaire</span><strong>${escapeHtml(data.priceBook || '')}</strong></div><label><span>Devise du devis</span><select class="lc-select" data-revenue-currency>${currencyOptions}</select></label><div><span>Taux verrouillé</span><strong data-revenue-rate></strong></div><div><span>Validité</span><strong>${escapeHtml(data.validUntil || '')}</strong></div></div><div class="lc-table-wrap"><table class="lc-table lc-revenue-quote-table"><caption class="lc-sr-only">Lignes de devis et calcul de marge</caption><thead><tr><th scope="col">Produit</th><th scope="col">Qté</th><th scope="col">Prix catalogue</th><th scope="col">Remise</th><th scope="col">Prix net</th><th scope="col">Coût</th><th scope="col">Marge</th><th scope="col"><span class="lc-sr-only">Actions</span></th></tr></thead><tbody>${rows}</tbody></table></div><button class="lc-revenue-add-line" type="button" data-revenue-quote-action="add-product">+ Ajouter un produit</button><div class="lc-revenue-quote__footer"><div class="lc-revenue-guardrails"><strong>Garde-fous de tarification</strong><span data-revenue-guardrail></span></div><dl><div><dt>Prix catalogue</dt><dd data-revenue-subtotal></dd></div><div><dt>Remise totale</dt><dd data-revenue-discount-total></dd></div><div><dt>Valeur nette</dt><dd data-revenue-net-total></dd></div><div><dt>Coût estimé</dt><dd data-revenue-cost-total></dd></div><div class="is-total"><dt>Marge</dt><dd data-revenue-margin-total></dd></div></dl></div></section>`;
    this.recalculate();
    this.querySelectorAll('[data-revenue-quantity], [data-revenue-discount]').forEach(input => input.addEventListener('input', () => this.recalculate(true)));
    this.querySelector('[data-revenue-currency]').addEventListener('change', () => this.recalculate(true));
    this.querySelectorAll('[data-revenue-quote-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.revenueQuoteAction, { totals: this.totals, currency: this.currency })));
    this.querySelectorAll('[data-revenue-line]').forEach(button => button.addEventListener('click', () => this.emitAction('quote-line-menu', { index: Number(button.dataset.revenueLine) })));
  }

  recalculate(emit = false) {
    const data = this.data;
    const currencySelect = this.querySelector('[data-revenue-currency]');
    this.currency = currencySelect?.value || data.currency || 'EUR';
    const selected = (data.currencies || []).find(item => item.code === this.currency) || { rate: 1 };
    const rate = Number(selected.rate || 1);
    let listTotal = 0;
    let netTotal = 0;
    let costTotal = 0;
    (data.items || []).forEach((item, index) => {
      item.quantity = Number(this.querySelector(`[data-revenue-quantity="${index}"]`)?.value || item.quantity || 1);
      item.discount = Number(this.querySelector(`[data-revenue-discount="${index}"]`)?.value || 0);
      const list = Number(item.listPrice || 0) * item.quantity;
      const net = list * (1 - item.discount / 100);
      const cost = Number(item.cost || 0) * item.quantity;
      const marginPercent = net ? (net - cost) / net * 100 : 0;
      listTotal += list;
      netTotal += net;
      costTotal += cost;
      this.querySelector(`[data-revenue-list="${index}"]`).textContent = revenueMoney(list * rate, this.currency);
      this.querySelector(`[data-revenue-net="${index}"]`).textContent = revenueMoney(net * rate, this.currency);
      this.querySelector(`[data-revenue-cost="${index}"]`).textContent = revenueMoney(cost * rate, this.currency);
      const margin = this.querySelector(`[data-revenue-margin="${index}"]`);
      margin.textContent = `${marginPercent.toFixed(1)} %`;
      margin.className = `lc-revenue-margin ${marginPercent < Number(data.marginFloor || 25) ? 'is-low' : 'is-good'}`;
    });
    const discountTotal = listTotal - netTotal;
    const marginTotal = netTotal - costTotal;
    const marginPercent = netTotal ? marginTotal / netTotal * 100 : 0;
    this.totals = { listTotal, discountTotal, netTotal, costTotal, marginTotal, marginPercent, rate };
    this.querySelector('[data-revenue-rate]').textContent = `1 ${escapeHtml(data.baseCurrency || 'EUR')} = ${rate.toFixed(4)} ${this.currency}`;
    this.querySelector('[data-revenue-subtotal]').textContent = revenueMoney(listTotal * rate, this.currency);
    this.querySelector('[data-revenue-discount-total]').textContent = `− ${revenueMoney(discountTotal * rate, this.currency)}`;
    this.querySelector('[data-revenue-net-total]').textContent = revenueMoney(netTotal * rate, this.currency);
    this.querySelector('[data-revenue-cost-total]').textContent = revenueMoney(costTotal * rate, this.currency);
    this.querySelector('[data-revenue-margin-total]').textContent = `${revenueMoney(marginTotal * rate, this.currency)} · ${marginPercent.toFixed(1)} %`;
    const belowFloor = marginPercent < Number(data.marginFloor || 25);
    const guardrail = this.querySelector('[data-revenue-guardrail]');
    guardrail.className = `lc-badge lc-badge--${belowFloor ? 'warning' : 'success'}`;
    guardrail.textContent = belowFloor ? `Marge sous le seuil de ${Number(data.marginFloor || 25)} %` : 'Tous les garde-fous sont respectés';
    if (emit) this.emitAction('quote-pricing-change', { totals: this.totals, currency: this.currency });
  }
}

class LcRevenuePricingWaterfall extends JsonComponent {
  render() {
    const data = this.data;
    const currency = data.currency || 'EUR';
    const steps = data.steps || [];
    const max = Math.max(1, ...steps.map(step => Math.abs(Number(step.amount))));
    const rows = steps.map((step, index) => `<li><span class="lc-revenue-waterfall__label"><i style="background:${escapeHtml(step.color || '#0176d3')}"></i><strong>${escapeHtml(step.label)}</strong><small>${escapeHtml(step.detail || '')}</small></span><span class="lc-revenue-waterfall__bar"><b style="width:${Math.abs(Number(step.amount)) / max * 100}%;background:${escapeHtml(step.color || '#0176d3')}"></b></span><strong class="${Number(step.amount) < 0 ? 'is-negative' : ''}">${Number(step.amount) < 0 ? '− ' : ''}${revenueMoney(Math.abs(Number(step.amount)), currency)}</strong></li>`).join('');
    this.innerHTML = `<section class="lc-panel" aria-labelledby="${this.id || 'pricing-waterfall'}-title"><div class="lc-panel__header"><div><h2 class="lc-panel__title" id="${this.id || 'pricing-waterfall'}-title">${escapeHtml(data.title || 'Cascade de prix')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><span class="lc-badge">${escapeHtml(data.scope || 'Total du devis')}</span></div><ol class="lc-revenue-waterfall">${rows}</ol></section>`;
  }
}

class LcRevenueCurrencyManager extends JsonComponent {
  render() {
    const data = this.data;
    const rows = (data.rates || []).map((rate, index) => `<tr><th scope="row">${escapeHtml(rate.code)}<small>${escapeHtml(rate.label || '')}</small></th><td>${Number(rate.rate).toFixed(4)}</td><td>${escapeHtml(rate.source)}</td><td>${escapeHtml(rate.updated)}</td><td><span class="lc-badge lc-badge--${rate.locked ? 'success' : 'warning'}">${rate.locked ? 'Verrouillé' : 'Flottant'}</span></td><td><button class="lc-icon-button" type="button" aria-label="Gérer le taux ${escapeHtml(rate.code)}" data-revenue-rate-index="${index}">⋮</button></td></tr>`).join('');
    this.innerHTML = `<section class="lc-panel" aria-labelledby="${this.id || 'currency-manager'}-title"><div class="lc-panel__header"><div><h2 class="lc-panel__title" id="${this.id || 'currency-manager'}-title">${escapeHtml(data.title || 'Gestion multi-devises')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><button class="lc-button" type="button" data-revenue-refresh-rates>Actualiser les taux</button></div><div class="lc-table-wrap"><table class="lc-table lc-revenue-currency-table"><caption class="lc-sr-only">Taux de change disponibles pour le devis</caption><thead><tr><th scope="col">Devise</th><th scope="col">Taux</th><th scope="col">Source</th><th scope="col">Mise à jour</th><th scope="col">Politique</th><th scope="col"><span class="lc-sr-only">Actions</span></th></tr></thead><tbody>${rows}</tbody></table></div><div class="lc-revenue-currency-note"><strong>${escapeHtml(data.policyTitle || 'Politique de conversion')}</strong><span>${escapeHtml(data.policy || '')}</span></div></section>`;
    this.querySelector('[data-revenue-refresh-rates]').addEventListener('click', () => this.emitAction('currency-rates-refresh'));
    this.querySelectorAll('[data-revenue-rate-index]').forEach(button => button.addEventListener('click', () => this.emitAction('currency-rate-manage', { index: Number(button.dataset.revenueRateIndex) })));
  }
}

class LcRevenueApprovalCenter extends JsonComponent {
  render() {
    const data = this.data;
    const rules = (data.rules || []).map(rule => `<li><span class="lc-revenue-rule__icon is-${escapeHtml(rule.result)}" aria-hidden="true">${rule.result === 'pass' ? '✓' : rule.result === 'fail' ? '!' : '•'}</span><span><strong>${escapeHtml(rule.label)}</strong><small>${escapeHtml(rule.detail)}</small></span><span class="lc-badge lc-badge--${rule.result === 'pass' ? 'success' : rule.result === 'fail' ? 'warning' : 'brand'}">${escapeHtml(rule.value)}</span></li>`).join('');
    const steps = (data.steps || []).map((step, index) => `<li class="${step.state === 'complete' ? 'is-complete' : step.state === 'current' ? 'is-current' : ''}"><span class="lc-approval-node">${step.state === 'complete' ? '✓' : index + 1}</span><span><strong>${escapeHtml(step.label)}</strong><small>${escapeHtml(step.owner)}</small></span><span><span class="lc-badge lc-badge--${revenueTone(step.status)}">${escapeHtml(step.status)}</span><small>${escapeHtml(step.time || '')}</small></span></li>`).join('');
    const history = (data.history || []).map(item => `<li><span class="lc-avatar lc-avatar--small">${escapeHtml(item.initials)}</span><span><strong>${escapeHtml(item.actor)}</strong><small>${escapeHtml(item.action)} · ${escapeHtml(item.time)}</small><p>${escapeHtml(item.comment || '')}</p></span></li>`).join('');
    this.innerHTML = `<section class="lc-panel lc-revenue-approval" aria-labelledby="${this.id || 'revenue-approval'}-title"><div class="lc-panel__header"><div class="lc-panel__heading"><span class="lc-object-icon lc-object-icon--revenue" aria-hidden="true">✓</span><div><h2 class="lc-panel__title" id="${this.id || 'revenue-approval'}-title">${escapeHtml(data.title || 'Centre d’approbation')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><div class="lc-panel__actions"><button class="lc-button" type="button" data-revenue-approval-action="request-change">Demander une modification</button><button class="lc-button lc-button--brand" type="button" data-revenue-approval-action="approve">Approuver</button></div></div><div class="lc-revenue-approval__summary"><div><span>Valeur nette</span><strong>${escapeHtml(data.netValue)}</strong></div><div><span>Remise</span><strong>${escapeHtml(data.discount)}</strong></div><div><span>Marge</span><strong>${escapeHtml(data.margin)}</strong></div><div><span>Devise</span><strong>${escapeHtml(data.currency)}</strong></div><div><span>Expiration</span><strong>${escapeHtml(data.expires)}</strong></div></div><div class="lc-revenue-approval__grid"><section><h3>Contrôles et seuils</h3><ul class="lc-revenue-rules">${rules}</ul></section><section><h3>Parcours d’approbation</h3><ol class="lc-approval-journey">${steps}</ol></section><section><h3>Historique de décision</h3><ol class="lc-revenue-history">${history}</ol></section></div></section>`;
    this.querySelectorAll('[data-revenue-approval-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.revenueApprovalAction)));
  }
}

class LcRevenueQuotePipeline extends JsonComponent {
  render() {
    const data = this.data;
    const stages = (data.stages || []).map((stage, stageIndex) => {
      const quotes = (stage.quotes || []).map((quote, quoteIndex) => `<button class="lc-revenue-pipeline-card" type="button" aria-pressed="false" data-revenue-quote-card="${stageIndex}:${quoteIndex}"><span class="lc-revenue-pipeline-card__top"><small>${escapeHtml(quote.number)}</small><span class="lc-badge lc-badge--${revenueTone(quote.risk)}">${escapeHtml(quote.risk)}</span></span><strong>${escapeHtml(quote.account)}</strong><span>${escapeHtml(quote.name)}</span><dl><div><dt>Valeur</dt><dd>${escapeHtml(quote.value)}</dd></div><div><dt>Marge</dt><dd>${escapeHtml(quote.margin)}</dd></div></dl><small>${escapeHtml(quote.owner)} · ${escapeHtml(quote.age)}</small></button>`).join('');
      return `<section class="lc-revenue-pipeline-stage"><header><div><strong>${escapeHtml(stage.name)}</strong><small>${escapeHtml(stage.count)} devis</small></div><span>${escapeHtml(stage.value)}</span></header><div>${quotes}</div></section>`;
    }).join('');
    const metrics = (data.metrics || []).map(metric => `<div><span>${escapeHtml(metric.label)}</span><strong>${escapeHtml(metric.value)}</strong><small>${escapeHtml(metric.trend || '')}</small></div>`).join('');
    this.innerHTML = `<section class="lc-panel" aria-labelledby="${this.id || 'revenue-pipeline'}-title"><div class="lc-panel__header"><div><h2 class="lc-panel__title" id="${this.id || 'revenue-pipeline'}-title">${escapeHtml(data.title || 'Pipeline des devis')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><div class="lc-panel__actions"><button class="lc-button" type="button" data-revenue-pipeline-action="filters">Filtres</button><button class="lc-button lc-button--brand" type="button" data-revenue-pipeline-action="new-quote">Nouveau devis</button></div></div><div class="lc-revenue-pipeline-metrics">${metrics}</div><div class="lc-revenue-pipeline">${stages}</div></section>`;
    this.querySelectorAll('[data-revenue-quote-card]').forEach(button => button.addEventListener('click', () => {
      const [stageIndex, quoteIndex] = button.dataset.revenueQuoteCard.split(':').map(Number);
      this.querySelectorAll('[data-revenue-quote-card]').forEach(item => {
        const selected = item === button;
        item.classList.toggle('is-selected', selected);
        item.setAttribute('aria-pressed', String(selected));
      });
      this.emitAction('quote-select', { stageIndex, quoteIndex, quote: data.stages[stageIndex].quotes[quoteIndex] });
    }));
    this.querySelectorAll('[data-revenue-pipeline-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.revenuePipelineAction)));
  }
}

const definitions = {
  'lc-revenue-product-configurator': LcRevenueProductConfigurator,
  'lc-revenue-quote-pricing': LcRevenueQuotePricing,
  'lc-revenue-pricing-waterfall': LcRevenuePricingWaterfall,
  'lc-revenue-currency-manager': LcRevenueCurrencyManager,
  'lc-revenue-approval-center': LcRevenueApprovalCenter,
  'lc-revenue-quote-pipeline': LcRevenueQuotePipeline,
};

for (const [name, constructor] of Object.entries(definitions)) {
  if (!customElements.get(name)) customElements.define(name, constructor);
}
