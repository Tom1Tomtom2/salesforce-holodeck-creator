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
| App conseiller / clienteling (vue 360) | `client-app.html` | mobile | Data Cloud — historique réconcilié | — (statique) |
| Console SAV siège | `service-console.html` | desktop | Agentforce + MuleSoft (panneau) | tracker `.st.now` qui pulse |
| Caisse / TPV boutique (retour, vente) | `tpv-pos.html` | desktop | MuleSoft → Data Cloud & Salesforce | dot de sync qui pulse |

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
- **datacloud-profil.html** — `title`, `act-tag`, `sf-logo`, `sf-app`, `sf-tabs`, `brand`, `identity`, `stream`, `segments`
  (garde `.live-2`/`.live-1` en tête du flux, une seule pastille `.seg.on`)
- **datacloud-pipeline.html** — `title`, `act-tag`, `sf-logo`, `sf-app`, `sf-tabs`, `brand`, `prod-label`, `status-chip`, `intro`, `flow`, `cards`, `status`
  (garde le 3e nœud en `.node.dest`)
- **client-app.html** — `title`, `act-tag`, `brand`, `advisor`, `client-hero`, `appointment` (retirable), `history`, `cta`
- **service-console.html** — `title`, `act-tag`, `sf-logo`, `sf-app`, `sf-tabs`, `tabbar`, `contact`, `case`, `agent`

### Header Salesforce Lightning (3 écrans desktop : datacloud-profil, datacloud-pipeline, service-console)
Ces 3 écrans portent en haut le **header Lightning** (défini dans `shared.css` : `.lightning`).
Il reste **aux couleurs Salesforce** (fond blanc, bleu `#0176d3`) — NE le repeins PAS à `--accent`,
c'est ce qui fait reconnaître Salesforce. Seuls 3 SLOTs se remplissent :
- `sf-logo` — **le logo du CLIENT** (remplace le cloud Salesforce) : wordmark `.brand` ou `<img class="brand-logo" src="logo.png" alt="Marque">`.
- `sf-app` — le nom de l'app (ex. « Sales », « Service - Console », « Data Cloud »).
- `sf-tabs` — les onglets ; le 1er en `.ln-tab.on` = actif (souligné bleu). `<svg class="caret">` pour un menu déroulant.
La recherche, le bouton « Ask » et le cluster d'icônes (droite) sont **verrouillés** — n'y touche pas.
- **tpv-pos.html** — `title`, `act-tag`, `pos-name`, `store`, `scan`, `refund` (garde `.sync`)

## Neutralisation déjà faite

Les templates sont **génériques** : marque « Nova », couleurs pilotées par `--accent`
(réécrit en Phase 3 depuis `:root` de `shared.css`), visuels produit = dégradés d'accent
(aucune image externe). Tu n'as qu'à remplir les SLOTs à la marque de la story.
