import { JsonComponent, escapeHtml, lcIcon } from './lightning-components.js';

const clamp = (value, min, max) => Math.max(min, Math.min(max, Number(value)));
const palette = ['#0176d3', '#2e844a', '#fe9339', '#9050e9', '#0b827c', '#ba0517'];

function statusClass(status = '') {
  const normalized = status.toLowerCase().replaceAll(' ', '-');
  if (['completed', 'available', 'on-site', 'success'].includes(normalized)) return 'success';
  if (['late', 'critical', 'blocked', 'error'].includes(normalized)) return 'error';
  if (['en-route', 'travel', 'warning', 'at-risk'].includes(normalized)) return 'warning';
  return 'brand';
}

function svgText(value) {
  return escapeHtml(value).replaceAll('&nbsp;', ' ');
}

class LcMap extends JsonComponent {
  render() {
    const data = this.data;
    const markers = data.markers || [];
    const useLeaflet = data.provider === 'openstreetmap' && Boolean(window.L);
    const statuses = [...new Set(markers.map(marker => marker.status).filter(Boolean))];
    const markerMarkup = useLeaflet ? '' : markers.map((marker, index) => `
      <button class="lc-map-marker lc-map-marker--${statusClass(marker.status)}" type="button" style="left:${clamp(marker.x, 2, 98)}%;top:${clamp(marker.y, 4, 94)}%" data-marker="${index}" aria-label="${escapeHtml(marker.label)}, ${escapeHtml(marker.status)}">
        <span>${index + 1}</span>
      </button>`).join('');
    const list = markers.map((marker, index) => `
      <button class="lc-map-list__item" type="button" data-list-marker="${index}" aria-label="${escapeHtml(marker.label)}, ${escapeHtml(marker.status)}">
        <span class="lc-map-list__number">${index + 1}</span>
        <span><strong>${escapeHtml(marker.label)}</strong><small>${escapeHtml(marker.address || '')}</small></span>
        <span class="lc-badge lc-badge--${statusClass(marker.status)}">${escapeHtml(marker.status || '')}</span>
      </button>`).join('');
    const filters = ['All', ...statuses].map((status, index) => `<button class="lc-map-filter ${index === 0 ? 'lc-map-filter--active' : ''}" type="button" aria-pressed="${index === 0}" data-map-filter="${escapeHtml(status)}">${escapeHtml(status)}</button>`).join('');
    const locationAction = data.allowGeolocation ? `<button class="lc-button lc-map-location" type="button" data-map-location>${lcIcon('location')} Use my location</button>` : '';
    const mapContent = useLeaflet
      ? '<div class="lc-map-leaflet" data-leaflet-map></div>'
      : `<svg class="lc-map-art" viewBox="0 0 800 500" preserveAspectRatio="none" aria-hidden="true">
          <rect width="800" height="500" fill="#eef4e8"/>
          <path d="M0 85C130 58 198 122 332 91s233-20 468 34M-20 330c170-74 260-62 395-14s264 45 445-17" fill="none" stroke="#d5ddcf" stroke-width="36"/>
          <path d="M110-20c28 138 66 196 137 272s129 153 151 268M580-30c-23 118-20 202 29 281s75 151 91 279" fill="none" stroke="#fff" stroke-width="25"/>
          <path d="M-20 190c182 8 275 38 403 111s249 95 440 89M110-20c28 138 66 196 137 272s129 153 151 268M580-30c-23 118-20 202 29 281s75 151 91 279" fill="none" stroke="#ccd6df" stroke-width="3"/>
          <path d="M0 454c120-35 212-25 315 8s236 37 485-19" fill="none" stroke="#90d0fe" stroke-width="25" opacity=".75"/>
          <g fill="#d9e7d4"><rect x="62" y="116" width="110" height="56" rx="9"/><rect x="316" y="36" width="125" height="62" rx="9"/><rect x="471" y="334" width="120" height="64" rx="9"/><rect x="620" y="154" width="92" height="55" rx="9"/></g>
        </svg>`;
    this.innerHTML = `
      <section class="lc-panel lc-map" aria-labelledby="${this.id || 'map-title'}">
        <div class="lc-panel__header"><div class="lc-panel__heading"><span class="lc-object-icon lc-object-icon--map">${lcIcon('account')}</span><div><h2 class="lc-panel__title" id="${this.id || 'map-title'}">${escapeHtml(data.title || 'Service Map')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || `${markers.length} locations`)}</div></div></div><div class="lc-panel__actions">${locationAction}${filters}</div></div>
        <div class="lc-map__layout">
          <div class="lc-map-list" aria-label="Locations">${list}</div>
          <div class="lc-map-canvas" role="region" aria-label="${escapeHtml(data.accessibleLabel || 'Map showing service locations')}">
            ${mapContent}
            ${markerMarkup}
            <div class="lc-map-popover" hidden data-map-popover></div>
            <div class="lc-map-legend"><span><i class="lc-map-dot lc-map-dot--brand"></i> Scheduled</span><span><i class="lc-map-dot lc-map-dot--warning"></i> En route</span><span><i class="lc-map-dot lc-map-dot--success"></i> Completed</span></div>
          </div>
        </div>
      </section>`;
    const select = index => {
      const marker = markers[index];
      if (!marker) return;
      this.querySelectorAll('[data-marker], [data-list-marker]').forEach(element => element.classList.toggle('is-selected', Number(element.dataset.marker ?? element.dataset.listMarker) === index));
      const popover = this.querySelector('[data-map-popover]');
      if (this.leafletMarkers?.[index]) {
        this.leafletMarkers[index].openPopup();
        this.map.panTo(this.leafletMarkers[index].getLatLng());
      } else {
        popover.innerHTML = `<strong>${escapeHtml(marker.label)}</strong><span>${escapeHtml(marker.address || '')}</span><span>${escapeHtml(marker.technician || 'Unassigned')} · ${escapeHtml(marker.time || '')}</span><button class="lc-button" type="button" data-open-marker>Open appointment</button>`;
        popover.hidden = false;
        popover.style.left = `${clamp(marker.x, 20, 75)}%`;
        popover.style.top = `${clamp(marker.y, 18, 68)}%`;
        popover.querySelector('[data-open-marker]').addEventListener('click', () => this.emitAction('open-map-record', { index, marker }));
      }
      this.emitAction('map-select', { index, marker });
    };
    this.querySelectorAll('[data-marker]').forEach(button => button.addEventListener('click', () => select(Number(button.dataset.marker))));
    this.querySelectorAll('[data-list-marker]').forEach(button => button.addEventListener('click', () => select(Number(button.dataset.listMarker))));
    this.querySelectorAll('[data-map-filter]').forEach(button => button.addEventListener('click', () => {
      const filter = button.dataset.mapFilter;
      this.querySelectorAll('[data-map-filter]').forEach(filterButton => {
        const active = filterButton === button;
        filterButton.classList.toggle('lc-map-filter--active', active);
        filterButton.setAttribute('aria-pressed', String(active));
      });
      markers.forEach((marker, index) => {
        const visible = filter === 'All' || marker.status === filter;
        const svgMarker = this.querySelector(`[data-marker="${index}"]`);
        if (svgMarker) svgMarker.hidden = !visible;
        this.querySelector(`[data-list-marker="${index}"]`).hidden = !visible;
        if (this.leafletMarkers?.[index]) {
          if (visible && !this.map.hasLayer(this.leafletMarkers[index])) this.leafletMarkers[index].addTo(this.map);
          if (!visible && this.map.hasLayer(this.leafletMarkers[index])) this.map.removeLayer(this.leafletMarkers[index]);
        }
      });
    }));
    if (useLeaflet) this.initializeLeaflet(markers, select);
    this.querySelector('[data-map-location]')?.addEventListener('click', () => this.locateUser());
  }

  initializeLeaflet(markers, select) {
    const data = this.data;
    const center = data.center || {};
    this.map = window.L.map(this.querySelector('[data-leaflet-map]'), { zoomControl: true }).setView([
      Number(center.latitude ?? 48.8566),
      Number(center.longitude ?? 2.3522),
    ], Number(data.zoom ?? 11));
    window.L.tileLayer(data.tileUrl || 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(this.map);
    this.leafletMarkers = markers.map((marker, index) => {
      if (!Number.isFinite(Number(marker.latitude)) || !Number.isFinite(Number(marker.longitude))) return null;
      const icon = window.L.divIcon({
        className: 'lc-leaflet-marker-wrap',
        html: `<span class="lc-leaflet-marker lc-leaflet-marker--${statusClass(marker.status)}"><span>${index + 1}</span></span>`,
        iconSize: [34, 42],
        iconAnchor: [17, 42],
        popupAnchor: [0, -38],
      });
      const leafletMarker = window.L.marker([Number(marker.latitude), Number(marker.longitude)], { icon, title: marker.label }).addTo(this.map);
      leafletMarker.bindPopup(`<strong>${escapeHtml(marker.label)}</strong><br><span>${escapeHtml(marker.address || '')}</span><br><span>${escapeHtml(marker.technician || 'Unassigned')} · ${escapeHtml(marker.time || '')}</span>`);
      leafletMarker.on('click', () => select(index));
      return leafletMarker;
    });
    window.setTimeout(() => this.map.invalidateSize(), 0);
  }

  locateUser() {
    const button = this.querySelector('[data-map-location]');
    if (!navigator.geolocation) {
      this.emitAction('geolocation-error', { message: 'Geolocation is not supported by this browser.' });
      return;
    }
    button.disabled = true;
    button.classList.add('is-loading');
    navigator.geolocation.getCurrentPosition(position => {
      const coordinates = [position.coords.latitude, position.coords.longitude];
      if (this.map) {
        this.map.setView(coordinates, Math.max(Number(this.data.zoom ?? 11), 14));
        if (this.userMarker) this.userMarker.setLatLng(coordinates);
        else this.userMarker = window.L.circleMarker(coordinates, { radius: 9, color: '#fff', weight: 3, fillColor: '#0176d3', fillOpacity: 1 }).addTo(this.map).bindPopup('Your current position');
        this.userMarker.openPopup();
      }
      button.disabled = false;
      button.classList.remove('is-loading');
      this.emitAction('geolocation-success', { latitude: coordinates[0], longitude: coordinates[1] });
    }, error => {
      const messages = {
        1: 'Location permission was denied.',
        2: 'Your current position is unavailable.',
        3: 'Location request timed out.',
      };
      button.disabled = false;
      button.classList.remove('is-loading');
      this.emitAction('geolocation-error', { message: messages[error.code] || 'Unable to retrieve your current position.' });
    }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 });
  }

  disconnectedCallback() {
    this.map?.remove();
  }
}

class LcRouteMap extends JsonComponent {
  render() {
    const data = this.data;
    const stops = data.stops || [];
    const points = stops.map(stop => `${clamp(stop.x, 2, 98) * 8},${clamp(stop.y, 3, 94) * 5}`).join(' ');
    const stopMarkup = stops.map((stop, index) => `<button class="lc-route-stop ${index === Number(data.current) ? 'lc-route-stop--current' : ''}" type="button" style="left:${clamp(stop.x, 2, 98)}%;top:${clamp(stop.y, 3, 94)}%" data-stop="${index}" aria-label="Stop ${index + 1}: ${escapeHtml(stop.label)}"><span>${index + 1}</span></button>`).join('');
    const itinerary = stops.map((stop, index) => `<li><button type="button" data-route-item="${index}"><span>${index + 1}</span><strong>${escapeHtml(stop.time || '')}</strong><span>${escapeHtml(stop.label)}</span></button></li>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Technician Route')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || `${stops.length} stops`)}</div></div></div><div class="lc-route"><ol class="lc-route__itinerary">${itinerary}</ol><div class="lc-route__canvas"><svg viewBox="0 0 800 500" preserveAspectRatio="none" aria-hidden="true"><rect width="800" height="500" fill="#eef4e8"/><path d="M0 120h800M0 280h800M180 0v500M510 0v500M690 0v500" stroke="#fff" stroke-width="28"/><path d="M0 120h800M0 280h800M180 0v500M510 0v500M690 0v500" stroke="#ccd6df" stroke-width="3"/><polyline points="${points}" fill="none" stroke="#0176d3" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="12 8"/></svg>${stopMarkup}</div></div></section>`;
    const select = index => this.emitAction('route-stop', { index, stop: stops[index] });
    this.querySelectorAll('[data-stop]').forEach(button => button.addEventListener('click', () => select(Number(button.dataset.stop))));
    this.querySelectorAll('[data-route-item]').forEach(button => button.addEventListener('click', () => select(Number(button.dataset.routeItem))));
  }
}

class LcTechnicianRoster extends JsonComponent {
  render() {
    const data = this.data;
    const technicians = (data.technicians || []).map((technician, index) => `<button class="lc-tech-card" type="button" data-tech="${index}"><span class="lc-avatar lc-avatar--small">${escapeHtml(technician.initials)}</span><span class="lc-tech-card__body"><strong>${escapeHtml(technician.name)}</strong><small>${escapeHtml((technician.skills || []).join(' · '))}</small></span><span><span class="lc-badge lc-badge--${statusClass(technician.status)}">${escapeHtml(technician.status)}</span><small>${escapeHtml(technician.workload || '')}</small></span></button>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Technicians')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || `${(data.technicians || []).length} resources`)}</div></div></div><div class="lc-tech-roster">${technicians}</div></section>`;
    this.querySelectorAll('[data-tech]').forEach(button => button.addEventListener('click', () => {
      const index = Number(button.dataset.tech);
      this.querySelectorAll('[data-tech]').forEach(item => item.classList.toggle('is-selected', item === button));
      this.emitAction('technician-select', { index, technician: data.technicians[index] });
    }));
  }
}

function timeToMinutes(value, fallback = 480) {
  const [hours, minutes] = String(value || '').split(':').map(Number);
  return Number.isFinite(hours) ? hours * 60 + (minutes || 0) : fallback;
}

class LcDispatchConsole extends JsonComponent {
  render() {
    const data = this.data;
    const startHour = Number(data.startHour ?? 8);
    const endHour = Number(data.endHour ?? 18);
    const span = Math.max(1, (endHour - startHour) * 60);
    const technicians = data.technicians || [];
    const hours = Array.from({ length: endHour - startHour + 1 }, (_, index) => `<span style="left:${(index / (endHour - startHour)) * 100}%">${startHour + index}:00</span>`).join('');
    const rows = technicians.map((technician, techIndex) => {
      const appointments = (technician.appointments || []).map((appointment, appointmentIndex) => {
        const start = timeToMinutes(appointment.start) - startHour * 60;
        const end = timeToMinutes(appointment.end, timeToMinutes(appointment.start) + 60) - startHour * 60;
        const left = clamp((start / span) * 100, 0, 98);
        const width = clamp(((end - start) / span) * 100, 4, 100 - left);
        return `<button class="lc-dispatch-appt lc-dispatch-appt--${statusClass(appointment.status)} ${appointment.conflict ? 'lc-dispatch-appt--conflict' : ''}" type="button" style="left:${left}%;width:${width}%" data-appt="${techIndex}:${appointmentIndex}" title="${escapeHtml(`${appointment.start}-${appointment.end} ${appointment.title}`)}"><strong>${escapeHtml(appointment.title)}</strong><span>${escapeHtml(appointment.start)} · ${escapeHtml(appointment.status)}</span></button>`;
      }).join('');
      return `<div class="lc-dispatch-row"><button class="lc-dispatch-resource" type="button" data-resource="${techIndex}"><span class="lc-avatar lc-avatar--small">${escapeHtml(technician.initials)}</span><span><strong>${escapeHtml(technician.name)}</strong><small>${escapeHtml(technician.territory || '')}</small></span></button><div class="lc-dispatch-track">${appointments}</div></div>`;
    }).join('');
    this.innerHTML = `<section class="lc-panel lc-dispatch"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Dispatch Console')}</h2><div class="lc-panel__meta">${escapeHtml(data.date || '')} · ${technicians.length} technicians</div></div><div class="lc-panel__actions"><button class="lc-button" type="button" data-dispatch-action="optimize">Optimize Schedule</button><button class="lc-button lc-button--brand" type="button" data-dispatch-action="appointment">New Appointment</button></div></div><div class="lc-dispatch-hours"><span></span><div>${hours}</div></div><div class="lc-dispatch-grid">${rows}</div><div class="lc-dispatch-legend"><span><i class="lc-map-dot lc-map-dot--brand"></i> Scheduled</span><span><i class="lc-map-dot lc-map-dot--warning"></i> Travel</span><span><i class="lc-map-dot lc-map-dot--success"></i> Completed</span><span><i class="lc-map-dot lc-map-dot--error"></i> Conflict</span></div></section>`;
    this.querySelectorAll('[data-appt]').forEach(button => button.addEventListener('click', () => {
      const [techIndex, appointmentIndex] = button.dataset.appt.split(':').map(Number);
      this.querySelectorAll('[data-appt]').forEach(item => item.classList.toggle('is-selected', item === button));
      this.emitAction('appointment-select', { techIndex, appointmentIndex, technician: technicians[techIndex], appointment: technicians[techIndex].appointments[appointmentIndex] });
    }));
    this.querySelectorAll('[data-resource]').forEach(button => button.addEventListener('click', () => this.emitAction('technician-select', { index: Number(button.dataset.resource), technician: technicians[Number(button.dataset.resource)] })));
    this.querySelectorAll('[data-dispatch-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.dispatchAction)));
  }
}

class LcServiceAppointment extends JsonComponent {
  render() {
    const data = this.data;
    const details = (data.details || []).map(item => `<div><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.value)}</strong></div>`).join('');
    this.innerHTML = `<article class="lc-panel lc-appointment"><div class="lc-panel__header"><div class="lc-panel__heading"><span class="lc-object-icon lc-object-icon--appointment">${lcIcon('event')}</span><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Service Appointment')}</h2><div class="lc-panel__meta">${escapeHtml(data.number || '')}</div></div></div><span class="lc-badge lc-badge--${statusClass(data.status)}">${escapeHtml(data.status || '')}</span></div><div class="lc-appointment__body"><div class="lc-appointment__time"><strong>${escapeHtml(data.time || '')}</strong><span>${escapeHtml(data.duration || '')}</span></div><div class="lc-appointment__address">${escapeHtml(data.address || '')}</div><div class="lc-appointment__details">${details}</div><div class="lc-panel__actions"><button class="lc-button lc-button--brand" type="button" data-appt-action="start">${escapeHtml(data.primaryAction || 'Start Travel')}</button><button class="lc-button" type="button" data-appt-action="details">View Details</button></div></div></article>`;
    this.querySelectorAll('[data-appt-action]').forEach(button => button.addEventListener('click', () => this.emitAction(button.dataset.apptAction, { appointment: data })));
  }
}

class LcWorkOrder extends JsonComponent {
  render() {
    const data = this.data;
    const fields = (data.fields || []).map(item => `<div class="lc-kv-row"><span class="lc-kv-row__label">${escapeHtml(item.label)}</span><span class="lc-kv-row__value">${escapeHtml(item.value)}</span></div>`).join('');
    const checklist = (data.checklist || []).map((item, index) => `<label class="lc-check-item"><input type="checkbox" data-check="${index}" ${item.done ? 'checked' : ''}><span>${escapeHtml(item.label)}</span></label>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div class="lc-panel__heading"><span class="lc-object-icon lc-object-icon--work-order">${lcIcon('case')}</span><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Work Order')}</h2><div class="lc-panel__meta">${escapeHtml(data.number || '')}</div></div></div><span class="lc-badge lc-badge--${statusClass(data.priority)}">${escapeHtml(data.priority || '')}</span></div><div class="lc-work-order"><div class="lc-kv-list">${fields}</div><div class="lc-work-order__section"><h3>Checklist</h3>${checklist}</div></div></section>`;
    this.querySelectorAll('[data-check]').forEach(input => input.addEventListener('change', () => this.emitAction('work-order-check', { index: Number(input.dataset.check), checked: input.checked })));
  }
}

class LcPartsInventory extends JsonComponent {
  render() {
    const data = this.data;
    const rows = (data.parts || []).map((part, index) => `<tr><td>${escapeHtml(part.sku)}</td><td><strong>${escapeHtml(part.name)}</strong></td><td>${escapeHtml(part.required)}</td><td>${escapeHtml(part.vanStock)}</td><td><span class="lc-badge lc-badge--${part.vanStock >= part.required ? 'success' : 'error'}">${part.vanStock >= part.required ? 'Available' : 'Restock'}</span></td><td><button class="lc-icon-button" type="button" aria-label="Actions for ${escapeHtml(part.name)}" data-part="${index}">${lcIcon('chevron')}</button></td></tr>`).join('');
    this.innerHTML = `<section class="lc-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Parts Inventory')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || 'Technician van stock')}</div></div><button class="lc-button" type="button" data-inventory-action="restock">Request Restock</button></div><div class="lc-table-wrap"><table class="lc-table lc-parts-table"><thead><tr><th>SKU</th><th>Part</th><th>Required</th><th>Van Stock</th><th>Status</th><th><span class="lc-sr-only">Actions</span></th></tr></thead><tbody>${rows}</tbody></table></div></section>`;
    this.querySelector('[data-inventory-action]').addEventListener('click', () => this.emitAction('restock'));
    this.querySelectorAll('[data-part]').forEach(button => button.addEventListener('click', () => this.emitAction('part-select', { index: Number(button.dataset.part), part: data.parts[Number(button.dataset.part)] })));
  }
}

function mobileTone(tone = '') {
  const normalized = tone.toLowerCase().replaceAll(' ', '-');
  if (['success', 'covered', 'completed', 'eligible'].includes(normalized)) return 'success';
  if (['warning', 'expiring', 'pending'].includes(normalized)) return 'warning';
  if (['error', 'expired', 'ineligible'].includes(normalized)) return 'error';
  return 'brand';
}

function mobileBadge(item = {}) {
  return `<span class="lc-fs-mobile-badge lc-fs-mobile-badge--${mobileTone(item.tone || item.label)}">${escapeHtml(item.label || '')}</span>`;
}

function mobileFacts(items = []) {
  return items.map(item => `<div><dt>${escapeHtml(item.label)}</dt><dd>${escapeHtml(item.value)}</dd></div>`).join('');
}

class LcFsMobileShell extends JsonComponent {
  render() {
    const data = this.data;
    const content = [...this.children].filter(child => child.localName !== 'script');
    content.forEach(child => child.remove());
    const navItems = data.navItems || [];
    const actions = (data.actions || []).map((action, index) => `<button class="lc-fs-mobile-icon" type="button" data-shell-action="${index}" aria-label="${escapeHtml(action.label)}">${lcIcon(action.icon || 'activity')}<span>${escapeHtml(action.label)}</span></button>`).join('');
    const navigation = navItems.map((item, index) => `<button class="${item.active ? 'is-active' : ''}" type="button" data-shell-nav="${index}" ${item.active ? 'aria-current="page"' : ''}>${lcIcon(item.icon || 'activity')}<span>${escapeHtml(item.label)}</span></button>`).join('');
    this.innerHTML = `<section class="lc-fs-mobile-shell" aria-label="${escapeHtml(data.accessibleLabel || 'Application mobile Field Service')}"><header class="lc-fs-mobile-topbar"><button class="lc-fs-mobile-profile" type="button" data-shell-profile aria-label="${escapeHtml(data.profileLabel || 'Ouvrir le profil')}"><span>${escapeHtml(data.initials || 'FS')}</span></button><div><strong>${escapeHtml(data.appName || 'Field Service')}</strong><small>${escapeHtml(data.context || '')}</small></div><div class="lc-fs-mobile-topbar__actions">${actions}</div></header><div class="lc-fs-mobile-content" data-shell-content></div>${navigation ? `<nav class="lc-fs-mobile-nav" aria-label="Navigation principale">${navigation}</nav>` : ''}</section>`;
    this.querySelector('[data-shell-content]').append(...content);
    this.querySelector('[data-shell-profile]')?.addEventListener('click', () => this.emitAction('mobile-profile'));
    this.querySelectorAll('[data-shell-action]').forEach(button => button.addEventListener('click', () => {
      const index = Number(button.dataset.shellAction);
      this.emitAction(data.actions[index].action || 'mobile-action', { index, item: data.actions[index] });
    }));
    this.querySelectorAll('[data-shell-nav]').forEach(button => button.addEventListener('click', () => {
      const index = Number(button.dataset.shellNav);
      this.querySelectorAll('[data-shell-nav]').forEach(item => {
        const active = item === button;
        item.classList.toggle('is-active', active);
        if (active) item.setAttribute('aria-current', 'page');
        else item.removeAttribute('aria-current');
      });
      this.emitAction(data.navItems[index].action || 'mobile-navigate', { index, item: data.navItems[index] });
    }));
  }
}

class LcFsMobileWorkOrder extends JsonComponent {
  render() {
    const data = this.data;
    const facts = mobileFacts(data.facts || []);
    const sections = (data.sections || []).map((section, index) => `<button class="lc-fs-mobile-row" type="button" data-work-section="${index}"><span class="lc-fs-mobile-row__icon">${lcIcon(section.icon || 'task')}</span><span><strong>${escapeHtml(section.label)}</strong><small>${escapeHtml(section.meta || '')}</small></span>${section.badge ? mobileBadge(section.badge) : ''}${lcIcon('chevron')}</button>`).join('');
    this.innerHTML = `<article class="lc-fs-mobile-page" aria-labelledby="${this.id || 'fs-work-order'}-title"><header class="lc-fs-mobile-hero"><div class="lc-fs-mobile-eyebrow">${escapeHtml(data.eyebrow || 'Ordre de travail')}</div><div class="lc-fs-mobile-title-row"><h1 id="${this.id || 'fs-work-order'}-title">${escapeHtml(data.title || '')}</h1>${data.status ? mobileBadge(data.status) : ''}</div><p>${escapeHtml(data.summary || '')}</p></header><dl class="lc-fs-mobile-facts">${facts}</dl><div class="lc-fs-mobile-rows">${sections}</div>${data.primaryAction ? `<div class="lc-fs-mobile-sticky"><button class="lc-button lc-button--brand" type="button" data-work-action>${escapeHtml(data.primaryAction)}</button></div>` : ''}</article>`;
    this.querySelectorAll('[data-work-section]').forEach(button => button.addEventListener('click', () => {
      const index = Number(button.dataset.workSection);
      this.emitAction('mobile-work-section', { index, section: data.sections[index] });
    }));
    this.querySelector('[data-work-action]')?.addEventListener('click', () => this.emitAction('mobile-work-action', { workOrder: data }));
  }
}

class LcFsMobileWorkPlan extends JsonComponent {
  render() {
    const data = this.data;
    const steps = data.steps || [];
    const completed = steps.filter(step => step.done).length;
    const progress = steps.length ? Math.round(completed / steps.length * 100) : 0;
    const stepMarkup = steps.map((step, index) => `<li><label class="lc-fs-mobile-step"><input type="checkbox" data-plan-step="${index}" ${step.done ? 'checked' : ''}><span class="lc-fs-mobile-step__check" aria-hidden="true">${lcIcon('check')}</span><span><strong>${escapeHtml(step.label)}</strong><small>${escapeHtml(step.detail || '')}</small></span>${step.duration ? `<em>${escapeHtml(step.duration)}</em>` : ''}</label></li>`).join('');
    this.innerHTML = `<section class="lc-fs-mobile-page" aria-labelledby="${this.id || 'fs-plan'}-title"><header class="lc-fs-mobile-section-head"><span>${escapeHtml(data.eyebrow || 'Plan de travail')}</span><h1 id="${this.id || 'fs-plan'}-title">${escapeHtml(data.title || '')}</h1><p>${escapeHtml(data.summary || '')}</p></header><div class="lc-fs-mobile-progress"><div><strong data-plan-count>${completed} sur ${steps.length}</strong><span>étapes terminées</span></div><span>${progress}%</span><div role="progressbar" aria-label="Progression du plan de travail" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progress}" data-plan-progress><i style="width:${progress}%"></i></div></div><ol class="lc-fs-mobile-steps">${stepMarkup}</ol>${data.primaryAction ? `<div class="lc-fs-mobile-sticky"><button class="lc-button lc-button--brand" type="button" data-plan-action>${escapeHtml(data.primaryAction)}</button></div>` : ''}</section>`;
    const update = () => {
      const done = [...this.querySelectorAll('[data-plan-step]')].filter(input => input.checked).length;
      const percent = steps.length ? Math.round(done / steps.length * 100) : 0;
      this.querySelector('[data-plan-count]').textContent = `${done} sur ${steps.length}`;
      const bar = this.querySelector('[data-plan-progress]');
      bar.setAttribute('aria-valuenow', String(percent));
      bar.querySelector('i').style.width = `${percent}%`;
    };
    this.querySelectorAll('[data-plan-step]').forEach(input => input.addEventListener('change', () => {
      update();
      this.emitAction('mobile-plan-step', { index: Number(input.dataset.planStep), checked: input.checked });
    }));
    this.querySelector('[data-plan-action]')?.addEventListener('click', () => this.emitAction('mobile-plan-action'));
  }
}

class LcFsMobileCoverage extends JsonComponent {
  render() {
    const data = this.data;
    const coverage = data.coverage || {};
    const requirements = (data.requirements || []).map(item => `<li class="${item.met ? 'is-met' : 'is-missing'}"><span>${lcIcon(item.met ? 'check' : 'close')}</span><span><strong>${escapeHtml(item.label)}</strong><small>${escapeHtml(item.detail || '')}</small></span></li>`).join('');
    this.innerHTML = `<section class="lc-fs-mobile-page" aria-labelledby="${this.id || 'fs-coverage'}-title"><header class="lc-fs-mobile-section-head"><span>${escapeHtml(data.eyebrow || 'Couverture')}</span><h1 id="${this.id || 'fs-coverage'}-title">${escapeHtml(data.title || '')}</h1><p>${escapeHtml(data.summary || '')}</p></header><article class="lc-fs-mobile-coverage-card lc-fs-mobile-coverage-card--${mobileTone(coverage.tone)}"><div><span class="lc-fs-mobile-row__icon">${lcIcon('case')}</span><div><strong>${escapeHtml(coverage.label || '')}</strong><small>${escapeHtml(coverage.detail || '')}</small></div></div>${mobileBadge({ label: coverage.status || '', tone: coverage.tone })}<dl>${mobileFacts(coverage.facts || [])}</dl></article><section class="lc-fs-mobile-subsection"><h2>${escapeHtml(data.requirementsTitle || 'Conditions de prise en charge')}</h2><ul class="lc-fs-mobile-requirements">${requirements}</ul></section>${data.primaryAction ? `<div class="lc-fs-mobile-sticky"><button class="lc-button lc-button--brand" type="button" data-coverage-action>${escapeHtml(data.primaryAction)}</button></div>` : ''}</section>`;
    this.querySelector('[data-coverage-action]')?.addEventListener('click', () => this.emitAction('mobile-coverage-action', { coverage }));
  }
}

class LcFsMobilePartReturn extends JsonComponent {
  render() {
    const data = this.data;
    const reasons = data.reasons || [];
    const reasonOptions = reasons.map(reason => `<option value="${escapeHtml(reason)}">${escapeHtml(reason)}</option>`).join('');
    const checklist = (data.checklist || []).map((item, index) => `<label class="lc-fs-mobile-return-check"><input type="checkbox" data-return-check="${index}" ${item.done ? 'checked' : ''}><span>${escapeHtml(item.label)}</span></label>`).join('');
    this.innerHTML = `<section class="lc-fs-mobile-page" aria-labelledby="${this.id || 'fs-return'}-title"><header class="lc-fs-mobile-section-head"><span>${escapeHtml(data.eyebrow || 'Retour de pièce')}</span><h1 id="${this.id || 'fs-return'}-title">${escapeHtml(data.title || '')}</h1><p>${escapeHtml(data.summary || '')}</p></header><article class="lc-fs-mobile-part"><span class="lc-fs-mobile-part__visual" aria-hidden="true">${lcIcon('case')}</span><div><strong>${escapeHtml(data.part?.name || '')}</strong><small>${escapeHtml(data.part?.sku || '')}</small><span>${escapeHtml(data.part?.serial || '')}</span></div>${data.part?.status ? mobileBadge(data.part.status) : ''}</article><form class="lc-fs-mobile-return-form"><label for="${this.id || 'fs-return'}-reason">${escapeHtml(data.reasonLabel || 'Motif du retour')}</label><select class="lc-select" id="${this.id || 'fs-return'}-reason" name="reason">${reasonOptions}</select><fieldset><legend>${escapeHtml(data.checklistTitle || 'Avant de continuer')}</legend>${checklist}</fieldset><button class="lc-button lc-button--brand" type="submit">${escapeHtml(data.primaryAction || 'Créer le retour')}</button></form></section>`;
    this.querySelector('form').addEventListener('submit', event => {
      event.preventDefault();
      const checked = [...this.querySelectorAll('[data-return-check]')];
      const missing = checked.filter(input => !input.checked);
      if (missing.length) {
        missing[0].focus();
        this.emitAction('mobile-return-error', { message: data.errorMessage || 'Terminez la liste de contrôle avant de créer le retour.' });
        return;
      }
      this.emitAction('mobile-return-submit', { reason: new FormData(event.currentTarget).get('reason'), part: data.part });
    });
  }
}

class LcFsMobileAgentSummary extends JsonComponent {
  render() {
    const data = this.data;
    const highlights = (data.highlights || []).map(item => `<li><span>${lcIcon(item.icon || 'spark')}</span><div><strong>${escapeHtml(item.label)}</strong><small>${escapeHtml(item.detail || '')}</small></div></li>`).join('');
    const actions = (data.actions || []).map((action, index) => `<button class="lc-button ${index === 0 ? 'lc-button--brand' : ''}" type="button" data-agent-action="${index}">${escapeHtml(action.label)}</button>`).join('');
    this.innerHTML = `<section class="lc-fs-mobile-page lc-fs-mobile-agent" aria-labelledby="${this.id || 'fs-agent'}-title"><div class="lc-fs-mobile-agent__mark" aria-hidden="true">${lcIcon('spark')}</div><header><span>${escapeHtml(data.eyebrow || 'Agentforce')}</span><h1 id="${this.id || 'fs-agent'}-title">${escapeHtml(data.title || '')}</h1><p>${escapeHtml(data.summary || '')}</p></header><ul>${highlights}</ul>${data.note ? `<aside><strong>${escapeHtml(data.noteLabel || 'À vérifier')}</strong><p>${escapeHtml(data.note)}</p></aside>` : ''}<div class="lc-fs-mobile-agent__actions">${actions}</div></section>`;
    this.querySelectorAll('[data-agent-action]').forEach(button => button.addEventListener('click', () => {
      const index = Number(button.dataset.agentAction);
      this.emitAction(data.actions[index].action || 'mobile-agent-action', { index, item: data.actions[index] });
    }));
  }
}

class LcDashboardFilters extends JsonComponent {
  render() {
    const data = this.data;
    const filters = (data.filters || []).map((filter, index) => `<label><span>${escapeHtml(filter.label)}</span><select class="lc-select" data-dashboard-filter="${index}">${(filter.options || []).map(option => `<option ${option === filter.value ? 'selected' : ''}>${escapeHtml(option)}</option>`).join('')}</select></label>`).join('');
    this.innerHTML = `<form class="lc-dashboard-filters"><div><h2>${escapeHtml(data.title || 'Dashboard Filters')}</h2><span>${escapeHtml(data.meta || '')}</span></div>${filters}<button class="lc-button" type="reset">Reset</button></form>`;
    this.querySelectorAll('[data-dashboard-filter]').forEach(select => select.addEventListener('change', () => this.emitAction('dashboard-filter', { index: Number(select.dataset.dashboardFilter), value: select.value })));
    this.querySelector('form').addEventListener('reset', () => window.setTimeout(() => this.emitAction('dashboard-reset'), 0));
  }
}

class LcChartBar extends JsonComponent {
  render() {
    const data = this.data;
    const items = data.items || [];
    const max = Math.max(1, ...items.map(item => Number(item.value)));
    const bars = items.map((item, index) => { const width = (Number(item.value) / max) * 100; return `<div class="lc-bar-row"><span>${escapeHtml(item.label)}</span><div><i style="width:${width}%;background:${escapeHtml(item.color || palette[index % palette.length])}"></i></div><strong>${escapeHtml(item.display ?? item.value)}</strong></div>`; }).join('');
    this.innerHTML = chartPanel(data, `<div class="lc-bar-chart" role="img" aria-label="${escapeHtml(data.accessibleLabel || data.title || 'Bar chart')}">${bars}</div>`);
  }
}

class LcChartDonut extends JsonComponent {
  render() {
    const data = this.data;
    const items = data.items || [];
    const total = items.reduce((sum, item) => sum + Number(item.value), 0) || 1;
    let offset = 0;
    const segments = items.map((item, index) => { const percent = Number(item.value) / total * 100; const segment = `<circle cx="70" cy="70" r="52" fill="none" stroke="${escapeHtml(item.color || palette[index % palette.length])}" stroke-width="20" stroke-dasharray="${percent} ${100 - percent}" stroke-dashoffset="${-offset}" pathLength="100"/>`; offset += percent; return segment; }).join('');
    const legend = items.map((item, index) => `<li><i style="background:${escapeHtml(item.color || palette[index % palette.length])}"></i><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.display ?? item.value)}</strong></li>`).join('');
    const chart = `<div class="lc-donut-chart" role="img" aria-label="${escapeHtml(data.accessibleLabel || data.title || 'Donut chart')}"><svg viewBox="0 0 140 140"><g transform="rotate(-90 70 70)">${segments}</g><text x="70" y="66" text-anchor="middle">${escapeHtml(data.centerValue ?? total)}</text><text x="70" y="84" text-anchor="middle" class="sub">${escapeHtml(data.centerLabel || 'Total')}</text></svg><ul>${legend}</ul></div>`;
    this.innerHTML = chartPanel(data, chart);
  }
}

class LcChartGauge extends JsonComponent {
  render() {
    const data = this.data;
    const percent = clamp((Number(data.value) - Number(data.min || 0)) / Math.max(1, Number(data.max || 100) - Number(data.min || 0)) * 100, 0, 100);
    const angle = -180 + percent * 1.8;
    const chart = `<div class="lc-gauge" role="meter" aria-label="${escapeHtml(data.accessibleLabel || data.title || 'Gauge')}" aria-valuenow="${Number(data.value)}" aria-valuemin="${Number(data.min || 0)}" aria-valuemax="${Number(data.max || 100)}"><svg viewBox="0 0 240 135"><path d="M25 115a95 95 0 0 1 190 0" pathLength="100" fill="none" stroke="#dddbda" stroke-width="18" stroke-linecap="round"/><path d="M25 115a95 95 0 0 1 190 0" pathLength="100" fill="none" stroke="${escapeHtml(data.color || '#2e844a')}" stroke-width="18" stroke-linecap="round" stroke-dasharray="${percent} ${100 - percent}"/><g transform="rotate(${angle} 120 115)"><path d="M120 111 190 115 120 119Z" fill="#181818"/></g><circle cx="120" cy="115" r="8" fill="#181818"/><text x="120" y="82" text-anchor="middle">${escapeHtml(data.display ?? data.value)}</text></svg><div><span>${escapeHtml(data.min ?? 0)}</span><strong>${escapeHtml(data.label || '')}</strong><span>${escapeHtml(data.max ?? 100)}</span></div></div>`;
    this.innerHTML = chartPanel(data, chart);
  }
}

class LcChartLine extends JsonComponent {
  render() {
    const data = this.data;
    const series = data.series || [];
    const values = series.flatMap(item => item.values || []);
    const max = Math.max(1, ...values.map(Number));
    const min = Math.min(0, ...values.map(Number));
    const range = Math.max(1, max - min);
    const length = Math.max(2, ...series.map(item => item.values?.length || 0));
    const lines = series.map((item, seriesIndex) => { const points = (item.values || []).map((value, index) => `${40 + index * (520 / (length - 1))},${220 - ((Number(value) - min) / range) * 180}`).join(' '); return `<polyline points="${points}" fill="none" stroke="${escapeHtml(item.color || palette[seriesIndex % palette.length])}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>`; }).join('');
    const labels = (data.labels || []).map((label, index) => `<text x="${40 + index * (520 / (length - 1))}" y="248" text-anchor="middle">${svgText(label)}</text>`).join('');
    const legend = series.map((item, index) => `<span><i style="background:${escapeHtml(item.color || palette[index % palette.length])}"></i>${escapeHtml(item.label)}</span>`).join('');
    const chart = `<div class="lc-line-chart" role="img" aria-label="${escapeHtml(data.accessibleLabel || data.title || 'Line chart')}"><svg viewBox="0 0 600 270"><g stroke="#e5e5e5"><path d="M40 40h520M40 100h520M40 160h520M40 220h520"/></g>${lines}<g class="labels">${labels}</g></svg><div class="lc-chart-legend">${legend}</div></div>`;
    this.innerHTML = chartPanel(data, chart);
  }
}

class LcLeaderboard extends JsonComponent {
  render() {
    const data = this.data;
    const rows = (data.items || []).map((item, index) => `<li><span class="lc-leaderboard__rank">${index + 1}</span><span class="lc-avatar lc-avatar--small">${escapeHtml(item.initials)}</span><span><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.subtitle || '')}</small></span><strong>${escapeHtml(item.value)}</strong><span class="lc-badge lc-badge--${statusClass(item.status)}">${escapeHtml(item.status || '')}</span></li>`).join('');
    this.innerHTML = chartPanel(data, `<ol class="lc-leaderboard">${rows}</ol>`);
  }
}

function chartPanel(data, content) {
  return `<section class="lc-panel lc-chart-panel"><div class="lc-panel__header"><div><h2 class="lc-panel__title">${escapeHtml(data.title || 'Chart')}</h2><div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div></div>${data.action ? `<button class="lc-icon-button" type="button" aria-label="${escapeHtml(data.action)}">${lcIcon('chevron')}</button>` : ''}</div><div class="lc-chart-panel__body">${content}</div></section>`;
}

const newDefinitions = {
  'lc-map': LcMap,
  'lc-route-map': LcRouteMap,
  'lc-technician-roster': LcTechnicianRoster,
  'lc-dispatch-console': LcDispatchConsole,
  'lc-service-appointment': LcServiceAppointment,
  'lc-work-order': LcWorkOrder,
  'lc-parts-inventory': LcPartsInventory,
  'lc-fs-mobile-shell': LcFsMobileShell,
  'lc-fs-mobile-work-order': LcFsMobileWorkOrder,
  'lc-fs-mobile-work-plan': LcFsMobileWorkPlan,
  'lc-fs-mobile-coverage': LcFsMobileCoverage,
  'lc-fs-mobile-part-return': LcFsMobilePartReturn,
  'lc-fs-mobile-agent-summary': LcFsMobileAgentSummary,
  'lc-dashboard-filters': LcDashboardFilters,
  'lc-chart-bar': LcChartBar,
  'lc-chart-donut': LcChartDonut,
  'lc-chart-gauge': LcChartGauge,
  'lc-chart-line': LcChartLine,
  'lc-leaderboard': LcLeaderboard,
};

for (const [name, constructor] of Object.entries(newDefinitions)) {
  if (!customElements.get(name)) customElements.define(name, constructor);
}
