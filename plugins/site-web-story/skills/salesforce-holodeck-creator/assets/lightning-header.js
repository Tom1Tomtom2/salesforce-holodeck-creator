(() => {
  const icon = paths => `<svg viewBox="0 0 520 520" aria-hidden="true">${paths}</svg>`;
  const icons = {
    agentforce: icon('<path d="m349 272-69 34a105 105 0 0 0-47 47l-33 67c-5 10-19 10-24 0l-34-68a105 105 0 0 0-47-47l-68-34a13 13 0 0 1 0-24l68-34a105 105 0 0 0 47-47l34-68a13 13 0 0 1 24 0l34 68a105 105 0 0 0 47 47l68 34c10 5 10 19 0 24Zm148 150-30-14a45 45 0 0 1-20-20l-14-30a6 6 0 0 0-10 0l-15 30a45 45 0 0 1-20 20l-30 15c-3 2-3 8 0 10l30 15a45 45 0 0 1 20 20l15 29c2 4 8 4 10 0l14-30a45 45 0 0 1 20-20l30-14c4-2 4-8 0-10Zm0-335-30-15a45 45 0 0 1-20-20l-14-29a6 6 0 0 0-10 0l-15 30a45 45 0 0 1-20 20l-30 14c-3 2-3 8 0 10l30 15a45 45 0 0 1 20 20l15 29c2 4 8 4 10 0l15-30a45 45 0 0 1 20-20l29-14c4-2 4-8 0-10"/>'),
    favorite: icon('<path d="m274 31 46 150c2 6 8 9 14 9h150c15 0 21 20 9 29l-122 90c-5 4-7 11-5 17l58 154c4 14-11 26-23 17l-131-98c-5-4-12-4-18 0l-132 98c-12 9-28-3-23-17l56-154c2-6 0-13-5-17L26 219c-12-9-5-29 9-29h150c7 0 12-2 14-9l47-151c4-14 24-13 28 1"/>'),
    down: icon('<path d="M476 178 271 385c-6 6-16 6-22 0L44 178c-6-6-6-16 0-22l22-22c6-6 16-6 22 0l161 163c6 6 16 6 22 0l161-162c6-6 16-6 22 0l22 22c5 6 5 15 0 21"/>'),
    add: icon('<path d="M300 290h165c8 0 15-7 15-15v-30c0-8-7-15-15-15H300c-6 0-10-4-10-10V55c0-8-7-15-15-15h-30c-8 0-15 7-15 15v165c0 6-4 10-10 10H55c-8 0-15 7-15 15v30c0 8 7 15 15 15h165c6 0 10 4 10 10v165c0 8 7 15 15 15h30c8 0 15-7 15-15V300c0-6 4-10 10-10"/>'),
    trailhead: icon('<path d="M278 20a59 59 0 1 1 0 118 59 59 0 0 1 0-118m152 161c-12-1-23 7-24 18l-6 58c-2 0-3 3-5 3h-55l-38-67c-3-6-9-11-16-12l-58-8c-10-1-20 4-24 14l-44 113c-3 9 1 18 9 23l108 74 9 84c1 11 11 19 22 19 13 0 23-10 22-22l-10-103c0-5-3-10-8-14l-59-66 22-54 26 45c4 6 11 13 19 13h76l-22 180c-1 11 7 20 19 21l2-1c11 0 20-8 22-19l33-278c1-10-8-20-20-21m-308 96 37-95 9-18-5-1a67 67 0 0 0-72 44l-20 52a20 20 0 0 0 14 27l9 2c12 5 24-1 28-11m14 75L91 486c-2 7 3 13 10 13h25c9 0 18-6 21-14l44-97-50-31z"/>'),
    help: icon('<path d="M284 380h-50c-8 0-14-6-14-14v-15c0-42 27-80 67-94a80 80 0 0 0-24-155c-22-1-43 7-59 22a70.4 70.4 0 0 0-23 44c-1 6-7 11-15 11h-50c-9 0-16-7-15-16 4-38 21-72 48-99 32-30 73-46 117-45 83 3 151 71 154 154 3 70-40 133-105 157-9 4-15 11-15 20v15c0 9-8 15-16 15m16 105c0 8-7 15-15 15h-50c-8 0-15-7-15-15v-50c0-8 7-15 15-15h50c8 0 15 7 15 15z"/>'),
    settings: icon('<path d="M261 191c-39 0-70 31-70 70s31 70 70 70 70-31 70-70-31-70-70-70m210 133-37-31a195 195 0 0 0 0-68l37-31c12-10 16-28 8-42l-16-28a34 34 0 0 0-40-14l-46 17a168 168 0 0 0-59-34l-8-47c-3-16-17-25-33-25h-32c-16 0-30 9-33 25l-8 46a180 180 0 0 0-60 34l-46-17-11-2c-12 0-23 6-29 16l-16 28c-8 14-5 32 8 42l37 31a195 195 0 0 0 0 68l-37 31a34 34 0 0 0-8 42l16 28a34 34 0 0 0 40 14l46-17c18 16 38 27 59 34l8 48a33 33 0 0 0 33 27h32c16 0 30-12 33-28l8-48a170 170 0 0 0 62-37l43 17 12 2c12 0 23-6 29-16l15-26c9-11 5-29-7-39m-210 47c-61 0-110-49-110-110s49-110 110-110 110 49 110 110-49 110-110 110"/>'),
    notification: icon('<path d="M460 330h-5a35 35 0 0 1-35-35V180A160 160 0 0 0 252 20c-86 4-152 78-152 165v111c0 19-16 34-35 34h-5c-22 0-40 19-40 41v15c0 7 7 14 15 14h450c8 0 15-7 15-15v-15a40 40 0 0 0-40-40M309 440h-98a10 10 0 0 0-10 12c5 28 30 48 59 48s54-21 59-48a10 10 0 0 0-10-12"/>'),
  };

  const action = (name, label, extra = '') => `<button class="ln-utility ${extra}" type="button" aria-label="${label}" title="${label}" data-ln-action="${name}">${icons[name]}</button>`;

  document.querySelectorAll('.lightning .ln-top').forEach(header => {
    if (header.querySelector('.ln-utilities')) return;
    const oldAsk = header.querySelector('.ln-ask');
    const oldIcons = header.querySelector('.ln-icons');
    const agentLauncher = header.querySelector('[data-agent-launcher]');
    const avatarSlot = oldIcons?.querySelector('[class~="ln-avatar"]');
    const avatar = avatarSlot?.outerHTML || '<span class="ln-avatar"></span>';
    const utilities = document.createElement('div');
    utilities.className = 'ln-utilities';
    utilities.setAttribute('aria-label', 'Actions globales Salesforce');
    utilities.innerHTML = `${action('agentforce', 'Ouvrir Agentforce', 'ln-ask')}<span class="ln-favorites">${action('favorite', 'Favoris')}${action('down', 'Menu des favoris')}</span>${action('add', 'Créer')}${action('trailhead', 'Trailhead')}${action('help', 'Aide')}${action('settings', 'Configuration')}<span class="ln-bell">${action('notification', 'Notifications')}<span class="badge">8</span></span><span class="ln-profile" title="Profil utilisateur">${avatar}<span class="ln-sr-only">Profil utilisateur</span></span>`;
    if (agentLauncher) {
      const placeholder = utilities.querySelector('[data-ln-action="agentforce"]');
      agentLauncher.classList.add('ln-utility', 'ln-ask');
      agentLauncher.innerHTML = `${icons.agentforce}<span class="ln-sr-only">Ouvrir Agentforce</span>`;
      placeholder.replaceWith(agentLauncher);
    }
    if (oldAsk !== agentLauncher) oldAsk?.remove();
    oldIcons?.replaceWith(utilities);
    if (!oldIcons) header.append(utilities);
  });
})();
