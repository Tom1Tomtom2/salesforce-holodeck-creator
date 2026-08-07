import { JsonComponent, escapeHtml, lcIcon } from './lightning-components.js';

class LcPipelineInspectionSummary extends JsonComponent {
  render() {
    const data = this.data;
    const tabs = (data.tabs || []).map((tab, index) => `<button type="button" role="tab" aria-selected="${index === Number(data.activeTab || 0)}" data-inspection-tab="${index}">${escapeHtml(tab)}</button>`).join('');
    const filters = (data.filters || []).map((filter, index) => `<button class="lc-button" type="button" data-inspection-filter="${index}">${escapeHtml(filter.label)} <strong>${escapeHtml(filter.value)}</strong></button>`).join('');
    const metrics = (data.metrics || []).map(metric => `<div><span>${escapeHtml(metric.label)}</span><strong class="${metric.direction === 'down' ? 'is-down' : metric.direction === 'up' ? 'is-up' : ''}">${escapeHtml(metric.value)}</strong></div>`).join('');
    this.innerHTML = `<section class="lc-pi-summary" aria-labelledby="pipeline-inspection-summary-title"><h2 class="lc-sr-only" id="pipeline-inspection-summary-title">${escapeHtml(data.title || 'Pipeline Inspection')}</h2><div class="lc-pi-summary__toolbar"><div class="lc-pi-summary__tabs" role="tablist" aria-label="Vues Pipeline Inspection">${tabs}</div><span>${escapeHtml(data.updated || '')}</span><div class="lc-pi-summary__filters">${filters}</div></div><div class="lc-pi-summary__metrics">${metrics}</div></section>`;
    this.querySelectorAll('[data-inspection-tab]').forEach(button => button.addEventListener('click', () => {
      this.querySelectorAll('[data-inspection-tab]').forEach(tab => tab.setAttribute('aria-selected', String(tab === button)));
      this.emitAction('pipeline-inspection-tab', { index: Number(button.dataset.inspectionTab) });
    }));
    this.querySelectorAll('[data-inspection-filter]').forEach(button => button.addEventListener('click', () => this.emitAction('pipeline-inspection-filter', { index: Number(button.dataset.inspectionFilter) })));
  }
}

class LcOpportunityInsightPanel extends JsonComponent {
  render() {
    const data = this.data;
    const stats = (data.stats || []).map(stat => `<div><span>${escapeHtml(stat.label)}</span><strong class="${stat.tone ? `is-${escapeHtml(stat.tone)}` : ''}">${escapeHtml(stat.value)}</strong></div>`).join('');
    const tabs = (data.tabs || []).map((tab, index) => `<button type="button" role="tab" aria-selected="${index === Number(data.activeTab || 0)}" data-insight-tab="${index}">${escapeHtml(tab)}</button>`).join('');
    const groups = (data.groups || []).map((group, groupIndex) => {
      const items = (group.items || []).map((item, itemIndex) => `<li><span class="lc-pi-signal is-${escapeHtml(item.tone || 'info')}">${item.tone === 'warning' ? '!' : '↑'}</span><div><strong>${escapeHtml(item.title)}</strong><p>${escapeHtml(item.detail)}</p>${item.action ? `<button type="button" data-insight-action="${groupIndex}:${itemIndex}">${escapeHtml(item.action)}</button>` : ''}</div><button class="lc-icon-button" type="button" aria-label="Masquer l'insight ${escapeHtml(item.title)}" data-insight-dismiss="${groupIndex}:${itemIndex}">×</button></li>`).join('');
      return `<section><h3>${escapeHtml(group.title)}</h3><ul>${items}</ul></section>`;
    }).join('');
    const actions = (data.actions || []).map(action => `<button class="lc-button ${action.primary ? 'lc-button--brand' : ''}" type="button" data-panel-action="${escapeHtml(action.action)}">${escapeHtml(action.label)}</button>`).join('');
    this.innerHTML = `<aside class="lc-pi-insights" aria-labelledby="opportunity-insights-title"><header><div><span>${escapeHtml(data.eyebrow || 'Opportunité')}</span><h2 id="opportunity-insights-title">${escapeHtml(data.title || '')}</h2></div><button class="lc-icon-button" type="button" aria-label="Fermer le panneau d'inspection" data-panel-action="close">×</button></header><div class="lc-pi-insights__stats">${stats}</div><div class="lc-pi-insights__tabs" role="tablist" aria-label="Détails de l'opportunité">${tabs}</div><div class="lc-pi-insights__content">${groups}</div><footer>${actions}</footer></aside>`;
    this.querySelectorAll('[data-insight-tab]').forEach(button => button.addEventListener('click', () => {
      this.querySelectorAll('[data-insight-tab]').forEach(tab => tab.setAttribute('aria-selected', String(tab === button)));
      this.emitAction('opportunity-insight-tab', { index: Number(button.dataset.insightTab) });
    }));
    this.querySelectorAll('[data-insight-action]').forEach(button => button.addEventListener('click', () => this.emitAction('opportunity-insight-action', { item: button.dataset.insightAction })));
    this.querySelectorAll('[data-insight-dismiss]').forEach(button => button.addEventListener('click', () => {
      button.closest('li').remove();
      this.emitAction('opportunity-insight-dismiss', { item: button.dataset.insightDismiss });
    }));
    this.querySelectorAll('[data-panel-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.panelAction)));
  }
}

const definitions = {
  'lc-pipeline-inspection-summary': LcPipelineInspectionSummary,
  'lc-opportunity-insight-panel': LcOpportunityInsightPanel,
};

for (const [name, constructor] of Object.entries(definitions)) {
  if (!customElements.get(name)) customElements.define(name, constructor);
}
