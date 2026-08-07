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
`client-app` et les templates `fieldservice-mobile-*` — dessinent déjà leur propre coque `.phone` ; `build_site.py` les recadre au lieu d'en
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
| Field Service mobile — ordre de travail | `fieldservice-mobile-work-order.html` | mobile | Field Service — contexte technicien | sections pilotées par JSON |
| Field Service mobile — plan de travail | `fieldservice-mobile-work-plan.html` | mobile | Field Service — exécution guidée | checklist interactive |
| Field Service mobile — couverture | `fieldservice-mobile-coverage.html` | mobile | Field Service — éligibilité | couverture et conditions |
| Field Service mobile — retour de pièce | `fieldservice-mobile-part-return.html` | mobile | Field Service — stock mobile | validation avant retour |
| Field Service mobile — résumé Agentforce | `fieldservice-mobile-agent-summary.html` | mobile | Agentforce — compte rendu | synthèse à valider |
| Marketing Cloud (campagne, parcours, e-mail, segment) | `lightning-marketing.html` | desktop | Agentforce (email studio) / Einstein (segment) | canvas de parcours + sparklines |
| Pipeline commercial Sales Cloud | `lightning-sales.html` | desktop | Einstein — inspection des affaires | Kanban + scoring + activité |
| Analyse des mouvements Pipeline Inspection | `lightning-pipeline-inspection.html` | desktop | Einstein — signaux et risques de l'affaire | waterfall + table + panneau d'insights |
| Devis, tarification et approbation Revenue Cloud | `lightning-revenue.html` | desktop | Agentforce — analyse de marge | recalcul des totaux + parcours d'approbation |
| Portail client — produits et demande de prêt | `financial-loan-portal.html` | desktop | Experience Cloud + Financial Services Cloud | formulaire multi-étapes |
| Loan processor — instruction du dossier | `financial-loan-processor.html` | desktop | Financial Services Cloud + Agentforce | résumé, progression, assistant |
| Loan underwriter — analyse et décision | `financial-loan-underwriter.html` | desktop | Financial Services Cloud + Agentforce | ratios, contrôles, recommandation |
| Accueil Commerce B2B Consumer Goods | `consumer-commerce-home.html` | desktop | Commerce Cloud | catalogue et bénéfices B2B |
| Saisie de commande Consumer Goods | `consumer-commerce-order.html` | desktop | Commerce Cloud + Agentforce | sélection produits et assistant contextuel |
| Performance réseau Consumer Goods | `consumer-service-performance.html` | desktop | Consumer Goods Cloud + Service Cloud + Agentforce | magasins, KPI et activité service |
| Cockpit compte Consumer Goods | `consumer-service-account.html` | desktop | Consumer Goods Cloud + Agentforce | ventes, programmes et actifs |
| Dossier de service Consumer Goods | `consumer-service-case.html` | desktop | Service Cloud + Agentforce | dossier, chronologie et résolution |
| Actif connecté Consumer Goods | `consumer-service-asset.html` | desktop | Service Cloud + Agentforce | télémétrie, diagnostic et intervention |
| Plan promotionnel Consumer Goods | `consumer-sales-trade-plan.html` | desktop | Consumer Goods Cloud + Agentforce | calendrier TPM et scénarios |
| Sales Agreement Consumer Goods | `consumer-sales-agreement.html` | desktop | Consumer Goods Cloud + Agentforce | engagement, réalisé et forecast |
| Advanced Forecast Consumer Goods | `consumer-sales-forecast.html` | desktop | Consumer Goods Cloud + Agentforce | business planning et forecast ajustable |
| Accord commercial Manufacturing | `manufacturing-sales-agreement.html` | desktop | Manufacturing Cloud + Agentforce | engagements par produit et période, calculs |
| Objectif de compte Manufacturing | `manufacturing-account-target.html` | desktop | Manufacturing Cloud | synthèse, affectations et distribution |
| Service actif et garanties Manufacturing | `manufacturing-asset-service.html` | desktop | Manufacturing Cloud + Service Cloud + Agentforce | identité, couvertures, dossiers, interventions et jalons |
| Hiérarchie des actifs Manufacturing | `manufacturing-asset-hierarchy.html` | desktop | Manufacturing Cloud | arbre accessible, recherche et navigation clavier |
| Configurateur produits Revenue Cloud Advanced | `revenue-product-configurator.html` | desktop | Revenue Cloud Advanced | catalogue, attributs et règles de configuration |
| Atelier de devis Revenue Cloud Advanced | `revenue-quote-workspace.html` | desktop | Revenue Cloud Advanced + Agentforce | tarification, marge, multi-devises et recommandation |
| Centre d’approbation Revenue Cloud Advanced | `revenue-approval-center.html` | desktop | Revenue Cloud Advanced | garde-fous, chaîne et historique de décision |
| Pipeline des devis Revenue Cloud Advanced | `revenue-quote-pipeline.html` | desktop | Revenue Cloud Advanced | board quote-to-cash, marge et risques |

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
- **financial-loan-portal.html** — `title`, `act-tag`, `brand`, `nav`, `heading`, `catalog`
  (`lc-loan-product-catalog`), `application` (`lc-loan-application-form`)
- **financial-loan-processor.html** — `title`, `act-tag`, `sf-*`, `header`, `path`, `tree`
  (`lc-loan-record-tree`), `summary` (`lc-structured-summary`), `actions`, `agent`
  (`lc-agent-conversation`)
- **financial-loan-underwriter.html** — `title`, `act-tag`, `sf-*`, `header`, `ratios`
  (`lc-loan-key-ratios`), `stages` (`lc-loan-stage-board`), `conditions`, `recommendation`, `agent`
- **consumer-commerce-home.html** — `title`, `act-tag`, `brand`, `nav`, `commerce`
  (`lc-b2b-commerce-home`)
- **consumer-commerce-order.html** — `title`, `act-tag`, `brand`, `nav`, `heading`, `order`
  (`lc-consumer-order-capture`), `agent` (`lc-agent-overlay`)
- **consumer-service-performance.html** — `title`, `act-tag`, `sf-*`, `heading`, `performance`
  (`lc-retail-store-performance`), `agent` (`lc-agent-overlay`)
- **consumer-service-account.html** — `title`, `act-tag`, `sf-*`, `header`, `cockpit`
  (`lc-retail-account-cockpit`), `activities`, `agent` (`lc-agent-overlay`)
- **consumer-service-case.html** — `title`, `act-tag`, `sf-*`, `header`, `path`, `summary`,
  `timeline`, `workorders`, `agent` (`lc-agent-overlay`)
- **consumer-service-asset.html** — `title`, `act-tag`, `sf-*`, `header`, `telemetry`
  (`lc-asset-telemetry`), `history`, `agent` (`lc-agent-overlay`)
- **consumer-sales-trade-plan.html** — `title`, `act-tag`, `sf-*`, `heading`, `calendar`
  (`lc-trade-promotion-calendar`), `agent` (`lc-agent-overlay`)
- **consumer-sales-agreement.html** — `title`, `act-tag`, `sf-*`, `header`, `agreement`
  (`lc-sales-agreement-forecast`), `agent` (`lc-agent-overlay`)
- **consumer-sales-forecast.html** — `title`, `act-tag`, `sf-*`, `heading`, `planner`
  (`lc-trade-business-planner`), `agent` (`lc-agent-overlay`)
- **manufacturing-sales-agreement.html** — `title`, `act-tag`, `sf-*`, `header`, `agreement`
  (`lc-manufacturing-agreement-terms`), `agent` (`lc-agent-overlay`)
- **manufacturing-account-target.html** — `title`, `act-tag`, `sf-*`, `header`, `target`
  (`lc-account-manager-target`)
- **manufacturing-asset-service.html** — `title`, `act-tag`, `sf-*`, `header`, `overview`
  (`lc-manufacturing-asset-overview`), `warranties`, `cases`, `workorders` (trois `lc-related-list`
  avec des IDs hôtes uniques), `milestones` (`lc-asset-milestones`), `agent` (`lc-agent-overlay`).
  Le job d’écran reste `asset-service`; la garantie est exposée par le composant au job `warranty-management`.
- **manufacturing-asset-hierarchy.html** — `title`, `act-tag`, `sf-*`, `header`, `hierarchy`
  (`lc-asset-hierarchy`). L’arbre suit le modèle ARIA tree/treeitem/group et prend en charge les flèches,
  Origine/Fin, Entrée et Espace.
- **revenue-product-configurator.html** — `title`, `act-tag`, `sf-*`, `configurator`
  (`lc-revenue-product-configurator`). Le composant couvre catalogue, sélection, quantités, attributs et résumé ;
  la sélection et les quantités recalculent le total ponctuel dans la démo.
- **revenue-quote-workspace.html** — `title`, `act-tag`, `sf-*`, `header`, `pricing`
  (`lc-revenue-quote-pricing`), `waterfall` (`lc-revenue-pricing-waterfall`), `currencies`
  (`lc-revenue-currency-manager`), `recommendation` (`lc-ai-recommendation`).
- **revenue-approval-center.html** — `title`, `act-tag`, `sf-*`, `header`, `approval`
  (`lc-revenue-approval-center`).
- **revenue-quote-pipeline.html** — `title`, `act-tag`, `sf-*`, `pipeline`
  (`lc-revenue-quote-pipeline`). Ce board suit les devis et leurs garde-fous, pas les opportunités Sales Cloud.
  L'exemple complet `registry/examples/revenue-cloud-advanced-quotes.json` enchaîne configuration,
  tarification multi-devises, approbation et pilotage en conservant le même compte et le même devis.

`lc-agent-overlay` a deux modes de déclenchement : la valeur par défaut affiche une capsule
flottante sur les sites externes ; `data-mode="lightning"` remplace le bouton Ask du shell
Salesforce par une icône Agentforce et ouvre une barre latérale sous l'en-tête global.

Tout écran qui contient `.lightning` reçoit automatiquement la barre d'actions globale commune :
Agentforce, favoris, création, Trailhead, aide, configuration, notifications, puis l'avatar issu du
SLOT `sf-avatar`. `build_site.py` injecte `lightning-header.js` ; ne redessine pas cette barre dans un
nouveau template.

Pour que l'avatar suive le personnage connecté dans chaque acte, donne une `image` à chaque personnage
de `intro.cast[]`, puis ajoute `"persona": "Nom exact du personnage"` à l'écran Salesforce. Le builder
injecte alors automatiquement cette image dans `sf-avatar`. Un contenu explicite dans le SLOT
`sf-avatar` reste prioritaire ; sans `persona` ni SLOT explicite, le template conserve son avatar neutre.

### Écrans Lightning composables (kit `<lc-*>`)
Ces templates sont **composés de web components** `<lc-*>` (voir la section « Kit de composants » plus bas).
Chaque SLOT de contenu enveloppe un composant + son `<script type="application/json">` : **ne modifie
que le JSON, jamais la structure du composant**. Le header Lightning (`sf-*`) est le même que les autres écrans SF.
- **lightning-record.html** (fiche client 360) — `title`, `act-tag`, `sf-logo`, `sf-app`, `sf-tabs`, `sf-avatar`, `header` (`lc-record-header`), `customer` (`lc-customer-360`), `related` (`lc-related-list`), `feed` (`lc-engagement-feed`), `assistant` (`lc-ai-recommendation` = **Agentforce, clin d'œil produit, garde-le**)
- **lightning-dashboard.html** (tableau de bord) — `title`, `act-tag`, `sf-*`, `heading`, `filters` (`lc-dashboard-filters`), `kpis` (`lc-kpi-grid`), `donut` (`lc-chart-donut`), `gauge` (`lc-chart-gauge`), `trend` (`lc-chart-line`), `bars` (`lc-chart-bar`), `leaderboard` (`lc-leaderboard`), `insight` (`lc-ai-recommendation` = **Einstein, clin d'œil, garde-le**)
- **lightning-fieldservice.html** (Field Service) — `title`, `act-tag`, `sf-*`, `heading`, `roster` (`lc-technician-roster`), `appointment` (`lc-service-appointment`), `dispatch` (`lc-dispatch-console`), `map` (`lc-map`), `workorder` (`lc-work-order`), `parts` (`lc-parts-inventory`), `assistant` (`lc-ai-recommendation` = **Einstein optimisation, clin d'œil, garde-le**)
- **fieldservice-mobile-*.html** — `title`, `act-tag`, `app`. Le SLOT `app` contient une coque
  `lc-fs-mobile-shell` et une surface métier (`lc-fs-mobile-work-order`, `lc-fs-mobile-work-plan`,
  `lc-fs-mobile-coverage`, `lc-fs-mobile-part-return` ou `lc-fs-mobile-agent-summary`). Reprends le bloc
  complet et n'ajuste que les deux objets JSON. La coque, la barre haute et la navigation basse restent communes.
- **lightning-marketing.html** (Marketing Cloud) — `title`, `act-tag`, `sf-*`, `header` (`lc-marketing-header`), `campaign` (`lc-campaign-workspace`), `journey` (`lc-journey-builder`), `email` (`lc-email-studio`), `segment` (`lc-segment-builder`), `performance` (`lc-marketing-performance`)
  (**6 surfaces empilées en 1/1, chacune RETIRABLE** : un acte MC montre en général UNE surface — vide les SLOTs des autres pour les masquer. Ex. acte « je construis mon parcours » → garde `header`+`campaign`+`journey`, vide `email`/`segment`/`performance`. Le panneau **Agentforce** de `email` et le panneau **Einstein** de `segment` sont les clins d'œil produit : garde-les quand la surface est affichée. `journey` : les nœuds se placent sur une grille `row`/`column` reliée par un connecteur SVG **fixe** — garde le schéma start→email→wait→decision→3 branches→…→end, n'ajuste que les libellés.)
- **lightning-sales.html** (Sales Cloud) — `title`, `act-tag`, `sf-*`, `overview`
  (`lc-sales-overview`), `pipeline` (`lc-pipeline-board`), `inspection` (`lc-deal-inspection`),
  `activity` (`lc-sales-activity`). Le pipeline est un **Kanban d'opportunités** en 2/3 ; la colonne 1/3
  conserve l'inspection Einstein et l'activité. Ajuste les étapes, montants, risques et propriétaires,
  sans changer la structure. `inspection` est le clin d'œil produit : garde-le.
- **lightning-pipeline-inspection.html** (Sales Cloud Pipeline Inspection) — `title`, `act-tag`,
  `sf-*`, `heading`, `summary` (`lc-pipeline-inspection-summary`), `waterfall`
  (`lc-revenue-waterfall`), `opportunities` (`lc-risk-deal-table`), `insights`
  (`lc-opportunity-insight-panel`). `summary.metrics` et `waterfall.items` doivent raconter les mêmes
  mouvements ; le total final du waterfall doit correspondre au pipeline d'ouverture corrigé des entrées
  et sorties. `insights` décrit l'opportunité mise en avant dans la table. Garde au moins un signal
  d'attention et un signal positif : c'est la valeur Einstein de l'écran.
- **lightning-revenue.html** (Revenue Cloud) — `title`, `act-tag`, `sf-*`, `header`
  (`lc-record-header`), `path` (`lc-status-path`), `quote` (`lc-quote-builder`), `approval`
  (`lc-quote-approval`), `agent` (`lc-agent-overlay`). Le devis occupe 2/3 ; approbation et Revenue Agent
  occupent 1/3. Le composant recalcule quantité, prix, remise et taxes en temps réel. Les données sont des
  nombres bruts (`quantity`, `unitPrice`, `discount`, `taxRate`) ; la devise est définie par `currency`.
  Garde `approval` et `agent` : ils matérialisent la gouvernance de marge et la valeur Agentforce.

## B2B vs B2C — quels écrans existent

La bibliothèque a été bâtie pour des parcours **grand public (B2C)** : acquisition (instagram, email),
conversation/SAV (whatsapp, service-console), boutique (site-ecommerce, tpv-pos), fidélité, et les vues
Salesforce transverses (datacloud-*, lightning-record/dashboard/fieldservice). Pour une démo **B2B**
(vente entreprise : lead → opportunité → prévision → devis → onboarding → renouvellement), la couverture
est **partielle** — voici l'état honnête, à annoncer à l'utilisateur en Phase 2 :

| Besoin B2B | Écran dispo aujourd'hui | Statut |
|---|---|---|
| Prospection / réengagement compte | `email-marketing`, `whatsapp` | ✅ réutilisable (adapter le ton B2B) |
| Fiche compte / contact 360 | `lightning-record` | ✅ (persona = contact du compte) |
| Console commerciale / relance | `service-console` | ⚠️ proche (conçue SAV, se détourne en console vente) |
| Pipeline & inspection des ventes | `lightning-sales` | ✅ Kanban, risques et meilleure action |
| Explication des variations du pipeline | `lightning-pipeline-inspection` | ✅ waterfall, opportunités et insights Einstein |
| Prévision agrégée / forecast hiérarchique | `lightning-dashboard` | ⚠️ proche (KPI/charts génériques) ; composants forecast disponibles mais non câblés |
| **Devis (CPQ / Revenue Cloud)** | `lightning-revenue` | ✅ configuration, calcul temps réel, approbation et Revenue Agent |
| **Devis Revenue Cloud Advanced** | `revenue-product-configurator`, `revenue-quote-workspace`, `revenue-approval-center`, `revenue-quote-pipeline` | ✅ configuration, pricing, marge, multi-devises, approbation et pipeline des devis |
| Portail partenaire / Experience Cloud | — | ❌ **à créer** (aucun composant dédié — chrome à dessiner) |
| **Marketing Cloud (campagne, parcours, e-mail studio, segment)** | `lightning-marketing` | ✅ (câblé — 6 surfaces masquables) — utile B2C **et** B2B (nurturing) |

**Règle** : si le brief réclame un écran ❌, ne l'improvise pas — signale-le et prends le ⚠️ le plus
proche en attendant. Les composants de forecast avancé (`lc-forecast-*`, `lc-team-attainment`,
`lc-pipeline-velocity`, `lc-win-rate-heatmap`) existent dans le kit mais ne sont pas encore câblés.
Pour un besoin ❌ ou ⚠️, crée le template à partir du cahier des charges puis ajoute ses libellés EN
à `KIT_I18N`. On ne construit jamais un écran spéculatif.

## Kit de composants Lightning (`assets/lightning-kit/`)

Les templates `lightning-*` sont **composables** : au lieu d'une chrome figée, leur corps est fait de
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
