import { JsonComponent, escapeHtml, lcIcon } from './lightning-components.js';

const nodeIcons = { start: '▶', email: '✉', whatsapp: '◉', sms: 'SMS', wait: '◷', decision: '◆', action: 'ϟ', assignment: '≡', end: '■' };
const nodeTones = { start: 'teal', email: 'navy', whatsapp: 'navy', sms: 'navy', wait: 'orange', decision: 'orange', action: 'navy', assignment: 'orange', end: 'red' };

class LcMarketingHeader extends JsonComponent {
  render() {
    const data = this.data;
    const actions = (data.actions || []).map(action => `<button class="lc-button ${action.primary ? 'lc-button--brand' : ''}" type="button" data-marketing-action="${escapeHtml(action.action)}">${escapeHtml(action.label)}</button>`).join('');
    const metrics = (data.metrics || []).map(metric => `<div><span>${escapeHtml(metric.label)}</span><strong>${escapeHtml(metric.value)}</strong></div>`).join('');
    this.innerHTML = `<section class="lc-marketing-header" aria-labelledby="marketing-title"><div class="lc-marketing-header__main"><span class="lc-object-icon lc-object-icon--campaign">◎</span><div><span>${escapeHtml(data.type || 'Campaign')}</span><h1 id="marketing-title">${escapeHtml(data.title || 'Marketing Campaign')}</h1><p>${escapeHtml(data.subtitle || '')}</p></div></div><div class="lc-marketing-header__actions"><span class="lc-badge">${escapeHtml(data.status || '')}</span>${actions}</div><div class="lc-marketing-header__metrics">${metrics}</div></section>`;
    this.querySelectorAll('[data-marketing-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.marketingAction)));
  }
}

class LcCampaignWorkspace extends JsonComponent {
  render() {
    const data = this.data;
    const segments = (data.segments || []).map((segment, index) => `<button class="lc-campaign-item" type="button" data-campaign-segment="${index}"><span class="lc-campaign-item__icon is-segment">◎</span><span><strong>${escapeHtml(segment.name)}</strong><small>${escapeHtml(segment.population)} people</small></span><span aria-hidden="true">›</span></button>`).join('');
    const messages = (data.messages || []).map((message, index) => `<button class="lc-campaign-message" type="button" data-campaign-message="${index}"><span class="lc-campaign-item__icon">${message.channel === 'Email' ? '✉' : '◉'}</span><span><small>${escapeHtml(message.channel)}</small><strong>${escapeHtml(message.title)}</strong><span>${escapeHtml(message.subject)}</span></span><span class="lc-badge ${message.status === 'Ready' ? 'lc-badge--success' : ''}">${escapeHtml(message.status)}</span></button>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div class="lc-panel__heading"><span class="lc-object-icon lc-object-icon--flow">≈</span><div><h2 class="lc-panel__title">${escapeHtml(data.title)}</h2><div class="lc-panel__meta">${escapeHtml(data.flowType)}</div></div></div><div class="lc-panel__actions"><button class="lc-button" type="button" data-open-flow>Open Flow</button><button class="lc-button lc-button--brand" type="button" data-activate-flow>Activate</button></div></div><div class="lc-campaign-facts"><div><span>Status</span><strong>${escapeHtml(data.status)}</strong></div><div><span>Owner</span><strong>${escapeHtml(data.owner)}</strong></div><div><span>Flow Type</span><strong>${escapeHtml(data.flowType)}</strong></div></div><div class="lc-campaign-section"><h3>Start: Segments (${(data.segments || []).length})</h3>${segments}</div><div class="lc-campaign-section"><h3>Messages (${(data.messages || []).length})</h3>${messages}</div></section>`;
    this.querySelector('[data-open-flow]').addEventListener('click', () => this.emitAction('open-flow'));
    this.querySelector('[data-activate-flow]').addEventListener('click', () => this.emitAction('activate-flow'));
    this.querySelectorAll('[data-campaign-segment]').forEach(button => button.addEventListener('click', () => this.emitAction('campaign-segment-select', { segment: data.segments[Number(button.dataset.campaignSegment)] })));
    this.querySelectorAll('[data-campaign-message]').forEach(button => button.addEventListener('click', () => this.emitAction('campaign-message-select', { message: data.messages[Number(button.dataset.campaignMessage)] })));
  }
}

class LcJourneyBuilder extends JsonComponent {
  render() {
    const data = this.data;
    const nodes = data.nodes || [];
    const nodeMarkup = nodes.map((node, index) => `<div class="lc-journey-node-wrap" style="grid-row:${Number(node.row)};grid-column:${Number(node.column)}"><span class="lc-journey-branch">${escapeHtml(node.branch || '')}</span><button class="lc-journey-node" type="button" data-journey-node="${index}"><span class="lc-journey-node__icon is-${nodeTones[node.type] || 'navy'}">${escapeHtml(nodeIcons[node.type] || '•')}</span><span><strong>${escapeHtml(node.title)}</strong><small>${escapeHtml(node.subtitle)}</small></span></button>${node.type !== 'end' ? `<button class="lc-journey-add" type="button" aria-label="Add element after ${escapeHtml(node.title)}" data-journey-add="${index}">+</button>` : ''}</div>`).join('');
    const picker = (data.picker || []).map((item, index) => `<button type="button" data-picker-item="${index}"><span>${['◈', '↕', '▽', '◷', '◷', '◷', '◇', '✉', 'SMS', '◉'][index] || '+'}</span>${escapeHtml(item)}</button>`).join('');
    this.innerHTML = `<section class="lc-panel lc-journey-builder"><div class="lc-journey-toolbar"><div><strong>${escapeHtml(data.title)}</strong><span>${escapeHtml(data.saved)} · <b>${escapeHtml(data.status)}</b></span></div><div><button class="lc-button" type="button" data-journey-action="debug">Debug</button><button class="lc-button" type="button" data-journey-action="save-version">Save As New Version</button><button class="lc-button lc-button--brand" type="button" data-journey-action="save-journey">Save</button></div></div><div class="lc-journey-canvas"><svg viewBox="0 0 900 930" preserveAspectRatio="none" aria-hidden="true"><path d="M450 75V475M450 475C450 525 195 505 195 575V720C195 770 450 750 450 815M450 475V815M450 475C450 525 705 505 705 575V720C705 770 450 750 450 815M450 815V900"/></svg><div class="lc-journey-grid">${nodeMarkup}</div><div class="lc-element-picker" hidden data-element-picker><div><strong>Add Element</strong><button type="button" aria-label="Close element picker" data-close-picker>×</button></div><input class="lc-input" type="search" placeholder="Search..." aria-label="Search journey elements"><div>${picker}</div></div><div class="lc-journey-zoom"><button type="button" aria-label="Zoom out">−</button><button type="button" aria-label="Fit journey">↗</button><button type="button" aria-label="Zoom in">+</button></div></div></section>`;
    const pickerElement = this.querySelector('[data-element-picker]');
    this.querySelectorAll('[data-journey-add]').forEach(button => button.addEventListener('click', () => { pickerElement.hidden = false; this.activeNode = Number(button.dataset.journeyAdd); pickerElement.querySelector('input').focus(); }));
    this.querySelector('[data-close-picker]').addEventListener('click', () => { pickerElement.hidden = true; });
    this.querySelectorAll('[data-picker-item]').forEach(button => button.addEventListener('click', () => { const item = data.picker[Number(button.dataset.pickerItem)]; pickerElement.hidden = true; this.emitAction('journey-element-add', { afterIndex: this.activeNode, element: item }); }));
    this.querySelectorAll('[data-journey-node]').forEach(button => button.addEventListener('click', () => this.emitAction('journey-node-select', { node: nodes[Number(button.dataset.journeyNode)] })));
    this.querySelectorAll('[data-journey-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.journeyAction)));
  }
}

class LcEmailStudio extends JsonComponent {
  render() {
    const data = this.data;
    const components = (data.components || []).map((component, index) => `<button type="button" data-email-component="${index}"><span>${['▣', '—', 'A', '</>', '▧', '☷', '¶', '▥'][index] || '□'}</span>${escapeHtml(component)}</button>`).join('');
    const messages = (data.assistant || []).map(message => `<div class="lc-assistant-message is-${escapeHtml(message.role)}"><span>${message.role === 'assistant' ? '✦' : '●'}</span><p>${escapeHtml(message.text)}</p></div>`).join('');
    const email = data.email || {};
    this.innerHTML = `<section class="lc-panel lc-email-studio"><div class="lc-email-toolbar"><div><strong>${escapeHtml(data.title)}</strong><span>Last saved a few seconds ago</span></div><label>View Mode <select class="lc-select" data-email-mode><option>Desktop</option><option>Mobile</option></select></label><button class="lc-button lc-button--brand" type="button" data-email-save>Save</button></div><div class="lc-email-layout"><aside class="lc-email-palette"><h2>Components</h2><input class="lc-input" type="search" placeholder="Search" aria-label="Search email components"><div>${components}</div></aside><main class="lc-email-editor"><div class="lc-email-meta"><label><span>Subject Line</span><input class="lc-input" value="${escapeHtml(data.subject)}" data-email-subject></label><label><span>Preheader</span><input class="lc-input" value="${escapeHtml(data.preheader)}" data-email-preheader></label></div><div class="lc-email-preview"><article class="lc-email-artboard"><header><strong>${escapeHtml(email.brand)}</strong></header><div class="lc-email-hero"><span>${escapeHtml(email.hero)}</span></div><div class="lc-email-copy"><span>${escapeHtml(email.eyebrow)}</span><h2>${escapeHtml(email.headline)}</h2><p>${escapeHtml(email.body)}</p><button type="button" data-email-cta>${escapeHtml(email.cta)}</button><small>${escapeHtml(email.footer)}</small></div></article></div></main><aside class="lc-marketing-assistant"><header><strong>Agentforce</strong><span>✦</span></header><div>${messages}</div><div class="lc-assistant-actions"><button class="lc-button" type="button" data-ai-action="apply-copy">Apply</button><button class="lc-button" type="button" data-ai-action="try-again">Try Again</button></div><label><span class="lc-sr-only">Ask Agentforce</span><textarea class="lc-textarea" placeholder="Describe your task or ask a question..."></textarea></label></aside></div></section>`;
    this.querySelector('[data-email-mode]').value = data.viewMode || 'Desktop';
    this.querySelector('[data-email-mode]').addEventListener('change', event => this.querySelector('.lc-email-artboard').classList.toggle('is-mobile', event.target.value === 'Mobile'));
    this.querySelector('[data-email-save]').addEventListener('click', () => this.emitAction('save-email'));
    this.querySelectorAll('[data-email-component]').forEach(button => button.addEventListener('click', () => this.emitAction('email-component-add', { component: data.components[Number(button.dataset.emailComponent)] })));
    this.querySelectorAll('[data-ai-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.aiAction)));
    this.querySelector('[data-email-cta]').addEventListener('click', () => this.emitAction('email-cta-preview'));
  }
}

class LcSegmentBuilder extends JsonComponent {
  render() {
    const data = this.data;
    const percentage = Number(data.population) / Math.max(1, Number(data.totalPopulation)) * 100;
    const attributes = (data.attributes || []).map(attribute => `<button type="button" data-segment-attribute="${escapeHtml(attribute)}">${escapeHtml(attribute)}<span>›</span></button>`).join('');
    const rules = (data.rules || []).map((rule, index) => `<section class="lc-rule-group"><header><span>⋮⋮</span><strong>${escapeHtml(rule.group)}</strong><span>Count</span><b>${escapeHtml(rule.count)}</b></header>${(rule.conditions || []).map(condition => `<div><span>⋮⋮</span>${escapeHtml(condition)}</div>`).join('')}<button type="button" data-add-rule="${index}">+ Add condition</button></section>`).join('');
    const messages = (data.assistant || []).map(message => `<div class="lc-assistant-message is-${escapeHtml(message.role)}"><span>${message.role === 'assistant' ? '✦' : '●'}</span><p>${escapeHtml(message.text)}</p></div>`).join('');
    this.innerHTML = `<section class="lc-panel lc-segment-builder"><div class="lc-segment-title"><div><span>Segment</span><h2>${escapeHtml(data.title)}</h2></div><div><span>Segment On</span><strong>${escapeHtml(data.object)}</strong></div><button class="lc-button lc-button--brand" type="button" data-save-segment>Save Segment</button></div><div class="lc-segment-layout"><aside class="lc-attribute-panel"><div class="lc-tabs"><button class="lc-tab" type="button" aria-selected="true">Attributes</button><button class="lc-tab" type="button">Segments</button></div><input class="lc-input" type="search" placeholder="Search..." aria-label="Search segment attributes"><h3>Related Attributes</h3><div>${attributes}</div></aside><main class="lc-segment-rules"><div class="lc-segment-population"><button type="button" aria-label="Refresh segment population">↻</button><div><span>Segment Population</span><strong>${Number(data.population).toLocaleString('en-US')}</strong><small>${percentage.toFixed(1)}% of ${Number(data.totalPopulation).toLocaleString('en-US')} total population</small></div><div class="lc-progress" role="progressbar" aria-label="Segment population percentage" aria-valuenow="${percentage}" aria-valuemin="0" aria-valuemax="100"><div class="lc-progress__bar" style="width:${percentage}%"></div></div></div><div class="lc-segment-description"><strong>${escapeHtml(data.description)}</strong></div><div class="lc-segment-include"><button type="button" aria-selected="true">Include</button><button type="button">Exclude</button></div>${rules}</main><aside class="lc-marketing-assistant"><header><strong>Einstein</strong><span>✦</span></header><div>${messages}</div><div class="lc-assistant-actions"><button class="lc-button" type="button" data-segment-ai="regenerate-segment">Regenerate</button><button class="lc-button" type="button" data-segment-ai="explain-attributes">Explain Attributes</button></div><label><span class="lc-sr-only">Ask Einstein about this segment</span><textarea class="lc-textarea" placeholder="Describe your task or ask a question..."></textarea></label></aside></div></section>`;
    this.querySelector('[data-save-segment]').addEventListener('click', () => this.emitAction('save-segment'));
    this.querySelectorAll('[data-segment-attribute]').forEach(button => button.addEventListener('click', () => this.emitAction('segment-attribute-select', { attribute: button.dataset.segmentAttribute })));
    this.querySelectorAll('[data-add-rule]').forEach(button => button.addEventListener('click', () => this.emitAction('segment-rule-add', { groupIndex: Number(button.dataset.addRule) })));
    this.querySelectorAll('[data-segment-ai]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.segmentAi)));
  }
}

class LcMarketingPerformance extends JsonComponent {
  render() {
    const data = this.data;
    const channels = (data.channels || []).map(channel => `<button type="button" class="${channel === data.activeChannel ? 'is-active' : ''}" data-channel="${escapeHtml(channel)}">${escapeHtml(channel)}</button>`).join('');
    const metrics = (data.metrics || []).map(metric => { const values = metric.values || []; const min = Math.min(...values.map(Number)); const max = Math.max(...values.map(Number), min + 1); const points = values.map((value, index) => `${4 + index * (142 / Math.max(1, values.length - 1))},${39 - (Number(value) - min) / (max - min) * 34}`).join(' '); return `<article class="lc-marketing-metric"><span>${escapeHtml(metric.label)}</span><strong>${escapeHtml(metric.value)}</strong><small class="${metric.direction === 'up' ? 'is-up' : 'is-down'}">${escapeHtml(metric.change)}</small><svg viewBox="0 0 150 44" aria-hidden="true"><polyline points="${points}" fill="none" stroke="#0176d3" stroke-width="3"/></svg></article>`; }).join('');
    const rows = (data.campaigns || []).map((campaign, index) => `<tr><td><button type="button" data-performance-campaign="${index}">${escapeHtml(campaign.name)}</button></td><td>${escapeHtml(campaign.channel)}</td><td>${escapeHtml(campaign.sent)}</td><td>${escapeHtml(campaign.delivered)}</td><td>${escapeHtml(campaign.opens)}</td><td>${escapeHtml(campaign.clicks)}</td><td>${escapeHtml(campaign.ctr)}</td><td><strong>${escapeHtml(campaign.revenue)}</strong></td></tr>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title)}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div><label>Content <select class="lc-select"><option>All</option><option>Campaign</option><option>Transactional</option></select></label></div><div class="lc-channel-tabs">${channels}</div><div class="lc-marketing-metrics">${metrics}</div><div class="lc-performance-table"><h3>Successful Send Details</h3><div class="lc-table-wrap"><table class="lc-table"><thead><tr><th>Campaign Name</th><th>Channel</th><th>Sent</th><th>Delivered</th><th>Opens</th><th>Clicks</th><th>CTR</th><th>Revenue</th></tr></thead><tbody>${rows}</tbody></table></div></div></section>`;
    this.querySelectorAll('[data-channel]').forEach(button => button.addEventListener('click', () => { this.querySelectorAll('[data-channel]').forEach(item => item.classList.toggle('is-active', item === button)); this.emitAction('marketing-channel-select', { channel: button.dataset.channel }); }));
    this.querySelectorAll('[data-performance-campaign]').forEach(button => button.addEventListener('click', () => this.emitAction('performance-campaign-select', { campaign: data.campaigns[Number(button.dataset.performanceCampaign)] })));
  }
}

const definitions = {
  'lc-marketing-header': LcMarketingHeader,
  'lc-campaign-workspace': LcCampaignWorkspace,
  'lc-journey-builder': LcJourneyBuilder,
  'lc-email-studio': LcEmailStudio,
  'lc-segment-builder': LcSegmentBuilder,
  'lc-marketing-performance': LcMarketingPerformance,
};

for (const [name, constructor] of Object.entries(definitions)) {
  if (!customElements.get(name)) customElements.define(name, constructor);
}
