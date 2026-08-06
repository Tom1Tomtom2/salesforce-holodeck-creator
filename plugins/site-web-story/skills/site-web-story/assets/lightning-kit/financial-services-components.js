import { JsonComponent, escapeHtml, lcIcon } from './lightning-components.js';

function loanControl(field, index) {
  const id = `loan-field-${index}`;
  const required = field.required ? ' required' : '';
  const requiredMark = field.required ? '<span aria-hidden="true">*</span> ' : '';
  if (field.type === 'select') {
    const options = (field.options || []).map(option => `<option ${option === field.value ? 'selected' : ''}>${escapeHtml(option)}</option>`).join('');
    return `<label for="${id}">${requiredMark}${escapeHtml(field.label)}</label><select class="lc-select" id="${id}" name="${escapeHtml(field.name || field.label)}"${required}>${options}</select>`;
  }
  return `<label for="${id}">${requiredMark}${escapeHtml(field.label)}</label><input class="lc-input" id="${id}" name="${escapeHtml(field.name || field.label)}" type="${escapeHtml(field.type || 'text')}" value="${escapeHtml(field.value || '')}" placeholder="${escapeHtml(field.placeholder || '')}" autocomplete="${escapeHtml(field.autocomplete || 'off')}"${required}>`;
}

function loanTone(state = '') {
  const normalized = state.toLowerCase();
  if (['complete', 'completed', 'approved', 'received', 'verified'].some(value => normalized.includes(value))) return 'success';
  if (['blocked', 'rejected', 'missing', 'overdue'].some(value => normalized.includes(value))) return 'error';
  if (['progress', 'review', 'requested', 'pending'].some(value => normalized.includes(value))) return 'warning';
  return 'brand';
}

class LcLoanProductCatalog extends JsonComponent {
  render() {
    const data = this.data;
    const products = (data.products || []).map((product, index) => `<article class="lc-loan-product"><div class="lc-loan-product__visual" aria-hidden="true"><span>${['%', '⌂', '✓'][index % 3]}</span></div><div class="lc-loan-product__body"><h2>${escapeHtml(product.name)}</h2><p>${escapeHtml(product.description)}</p><button class="lc-loan-product__link" type="button" data-loan-product="${index}">${escapeHtml(product.action || 'En savoir plus')} <span aria-hidden="true">→</span></button></div></article>`).join('');
    this.innerHTML = `<section aria-labelledby="${this.id || 'loan-products-title'}"><div class="lc-loan-hero"><div><span>${escapeHtml(data.eyebrow || 'Financement')}</span><h1 id="${this.id || 'loan-products-title'}">${escapeHtml(data.title || 'Des prêts adaptés à vos projets')}</h1><p>${escapeHtml(data.subtitle || '')}</p></div></div><div class="lc-loan-products">${products}</div></section>`;
    this.querySelectorAll('[data-loan-product]').forEach(button => button.addEventListener('click', () => this.emitAction('loan-product-select', { index: Number(button.dataset.loanProduct), product: data.products[Number(button.dataset.loanProduct)] })));
  }
}

class LcLoanApplicationForm extends JsonComponent {
  render() {
    const data = this.data;
    const fields = (data.fields || []).map((field, index) => `<div class="lc-loan-field ${field.wide ? 'is-wide' : ''}">${loanControl(field, index)}</div>`).join('');
    const steps = (data.steps || []).map((step, index) => `<li class="${index < Number(data.currentStep || 0) ? 'is-complete' : index === Number(data.currentStep || 0) ? 'is-current' : ''}" ${index === Number(data.currentStep || 0) ? 'aria-current="step"' : ''}><span>${index < Number(data.currentStep || 0) ? '✓' : index + 1}</span>${escapeHtml(step)}</li>`).join('');
    this.innerHTML = `<section class="lc-panel lc-loan-application"><form><div class="lc-loan-form"><div class="lc-loan-form__header"><span>${escapeHtml(data.eyebrow || 'Demande de prêt')}</span><h1>${escapeHtml(data.title || 'Informations personnelles')}</h1><p>${escapeHtml(data.description || '')}</p></div><div class="lc-loan-fields">${fields}</div><div class="lc-loan-form__actions"><button class="lc-button" type="button" data-loan-back>${escapeHtml(data.backLabel || 'Retour')}</button><button class="lc-button lc-button--brand" type="submit">${escapeHtml(data.nextLabel || 'Enregistrer et continuer')}</button></div></div><aside class="lc-loan-steps" aria-label="Étapes de la demande"><h2>${escapeHtml(data.stepsTitle || 'Étapes')}</h2><ol>${steps}</ol></aside></form></section>`;
    this.querySelector('[data-loan-back]').addEventListener('click', () => this.emitAction('loan-form-back'));
    this.querySelector('form').addEventListener('submit', event => {
      event.preventDefault();
      this.emitAction('loan-form-next', { values: Object.fromEntries(new FormData(event.currentTarget)) });
    });
  }
}

class LcLoanRecordTree extends JsonComponent {
  render() {
    const data = this.data;
    const groups = (data.groups || []).map((group, groupIndex) => `<section class="lc-loan-tree__group"><button type="button" aria-expanded="true" data-loan-group="${groupIndex}"><span aria-hidden="true">⌄</span><strong>${escapeHtml(group.label)}</strong><span class="lc-badge">${(group.items || []).length}</span></button><div data-loan-group-content="${groupIndex}">${(group.items || []).map((item, itemIndex) => `<button class="lc-loan-tree__item ${item.active ? 'is-active' : ''}" type="button" data-loan-item="${groupIndex}:${itemIndex}"><span class="lc-object-icon">${lcIcon(item.icon || 'activity')}</span>${escapeHtml(item.label)}</button>`).join('')}</div></section>`).join('');
    this.innerHTML = `<nav class="lc-panel lc-loan-tree" aria-label="${escapeHtml(data.label || 'Dossier de prêt')}"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Dossier')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div>${data.root ? `<button class="lc-loan-tree__root is-active" type="button" data-loan-root>${escapeHtml(data.root)}</button>` : ''}<div class="lc-loan-tree__groups">${groups}</div></nav>`;
    this.querySelectorAll('[data-loan-group]').forEach(button => button.addEventListener('click', () => {
      const content = this.querySelector(`[data-loan-group-content="${button.dataset.loanGroup}"]`);
      const expanded = button.getAttribute('aria-expanded') === 'true';
      button.setAttribute('aria-expanded', String(!expanded));
      button.firstElementChild.textContent = expanded ? '›' : '⌄';
      content.hidden = expanded;
    }));
    this.querySelectorAll('[data-loan-item]').forEach(button => button.addEventListener('click', () => this.emitAction('loan-record-select', { path: button.dataset.loanItem })));
  }
}

class LcLoanKeyRatios extends JsonComponent {
  render() {
    const data = this.data;
    const facts = (data.facts || []).map(fact => `<div><span>${escapeHtml(fact.label)}</span><strong>${escapeHtml(fact.value)}</strong></div>`).join('');
    const ratios = (data.ratios || []).map(ratio => {
      const value = Math.max(0, Math.min(100, Number(ratio.value)));
      return `<article class="lc-loan-ratio"><div class="lc-loan-ratio__chart" role="img" aria-label="${escapeHtml(`${ratio.label}: ${ratio.display || `${value}%`}`)}" style="--loan-ratio:${value};--loan-ratio-color:${escapeHtml(ratio.color || '#0176d3')}"><span>${escapeHtml(ratio.display || `${value}%`)}</span></div><h3>${escapeHtml(ratio.label)}</h3><p>${escapeHtml(ratio.context || '')}</p></article>`;
    }).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Ratios clés')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><div class="lc-loan-facts">${facts}</div><div class="lc-loan-ratios">${ratios}</div></section>`;
  }
}

class LcLoanStageBoard extends JsonComponent {
  render() {
    const data = this.data;
    const stages = (data.stages || []).map((stage, index) => `<article class="lc-loan-stage is-${escapeHtml(loanTone(stage.state))}"><header><span>${index + 1}</span><h3>${escapeHtml(stage.label)}</h3><span class="lc-badge lc-badge--${escapeHtml(loanTone(stage.state))}">${escapeHtml(stage.state)}</span></header>${stage.owner ? `<div><span>Responsable</span><strong>${escapeHtml(stage.owner)}</strong></div>` : ''}${stage.completed ? `<div><span>Terminé le</span><strong>${escapeHtml(stage.completed)}</strong></div>` : ''}<button type="button" aria-label="Ouvrir ${escapeHtml(stage.label)}" data-loan-stage="${index}">${lcIcon('chevron')}</button></article>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Vue des étapes')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><label class="lc-loan-stage-filter"><span>Afficher</span><select class="lc-select" data-loan-stage-filter>${(data.filters || ['Toutes']).map(filter => `<option>${escapeHtml(filter)}</option>`).join('')}</select></label></div><div class="lc-loan-stage-board">${stages}</div></section>`;
    this.querySelectorAll('[data-loan-stage]').forEach(button => button.addEventListener('click', () => this.emitAction('loan-stage-select', { index: Number(button.dataset.loanStage), stage: data.stages[Number(button.dataset.loanStage)] })));
    this.querySelector('[data-loan-stage-filter]').addEventListener('change', event => this.emitAction('loan-stage-filter', { value: event.target.value }));
  }
}

class LcStructuredSummary extends JsonComponent {
  render() {
    const data = this.data;
    const sections = (data.sections || []).map(section => `<section class="lc-structured-summary__section"><h3>${escapeHtml(section.title)}</h3>${section.description ? `<p>${escapeHtml(section.description)}</p>` : ''}<dl>${(section.items || []).map(item => `<div><dt>${escapeHtml(item.label)}</dt><dd>${escapeHtml(item.value)}</dd></div>`).join('')}</dl>${section.bullets ? `<ul>${section.bullets.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>` : ''}</section>`).join('');
    this.innerHTML = `<section class="lc-panel lc-structured-summary"><div class="lc-panel__header"><div class="lc-panel__heading"><span class="lc-object-icon">${lcIcon(data.icon || 'spark')}</span><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Résumé')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div>${data.badge ? `<span class="lc-badge">${escapeHtml(data.badge)}</span>` : ''}</div><div class="lc-structured-summary__body">${data.alert ? `<div class="lc-structured-summary__alert">${escapeHtml(data.alert)}</div>` : ''}${sections}</div></section>`;
  }
}

class LcAgentConversation extends JsonComponent {
  render() {
    const data = this.data;
    const messages = (data.messages || []).map(message => `<div class="lc-agent-message is-${escapeHtml(message.role || 'assistant')}"><span class="lc-agent-message__avatar" aria-hidden="true">${message.role === 'user' ? '●' : '✦'}</span><div><strong>${escapeHtml(message.author || (message.role === 'user' ? 'Vous' : 'Agentforce'))}</strong><p>${escapeHtml(message.text)}</p>${message.bullets ? `<ul>${message.bullets.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>` : ''}</div></div>`).join('');
    this.innerHTML = `<section class="lc-panel lc-agent-conversation" aria-labelledby="${this.id || 'agent-conversation-title'}"><div class="lc-agent-conversation__header"><div><span>✦</span><h2 id="${this.id || 'agent-conversation-title'}">${escapeHtml(data.title || 'Agentforce')}</h2></div><span class="lc-badge lc-badge--success">${escapeHtml(data.status || 'Disponible')}</span></div><div class="lc-agent-conversation__messages">${messages}</div><form><label class="lc-sr-only" for="${this.id || 'agent'}-prompt">${escapeHtml(data.promptLabel || 'Décrivez votre demande')}</label><textarea class="lc-textarea" id="${this.id || 'agent'}-prompt" name="prompt" placeholder="${escapeHtml(data.placeholder || 'Décrivez votre demande ou posez une question…')}"></textarea><button class="lc-button lc-button--brand" type="submit">${escapeHtml(data.sendLabel || 'Envoyer')}</button></form></section>`;
    this.querySelector('form').addEventListener('submit', event => {
      event.preventDefault();
      const prompt = new FormData(event.currentTarget).get('prompt');
      if (String(prompt).trim()) this.emitAction('agent-message', { prompt });
    });
  }
}

const definitions = {
  'lc-loan-product-catalog': LcLoanProductCatalog,
  'lc-loan-application-form': LcLoanApplicationForm,
  'lc-loan-record-tree': LcLoanRecordTree,
  'lc-loan-key-ratios': LcLoanKeyRatios,
  'lc-loan-stage-board': LcLoanStageBoard,
  'lc-structured-summary': LcStructuredSummary,
  'lc-agent-conversation': LcAgentConversation,
};

for (const [name, constructor] of Object.entries(definitions)) {
  if (!customElements.get(name)) customElements.define(name, constructor);
}
