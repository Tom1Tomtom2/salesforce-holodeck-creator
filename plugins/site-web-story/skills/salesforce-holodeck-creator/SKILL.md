---
name: salesforce-holodeck-creator
description: |
  MUST TRIGGER dès que l'utilisateur dit qu'il souhaite faire, créer, construire,
  préparer, générer ou améliorer une démo pour un client, un prospect, une marque,
  un compte ou un rendez-vous commercial, même s'il ne mentionne pas Salesforce.
  MUST aussi déclencher pour toute demande de holodeck pour un client ou prospect.
  Exemples : « je veux faire une démo pour ce client », « prépare une démo client »,
  « démo pour le client X », « customer demo », « client demo », « sales demo »,
  « holodeck client », « holodeck pour Acme », « démo holodeck », « prépare-moi une
  démo pour X », « parcours client Salesforce », « story de marque », « démo comme
  agnès b. » ou des maquettes d'écrans Salesforce reliées par une narration.

  Construit une démonstration client Salesforce narrative depuis une marque, une
  URL et, facultativement, un cahier des charges ou un brief. Assemble un site
  statique en plusieurs actes à partir de templates HTML/CSS, puis génère des
  notes présentateur et une revue visuelle automatisée. Le brief complémentaire
  reste facultatif et ne doit jamais bloquer le démarrage.

  DO NOT TRIGGER uniquement si l'utilisateur demande explicitement de reskinner
  des captures avec Gemini, d'utiliser le holodeck app.py, de construire une vraie
  application Salesforce/LWC/Experience Cloud, un site marchand de production,
  ou un simple diagramme ou une slide unique.
version: "1.12.0"
---

# Salesforce Holodeck Creator

Skill conversationnelle. **Tu es l'orchestrateur.** Le livrable est un dossier de
site statique assemblé depuis des templates HTML/CSS artisanaux. Tu écris le brief,
la narration et le manifest ; `build_site.py` assemble les écrans. Pas d'images
générées, pas de serveur applicatif. Suis les 3 phases dans l'ordre. N'avance pas
à la phase suivante sans validation de l'utilisateur.

Cette skill est le pendant "artisanal" du holodeck `app.py` (qui, lui, reskine des
captures via Gemini). Ici tout est dessiné en markup, comme la démo agnès b.

## Assets de la skill (chemins relatifs à ce dossier)
- `assets/shared.css` — design tokens + composants (`.chip` `.btn` `.phone` `.act-tag`
  `.why` `.accent-band` `.brand` `.brand-mark`). **Base de tout écran.**
- `assets/index.template.html` — squelette de la **page story** (scrollytelling) : hero, écran
  d'intro (personnages + frise), puis une section par acte (récit + vrai écran en iframe live).
- `templates/*.html` — **bibliothèque d'écrans complets, chrome verrouillée + SLOTs.**
  C'est le cœur : tu pars TOUJOURS d'un template, tu ne redessines jamais un écran.
- `assets/lightning-kit/` — **kit de composants `<lc-*>`** (record 360, charts, dispatch, carte, parcours marketing…)
  utilisé par les templates `lightning-record` / `lightning-dashboard` / `lightning-fieldservice` / `lightning-marketing`
  et les écrans sectoriels Consumer Goods, Financial Services et Manufacturing.
  Écrans Salesforce **composables** : chaque bloc lit sa config d'un `<script JSON>` slotté. Détails dans `references/screens.md`.
- `references/screens.md` — table canal → template + liste des SLOTs de chaque template.
- `references/fidelite-salesforce.md` — grille de relecture des écrans **desktop Salesforce**
  (crédibilité du shell Lightning, dimensions de référence, pièges à éviter). Passe-la sur ces écrans.
- `references/story-recipes.md` — recettes narratives prêtes à adapter (acquisition,
  service, vente B2B, Field Service, marketing, pilotage). Utilise-les comme accélérateur,
  jamais comme catalogue automatique.
- `references/extending.md` — workflow mainteneur pour ajouter un composant `<lc-*>`, créer
  un template, cataloguer l'asset, ajouter une icône produit et valider l'extension.
- `references/troubleshooting.md` — diagnostic des erreurs d'installation, crawl, SLOT, JSON,
  registre, bundle JavaScript, assets et cadrage visuel.
- `registry/*.json` — catalogue machine-readable des composants, écrans, produits et
  industries. Lis `registry/screens.json` pour choisir un écran et `registry/components.json`
  pour vérifier sa couverture ; règles d'extension dans `references/registry.md`.
- `scripts/validate_registry.py` — vérifie que le catalogue reste aligné sur les templates,
  les SLOTs et les définitions `<lc-*>`. Le builder l'exécute automatiquement.
- `scripts/build_site.py` — assemble le site depuis un manifest JSON (copie les
  templates, injecte les SLOTs, réécrit les tokens, génère le hub). **C'est lui qui
  écrit le HTML, pas toi.**
- `scripts/crawl_brand.py` — crawle le site de la marque avec un **vrai navigateur**
  (Chromium/Chrome headless furtif) et pré-remplit la Phase 1 : logo, images produit
  HD, palette, typo, secteur. **À lancer avant de proposer l'ambiance.** WebFetch/curl
  échouent sur les sites de marque (anti-bot CDN → 503) ; ce script exécute le JS et passe.
- `scripts/review_site.py` — ouvre le build dans Chromium, capture chaque écran et le
  hub, produit une planche contact et remonte les erreurs visibles avant restitution.

---

## Phase 1 — Intro : marque + ambiance

0. **Cahier des charges (si l'utilisateur en fournit un).** Un cahier des charges = le document
   client qui liste les besoins/objectifs de la démo (PDF, Word, texte collé, ou lien). Quand il y
   en a un, **il devient la colonne vertébrale de la story** — tu ne la devines plus, tu la déduis
   du document. Tu sais déjà lire un PDF/Word/texte : lis-le et **restitue un « brief » structuré en
   markdown, puis demande validation** avant d'avancer. Le brief tient en ~8 puces :
   - **Objectif de la démo** (ce que le client veut prouver/vendre : moderniser le SAV, unifier
     web↔magasin, accélérer le cycle de vente B2B…) ;
   - **Cible / segment** : grand public (B2C) **ou** entreprise (B2B) — ça change le persona et les
     canaux (voir Phase 2) ;
   - **Persona(s)** imposés par le doc (rôles, fonctions) ;
   - **Parcours / moments** à démontrer (les étapes que le client cite explicitement) ;
   - **Produits Salesforce** attendus (Sales Cloud, Service Cloud, Data Cloud, Agentforce, CPQ/Revenue,
     Marketing Cloud, MuleSoft…) — s'ils sont nommés, respecte-les ; sinon propose ;
   - **Canaux / écrans** demandés (email, WhatsApp, console, dashboard, pipeline commercial, devis…) ;
   - **Contraintes** : ton, langue, secteur, éléments à ne PAS montrer, marque à respecter ;
   - **Exigences non couvertes par un template existant** — signale-les EXPLICITEMENT (« le doc
     demande un écran de prévision des ventes ; aucun template ne le couvre encore »). **N'improvise
     jamais l'écran manquant** (règle d'or) : liste-le comme un manque à combler côté skill, et
     propose de continuer avec le template le plus proche en attendant. Voir `references/screens.md`
     (§ B2B) pour ce qui existe et ce qui reste à créer.
   Le reste de la Phase 1 (crawl marque, recherche stratégie, ambiance) s'applique toujours : le
   cahier des charges dit **quoi** démontrer, le crawl + la recherche disent **à quoi ça ressemble**.

1. Demande **le nom de la marque** et **l'URL du site** (si pas déjà donnés).
   Propose ensuite un **brief facultatif**, dans le même message, sans bloquer la suite :
   - audience du pitch (direction, métier, IT, mixte),
   - objectif du rendez-vous,
   - durée cible de la démo,
   - tension métier à illustrer,
   - produits Salesforce imposés ou à éviter,
    - faits/chiffres fournis et sujets sensibles à ne pas inventer.

   **Choix des licences Salesforce — obligatoire dès qu'un écran sectoriel est envisagé.** Présente
   explicitement deux options à l'utilisateur :
   - expérience construite avec les Clouds déjà licenciés (par exemple Sales Cloud / Service Cloud) ;
   - expérience sectorielle avec **Financial Services Cloud**, **Consumer Goods Cloud** ou
     **Manufacturing Cloud**. Ces produits ont des licences et droits distincts de Sales Cloud.
   Demande quel périmètre il souhaite utiliser avant de figer la story. Ne présente jamais un écran
   sectoriel comme une simple fonctionnalité de Sales Cloud. Enregistre le choix dans
   `license_selection` et garde `confirmed:false` tant que l'utilisateur ne l'a pas confirmé.

   Formulation attendue : « Si tu veux mieux cibler la démo, tu peux aussi me donner
   l'audience, l'objectif, la durée et les produits à mettre en avant. C'est facultatif ;
   sinon je les déduis de la marque et je te soumets mes hypothèses. » Ne pose pas six
   questions successives et ne retarde jamais le crawl en attendant ces réponses.
2. **Crawle le site** (n'utilise PAS WebFetch : les sites de marque renvoient 503 à un
   client sans JS) :
   ```bash
   python3 scripts/crawl_brand.py <url> --brand "<Marque>" --slug <slug>
   ```
   Il écrit `./<slug>-brand/` : `brand.json` (accent proposé, typo, secteur, CTA détectés),
   `logo.*`, et `product-N.*` (visuels produit HD). **Lis `brand.json`** pour l'ambiance.
   Inspecte les `product-N.*` avec l'outil de lecture de fichiers/images disponible
   dans Claude Code pour repérer les modèles/produits réels.
   - **Ce 1er crawl est « à l'aveugle »** (il tourne AVANT qu'on sache quels produits l'histoire va
     montrer) : il ramasse le logo, la palette, et quelques visuels de la home pour l'ambiance. Les
     **images produit EXACTES** se récupèrent en 2e passe, après la story validée (voir Phase 3 §1bis).
     Le champ `brand.json.product_links` = un **catalogue de liens produit RÉELS** (href + libellé)
     relevés sur la home, qui servira à cette 2e passe. Ne devine jamais une URL produit toi-même.
   - **Logo — cascade de sources** (le champ `brand.json.logo_source` dit laquelle a servi) :
     DOM du site → SVG inline → **Wikidata/Commons** (logo officiel, propriété P154, non bloqué
     par les anti-bot) → favicon `icon.horse`. Un site bloqué rend souvent quand même son **vrai
     logo** via Wikidata — regarde `logo_source` avant de conclure à un échec de logo.
   - **Vérifie `brand.json.status`** : si `"failed"`, le crawl a été bloqué (anti-bot) ou n'a
     rien récupéré — le champ `error` dit quoi. Ne te sers PAS des valeurs par défaut.
     (Un `status:"failed"` avec `logo_source:"Wikidata/Commons"` = seules les **images produit**
     manquent, le logo est bon — enchaîne sur le `--fetch` du Plan B pour les seules images.)
   - **Plan B quand le crawl échoue — demande les visuels à l'utilisateur.** Dis-lui que
     le crawl automatique n'a pas abouti, et **demande-lui de fournir en local** :
     1. **le logo de la marque** (fichier image : png/svg/jpg) ;
     2. **des photos produit** — indique combien il en faut : **1 par écran qui montre un
        produit** (fiche e-commerce, pub Instagram, carte WhatsApp, historique app…).
        Compte ces écrans dans la story et **annonce le nombre précis** (« il me faut
        2 photos produit pour cette story » — souvent 2 à 4). Minimum 2.
     Demande les **chemins des fichiers** (ex. `~/Desktop/logo.png`, `~/Desktop/manteau.jpg`).
     Tu les embarqueras dans le site en Phase 3 (clé `assets` du manifest + `.brand-logo` /
     `<img>` dans les slots). Déduis quand même l'accent/typo du nom + secteur (et signale-le).
   - **Backup par URL** — si l'utilisateur a des **URL** d'images produit (fiche marketplace,
     presse, réseaux) plutôt que des fichiers locaux, télécharge-les d'un coup :
     ```bash
     python3 scripts/crawl_brand.py --fetch <url1> <url2>… --slug <slug>
     ```
     Elles atterrissent en `product-N.*` dans `<slug>-brand/` (referer = origine de l'image,
     pour passer le CDN) : réfère-les ensuite par **basename** dans la clé `assets` du manifest,
     comme des fichiers fournis.
   - Si l'utilisateur ne peut/veut pas fournir d'images : **déduis l'ambiance du nom + secteur**
     (et signale-le) — le site reste en dégradés d'accent (contrat « zéro image »).
   - Première utilisation : `pip install -r requirements.txt && playwright install chromium`
     (Chrome système utilisé en priorité s'il est là).
3. **Recherche la stratégie de la marque** (pour que la story colle à ses vrais enjeux,
   pas juste à son catalogue). C'est de la synthèse — pas de parsing : tu lis et tu résumes.
   - **Google News (source de tête, passe l'anti-bot)** — presse récente et datée :
     ```
     Ouvre https://news.google.com/rss/search?q=<Marque>+stratégie&hl=fr&gl=FR&ceid=FR:fr
     ```
     Demande dans le prompt : les titres/sources/dates récents + 3 puces d'enjeux
     (croissance, international, retail vs digital, positionnement prix, durabilité, levée de fonds).
   - **Wikipédia en complément** (`fr.wikipedia.org/wiki/<Marque>`) : création, fondateur·rice,
     modèle éco (DTC / digital-first / boutiques), extensions de gamme, présence internationale, chiffres clés.
    - **Le site de marque lui-même** (pages `/à-propos`, `/engagements`, `/mission`) est souvent en **403
      avec les outils web simples** (même anti-bot que le crawl). N'insiste pas : Google News + Wikipédia suffisent.
   - **Contrat données réelles** : ne cite que ce que les sources disent ; date les faits ; si une source
     manque (marque confidentielle, pas de page Wikipédia), dis-le et déduis prudemment du secteur — n'invente
     pas de chiffre ni de levée de fonds. Voir la règle « données réelles » de la mémoire projet.
   - **Restitue une « lecture stratégique » en 3-5 puces** (mission, modèle, tension clé — ex. web↔boutique —,
     cible, cap récent) : c'est ce qui va orienter le persona, les actes et le mapping de valeur Salesforce en Phase 2.
4. Restitue une **ambiance proposée** en markdown, courte, à partir de `brand.json` :
   - couleur d'accent (hex, `proposed_tokens.--accent`) + 1 phrase de justification,
   - typo : mappe la `title_font` détectée sur la Google Font la plus proche (une police
     propriétaire type « AudiType » n'est pas sur Google Fonts → prends l'équivalent : ici Inter),
   - 1 phrase de positionnement, appuyée sur le secteur/produits vus dans les images **et sur la lecture stratégique**.
5. Montre aussi une **planche d'usage des assets** : pour chaque logo/photo retenu,
   indique l'écran pressenti et le cadrage (hero, carré, portrait, fond). Signale les
   visuels manquants ou mal adaptés plutôt que de forcer une image médiocre.
6. Reformule les éventuelles réponses au brief en une fiche courte. Quand le brief est
   absent, écris explicitement 2-4 hypothèses de travail faciles à corriger.
7. Demande validation / ajustement (couleur, assets, angle stratégique et hypothèses)
   avant de continuer.

## Phase 2 — Story (validée en chat, pas de formulaire web)

Propose en markdown une **story de parcours client**, inspirée des actes agnès b.
Adapte le nombre d'actes au secteur (retail, banque, télécom, auto…). **Ancre la story sur la
lecture stratégique de la Phase 1** (et, s'il y en a un, sur le **brief du cahier des charges** :
chaque besoin listé doit correspondre à au moins un acte). Que le persona, les moments et surtout
le mapping de valeur Salesforce répondent à la tension clé de la marque (ex. digital-first qui ouvre
des boutiques → unification web↔magasin par Data Cloud ; positionnement premium/prix juste →
fidélité plutôt que promo ; expansion internationale → activation multi-marché). Structure :

- **Thèse de démo** : une phrase causale qui résume toute l'histoire (« Parce que X,
  le client fait Y ; Salesforce détecte Z, déclenche A et produit B. »).
- **Persona** : prénom, profil en 1 ligne (âge, contexte, ce qu'il cherche). Vise un
  protagoniste principal ; deux maximum sauf si la démo comporte des chapitres explicites.
- **N actes** (vise 5–7, ou 3–4 pour une démo express), chacun :
  - `acte` (libellé, ex. « Acte 1 · Réengagement »),
  - `titre` court de l'écran,
  - `canal` ∈ instagram · whatsapp · email · site · console · app · dashboard · **lightning-sales / lightning-record / lightning-dashboard / lightning-fieldservice / lightning-marketing** (écrans Salesforce riches) · **financial-loan-portal / financial-loan-processor / financial-loan-underwriter** (Digital Lending) · **consumer-commerce-home / consumer-commerce-order / consumer-service-performance / consumer-service-account / consumer-service-case / consumer-service-asset / consumer-sales-trade-plan / consumer-sales-agreement / consumer-sales-forecast** (Consumer Goods),
  - `moment` (1 phrase : ce qui se passe),
  - `trigger` (ce qui déclenche l'acte),
  - `valeur` Salesforce (le produit mis en avant : Data Cloud, Marketing Cloud,
    Agentforce, Service Cloud, MuleSoft, Commerce…),
  - `result` (le résultat visible pour le client ou l'employé),
  - `transition` (la phrase qui rend l'acte suivant inévitable).

**Sélection des assets — deux axes indépendants.** Consulte `registry/screens.json` : choisis
d'abord le `job` qui sert l'acte, puis vérifie `products`. Utilise par défaut les écrans
`cross_industry: true`. Ne filtre sur `industries` que si le workflow ou l'interaction est
réellement sectoriel. Un simple changement de données ou de vocabulaire reste dans le manifest ;
il ne justifie ni un nouveau composant ni un nouvel écran. Voir `references/registry.md`.

Avant de soumettre la story, dresse la liste des `products` réellement utilisés par les écrans et
affiche un avertissement licence. Pour `financial-services-cloud`, `consumer-goods-cloud` et
`manufacturing-cloud`, écris explicitement « licence sectorielle distincte de Sales Cloud ».
Le manifest doit contenir :
`"license_selection":{"mode":"industry-cloud","label":"Expérience Manufacturing Cloud","confirmed":true}`
(adapte le label au choix utilisateur). Le hub affiche discrètement les produits utilisés ; les notes
présentateur conservent le détail des licences et le build avertit si un produit sectoriel n'a pas été confirmé.

Si l'histoire change de persona, de marché (B2C → B2B) ou de temporalité, crée des
**chapitres nommés**. Ne masque jamais une seconde histoire derrière un simple « bascule
côté… ». Chaque chapitre doit avoir un enjeu et une sortie clairs.

Avant de demander la validation, passe la story dans cette revue :
- chaque écran fait progresser l'enjeu central ;
- chaque acte produit un résultat observable ;
- chaque transition prépare réellement l'acte suivant ;
- aucun écran n'existe seulement pour cocher un produit Salesforce ;
- les noms, dates, montants, photos et statuts restent cohérents d'un écran à l'autre ;
- les faits vérifiés, hypothèses et données fictives de démonstration sont distingués.

**B2C ou B2B — adapte la grammaire de la story.** Le brief (ou le secteur) dit si la démo vise le
grand public (B2C) ou l'entreprise (B2B). Ce n'est pas qu'un ton, ça change la structure :
- **B2C (défaut, cas actuel)** : persona = un individu ; parcours acquisition → boutique/e-commerce
  → SAV → fidélité ; canaux Instagram/WhatsApp/email/site/app ; produits Marketing/Data Cloud, Service, Commerce.
- **B2B** : le « client » est un **compte** (une entreprise), pas une personne seule. Le persona
  devient un **duo/trio** — le **commercial Salesforce** (héros côté vendeur) + le **contact/comité
  d'achat** côté client (ex. Directeur Achats + utilisateur métier). Parcours type : **lead/signal →
  qualification → opportunité (pipeline) → prévision → devis (CPQ/Revenue) → signature → onboarding →
  expansion/renouvellement**. Canaux : LinkedIn/email de prospection, **console commerciale**,
  **pipeline & prévision** (`lightning-dashboard` / `lightning-sales`), **devis**, portail partenaire.
  Produits mis en avant : **Sales Cloud** (pipeline, prévision), **Revenue/CPQ** (devis), Agentforce
  (SDR/assistant vente), Data Cloud (scoring/intent). ⚠ **Vérifie dans `references/screens.md` (§ B2B)
  quels écrans B2B existent réellement.** Si le parcours B2B demande un écran non couvert (prévision,
  devis, portail partenaire…), **signale-le** et prends le template le plus proche — n'improvise pas
  un écran Salesforce de zéro (règle d'or). On créera le template manquant à partir de ton besoin.

Présente ça en **tableau ou liste numérotée**. Dis explicitement : « édite librement
(retire, ajoute, réordonne, change un canal) — on génère quand c'est bon ». **Attends
la validation.** N'écris aucun fichier avant.

## Phase 3 — Génération du site

Quand la story est validée, **tu n'écris pas de HTML.** Tu produis un seul
`manifest.json`, puis tu lances le script qui assemble le site. C'est ce qui rend
la skill rapide : recopier des templates de 130–190 lignes pour changer 4–9 zones
est du travail mécanique — le script le fait en une seconde, toi jamais.

### 1bis. Re-crawl ciblé des visuels (si le 1er crawl a réussi)
Maintenant que la story est **validée**, tu sais exactement quels produits apparaissent (fiche
e-commerce, pub Instagram, carte WhatsApp…). C'est le moment de récupérer leurs **vraies photos** —
plus précis que les visuels « à l'aveugle » de la Phase 1. **Uniquement si `brand.json.status == "ok"`**
(sinon reste sur le Plan B `--fetch` / assets fournis).
1. Ouvre `brand.json.product_links` (le catalogue de liens **réels** relevés en Phase 1). **Matche**
   chaque produit de la story à un lien via son `label` (ex. story « manteau Will » → `label` contenant
   « Will »). Ne prends QUE des `href` présents dans le catalogue — **ne devine, ne construis, ni ne
   complète aucune URL** (une URL inventée = 404 = image cassée ; contrat « données réelles »).
2. Re-crawle ces pages produit — leur visuel exact atterrit en `product-N.*` :
   ```bash
   python3 scripts/crawl_brand.py --pages <href1> <href2>… --slug <slug>
   ```
   (`--pages` visite des **pages** et en extrait l'og:image ; `--fetch` reste pour des **URL d'images
   directes**. Les deux écrivent `product-N.*` dans `<slug>-brand/`.)
3. `Read` les `product-N.*` obtenus pour vérifier que ce sont les bons produits, puis réfère-les par
   **basename** dans la clé `assets` du manifest (comme au Plan B). Si un produit de la story n'a AUCUN
   lien correspondant dans le catalogue, ne force pas : garde le dégradé d'accent pour cet écran, ou
   demande l'URL/le fichier à l'utilisateur. Un visuel générique vaut mieux qu'une URL inventée.

### 1. Écris `manifest.json`
Ton livrable créatif = la narration, les données et le cadrage répartis dans le manifest.
Structure :

```json
{
  "brand": "Nova",
  "slug": "nova",
  "story_title": "De la découverte à la fidélité",
  "tagline": "Le parcours de Camille, écran après écran. Descendez pour le suivre.",
  "brief": {
    "audience": "Direction marketing et service client",
    "objective": "Montrer la continuité acquisition → service",
    "duration_minutes": 8,
    "business_tension": "Les signaux web et service restent fragmentés",
    "salesforce_focus": ["Data Cloud", "Agentforce"]
  },
  "thesis": "Parce que ses signaux sont réconciliés, Camille reçoit une réponse cohérente du premier clic au SAV.",
  "tokens": { "--accent": "#1c2b4a", "--accent-dark": "#12203b", "--accent-soft": "#eaf0f8" },
  "font_import": "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');",
  "intro": {
    "kicker": "L'histoire",
    "title": "Une cliente, une conseillère, un parcours unifié",
    "lede": "De la publicité au conseil en boutique, chaque étape est reliée par Salesforce Data Cloud.",
    "cast": [
      { "name": "Camille", "role": "La cliente", "bio": "Repère un manteau, hésite, revient.", "image": "camille.jpg" },
      { "name": "Léa", "role": "La conseillère", "bio": "Accueille Camille avec une vue 360°." }
    ]
  },
  "screens": [
    {
      "file": "acte1-instagram.html", "template": "instagram", "channel": "Instagram",
      "chapter": "Acquérir et comprendre",
      "act": "Acte 1 · Acquisition", "title": "Publicité ciblée",
      "desc": "Récit affiché à côté de l'écran dans la story (2–3 phrases).", "animated": true,
      "trigger": "Camille montre un intérêt pour la catégorie.",
      "result": "Le clic est rattaché à une audience connue.",
      "transition": "Il faut maintenant transformer cet intérêt en demande qualifiée.",
      "presenter": {
        "duration_seconds": 40,
        "message": "L'acquisition est déjà reliée au profil client.",
        "show": "L'audience Data Cloud et la source du clic.",
        "question": "Comment mesurez-vous aujourd'hui la continuité entre média et CRM ?"
      },
      "display": { "mode": "phone" },
      "slots": {
        "title": "Nova — Publicité ciblée",
        "act-tag": "Acte 1 · Instagram — publicité ciblée (Data Cloud → Meta)",
        "post": "…", "why": "…"
      }
    }
  ]
}
```

Règles pour le manifest :
- **`template`** = le nom du canal (table canal → template dans `references/screens.md`).
  `registry/screens.json` est la source machine-readable pour la disponibilité et le classement.
  Si aucun ne colle, prends le plus proche et signale-le — n'invente pas d'écran.
- **`slots`** = un nom de SLOT valide → son contenu HTML. Les noms valides de chaque
  template sont listés dans `references/screens.md`. Un SLOT que tu omets garde le
  contenu d'exemple du template (pratique pour la chrome fixe).
- **SLOT de texte** (`title`, `act-tag`, `intro`…) : juste la chaîne.
- **SLOT structuré** (`stories`, `thread`, `flow`, `cards`, `history`…) : reprends le
  **bloc d'exemple du template** (lis-le dans `templates/<canal>.html`) et n'ajuste que
  le texte / le nombre de sous-blocs. Ne fabrique pas de nouvelle structure ni de
  nouvelles classes — la chrome est verrouillée.
- **Écrans composables `<lc-*>`** (`lightning-record`, `lightning-dashboard`, `lightning-fieldservice`,
  `lightning-marketing`, les écrans `fieldservice-mobile-*`, `financial-loan-portal`, `financial-loan-processor`,
     `financial-loan-underwriter`, les écrans `consumer-*` et `manufacturing-*`) :
  leurs SLOTs enveloppent un composant `<lc-*>` + un `<script type="application/json">`. Reprends le bloc
  d'exemple et **n'ajuste que le JSON** (valeurs), jamais la balise ni les clés attendues. Le marqueur SLOT
  est **autour** du `<script>` (un commentaire dedans casserait `JSON.parse`) — c'est déjà le cas, n'y touche pas.
  Ces écrans couvrent les cas Salesforce riches (CRM 360, dashboards, Field Service, Marketing Cloud).
  `lightning-marketing` empile 6 surfaces **retirables** (vide un SLOT pour masquer sa surface) : un acte MC
  montre en général UNE surface (Parcours OU Email OU Segment…). Voir `references/screens.md`. `build_site.py` embarque
  automatiquement le kit (JS+CSS) dans le site, chargé en `file://`. Voir `references/screens.md` § « Kit de composants ».
- **Garde toujours l'encart `.why`** (ou le panneau produit : Einstein, Agentforce,
  beacon Data Cloud…) : c'est la valeur Salesforce, signature de la démo.
- **`tokens`** : accent de marque (Phase 1). `font_import` seulement si tu changes de typo.
- **`desc`** = le **récit** affiché à côté de l'écran dans la story (2–3 phrases, incarnées par le
  persona) — c'est ce que le visiteur lit en scrollant, pas un simple résumé technique.
- **`thesis`** = la promesse causale de la démo. Elle apparaît dans les notes présentateur
  et sert de test de cohérence ; ne la remplace pas par une liste de produits.
- **`brief`** = facultatif. Reprends uniquement les informations fournies ou les hypothèses
  validées. Son absence n'empêche jamais le build.
- **`chapter`** = facultatif. Quand sa valeur change, le hub insère un séparateur narratif.
  Utilise-le pour les changements de persona, de marché ou de temporalité.
- **`persona`** = nom exact d'un personnage de `intro.cast[]`, sur un écran Salesforce. Le builder
  prend son `image` et alimente automatiquement le SLOT `sf-avatar`, afin que l'utilisateur connecté
  change avec l'acte. Un `sf-avatar` explicite dans `slots` reste prioritaire.
- **`license_selection`** = choix produit/licence confirmé avec l'utilisateur. `mode` vaut en général
  `core-clouds` ou `industry-cloud`, `label` décrit la configuration retenue et `confirmed` bloque
  l'absence silencieuse d'avertissement. Les produits réellement utilisés sont déduits des templates.
- **`trigger` / `result` / `transition`** = contrat causal de l'acte. Ils alimentent les
  notes présentateur ; `transition` peut aussi apparaître discrètement dans le récit du hub.
- **`presenter`** = notes facultatives de l'acte : `duration_seconds`, `message`, `show`,
  `question`. Le builder génère `presenter-notes.md` même si certaines valeurs manquent.
- **`display`** = cadrage facultatif dans le hub :
  - `{"mode":"phone"}` pour la coque mobile (déduit automatiquement du template),
  - `{"mode":"full","scale":0.53}` pour agrandir/réduire un écran desktop,
  - `{"mode":"crop","scale":0.65,"x":120,"y":60,"height":560}` pour cadrer la zone
    importante. `x`/`y` sont des pixels source retirés avant mise à l'échelle.
- **`url`** (écrans desktop) : ce qui s'affiche dans la barre d'adresse du cadre navigateur
  (ex. `sezane.com/le-manteau-will`, ou un libellé d'app `Data Cloud · Profil unifié`). Optionnel.
- **`tagline`** : sous-titre du hero (1 phrase d'accroche sous le titre). Optionnel.
- **`intro`** : l'écran de mise en situation entre le hero et le 1ᵉʳ acte. `title` + `lede`, et
  `cast[]` = les personnages (`name`, `role`, `bio`, `image` optionnelle). La **frise du parcours**
  (une étape par écran, titres repris des `screens`) est générée automatiquement — ne la liste pas.
  - `image` = un portrait de la **banque livrée avec la skill** (`assets/people/` : `femme-1..3`,
    `homme-1..2`, `agent-1..2`) → réfère-le par `people/<nom>.jpg`. Ou un fichier de `assets`
    (portrait fourni/crawlé), par basename. Sans `image`, l'initiale du prénom s'affiche dans une
    pastille. **Un agent Agentforce n'est pas un humain** : utilise `people/agent-*.jpg`, pas un
    portrait. Ne fabrique jamais un faux visage ni une fausse identité (contrat « données réelles »).
  - **Cohérence des visages — 1 personnage = 1 photo, réutilisée PARTOUT.** La photo choisie pour
    un personnage dans `cast[]` doit être la MÊME dans chaque écran où il apparaît (avatar de fiche
    `.avatar`/`.av`, carte conseiller `.pf`, et l'avatar du header SF `sf-avatar` si ce personnage
    est l'utilisateur connecté). Le build glisse une `<img src="people/…">` dans n'importe quel
    avatar rond (`.avatar`/`.av`/`.pf`/`.ln-avatar`) et la recadre. Deux personnages = deux photos ;
    jamais un visage qui n'est présenté nulle part dans l'histoire.
  - Le script ne copie dans le site QUE les portraits `people/` réellement référencés (aucun poids mort).
- **`animated: true`** : marque un écran animé (métadonnée ; plus de badge sur l'index scrollytelling).
- **`assets`** (Plan B, crawl échoué) : liste de chemins de fichiers fournis par l'utilisateur
  (logo + photos produit). Le script les copie dans `<slug>-story/` ; réfère-les par **basename** :
  - logo dans un slot `nav`/`brand` → `<img class="brand-logo" src="logo.png" alt="Marque">`
    (remplace le `<span class="brand">…` ; sur fond sombre, ajoute `style="filter:brightness(0) invert(1)"`).
  - photo produit dans une zone visuelle (`.post-img`, `.shot`, `.prod .img`, `.item .th`…) →
    mets-la en fond inline : `style="background-image:url('manteau.jpg');background-size:cover;background-position:center"`
    sur l'élément d'exemple (garde sa classe). Une photo = un écran produit.

### 2. Lance le script
```bash
python3 scripts/build_site.py manifest.json
```
Il copie chaque template dans `./<slug>-story/`, injecte les SLOTs entre les marqueurs,
réécrit les tokens `:root` de `shared.css`, et génère `index.html` : la **page story** en
scrollytelling (hero → intro personnages/frise → une section par acte avec l'écran en iframe).
Les écrans « téléphone » (instagram, whatsapp, landing-capture, client-app, fieldservice-mobile-*) sont affichés dans une
coque mobile ; les autres dans un cadre navigateur. Un clic sur un écran l'ouvre en plein écran.
Un SLOT mal orthographié → **erreur explicite** : corrige le nom dans le manifest
(noms valides dans `references/screens.md`) et relance. **Ne recopie jamais un template
toi-même**, même en cas d'erreur.

### 3. Restitue
Avant la restitution, lance la revue visuelle :
```bash
python3 scripts/review_site.py ./<slug>-story
```
Elle capture le hub et chaque écran dans `./<slug>-story/review/`, produit une planche
contact `contact-sheet.html` et un rapport `review-report.json` (console, erreurs de page,
assets cassés, débordements horizontaux). Lis le rapport et ouvre la planche contact.
Corrige le manifest puis rebuild au moins une fois si un défaut visible ou une erreur est
signalé. Ne présente pas un build que tu n'as pas regardé.

Le script imprime la liste des fichiers. Invite ensuite l'utilisateur à ouvrir
`./<slug>-story/index.html`. Mentionne aussi `presenter-notes.md` et la planche contact.

### Règles de qualité (ne pas simplifier)
- Une page = un écran autonome, ouvrable seul.
- **Toujours partir d'un `templates/*.html` ; ne réinvente jamais la chrome.** Si aucun
  template ne colle au canal voulu, prends le plus proche et signale-le — n'improvise pas
  un écran de zéro (c'est là que naissent les hallucinations).
- Chrome crédible : vrais éléments d'UI (barres, onglets, bulles, timelines) en HTML/SVG,
  pas de capture d'écran ni d'image externe. Les visuels produits = dégradés d'accent —
  **sauf** logo + photos fournis par l'utilisateur au Plan B (crawl échoué), embarqués
  localement via `assets` (jamais d'URL externe : uniquement des fichiers copiés à côté du site).
- Accessibilité de base : `lang`, `alt`, contrastes lisibles.
- « Gif animé » = CSS `@keyframes`, jamais de fichier GIF.
- Chaque écran garde son encart pédagogique `.why` (c'est la signature de la démo).

## Vérification
Vérifie le rendu, pas seulement les fichiers :
- le hero porte la marque et exprime la thèse de démo ;
- l'intro présente les personnages et la frise ;
- les chapitres rendent les changements de fil narratif explicites ;
- chaque acte montre un écran lisible, un résultat métier et une transition ;
- le chrome est crédible, les assets sont bien cadrés et aucun contenu « Nova » ne fuit ;
- aucun texte essentiel n'est coupé dans la planche contact ;
- `review-report.json` ne contient aucune erreur de page, console ou asset ;
- `presenter-notes.md` permet de pitcher la démo sans réinventer les transitions ;
- au moins une animation tourne et chaque écran conserve son encart `.why` ou panneau produit.

Un clic sur un écran l'ouvre en plein écran. Le défilement « accroché » et les apparitions
au scroll ne s'affichent qu'en Chrome/Edge ; ailleurs tout reste visible, sans animation.
