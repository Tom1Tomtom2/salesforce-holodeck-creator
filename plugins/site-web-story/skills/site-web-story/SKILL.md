---
name: site-web-story
description: |
  Construit un site web de démo narratif — un parcours client de marque en
  plusieurs "actes" — 100% écrit à la main par Claude en HTML/CSS artisanal
  (chrome Instagram/WhatsApp/console/email dessinée en markup, animations CSS).
  Mode conversationnel en 3 phases : marque + URL → ambiance + story validée en
  chat → génération d'un dossier de site statique navigable (hub + une page par
  écran). Zéro image générée, zéro serveur, zéro clé API. Si le crawl est bloqué,
  demande à l'utilisateur le logo + N photos produit et embarque-les dans le site.

  TRIGGER quand : l'utilisateur veut un site de démo qui raconte un parcours
  client (acquisition → boutique → SAV…), une "story de marque" cliquable,
  "comme la démo agnès b.", des maquettes d'écrans navigables pour un pitch.

  DO NOT TRIGGER quand : holodeck à images Gemini reskinnées (c'est app.py) ;
  vraie application Salesforce (LWC, Experience Cloud) ; site marchand réel en
  production ; simple diagramme ou slide unique.
version: "1.1.0"
---

# Site Web Story

Skill conversationnelle. **Tu es l'orchestrateur.** Le livrable est un dossier de
site statique où chaque écran est du HTML/CSS que **tu écris à la main** — pas
d'images générées, pas de serveur. Suis les 3 phases dans l'ordre. N'avance pas à
la phase suivante sans validation de l'utilisateur.

Cette skill est le pendant "artisanal" du holodeck `app.py` (qui, lui, reskine des
captures via Gemini). Ici tout est dessiné en markup, comme la démo agnès b.

## Assets de la skill (chemins relatifs à ce dossier)
- `assets/shared.css` — design tokens + composants (`.chip` `.btn` `.phone` `.act-tag`
  `.why` `.accent-band` `.brand` `.brand-mark`). **Base de tout écran.**
- `assets/index.template.html` — squelette du hub/sommaire.
- `templates/*.html` — **bibliothèque d'écrans complets, chrome verrouillée + SLOTs.**
  C'est le cœur : tu pars TOUJOURS d'un template, tu ne redessines jamais un écran.
- `references/screens.md` — table canal → template + liste des SLOTs de chaque template.
- `scripts/build_site.py` — assemble le site depuis un manifest JSON (copie les
  templates, injecte les SLOTs, réécrit les tokens, génère le hub). **C'est lui qui
  écrit le HTML, pas toi.**
- `scripts/crawl_brand.py` — crawle le site de la marque avec un **vrai navigateur**
  (Chromium/Chrome headless furtif) et pré-remplit la Phase 1 : logo, images produit
  HD, palette, typo, secteur. **À lancer avant de proposer l'ambiance.** WebFetch/curl
  échouent sur les sites de marque (anti-bot CDN → 503) ; ce script exécute le JS et passe.

---

## Phase 1 — Intro : marque + ambiance

1. Demande **le nom de la marque** et **l'URL du site** (si pas déjà donnés).
2. **Crawle le site** (n'utilise PAS WebFetch : les sites de marque renvoient 503 à un
   client sans JS) :
   ```bash
   python3 scripts/crawl_brand.py <url> --brand "<Marque>" --slug <slug>
   ```
   Il écrit `./<slug>-brand/` : `brand.json` (accent proposé, typo, secteur, CTA détectés),
   `logo.*`, et `product-N.*` (visuels produit HD). **Lis `brand.json`** pour l'ambiance.
   Regarde les `product-N.*` (`Read`) pour repérer les modèles/produits réels.
   - **Vérifie `brand.json.status`** : si `"failed"`, le crawl a été bloqué (anti-bot) ou n'a
     rien récupéré — le champ `error` dit quoi. Ne te sers PAS des valeurs par défaut.
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
   - Si l'utilisateur ne peut/veut pas fournir d'images : **déduis l'ambiance du nom + secteur**
     (et signale-le) — le site reste en dégradés d'accent (contrat « zéro image »).
   - Première utilisation : `pip install -r requirements.txt && playwright install chromium`
     (Chrome système utilisé en priorité s'il est là).
3. Restitue une **ambiance proposée** en markdown, courte, à partir de `brand.json` :
   - couleur d'accent (hex, `proposed_tokens.--accent`) + 1 phrase de justification,
   - typo : mappe la `title_font` détectée sur la Google Font la plus proche (une police
     propriétaire type « AudiType » n'est pas sur Google Fonts → prends l'équivalent : ici Inter),
   - 1 phrase de positionnement, appuyée sur le secteur/produits vus dans les images.
4. Demande validation / ajustement de la couleur avant de continuer.

## Phase 2 — Story (validée en chat, pas de formulaire web)

Propose en markdown une **story de parcours client**, inspirée des actes agnès b.
Adapte le nombre d'actes au secteur (retail, banque, télécom, auto…). Structure :

- **Persona** : prénom, profil en 1 ligne (âge, contexte, ce qu'il cherche).
- **N actes** (vise 5–8), chacun :
  - `acte` (libellé, ex. « Acte 1 · Réengagement »),
  - `titre` court de l'écran,
  - `canal` ∈ instagram · whatsapp · email · site · console · app · dashboard,
  - `moment` (1 phrase : ce qui se passe),
  - `valeur` Salesforce (le produit mis en avant : Data Cloud, Marketing Cloud,
    Agentforce, Service Cloud, MuleSoft, Commerce…).

Présente ça en **tableau ou liste numérotée**. Dis explicitement : « édite librement
(retire, ajoute, réordonne, change un canal) — on génère quand c'est bon ». **Attends
la validation.** N'écris aucun fichier avant.

## Phase 3 — Génération du site

Quand la story est validée, **tu n'écris pas de HTML.** Tu produis un seul
`manifest.json`, puis tu lances le script qui assemble le site. C'est ce qui rend
la skill rapide : recopier des templates de 130–190 lignes pour changer 4–9 zones
est du travail mécanique — le script le fait en une seconde, toi jamais.

### 1. Écris `manifest.json`
Ton seul livrable créatif = les **textes de la story** répartis dans les SLOTs.
Structure :

```json
{
  "brand": "Nova",
  "slug": "nova",
  "story_title": "De la découverte à la fidélité",
  "tokens": { "--accent": "#1c2b4a", "--accent-dark": "#12203b", "--accent-soft": "#eaf0f8" },
  "font_import": "@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');",
  "screens": [
    {
      "file": "acte1-instagram.html", "template": "instagram", "channel": "Instagram",
      "act": "Acte 1 · Acquisition", "title": "Publicité ciblée",
      "desc": "Résumé court affiché sur la carte du hub.", "animated": true,
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
  Si aucun ne colle, prends le plus proche et signale-le — n'invente pas d'écran.
- **`slots`** = un nom de SLOT valide → son contenu HTML. Les noms valides de chaque
  template sont listés dans `references/screens.md`. Un SLOT que tu omets garde le
  contenu d'exemple du template (pratique pour la chrome fixe).
- **SLOT de texte** (`title`, `act-tag`, `intro`…) : juste la chaîne.
- **SLOT structuré** (`stories`, `thread`, `flow`, `cards`, `history`…) : reprends le
  **bloc d'exemple du template** (lis-le dans `templates/<canal>.html`) et n'ajuste que
  le texte / le nombre de sous-blocs. Ne fabrique pas de nouvelle structure ni de
  nouvelles classes — la chrome est verrouillée.
- **Garde toujours l'encart `.why`** (ou le panneau produit : Einstein, Agentforce,
  beacon Data Cloud…) : c'est la valeur Salesforce, signature de la démo.
- **`tokens`** : accent de marque (Phase 1). `font_import` seulement si tu changes de typo.
- **`animated: true`** sur les écrans à animation CSS → badge `▶ animé` sur le hub.
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
réécrit les tokens `:root` de `shared.css`, et génère `index.html` (hub groupé par acte).
Un SLOT mal orthographié → **erreur explicite** : corrige le nom dans le manifest
(noms valides dans `references/screens.md`) et relance. **Ne recopie jamais un template
toi-même**, même en cas d'erreur.

### 3. Restitue
Le script imprime la liste des fichiers. Invite l'utilisateur à ouvrir
`./<slug>-story/index.html` (ou propose `preview_start` si dispo).

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
Ouvre `index.html` : le hub liste les actes, chaque carte ouvre son écran, le chrome est
crédible et à la marque, au moins une animation tourne, chaque écran a son encart `.why`.
