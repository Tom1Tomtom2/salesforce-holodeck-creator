import { JsonComponent, escapeHtml } from './lightning-components.js';

const cgColors = ['#1b78d0', '#38a3a5', '#8854d0', '#f07f3c', '#4c956c'];
let cgAgentOverlayCount = 0;

class LcB2bCommerceHome extends JsonComponent {
  render() {
    const data = this.data;
    const benefits = (data.benefits || []).map((item, index) => `<li><span aria-hidden="true">${['▣', '◇', '◎', '▤'][index % 4]}</span><div><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.description)}</small></div></li>`).join('');
    const categories = (data.categories || []).map((category, index) => `<button class="lc-commerce-category" type="button" data-commerce-category="${index}" style="--category-tone:${escapeHtml(category.color || cgColors[index % cgColors.length])}"><span class="lc-commerce-category__visual" aria-hidden="true">${escapeHtml(category.symbol || ['☕', '◉', '✦'][index % 3])}</span><strong>${escapeHtml(category.name)}</strong><small>${escapeHtml(category.description || '')}</small></button>`).join('');
    this.innerHTML = `<section class="lc-commerce-home" aria-labelledby="${this.id || 'commerce-home-title'}"><div class="lc-commerce-hero"><div><span>${escapeHtml(data.eyebrow || 'Commerce B2B')}</span><h1 id="${this.id || 'commerce-home-title'}">${escapeHtml(data.title || 'Équipez chaque point de vente')}</h1><p>${escapeHtml(data.subtitle || '')}</p><div>${(data.actions || []).map((action, index) => `<button class="lc-button ${index === 0 ? 'lc-button--brand' : ''}" type="button" data-commerce-action="${escapeHtml(action.action || action.label)}">${escapeHtml(action.label)}</button>`).join('')}</div></div></div><ul class="lc-commerce-benefits">${benefits}</ul><div class="lc-commerce-categories">${categories}</div></section>`;
    this.querySelectorAll('[data-commerce-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.commerceAction)));
    this.querySelectorAll('[data-commerce-category]').forEach(button => button.addEventListener('click', () => this.emitAction('commerce-category-select', { index: Number(button.dataset.commerceCategory), category: data.categories[Number(button.dataset.commerceCategory)] })));
  }
}

class LcAgentOverlay extends JsonComponent {
  connectedCallback() {
    this.data = this.querySelector('script[type="application/json"]') ? JSON.parse(this.querySelector('script[type="application/json"]').textContent) : {};
    this.mode = (this.dataset.mode || this.data.mode) === 'lightning' ? 'lightning' : 'external';
    this.dialogId = `${this.id || `lc-agent-overlay-${++cgAgentOverlayCount}`}-dialog`;
    this.render();
    if (this.mode === 'lightning') this.mountLightningLauncher();
    if (this.data.open !== false) this.open(false);
  }

  render() {
    const data = this.data;
    const messages = (data.messages || []).map(message => `<div class="lc-overlay-message is-${escapeHtml(message.role || 'assistant')}"><span aria-hidden="true">${message.role === 'user' ? '●' : '✦'}</span><div><strong>${escapeHtml(message.author || (message.role === 'user' ? 'Vous' : data.title || 'Agentforce'))}</strong><p>${escapeHtml(message.text)}</p>${message.bullets ? `<ul>${message.bullets.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>` : ''}</div></div>`).join('');
    const actions = (data.actions || []).map((action, index) => `<button type="button" data-overlay-action="${index}"><span aria-hidden="true">›</span>${escapeHtml(action.label || action)}</button>`).join('');
    const launcherContent = this.mode === 'lightning'
      ? `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.5 14.1 9l6.4 2.1-6.4 2.2L12 20l-2.1-6.7-6.4-2.2L9.9 9 12 2.5Zm6.2 1.2.8 2.4 2.3.8-2.3.8-.8 2.4-.8-2.4-2.3-.8 2.3-.8.8-2.4Z"/></svg><span class="lc-sr-only">${escapeHtml(data.launchLabel || 'Ouvrir Agentforce')}</span>`
      : `<span aria-hidden="true">✦</span> ${escapeHtml(data.launchLabel || 'Demander à Agentforce')}`;
    this.innerHTML = `<button class="lc-agent-launcher lc-agent-launcher--${this.mode}" type="button" aria-haspopup="dialog" aria-controls="${this.dialogId}" aria-expanded="false" data-agent-launcher>${launcherContent}</button><section class="lc-agent-overlay lc-agent-overlay--${this.mode}" id="${this.dialogId}" role="dialog" aria-labelledby="${this.dialogId}-title" hidden><header><div><span aria-hidden="true">✦</span><h2 id="${this.dialogId}-title">${escapeHtml(data.title || 'Agentforce')}</h2></div><button type="button" data-agent-close aria-label="Fermer Agentforce">×</button></header><div class="lc-agent-overlay__messages" role="log" aria-live="polite">${messages}</div>${actions ? `<div class="lc-agent-overlay__actions"><h3>${escapeHtml(data.actionsTitle || 'Actions recommandées')}</h3>${actions}</div>` : ''}<form><label class="lc-sr-only" for="${this.dialogId}-prompt">${escapeHtml(data.promptLabel || 'Votre demande')}</label><textarea class="lc-textarea" id="${this.dialogId}-prompt" name="prompt" placeholder="${escapeHtml(data.placeholder || 'Décrivez votre tâche ou posez une question…')}"></textarea><button type="submit" aria-label="Envoyer la demande">↑</button></form><footer>${escapeHtml(data.footer || 'Propulsé par Agentforce')}</footer></section>`;
    this.panel = this.querySelector('.lc-agent-overlay');
    this.launcher = this.querySelector('[data-agent-launcher]');
    this.launcher.addEventListener('click', () => this.panel.hidden ? this.open(true) : this.close());
    this.querySelector('[data-agent-close]').addEventListener('click', () => this.close());
    this.querySelectorAll('[data-overlay-action]').forEach(button => button.addEventListener('click', () => this.emitAction('agent-overlay-action', { index: Number(button.dataset.overlayAction), action: data.actions[Number(button.dataset.overlayAction)] })));
    this.querySelector('form').addEventListener('submit', event => {
      event.preventDefault();
      const prompt = new FormData(event.currentTarget).get('prompt');
      if (String(prompt).trim()) this.emitAction('agent-overlay-message', { prompt });
    });
    this.addEventListener('keydown', event => { if (event.key === 'Escape' && !this.panel.hidden) this.close(); });
  }

  mountLightningLauncher() {
    const target = document.querySelector('.lightning .ln-ask');
    if (!target) return;
    target.replaceWith(this.launcher);
  }

  open(moveFocus = true) {
    this.panel.hidden = false;
    this.launcher.hidden = this.mode === 'external';
    this.launcher.classList.add('is-active');
    this.launcher.setAttribute('aria-expanded', 'true');
    if (moveFocus) requestAnimationFrame(() => this.querySelector('[data-agent-close]')?.focus());
  }

  close() {
    this.panel.hidden = true;
    this.launcher.hidden = false;
    this.launcher.classList.remove('is-active');
    this.launcher.setAttribute('aria-expanded', 'false');
    this.launcher.focus();
  }
}

class LcRetailStorePerformance extends JsonComponent {
  render() {
    const data = this.data;
    const metrics = (data.metrics || []).map(metric => `<div><span>${escapeHtml(metric.label)}</span><strong>${escapeHtml(metric.value)}</strong><small>${escapeHtml(metric.context || '')}</small></div>`).join('');
    const max = Math.max(1, ...(data.stores || []).map(store => Number(store.value)));
    const bars = (data.stores || []).map(store => `<div class="lc-store-bar"><span>${escapeHtml(store.name)}</span><div><i style="width:${Number(store.value) / max * 100}%"></i></div><strong>${escapeHtml(store.display || store.value)}</strong></div>`).join('');
    const rows = (data.locations || []).map(location => `<tr><td>${escapeHtml(location.store)}</td><td>${escapeHtml(location.location)}</td><td>${escapeHtml(location.account)}</td><td>${escapeHtml(location.value)}</td></tr>`).join('');
    const scorecard = (data.scorecard || []).map((item, index) => `<li><span style="background:${escapeHtml(item.color || cgColors[index % cgColors.length])}" aria-hidden="true">${escapeHtml(item.icon || '●')}</span><div><strong>${escapeHtml(item.value)}</strong><small>${escapeHtml(item.label)}</small></div><i style="--score:${Number(item.progress || 0)}%"></i></li>`).join('');
    this.innerHTML = `<section class="lc-retail-performance"><div class="lc-panel lc-retail-performance__main"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Performance magasins')}</h2><div class="lc-panel__meta">${escapeHtml(data.updated || '')}</div></div></div><div class="lc-retail-filters">${(data.filters || []).map(filter => `<label><span>${escapeHtml(filter.label)}</span><select class="lc-select">${(filter.options || []).map(option => `<option>${escapeHtml(option)}</option>`).join('')}</select></label>`).join('')}</div><div class="lc-retail-metrics">${metrics}</div><div class="lc-retail-performance__canvas"><div><h3>${escapeHtml(data.chartTitle || 'Classement par volume')}</h3>${bars}</div><div class="lc-table-wrap"><table class="lc-table"><thead><tr><th>Magasin</th><th>Emplacement</th><th>Enseigne</th><th>Volume</th></tr></thead><tbody>${rows}</tbody></table></div></div></div><aside class="lc-panel lc-service-scorecard"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.scorecardTitle || 'Mon activité')}</h2><div class="lc-panel__meta">${escapeHtml(data.scorecardMeta || '')}</div></div></div><ol>${scorecard}</ol></aside></section>`;
  }
}

class LcRetailAccountCockpit extends JsonComponent {
  render() {
    const data = this.data;
    const max = Math.max(1, ...(data.products || []).map(product => Number(product.volume)));
    const products = (data.products || []).map(product => `<div class="lc-yoy-row"><span>${escapeHtml(product.name)}</span><div><i style="width:${Number(product.volume) / max * 100}%"></i></div><strong>${escapeHtml(product.volume)}</strong><em class="${Number(product.change) < 0 ? 'is-down' : ''}">${Number(product.change) > 0 ? '+' : ''}${escapeHtml(product.change)}%</em></div>`).join('');
    const programs = (data.programs || []).map(program => `<li><span>${escapeHtml(program.name)}</span><div role="progressbar" aria-label="${escapeHtml(program.name)}" aria-valuenow="${Number(program.progress)}" aria-valuemin="0" aria-valuemax="100"><i style="width:${Number(program.progress)}%"></i></div><strong>${escapeHtml(program.progress)}%</strong></li>`).join('');
    this.innerHTML = `<section class="lc-panel lc-account-cockpit"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Performance du compte')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><div class="lc-account-cockpit__grid"><div><h3>${escapeHtml(data.salesTitle || 'Ventes actuelles vs N-1')}</h3><div class="lc-yoy-chart">${products}</div></div><div><h3>${escapeHtml(data.programsTitle || 'Programmes clés')}</h3><ul class="lc-key-programs">${programs}</ul><div class="lc-account-assets">${(data.assets || []).map(asset => `<button type="button" data-account-asset="${escapeHtml(asset.name)}"><span aria-hidden="true">${escapeHtml(asset.symbol || '▣')}</span>${escapeHtml(asset.name)}</button>`).join('')}</div></div></div></section>`;
    this.querySelectorAll('[data-account-asset]').forEach(button => button.addEventListener('click', () => this.emitAction('account-asset-open', { asset: button.dataset.accountAsset })));
  }
}

class LcConsumerOrderCapture extends JsonComponent {
  render() {
    const data = this.data;
    const filters = (data.filters || []).map(filter => `<label><span>${escapeHtml(filter.label)}</span><select class="lc-select">${(filter.options || []).map(option => `<option>${escapeHtml(option)}</option>`).join('')}</select></label>`).join('');
    const rows = (data.products || []).map((product, index) => `<tr><td><input type="checkbox" aria-label="Sélectionner ${escapeHtml(product.name)}" ${product.selected ? 'checked' : ''}></td><td><input class="lc-input" type="number" min="0" value="${Number(product.quantity || 0)}" aria-label="Quantité pour ${escapeHtml(product.name)}" data-order-quantity="${index}"></td><td><strong>${escapeHtml(product.name)}</strong></td><td>${escapeHtml(product.code)}</td><td>${escapeHtml(product.shortCode)}</td><td>${escapeHtml(product.gtin)}</td></tr>`).join('');
    this.innerHTML = `<section class="lc-panel lc-order-capture"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Saisie de commande')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><form><fieldset><legend>Filtres produits</legend><div class="lc-order-filters">${filters}</div><button class="lc-button" type="button" data-order-search>Rechercher</button></fieldset><div class="lc-table-wrap"><table class="lc-table"><caption>${escapeHtml(data.tableTitle || 'Produits disponibles')}</caption><thead><tr><th>Sélection</th><th>Quantité</th><th>Description produit</th><th>Code produit</th><th>Code court</th><th>GTIN</th></tr></thead><tbody>${rows}</tbody></table></div><div class="lc-order-actions"><button class="lc-button" type="button" data-order-cancel>Retour et annuler</button><button class="lc-button lc-button--brand" type="submit">Ajouter au panier</button></div></form></section>`;
    this.querySelector('[data-order-search]').addEventListener('click', () => this.emitAction('order-search'));
    this.querySelector('[data-order-cancel]').addEventListener('click', () => this.emitAction('order-cancel'));
    this.querySelector('form').addEventListener('submit', event => { event.preventDefault(); this.emitAction('order-add-to-cart'); });
  }
}

class LcAssetTelemetry extends JsonComponent {
  render() {
    const data = this.data;
    const values = data.values || [];
    const min = Number(data.min || 0);
    const max = Number(data.max || 100);
    const range = Math.max(1, max - min);
    const x = index => 30 + index * (720 / Math.max(1, values.length - 1));
    const y = value => 260 - (Number(value) - min) / range * 210;
    const points = values.map((value, index) => `${x(index)},${y(value)}`).join(' ');
    const labels = (data.labels || []).map((label, index) => `<text x="${x(index)}" y="286" text-anchor="middle">${escapeHtml(label)}</text>`).join('');
    const alerts = (data.alerts || []).map(alert => `<li><span class="lc-badge lc-badge--error">${escapeHtml(alert.status || 'Alerte')}</span><div><strong>${escapeHtml(alert.title)}</strong><p>${escapeHtml(alert.description)}</p></div></li>`).join('');
    this.innerHTML = `<section class="lc-panel lc-asset-telemetry"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Télémétrie de l’actif')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><span class="lc-badge lc-badge--${data.status === 'Normal' ? 'success' : 'error'}">${escapeHtml(data.status || '')}</span></div><div class="lc-telemetry-chart" role="img" aria-label="${escapeHtml(data.accessibleLabel || data.title || 'Courbe de télémétrie')}"><svg viewBox="0 0 780 310"><rect x="30" y="${y(data.healthyMax)}" width="720" height="${Math.max(0, y(data.healthyMin) - y(data.healthyMax))}" fill="#dff6e7"/><g class="grid"><path d="M30 50H750M30 120H750M30 190H750M30 260H750"/></g><polyline points="${points}" fill="none" stroke="#1b78d0" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><g class="axis-labels">${labels}</g></svg></div><ul class="lc-telemetry-alerts">${alerts}</ul></section>`;
  }
}

class LcTradePromotionCalendar extends JsonComponent {
  render() {
    const data = this.data;
    const periods = data.periods || ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sept', 'Oct', 'Nov', 'Déc'];
    const gridColumns = `repeat(${periods.length}, minmax(62px, 1fr))`;
    const header = periods.map(period => `<span>${escapeHtml(period)}</span>`).join('');
    const rows = (data.rows || []).map((row, rowIndex) => {
      const bars = (row.items || []).map((item, itemIndex) => `<button type="button" class="lc-trade-calendar__bar" style="--bar-start:${Number(item.start)};--bar-span:${Number(item.span)};--bar-color:${escapeHtml(item.color || row.color || cgColors[rowIndex % cgColors.length])}" data-promotion="${rowIndex}:${itemIndex}" aria-label="${escapeHtml(`${row.label} : ${item.label}, période ${item.start} à ${Number(item.start) + Number(item.span) - 1}`)}"><span>${escapeHtml(item.label)}</span></button>`).join('');
      return `<div class="lc-trade-calendar__label"><strong>${escapeHtml(row.label)}</strong><small>${escapeHtml(row.description || '')}</small></div><div class="lc-trade-calendar__track" style="grid-template-columns:${gridColumns}">${bars}</div>`;
    }).join('');
    const legend = (data.legend || []).map((item, index) => `<span><i style="background:${escapeHtml(item.color || cgColors[index % cgColors.length])}"></i>${escapeHtml(item.label)}</span>`).join('');
    this.innerHTML = `<section class="lc-panel lc-trade-calendar"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Calendrier promotionnel')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><div class="lc-panel__actions"><button class="lc-button" type="button" data-calendar-action="scenario">${escapeHtml(data.scenarioLabel || 'Comparer les scénarios')}</button><button class="lc-button lc-button--brand" type="button" data-calendar-action="new">${escapeHtml(data.newLabel || 'Nouvelle promotion')}</button></div></div><div class="lc-trade-calendar__viewport"><div class="lc-trade-calendar__grid"><div class="lc-trade-calendar__corner">Levier commercial</div><div class="lc-trade-calendar__periods" style="grid-template-columns:${gridColumns}">${header}</div>${rows}</div></div><footer class="lc-trade-calendar__legend">${legend}</footer></section>`;
    this.querySelectorAll('[data-calendar-action]').forEach(button => button.addEventListener('click', () => this.emitAction(`trade-calendar-${button.dataset.calendarAction}`)));
    this.querySelectorAll('[data-promotion]').forEach(button => button.addEventListener('click', () => this.emitAction('trade-promotion-select', { item: button.dataset.promotion, label: button.textContent.trim() })));
  }
}

class LcSalesAgreementForecast extends JsonComponent {
  render() {
    const data = this.data;
    const periods = data.periods || [];
    const products = (data.products || []).map((product, productIndex) => {
      const values = (product.values || []).map((value, valueIndex) => `<td class="${Number(value.actual) < Number(value.planned) ? 'is-behind' : ''}"><span>${escapeHtml(value.planned)}</span><strong>${escapeHtml(value.actual)}</strong><small>${escapeHtml(value.forecast)}</small><button type="button" aria-label="Ajuster ${escapeHtml(product.name)} pour ${escapeHtml(periods[valueIndex])}" data-agreement-cell="${productIndex}:${valueIndex}">✎</button></td>`).join('');
      return `<tr><th scope="row"><strong>${escapeHtml(product.name)}</strong><small>${escapeHtml(product.code || '')}</small></th><td>${escapeHtml(product.price || '')}</td><td>${escapeHtml(product.total || '')}</td>${values}</tr>`;
    }).join('');
    const periodHeadings = periods.map(period => `<th scope="col">${escapeHtml(period)}</th>`).join('');
    const metrics = (data.metrics || []).map(metric => `<div><span>${escapeHtml(metric.label)}</span><strong>${escapeHtml(metric.value)}</strong><small class="${metric.direction === 'down' ? 'is-down' : ''}">${escapeHtml(metric.context || '')}</small></div>`).join('');
    this.innerHTML = `<section class="lc-panel lc-sales-agreement"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Sales Agreement & Forecast')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><div class="lc-panel__actions"><span class="lc-badge lc-badge--${data.status === 'Actif' ? 'success' : 'warning'}">${escapeHtml(data.status || '')}</span><button class="lc-button lc-button--brand" type="button" data-agreement-save>${escapeHtml(data.saveLabel || 'Enregistrer les ajustements')}</button></div></div><div class="lc-sales-agreement__metrics">${metrics}</div><div class="lc-sales-agreement__legend"><span>Planifié</span><strong>Réalisé</strong><small>Prévision révisée</small></div><div class="lc-table-wrap"><table class="lc-sales-agreement__table"><thead><tr><th scope="col">Produit</th><th scope="col">Prix</th><th scope="col">Total</th>${periodHeadings}</tr></thead><tbody>${products}</tbody></table></div></section>`;
    this.querySelector('[data-agreement-save]').addEventListener('click', () => this.emitAction('sales-agreement-save'));
    this.querySelectorAll('[data-agreement-cell]').forEach(button => button.addEventListener('click', () => this.emitAction('sales-agreement-adjust', { cell: button.dataset.agreementCell })));
  }
}

class LcTradeBusinessPlanner extends JsonComponent {
  render() {
    const data = this.data;
    const periods = data.periods || [];
    const rows = (data.rows || []).map((row, rowIndex) => {
      const cells = (row.values || []).map((value, valueIndex) => row.editable
        ? `<td><input class="lc-input" value="${escapeHtml(value)}" aria-label="${escapeHtml(`${row.label}, ${periods[valueIndex] || `période ${valueIndex + 1}`}`)}" data-planner-input="${rowIndex}:${valueIndex}"></td>`
        : `<td>${escapeHtml(value)}</td>`).join('');
      return `<tr class="${row.group ? 'is-group' : ''}"><th scope="row"><span style="--planner-level:${Number(row.level || 0)}">${escapeHtml(row.label)}</span></th><td><strong>${escapeHtml(row.total || '')}</strong></td>${cells}</tr>`;
    }).join('');
    this.innerHTML = `<section class="lc-panel lc-trade-planner"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Customer Business Plan')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><div class="lc-panel__actions"><button class="lc-button" type="button" data-planner-action="scenario">Ajouter un scénario</button><button class="lc-button lc-button--brand" type="button" data-planner-action="calculate">Enregistrer et calculer</button></div></div><div class="lc-trade-planner__filters">${(data.filters || []).map(filter => `<label><span>${escapeHtml(filter.label)}</span><select class="lc-select">${(filter.options || []).map(option => `<option>${escapeHtml(option)}</option>`).join('')}</select></label>`).join('')}</div><div class="lc-table-wrap"><table class="lc-trade-planner__table"><thead><tr><th scope="col">KPI / Produit</th><th scope="col">Total annuel</th>${periods.map(period => `<th scope="col">${escapeHtml(period)}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div><footer>Dernier calcul : <strong>${escapeHtml(data.calculated || 'à l’instant')}</strong></footer></section>`;
    this.querySelectorAll('[data-planner-action]').forEach(button => button.addEventListener('click', () => this.emitAction(`trade-planner-${button.dataset.plannerAction}`)));
    this.querySelectorAll('[data-planner-input]').forEach(input => input.addEventListener('change', () => this.emitAction('trade-planner-change', { cell: input.dataset.plannerInput, value: input.value })));
  }
}

const definitions = {
  'lc-b2b-commerce-home': LcB2bCommerceHome,
  'lc-agent-overlay': LcAgentOverlay,
  'lc-retail-store-performance': LcRetailStorePerformance,
  'lc-retail-account-cockpit': LcRetailAccountCockpit,
  'lc-consumer-order-capture': LcConsumerOrderCapture,
  'lc-asset-telemetry': LcAssetTelemetry,
  'lc-trade-promotion-calendar': LcTradePromotionCalendar,
  'lc-sales-agreement-forecast': LcSalesAgreementForecast,
  'lc-trade-business-planner': LcTradeBusinessPlanner,
};

for (const [name, constructor] of Object.entries(definitions)) {
  if (!customElements.get(name)) customElements.define(name, constructor);
}
