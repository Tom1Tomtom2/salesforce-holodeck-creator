const iconPaths = {
  account: '<path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16M9 7h2m2 0h2M9 11h2m2 0h2M9 15h2m2 0h2M3 21h18"/>',
  contact: '<path d="M8 7a4 4 0 1 0 8 0 4 4 0 0 0-8 0Zm-3 14a7 7 0 0 1 14 0M4 4h2m12 0h2M4 8h2m12 0h2M4 12h2m12 0h2"/>',
  case: '<path d="M9 6V4h6v2m-9 0h12a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2Zm-2 6h16M9 12v2h6v-2"/>',
  activity: '<path d="M7 3v3m10-3v3M4 9h16M5 5h14a1 1 0 0 1 1 1v14H4V6a1 1 0 0 1 1-1Zm3 8h3m-3 4h6"/>',
  task: '<path d="M9 5h10v16H5V9m0 0 4-4v4H5Zm5 4h5m-5 4h5"/>',
  email: '<path d="M3 5h18v14H3V5Zm0 2 9 7 9-7"/>',
  phone: '<path d="M7 3 4 6c0 7.7 6.3 14 14 14l3-3-4-4-3 2a12 12 0 0 1-5-5l2-3-4-4Z"/>',
  event: '<path d="M7 3v3m10-3v3M4 9h16M5 5h14a1 1 0 0 1 1 1v14H4V6a1 1 0 0 1 1-1Zm4 8h2v2H9v-2Zm4 0h2v2h-2v-2Z"/>',
  spark: '<path d="m12 2 2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2Zm7 15 .8 2.2L22 20l-2.2.8L19 23l-.8-2.2L16 20l2.2-.8L19 17Z"/>',
  trend: '<path d="m4 16 5-5 4 4 7-8m-5 0h5v5"/>',
  chevron: '<path d="m9 18 6-6-6-6"/>',
  close: '<path d="m6 6 12 12M18 6 6 18"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
  location: '<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="8"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2"/>',
};

export function lcIcon(name, label = '') {
  const path = iconPaths[name] || iconPaths.activity;
  const accessibility = label
    ? `role="img" aria-label="${escapeHtml(label)}"`
    : 'aria-hidden="true"';
  return `<span class="lc-icon" ${accessibility}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${path}</svg></span>`;
}

export function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

export function readJsonScript(element, selector = 'script[type="application/json"]') {
  const script = element.querySelector(selector);
  if (!script) return {};
  try {
    return JSON.parse(script.textContent);
  } catch (error) {
    console.error(`Invalid JSON in <${element.localName}>`, error);
    return {};
  }
}

export function buttonMarkup(action, kind = 'neutral') {
  const variant = kind === 'brand' ? ' lc-button--brand' : '';
  return `<button class="lc-button${variant}" type="button" data-action="${escapeHtml(action.action || action.label)}">${escapeHtml(action.label)}</button>`;
}

export class JsonComponent extends HTMLElement {
  connectedCallback() {
    this.data = readJsonScript(this);
    this.render();
  }

  emitAction(action, detail = {}) {
    this.dispatchEvent(new CustomEvent('lc-action', {
      bubbles: true,
      detail: { action, ...detail },
    }));
  }
}

class LcRecordHeader extends JsonComponent {
  render() {
    const data = this.data;
    const type = data.type || 'Record';
    const icon = (data.icon || type).toLowerCase();
    const highlights = (data.highlights || []).map(item => `
      <div class="lc-highlight">
        <div class="lc-highlight__label">${escapeHtml(item.label)}</div>
        <div class="lc-highlight__value">${item.href ? `<a href="${escapeHtml(item.href)}">${escapeHtml(item.value)}</a>` : escapeHtml(item.value)}</div>
      </div>`).join('');
    const actions = (data.actions || []).map((action, index) => buttonMarkup(action, index === 0 && action.primary ? 'brand' : 'neutral')).join('');
    this.innerHTML = `
      <section class="lc-record-header" aria-labelledby="${this.id || 'record-title'}">
        <div class="lc-record-header__identity">
          <span class="lc-object-icon lc-object-icon--${escapeHtml(icon)}">${lcIcon(icon)}</span>
          <div>
            <div class="lc-record-header__eyebrow">${escapeHtml(type)}</div>
            <h1 class="lc-record-header__title" id="${this.id || 'record-title'}">${escapeHtml(data.title || 'Untitled record')}</h1>
          </div>
        </div>
        <div class="lc-record-header__actions">${actions}</div>
        <div class="lc-highlights">${highlights}</div>
      </section>`;
    this.querySelectorAll('[data-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.action)));
    this.querySelectorAll('[data-row]').forEach(link => link.addEventListener('click', event => {
      if (link.getAttribute('href') === '#') event.preventDefault();
      this.emitAction('open-row', { row: Number(link.dataset.row) });
    }));
  }
}

class LcCustomer360 extends JsonComponent {
  render() {
    const data = this.data;
    const rows = (data.fields || []).map(field => `
      <div class="lc-kv-row">
        <div class="lc-kv-row__label">${escapeHtml(field.label)}</div>
        <div class="lc-kv-row__value">${field.href ? `<a href="${escapeHtml(field.href)}">${escapeHtml(field.value)}</a>` : escapeHtml(field.value)}</div>
      </div>`).join('');
    const badges = (data.badges || []).map(badge => `<span class="lc-badge ${badge.tone ? `lc-badge--${escapeHtml(badge.tone)}` : ''}">${escapeHtml(badge.label)}</span>`).join(' ');
    this.innerHTML = `
      <section class="lc-panel" aria-labelledby="${this.id || 'customer-360-title'}">
        <div class="lc-panel__header">
          <div class="lc-panel__heading">
            <span class="lc-object-icon lc-object-icon--contact">${lcIcon('contact')}</span>
            <div><h2 class="lc-panel__title" id="${this.id || 'customer-360-title'}">${escapeHtml(data.heading || 'Customer 360')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || 'Unified profile')}</div></div>
          </div>
        </div>
        <div style="padding:18px 16px 12px;display:flex;align-items:center;gap:12px">
          <span class="lc-avatar">${escapeHtml(data.initials || '')}</span>
          <div><div style="color:var(--lc-heading);font-size:18px">${escapeHtml(data.name)}</div><div style="margin-top:3px;color:var(--lc-text-weak)">${escapeHtml(data.subtitle || '')}</div><div style="margin-top:8px">${badges}</div></div>
        </div>
        <div class="lc-kv-list">${rows}</div>
      </section>`;
  }
}

class LcRelatedList extends JsonComponent {
  render() {
    const data = this.data;
    const columns = data.columns || [];
    const header = columns.map(column => `<th scope="col" style="width:${escapeHtml(column.width || 'auto')}">${escapeHtml(column.label)}</th>`).join('');
    const rows = (data.rows || []).map((row, rowIndex) => {
      const cells = columns.map(column => {
        const value = row[column.key] ?? '';
        const content = column.link ? `<a href="${escapeHtml(row.href || '#')}" data-row="${rowIndex}">${escapeHtml(value)}</a>` : escapeHtml(value);
        return `<td title="${escapeHtml(value)}">${content}</td>`;
      }).join('');
      return `<tr><td><input type="checkbox" aria-label="Sélectionner ${escapeHtml(row[columns[0]?.key] || `ligne ${rowIndex + 1}`)}"></td>${cells}<td><button class="lc-icon-button" type="button" aria-label="Actions pour ${escapeHtml(row[columns[0]?.key] || `ligne ${rowIndex + 1}`)}" data-row-menu="${rowIndex}">${lcIcon('chevron')}</button></td></tr>`;
    }).join('');
    const actions = (data.actions || []).map(action => buttonMarkup(action, action.primary ? 'brand' : 'neutral')).join('');
    this.innerHTML = `
      <section class="lc-panel" aria-labelledby="${this.id || 'related-list-title'}">
        <div class="lc-panel__header">
          <div class="lc-panel__heading"><span class="lc-object-icon lc-object-icon--${escapeHtml(data.icon || 'contact')}">${lcIcon(data.icon || 'contact')}</span><div><h2 class="lc-panel__title" id="${this.id || 'related-list-title'}">${escapeHtml(data.title || 'Related records')} (${(data.rows || []).length})</h2><div class="lc-panel__meta">${escapeHtml(data.meta || `${(data.rows || []).length} items`)}</div></div></div>
          <div class="lc-panel__actions">${actions}</div>
        </div>
        <div class="lc-table-wrap"><table class="lc-table"><thead><tr><th scope="col"><input type="checkbox" aria-label="Tout sélectionner"></th>${header}<th scope="col"><span class="lc-sr-only">Actions</span></th></tr></thead><tbody>${rows}</tbody></table></div>
        ${data.footer ? `<div class="lc-panel__footer"><button class="lc-button" type="button" data-action="view-all">${escapeHtml(data.footer)}</button></div>` : ''}
      </section>`;
    this.querySelectorAll('[data-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.action)));
    this.querySelectorAll('[data-row-menu]').forEach(button => button.addEventListener('click', () => this.emitAction('row-menu', { row: Number(button.dataset.rowMenu) })));
  }
}

class LcEngagementFeed extends JsonComponent {
  render() {
    const data = this.data;
    const groups = (data.groups || []).map((group, groupIndex) => {
      const items = (group.items || []).map(item => `
        <article class="lc-feed-item">
          <span class="lc-feed-item__icon ${item.tone ? `lc-feed-item__icon--${escapeHtml(item.tone)}` : ''}">${lcIcon(item.icon || 'activity')}</span>
          <div class="lc-feed-item__header"><button class="lc-feed-item__title" type="button" data-feed-action="${escapeHtml(item.action || item.title)}" style="padding:0;border:0;background:transparent;text-align:left">${escapeHtml(item.title)}</button><time class="lc-feed-item__time">${escapeHtml(item.time || '')}</time></div>
          <div class="lc-feed-item__description">${escapeHtml(item.description || '')}</div>
        </article>`).join('');
      return `<section><button class="lc-section-bar" type="button" aria-expanded="true" data-group="${groupIndex}" style="width:100%;border:0"><span>⌄ ${escapeHtml(group.label)}</span><span>${escapeHtml(group.hint || '')}</span></button><div class="lc-feed" data-group-content="${groupIndex}">${items}</div></section>`;
    }).join('');
    this.innerHTML = `
      <section class="lc-panel" aria-labelledby="${this.id || 'feed-title'}">
        <div class="lc-panel__header"><div class="lc-panel__heading"><span class="lc-object-icon lc-object-icon--activity">${lcIcon('activity')}</span><div><h2 class="lc-panel__title" id="${this.id || 'feed-title'}">${escapeHtml(data.title || 'Engagement Feed')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || 'All time · All activities')}</div></div></div></div>
        ${groups}
      </section>`;
    this.querySelectorAll('[data-group]').forEach(button => button.addEventListener('click', () => {
      const content = this.querySelector(`[data-group-content="${button.dataset.group}"]`);
      const expanded = button.getAttribute('aria-expanded') === 'true';
      button.setAttribute('aria-expanded', String(!expanded));
      content.hidden = expanded;
    }));
    this.querySelectorAll('[data-feed-action]').forEach(button => button.addEventListener('click', () => this.emitAction('feed-item', { item: button.dataset.feedAction })));
  }
}

class LcTabs extends JsonComponent {
  connectedCallback() {
    this.templates = [...this.querySelectorAll(':scope > template[data-label]')].map(template => ({
      label: template.dataset.label,
      content: template.content.cloneNode(true),
    }));
    this.data = this.templates.length ? {} : readJsonScript(this);
    this.render();
  }

  render() {
    const definitions = this.templates.length ? this.templates : (this.data.tabs || []);
    const tabs = definitions.map((tab, index) => `<button class="lc-tab" id="${this.id || 'tabs'}-tab-${index}" type="button" role="tab" aria-selected="${index === 0}" aria-controls="${this.id || 'tabs'}-panel-${index}" tabindex="${index === 0 ? 0 : -1}" data-tab="${index}">${escapeHtml(tab.label)}</button>`).join('');
    this.innerHTML = `<div class="lc-panel"><div class="lc-tabs" role="tablist">${tabs}</div><div data-panels></div></div>`;
    const panelContainer = this.querySelector('[data-panels]');
    definitions.forEach((tab, index) => {
      const panel = document.createElement('section');
      panel.className = 'lc-tab-panel';
      panel.id = `${this.id || 'tabs'}-panel-${index}`;
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', `${this.id || 'tabs'}-tab-${index}`);
      panel.hidden = index !== 0;
      if (this.templates.length) panel.append(tab.content);
      else panel.innerHTML = tab.html || '';
      panelContainer.append(panel);
    });
    const buttons = [...this.querySelectorAll('[role="tab"]')];
    const activate = index => {
      buttons.forEach((button, buttonIndex) => {
        const active = buttonIndex === index;
        button.setAttribute('aria-selected', String(active));
        button.tabIndex = active ? 0 : -1;
        this.querySelector(`#${this.id || 'tabs'}-panel-${buttonIndex}`).hidden = !active;
      });
      buttons[index].focus();
    };
    buttons.forEach((button, index) => {
      button.addEventListener('click', () => activate(index));
      button.addEventListener('keydown', event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        if (event.key === 'Home') activate(0);
        else if (event.key === 'End') activate(buttons.length - 1);
        else activate((index + (event.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length);
      });
    });
  }
}

class LcStatusPath extends JsonComponent {
  render() {
    const data = this.data;
    const current = Number(data.current ?? 0);
    const steps = (data.steps || []).map((step, index) => {
      const state = index < current ? 'lc-path__step--complete' : index === current ? 'lc-path__step--current' : '';
      return `<div class="lc-path__step ${state}"><span class="lc-path__dot">${index < current ? lcIcon('check') : index + 1}</span><span class="lc-path__label">${escapeHtml(step)}</span></div>`;
    }).join('');
    this.innerHTML = `<section class="lc-panel" aria-label="${escapeHtml(data.label || 'Progression')}"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Status')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div></div><div class="lc-path"><div class="lc-path__steps">${steps}</div></div></section>`;
  }
}

class LcKpiGrid extends JsonComponent {
  render() {
    const cards = (this.data.items || []).map(item => `
      <article class="lc-kpi">
        <div class="lc-kpi__label">${escapeHtml(item.label)}</div>
        <div class="lc-kpi__value">${escapeHtml(item.value)}</div>
        <div class="lc-kpi__trend ${item.direction === 'down' ? 'lc-kpi__trend--down' : ''}">${lcIcon('trend')} ${escapeHtml(item.trend || '')}</div>
        ${item.progress != null ? `<div class="lc-progress" role="progressbar" aria-label="${escapeHtml(item.label)}" aria-valuenow="${Number(item.progress)}" aria-valuemin="0" aria-valuemax="100"><div class="lc-progress__bar" style="width:${Math.max(0, Math.min(100, Number(item.progress)))}%"></div></div>` : ''}
      </article>`).join('');
    this.innerHTML = `<section class="lc-kpi-grid" aria-label="${escapeHtml(this.data.label || 'Key performance indicators')}">${cards}</section>`;
  }
}

class LcAiRecommendation extends JsonComponent {
  render() {
    const data = this.data;
    this.innerHTML = `
      <section class="lc-panel lc-ai-card" aria-labelledby="${this.id || 'ai-title'}">
        <div class="lc-ai-card__header">${lcIcon('spark')}<h2 id="${this.id || 'ai-title'}" style="margin:0;font-size:15px">${escapeHtml(data.title || 'Agentforce recommendation')}</h2></div>
        <div class="lc-ai-card__body"><div class="lc-ai-card__label">${escapeHtml(data.label || 'Suggested next action')}</div><div class="lc-ai-card__suggestion">${escapeHtml(data.suggestion || '')}</div><div class="lc-ai-card__actions"><button class="lc-button lc-button--brand" type="button" data-action="accept">${escapeHtml(data.acceptLabel || 'Apply')}</button><button class="lc-button" type="button" data-action="edit">${escapeHtml(data.editLabel || 'Edit')}</button></div>${data.draft ? `<div class="lc-ai-card__draft"><strong>Draft</strong><br>${escapeHtml(data.draft)}</div>` : ''}</div>
      </section>`;
    this.querySelectorAll('[data-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.action)));
  }
}

class LcSegmentChips extends JsonComponent {
  render() {
    const data = this.data;
    const items = (data.items || []).map((item, index) => `<button class="lc-segment ${item.active ? 'lc-segment--active' : ''}" type="button" aria-pressed="${Boolean(item.active)}" data-segment="${index}">${item.active ? '⚡ ' : ''}${escapeHtml(item.label)}</button>`).join('');
    this.innerHTML = `<section class="lc-panel" aria-labelledby="${this.id || 'segments-title'}"><div class="lc-panel__header"><div><h2 class="lc-panel__title" id="${this.id || 'segments-title'}">${escapeHtml(data.title || 'Segments')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || 'Recalculated in real time')}</div></div></div><div class="lc-segments">${items}</div></section>`;
    this.querySelectorAll('[data-segment]').forEach(button => button.addEventListener('click', () => {
      button.classList.toggle('lc-segment--active');
      const active = button.classList.contains('lc-segment--active');
      button.setAttribute('aria-pressed', String(active));
      this.emitAction('segment-toggle', { index: Number(button.dataset.segment), active });
    }));
  }
}

class LcEmptyState extends JsonComponent {
  render() {
    const data = this.data;
    this.innerHTML = `<section class="lc-panel"><div class="lc-empty"><svg class="lc-empty__illustration" viewBox="0 0 160 92" fill="none" aria-hidden="true"><path d="M12 78h136M28 76l22-25 17 16 20-31 19 26 14-13 22 27" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/><circle cx="42" cy="27" r="12" stroke="currentColor" stroke-width="4"/><path d="M42 19v16m-8-8h16" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></svg><h2 class="lc-empty__title">${escapeHtml(data.title || 'Nothing here yet')}</h2><p class="lc-empty__description">${escapeHtml(data.description || '')}</p>${data.action ? `<button class="lc-button lc-button--brand" type="button" data-action="empty-action" style="margin-top:16px">${escapeHtml(data.action)}</button>` : ''}</div></section>`;
    this.querySelector('[data-action]')?.addEventListener('click', () => this.emitAction('empty-action'));
  }
}

class LcDemoModal extends JsonComponent {
  connectedCallback() {
    this.data = readJsonScript(this);
    this.opener = null;
    this.render();
  }

  render() {
    const data = this.data;
    const fields = (data.fields || []).map((field, index) => {
      const id = `${this.id || 'modal'}-field-${index}`;
      if (field.type === 'textarea') return `<div class="lc-field"><label for="${id}">${escapeHtml(field.label)}</label><textarea class="lc-textarea" id="${id}" name="${escapeHtml(field.name || field.label)}">${escapeHtml(field.value || '')}</textarea></div>`;
      return `<div class="lc-field"><label for="${id}">${escapeHtml(field.label)}</label><input class="lc-input" id="${id}" name="${escapeHtml(field.name || field.label)}" type="${escapeHtml(field.type || 'text')}" value="${escapeHtml(field.value || '')}"></div>`;
    }).join('');
    this.innerHTML = `<div class="lc-modal" hidden><section class="lc-modal__dialog" role="dialog" aria-modal="true" aria-labelledby="${this.id || 'modal'}-title"><div class="lc-modal__header"><h2 class="lc-modal__title" id="${this.id || 'modal'}-title">${escapeHtml(data.title || 'Edit record')}</h2><button class="lc-icon-button" type="button" data-close aria-label="Close">${lcIcon('close')}</button></div><form><div class="lc-modal__body">${fields}</div><div class="lc-modal__footer"><button class="lc-button" type="button" data-close>Cancel</button><button class="lc-button lc-button--brand" type="submit">${escapeHtml(data.submitLabel || 'Save')}</button></div></form></section></div>`;
    this.modal = this.querySelector('.lc-modal');
    this.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => this.close()));
    this.querySelector('form').addEventListener('submit', event => {
      event.preventDefault();
      const values = Object.fromEntries(new FormData(event.currentTarget));
      this.emitAction('modal-submit', { values });
      this.close();
    });
    this.modal.addEventListener('click', event => { if (event.target === this.modal) this.close(); });
    this.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !this.modal.hidden) this.close();
      if (event.key === 'Tab' && !this.modal.hidden) this.trapFocus(event);
    });
  }

  open(opener = document.activeElement) {
    this.opener = opener;
    this.modal.hidden = false;
    document.body.style.overflow = 'hidden';
    requestAnimationFrame(() => this.querySelector('input, textarea, button')?.focus());
  }

  close() {
    this.modal.hidden = true;
    document.body.style.overflow = '';
    this.opener?.focus?.();
  }

  trapFocus(event) {
    const focusable = [...this.querySelectorAll('button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])')].filter(element => !element.closest('[hidden]'));
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable.at(-1);
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
}

class LcToastRegion extends HTMLElement {
  connectedCallback() {
    this.classList.add('lc-toast-region');
    this.setAttribute('aria-live', 'polite');
    this.setAttribute('aria-atomic', 'true');
  }

  show(message, tone = 'success', timeout = 3500) {
    const toast = document.createElement('div');
    toast.className = `lc-toast ${tone === 'error' ? 'lc-toast--error' : ''}`;
    toast.setAttribute('role', tone === 'error' ? 'alert' : 'status');
    toast.innerHTML = `${lcIcon(tone === 'error' ? 'close' : 'check')}<span>${escapeHtml(message)}</span><button class="lc-toast__close" type="button" aria-label="Close notification">×</button>`;
    toast.querySelector('button').addEventListener('click', () => toast.remove());
    this.append(toast);
    window.setTimeout(() => toast.remove(), timeout);
  }
}

const definitions = {
  'lc-record-header': LcRecordHeader,
  'lc-customer-360': LcCustomer360,
  'lc-related-list': LcRelatedList,
  'lc-engagement-feed': LcEngagementFeed,
  'lc-tabs': LcTabs,
  'lc-status-path': LcStatusPath,
  'lc-kpi-grid': LcKpiGrid,
  'lc-ai-recommendation': LcAiRecommendation,
  'lc-segment-chips': LcSegmentChips,
  'lc-empty-state': LcEmptyState,
  'lc-demo-modal': LcDemoModal,
  'lc-toast-region': LcToastRegion,
};

for (const [name, constructor] of Object.entries(definitions)) {
  if (!customElements.get(name)) customElements.define(name, constructor);
}
