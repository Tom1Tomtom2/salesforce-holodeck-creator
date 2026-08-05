# Templates d'écran — table canal → template + SLOTs

**Règle d'or : on part d'un template, on ne redessine jamais la chrome.**
Copie le fichier `templates/<canal>.html` dans le dossier de sortie, puis remplace
uniquement le contenu entre les marqueurs `<!-- SLOT: nom -->…<!-- /SLOT -->`.
Le `<style>` et la structure hors SLOT sont verrouillés.

Chaque template est autonome, lié à `shared.css` (déjà dans le `<link>`), et embarque
déjà son animation CSS et son clin d'œil produit Salesforce (le `.why` de l'écran).

**Format & page story.** La colonne *Format* pilote l'affichage de l'écran dans `index.html`
(scrollytelling) : `mobile` → coque téléphone, `desktop` → cadre navigateur avec barre d'adresse
(SLOT `url` du manifest). Les templates *mobile* — `instagram`, `whatsapp`, `landing-capture`,
`client-app` — dessinent déjà leur propre coque `.phone` ; `build_site.py` les recadre au lieu d'en
ajouter une (liste `PHONE_TEMPLATES` dans le script — la garder alignée sur cette colonne).

## Table canal → template

| Canal / besoin | Template | Format | Clin d'œil produit | Animation |
|---|---|---|---|---|
| Pub réseaux sociaux | `instagram.html` | mobile | Data Cloud → Meta (`.why`) | compteur de likes |
| Conversation, RDV, SAV, escalade | `whatsapp.html` | mobile | Agentforce / Data Cloud (`.who.ai`) | apparition en cascade `.step` |
| Email (bienvenue, cross-sell, fidélité) | `email-marketing.html` | desktop | Einstein Copy Insights (panneau) | — (statique) |
| Fiche produit / navigation e-commerce | `site-ecommerce.html` | desktop | Data Cloud beacon temps réel | dot qui pulse |
| Landing de capture + résolution d'identité | `landing-capture.html` | mobile | Data Cloud identity resolution (overlay) | fusion des fragments (scriptée) |
| Profil client unifié | `datacloud-profil.html` | desktop | Data Cloud — flux + segments | events « live » + segment qui s'allume |
| Acquisition / activation / re-segmentation | `datacloud-pipeline.html` | desktop | Data Cloud — pipeline vers Meta/Google | status-line qui pulse |
| Création de segment assistée IA | `datacloud-segment.html` | desktop | Data Cloud — Einstein génère le segment (panneau chat) | — (statique) |
| App conseiller / clienteling (vue 360) | `client-app.html` | mobile | Data Cloud — historique réconcilié | — (statique) |
| Console conseiller — appel vocal + IA | `service-console.html` | desktop | Service Assistant / Agentforce (panneau + guidage pas-à-pas) | point d'enregistrement + minuteur qui pulse |
| Caisse / TPV boutique (retour, vente) | `tpv-pos.html` | desktop | MuleSoft → Data Cloud & Salesforce | dot de sync qui pulse |
| Fiche client CRM 360 (Lightning composable) | `lightning-record.html` | desktop | Agentforce — meilleure action suivante (`lc-ai-recommendation`) | interactions du kit (toast, checklist) |
| Tableau de bord CRM Analytics | `lightning-dashboard.html` | desktop | Einstein — insight sur les indicateurs | graphiques SVG (donut/jauge/courbe) |
| Field Service (répartition, interventions) | `lightning-fieldservice.html` | desktop | Einstein — optimisation de tournée / conflit | carte + Gantt de dispatch |

`datacloud-pipeline.html` couvre 3 scènes du même gabarit (acquisition « lookalike »,
activation d'audience vers Meta, re-segmentation post-événement) : n'adapte que les SLOTs
`prod-label`, `intro`, `flow`, `cards`, `status`.

## SLOTs par template

- **instagram.html** — `title`, `act-tag`, `stories`, `post`, `why`
- **whatsapp.html** — `title`, `act-tag`, `brand-initial`, `contact-name`, `contact-status`, `thread`
  (palette dans le thread : `.msg in/out`, `.who ai`, `.prod`, `.slots`, `.rdv`, `.escalate` ;
  numérote l'apparition avec `step sN`)
- **email-marketing.html** — `title`, `act-tag`, `email`, `einstein`
- **site-ecommerce.html** — `title`, `act-tag`, `order-confirm` (retirable), `nav`, `pdp`, `beacon`
- **landing-capture.html** — `title`, `act-tag`, `url`, `landing`, `resolve`
  (garde les `id` cur/sub/resolve/f1/f2/mrg/uni : le `<script>` en bas les anime)
- **datacloud-profil.html** — `title`, `act-tag`, `sf-logo`, `sf-app`, `sf-tabs`, `sf-avatar`, `identity`, `stream`, `segments`
  (garde `.live-2`/`.live-1` en tête du flux, une seule pastille `.seg.on`)
- **datacloud-pipeline.html** — `title`, `act-tag`, `sf-logo`, `sf-app`, `sf-tabs`, `sf-avatar`, `brand`, `prod-label`, `status-chip`, `intro`, `flow`, `cards`, `status`
  (garde le 3e nœud en `.node.dest`)
- **datacloud-segment.html** — `title`, `act-tag`, `sf-logo`, `sf-app`, `sf-tabs`, `sf-avatar`, `seg-card`, `seg-metrics`, `seg-desc`, `attributes`, `chat`
  (modale « Créer un segment avec Einstein » : panneau gauche aperçu + panneau droit chat Einstein — le chat EST le clin d'œil produit, garde-le. Dans `chat`, le message utilisateur porte `<img src="people/…">` = le personnage qui pilote Data Cloud ; garde-le cohérent avec `cast[]`. Dans `attributes`, garde 2-3 lignes `.attr-tbl` cochées.)
- **client-app.html** — `title`, `act-tag`, `brand`, `advisor`, `client-hero`, `appointment` (retirable), `history`, `cta`
- **service-console.html** — `title`, `act-tag`, `sf-logo`, `sf-app`, `sf-tabs`, `sf-avatar`, `contact`, `phone`, `details`, `callhead`, `recap`, `transcript`, `assistant`
  (console conseiller « appel vocal » en 3 colonnes : **gauche** profil 360 — `contact` (bandeau + photo `people/…` + statuts + compteurs + 2 jauges CSAT/NPS, score réglé par `style="--v:87"`), `phone` (panneau CTI : état, numéro, minuteur, contrôles + bouton rouge Terminer), `details` (requête clé/valeur, crayon éditable) ; **centre** — `callhead` (en-tête appel + Modifier), `recap` (rappel de conversation généré par l'IA), `transcript` (bulles `.msg.in` client / `.msg.out` conseiller) ; **droite** — `assistant` = **Service Assistant (Agentforce)** : accueil + guidage pas-à-pas (blocs `.sa-step` avec Étape N + Suivant) + saisie. Le panneau `assistant` EST le clin d'œil produit, garde-le.)

### Header Salesforce Lightning (3 écrans desktop : datacloud-profil, datacloud-pipeline, service-console)
Ces 3 écrans portent en haut le **header Lightning** (défini dans `shared.css` : `.lightning`).
Il reste **aux couleurs Salesforce** (fond blanc, bleu `#0176d3`) — NE le repeins PAS à `--accent`,
c'est ce qui fait reconnaître Salesforce. Seuls 3 SLOTs se remplissent :
- `sf-logo` — **le logo du CLIENT** (remplace le cloud Salesforce) : wordmark `.brand` ou `<img class="brand-logo" src="logo.png" alt="Marque">`.
- `sf-app` — le nom de l'app (ex. « Sales », « Service - Console », « Data Cloud »).
- `sf-tabs` — les onglets ; le 1er en `.ln-tab.on` = actif (souligné bleu). `<svg class="caret">` pour un menu déroulant.
- `sf-avatar` — la photo de l'**utilisateur SF connecté** (haut droite) : `<img class="ln-avatar" src="people/xxx.jpg" alt="">`
  (portrait de la banque `assets/people/`), ou `<span class="ln-avatar"></span>` pour le dégradé neutre.
  **Cohérence** : c'est un personnage de l'histoire (souvent la conseillère/l'employé) → réutilise SA photo, pas un visage inédit.
La recherche, le bouton « Ask » et le cluster d'icônes (droite) sont **verrouillés** — n'y touche pas.
- **tpv-pos.html** — `title`, `act-tag`, `pos-name`, `store`, `scan`, `refund` (garde `.sync`)

### Écrans Lightning composables (kit `<lc-*>`)
Ces 3 templates sont **composés de web components** `<lc-*>` (voir la section « Kit de composants » plus bas).
Chaque SLOT de contenu enveloppe un composant + son `<script type="application/json">` : **ne modifie
que le JSON, jamais la structure du composant**. Le header Lightning (`sf-*`) est le même que les autres écrans SF.
- **lightning-record.html** (fiche client 360) — `title`, `act-tag`, `sf-logo`, `sf-app`, `sf-tabs`, `sf-avatar`, `header` (`lc-record-header`), `customer` (`lc-customer-360`), `related` (`lc-related-list`), `feed` (`lc-engagement-feed`), `assistant` (`lc-ai-recommendation` = **Agentforce, clin d'œil produit, garde-le**)
- **lightning-dashboard.html** (tableau de bord) — `title`, `act-tag`, `sf-*`, `heading`, `filters` (`lc-dashboard-filters`), `kpis` (`lc-kpi-grid`), `donut` (`lc-chart-donut`), `gauge` (`lc-chart-gauge`), `trend` (`lc-chart-line`), `bars` (`lc-chart-bar`), `leaderboard` (`lc-leaderboard`), `insight` (`lc-ai-recommendation` = **Einstein, clin d'œil, garde-le**)
- **lightning-fieldservice.html** (Field Service) — `title`, `act-tag`, `sf-*`, `heading`, `roster` (`lc-technician-roster`), `appointment` (`lc-service-appointment`), `dispatch` (`lc-dispatch-console`), `map` (`lc-map`), `workorder` (`lc-work-order`), `parts` (`lc-parts-inventory`), `assistant` (`lc-ai-recommendation` = **Einstein optimisation, clin d'œil, garde-le**)

## Kit de composants Lightning (`assets/lightning-kit/`)

Les 3 templates `lightning-*` sont **composables** : au lieu d'une chrome figée, leur corps est fait de
web components `<lc-*>` (record header, customer 360, charts, dispatch console, carte…) qui lisent chacun
leur configuration dans un `<script type="application/json">` enfant. C'est le **niveau 2 composable** de la
roadmap : la *chrome* (header Lightning) et *chaque composant* restent verrouillés et crédibles ; seule la
**donnée** se compose depuis le manifest. Un catalogue complet des composants est dans `assets/lightning-kit/`
(fichier source `SOURCE.md`).

**Règles pour ces templates :**
- Le SLOT enveloppe **tout le composant + son `<script>`** : dans le manifest, tu reprends le bloc d'exemple
  du template et **n'ajustes que le JSON** (valeurs). Ne réécris pas la balise `<lc-*>`, ne change pas les clés
  que le composant attend (regarde l'exemple).
- **Marqueur SLOT AUTOUR du `<script>`, jamais dedans** : un commentaire HTML à l'intérieur d'un `<script>`
  casse `JSON.parse` (le contenu d'un `<script>` est du texte brut). Les templates sont déjà écrits ainsi.
- `build_site.py` **bundle** le JS du kit (retire `import`/`export`, concatène) en `lightning-kit.js` et copie
  `lightning-kit.css` — mais **uniquement si un écran pose des `<lc-*>`**. Chargés en `<script>`/`<link>`
  classiques → **marchent en `file://`** (double-clic, zéro serveur), comme le reste de la skill.
- Le panneau `lc-ai-recommendation` (Agentforce/Einstein) est **le clin d'œil produit** de ces écrans : garde-le.
- **Mise en page** : chaque template est une **grille SLDS** (colonnes de largeurs définies), pas des blocs
  qui se répartissent librement. Une page est une pile de **rangées**, chaque rangée suivant un des patrons
  autorisés : **1/1** (plein largeur — bandeau, tableau, grand graphique), **1/3-2/3** (ou 2/3-1/3), ou
  **1/3-1/3-1/3**. On combine les rangées : `lightning-dashboard` empile ainsi un bandeau **1/1** (filtres + KPI),
  une rangée 2/3-1/3 (charts / Einstein) et un grand graphique **1/1** ; `lightning-record` et
  `lightning-fieldservice` = **2/3-1/3** (canvas à gauche, contexte + IA à droite). Les composants vivent
  **dans** une colonne (`.fs-main`/`.fs-rail`, `.lr-stack`, `.db-grid`) ou une rangée 1/1. Si tu ajoutes un bloc,
  mets-le dans une colonne/rangée existante (ou ajoute une rangée 1/1) — ne crée pas une grille imbriquée qui décroche.

**Francisation (shim au build) :** le kit vendoré est un **miroir exact de la source amont** (re-sync l'écrase),
donc ses libellés EN codés en dur (`Optimize Schedule`, `View Details`, en-têtes `SKU/Part…`, `Draft`, `Reset`,
légendes `Scheduled/Travel/…`) sont traduits **au moment du bundle** par le dico `KIT_I18N` de `build_site.py`.
Idem `statusClass()` : les statuts FR du manifest (`Terminé`, `Critique`, `Trajet`…) y sont mappés vers les
couleurs (vert/rouge/orange). **Quand tu ajoutes un composant** avec de nouveaux libellés EN, ajoute une ligne
`(EN, FR)` à `KIT_I18N` (chaque clé porte son contexte `>`/`</span>` pour rester unique) — c'est le **seul**
endroit du français, verrouillé au `--selfcheck`. Le build **lève** si une clé EN a disparu du kit (libellé
déplacé à la source) : signe qu'il faut mettre `KIT_I18N` à jour. Ne traduis pas les fichiers du kit à la main.

## Neutralisation déjà faite

Les templates sont **génériques** : marque « Nova », couleurs pilotées par `--accent`
(réécrit en Phase 3 depuis `:root` de `shared.css`), visuels produit = dégradés d'accent
(aucune image externe). Tu n'as qu'à remplir les SLOTs à la marque de la story.
