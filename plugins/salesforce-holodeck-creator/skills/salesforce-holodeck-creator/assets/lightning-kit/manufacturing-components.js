import { JsonComponent, escapeHtml } from './lightning-components.js';

class LcManufacturingAgreementTerms extends JsonComponent {
  render() {
    const data = this.data;
    const titleId = `${this.id || 'mfg-agreement'}-title`;
    const periods = data.periods || [];
    const labels = data.labels || {};
    const rows = (data.products || []).map(product => {
      const metrics = product.metrics || [];
      return metrics.map((metric, index) => `<tr>${index === 0 ? `<th scope="rowgroup" rowspan="${metrics.length}"><strong>${escapeHtml(product.name)}</strong><small>${escapeHtml(product.code || '')}</small></th>` : ''}<th scope="row">${escapeHtml(metric.name)}</th><td class="lc-mfg-agreement__total">${escapeHtml(metric.total)}</td>${(metric.values || []).map(value => `<td>${escapeHtml(value)}</td>`).join('')}</tr>`).join('');
    }).join('');
    const actions = (data.actions || []).map(action => {
      const item = typeof action === 'string' ? { label: action, action } : action;
      return `<button class="lc-button${item.primary ? ' lc-button--brand' : ''}" type="button" data-agreement-action="${escapeHtml(item.action || item.label)}">${escapeHtml(item.label)}</button>`;
    }).join('');
    const details = (data.calculation || []).map(item => `<div><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.value)}</strong></div>`).join('');
    this.innerHTML = `<section class="lc-panel lc-mfg-agreement" aria-labelledby="${titleId}"><div class="lc-panel__header"><div><h2 class="lc-panel__title" id="${titleId}">${escapeHtml(data.title || 'Conditions de l’accord')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><div class="lc-panel__actions">${actions}</div></div><div class="lc-table-wrap" role="region" aria-label="${escapeHtml(data.tableRegionLabel || 'Échéanciers de l’accord')}" tabindex="0"><table class="lc-table"><caption class="lc-sr-only">${escapeHtml(data.caption || 'Engagements par produit et par période')}</caption><thead><tr><th scope="col">${escapeHtml(labels.productName || 'Nom du produit')}</th><th scope="col">${escapeHtml(labels.metricLabel || 'Métrique')}</th><th scope="col">${escapeHtml(labels.totalLabel || 'Total')}</th>${periods.map(period => `<th scope="col">${escapeHtml(period)}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div><aside class="lc-mfg-calculation" aria-label="${escapeHtml(data.calculationTitle || 'Détail du calcul')}"><h3>${escapeHtml(data.calculationTitle || 'Détail du calcul')}</h3><div class="lc-mfg-calculation__grid">${details}</div></aside></section>`;
    this.querySelectorAll('[data-agreement-action]').forEach(button => button.addEventListener('click', () => this.emitAction('manufacturing-agreement-action', { action: button.dataset.agreementAction })));
  }
}

class LcAccountManagerTarget extends JsonComponent {
  render() {
    const data = this.data;
    const titleId = `${this.id || 'account-target'}-title`;
    const labels = data.labels || {};
    const metrics = (data.metrics || []).map(metric => `<div><span>${escapeHtml(metric.label)}</span><strong>${escapeHtml(metric.value)}</strong><small>${escapeHtml(metric.context || '')}</small></div>`).join('');
    const actions = (data.actions || []).map(action => {
      const item = typeof action === 'string' ? { label: action, action } : action;
      return `<button class="lc-button${item.primary ? ' lc-button--brand' : ''}" type="button" data-target-action="${escapeHtml(item.action || item.label)}">${escapeHtml(item.label)}</button>`;
    }).join('');
    const rows = (data.assignments || []).map(item => `<tr><th scope="row">${escapeHtml(item.name)}</th><td>${escapeHtml(item.role)}</td><td>${escapeHtml(item.region)}</td><td>${escapeHtml(item.targetPercentage)}</td><td>${escapeHtml(item.targetValue)}</td><td>${escapeHtml(item.distributeBy)}</td></tr>`).join('');
    const distributionEntries = (data.distributionEntries || []).map(item => `<tr><th scope="row">${escapeHtml(item.assignee)}</th><td>${escapeHtml(item.account)}</td><td>${escapeHtml(item.product)}</td><td>${escapeHtml(item.target)}</td></tr>`).join('');
    const assignmentsId = `${this.id || 'account-target'}-assignments`;
    const distributionId = `${this.id || 'account-target'}-distribution`;
    this.innerHTML = `<section class="lc-panel lc-account-target" aria-labelledby="${titleId}"><div class="lc-panel__header"><div><h2 class="lc-panel__title" id="${titleId}">${escapeHtml(data.title || 'Objectif du responsable de compte')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><div class="lc-panel__actions">${actions}</div></div><div class="lc-account-target__metrics">${metrics}</div><div class="lc-account-target__body"><section class="lc-account-target__assignments" aria-labelledby="${assignmentsId}"><h3 id="${assignmentsId}">${escapeHtml(data.assignmentsTitle || 'Affectations de l’équipe')}</h3><div class="lc-table-wrap"><table class="lc-table"><caption class="lc-sr-only">${escapeHtml(data.caption || 'Affectations et répartition de l’équipe')}</caption><thead><tr><th scope="col">${escapeHtml(labels.member || 'Membre')}</th><th scope="col">${escapeHtml(labels.role || 'Rôle')}</th><th scope="col">${escapeHtml(labels.region || 'Zone')}</th><th scope="col">${escapeHtml(labels.targetPercentage || 'Pourcentage cible')}</th><th scope="col">${escapeHtml(labels.targetValue || 'Valeur cible')}</th><th scope="col">${escapeHtml(labels.distributeBy || 'Distribuer par')}</th></tr></thead><tbody>${rows}</tbody></table></div></section><aside class="lc-account-target__distribution" aria-labelledby="${distributionId}"><h3 id="${distributionId}">${escapeHtml(data.distributionTitle || 'Distribution des objectifs')}</h3><div class="lc-table-wrap"><table class="lc-table"><caption class="lc-sr-only">${escapeHtml(data.distributionCaption || data.distributionTitle || 'Distribution des objectifs')}</caption><thead><tr><th scope="col">${escapeHtml(labels.assignee || 'Affectation')}</th><th scope="col">${escapeHtml(labels.account || 'Compte')}</th><th scope="col">${escapeHtml(labels.product || 'Produit')}</th><th scope="col">${escapeHtml(labels.target || 'Objectif')}</th></tr></thead><tbody>${distributionEntries}</tbody></table></div></aside></div></section>`;
    this.querySelectorAll('[data-target-action]').forEach(button => button.addEventListener('click', () => this.emitAction('account-manager-target-action', { action: button.dataset.targetAction })));
  }
}

class LcManufacturingAssetOverview extends JsonComponent {
  render() {
    const data = this.data;
    const titleId = `${this.id || 'mfg-asset'}-title`;
    const identity = (data.identity || []).map(item => `<div><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.value)}</strong></div>`).join('');
    const coverage = (data.coverage || []).map(item => `<li><strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(item.value)}</span><small>${escapeHtml(item.status)}</small></li>`).join('');
    this.innerHTML = `<section class="lc-panel lc-mfg-asset" aria-labelledby="${titleId}"><div class="lc-panel__header"><div><h2 class="lc-panel__title" id="${titleId}">${escapeHtml(data.title || 'Identité et couverture de l’actif')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><span class="lc-badge lc-badge--${escapeHtml(data.statusTone || 'success')}">${escapeHtml(data.status || 'En service')}</span></div><div class="lc-mfg-asset__body"><div class="lc-mfg-asset__identity">${identity}</div><ul class="lc-mfg-asset__coverage" aria-label="${escapeHtml(data.coverageLabel || 'Couvertures de l’actif')}">${coverage}</ul></div></section>`;
  }
}

class LcAssetMilestones extends JsonComponent {
  render() {
    const data = this.data;
    const titleId = `${this.id || 'asset-milestones'}-title`;
    const items = (data.items || []).map(item => `<li ${item.current ? 'aria-current="step"' : ''}><span aria-hidden="true"></span><div><strong>${escapeHtml(item.label)}</strong><time>${escapeHtml(item.date)}</time><p>${escapeHtml(item.description || '')}</p><small>${escapeHtml(item.status)}</small></div></li>`).join('');
    this.innerHTML = `<section class="lc-panel lc-asset-milestones" aria-labelledby="${titleId}"><div class="lc-panel__header"><div><h2 class="lc-panel__title" id="${titleId}">${escapeHtml(data.title || 'Cycle de vie de l’actif')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><ol>${items}</ol></section>`;
  }
}

class LcAssetHierarchy extends JsonComponent {
  render() {
    const data = this.data;
    const titleId = `${this.id || 'asset-hierarchy'}-title`;
    this.treeData = data.nodes || [];
    this.labels = data.labels || {};
    this.innerHTML = `<section class="lc-panel lc-asset-hierarchy" aria-labelledby="${titleId}"><div class="lc-panel__header"><div><h2 class="lc-panel__title" id="${titleId}">${escapeHtml(data.title || 'Hiérarchie des actifs')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><div class="lc-tree-search"><label for="${this.id || 'asset-hierarchy'}-search">${escapeHtml(this.labels.search || 'Rechercher dans la hiérarchie')}</label><div><input class="lc-input" id="${this.id || 'asset-hierarchy'}-search" type="search" placeholder="${escapeHtml(this.labels.placeholder || 'Nom, modèle ou numéro de série')}" data-tree-search><button class="lc-button" type="button" data-tree-clear aria-label="${escapeHtml(this.labels.clearAria || 'Effacer la recherche')}">${escapeHtml(this.labels.clear || 'Effacer')}</button></div><p role="status" aria-live="polite" data-tree-status></p></div><div class="lc-tree" role="tree" aria-label="${escapeHtml(data.treeLabel || 'Arborescence des actifs')}" data-tree></div></section>`;
    this.tree = this.querySelector('[data-tree]');
    this.filter('');
    this.querySelector('[data-tree-search]').addEventListener('input', event => this.filter(event.target.value));
    this.querySelector('[data-tree-clear]').addEventListener('click', () => {
      const input = this.querySelector('[data-tree-search]');
      input.value = '';
      this.filter('');
      input.focus();
    });
    this.tree.addEventListener('keydown', event => this.onTreeKeydown(event));
    this.tree.addEventListener('click', event => {
      const item = event.target.closest('[role="treeitem"]');
      if (item) this.activate(item, event.target.matches('[data-tree-toggle]'));
    });
  }

  nodeMarkup(node, level = 1, term = '') {
    const ownMatch = `${node.label} ${node.meta || ''}`.toLowerCase().includes(term);
    const children = (node.children || []).filter(child => ownMatch || this.nodeMatches(child, term));
    const type = escapeHtml(node.type || 'asset');
    return `<div role="treeitem" aria-level="${level}" data-node-type="${type}" ${children.length ? 'aria-expanded="true"' : ''} tabindex="-1"><div class="lc-tree__row">${children.length ? `<button type="button" data-tree-toggle tabindex="-1" aria-label="${escapeHtml(this.labels.toggle || 'Réduire ou développer')}">⌄</button>` : '<span aria-hidden="true"></span>'}<strong>${escapeHtml(node.label)}</strong><small>${escapeHtml(node.meta || '')}</small><em>${escapeHtml(node.status || '')}</em></div>${children.length ? `<div role="group">${children.map(child => this.nodeMarkup(child, level + 1, term)).join('')}</div>` : ''}</div>`;
  }

  renderTree(nodes, term = '') {
    this.tree.innerHTML = nodes.map(node => this.nodeMarkup(node, 1, term)).join('');
    const first = this.visibleItems()[0];
    if (first) first.tabIndex = 0;
  }

  visibleItems() {
    return [...this.tree.querySelectorAll('[role="treeitem"]')].filter(item => !item.hidden && !item.closest('[role="group"][hidden]'));
  }

  focusItem(item) {
    if (!item) return;
    this.tree.querySelectorAll('[role="treeitem"]').forEach(node => { node.tabIndex = node === item ? 0 : -1; });
    item.focus();
  }

  activate(item, toggle = false) {
    if (toggle && item.hasAttribute('aria-expanded')) {
      const expanded = item.getAttribute('aria-expanded') === 'true';
      item.setAttribute('aria-expanded', String(!expanded));
      item.querySelector(':scope > [role="group"]').hidden = expanded;
    } else {
      this.emitAction('asset-hierarchy-open', { label: item.querySelector(':scope > .lc-tree__row strong').textContent });
    }
    this.focusItem(item);
  }

  onTreeKeydown(event) {
    const item = event.target.closest('[role="treeitem"]');
    if (!item) return;
    const items = this.visibleItems();
    const index = items.indexOf(item);
    if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Home', 'End', 'Enter', ' '].includes(event.key)) return;
    event.preventDefault();
    if (event.key === 'ArrowDown') this.focusItem(items[Math.min(items.length - 1, index + 1)]);
    else if (event.key === 'ArrowUp') this.focusItem(items[Math.max(0, index - 1)]);
    else if (event.key === 'Home') this.focusItem(items[0]);
    else if (event.key === 'End') this.focusItem(items.at(-1));
    else if (event.key === 'ArrowRight' && item.getAttribute('aria-expanded') === 'false') this.activate(item, true);
    else if (event.key === 'ArrowRight' && item.getAttribute('aria-expanded') === 'true') this.focusItem(item.querySelector(':scope > [role="group"] > [role="treeitem"]'));
    else if (event.key === 'ArrowLeft' && item.getAttribute('aria-expanded') === 'true') this.activate(item, true);
    else if (event.key === 'ArrowLeft') {
      const parent = item.parentElement.closest('[role="treeitem"]');
      if (parent) this.focusItem(parent);
    } else if (event.key === 'Enter' || event.key === ' ') this.activate(item);
  }

  filter(query) {
    const term = query.trim().toLowerCase();
    const matches = this.treeData.filter(node => this.nodeMatches(node, term));
    this.renderTree(matches, term);
    const nodes = this.visibleItems();
    const assetCount = nodes.filter(item => item.dataset.nodeType === 'asset').length;
    const status = this.querySelector('[data-tree-status]');
    if (!nodes.length) status.textContent = this.labels.noResults || 'Aucun résultat';
    else status.textContent = `${assetCount} actif${assetCount > 1 ? 's' : ''} dans ${nodes.length} nœud${nodes.length > 1 ? 's' : ''}`;
  }

  nodeMatches(node, term) {
    if (!term) return true;
    return `${node.label} ${node.meta || ''}`.toLowerCase().includes(term) || (node.children || []).some(child => this.nodeMatches(child, term));
  }
}

const definitions = {
  'lc-manufacturing-agreement-terms': LcManufacturingAgreementTerms,
  'lc-account-manager-target': LcAccountManagerTarget,
  'lc-manufacturing-asset-overview': LcManufacturingAssetOverview,
  'lc-asset-milestones': LcAssetMilestones,
  'lc-asset-hierarchy': LcAssetHierarchy,
};

for (const [name, constructor] of Object.entries(definitions)) {
  if (!customElements.get(name)) customElements.define(name, constructor);
}
