# Étendre la bibliothèque

Ce guide explique comment ajouter des capacités sans casser le contrat de la skill. Le principe
directeur est de choisir l'extension la plus petite : données, puis écran, puis composant.

## Choisir le bon niveau

| Besoin | Action |
|---|---|
| Même interface, nouveaux noms, montants, statuts ou étapes | Modifier uniquement le JSON du manifest |
| Même primitive UI, nouvelle combinaison ou nouveau canal | Créer un template d'écran |
| Interaction ou structure absente du kit | Créer un composant `<lc-*>` |
| Variante propre à une industrie mais structure identique | Garder l'asset transverse et adapter les données |
| Workflow ou objets réellement propres à une industrie | Déclarer un asset sectoriel |

Avant d'ajouter quoi que ce soit, cherche dans :

1. `registry/screens.json` pour un écran existant ;
2. `registry/components.json` pour un composant existant mais non exposé ;
3. `templates/*.html` et `assets/lightning-kit/*-components.js` pour confirmer le contrat réel.

Avant de coder, lis aussi `component-charter.md` et `registry/taxonomy.json`. Toute contribution doit
annoncer son `job`, ses `products`, sa surface (`lightning`, `mobile`, `external`, `channel`) et son
scope (`cross-industry` ou `industry`). Le validateur bloque les jobs libres, les incohérences
job/produit et plusieurs écarts objectifs à la charte.

## Ajouter un composant `<lc-*>`

Pour initialiser tous les fichiers et la classification sans recopier ce guide, lance d'abord :

```bash
python3 scripts/create_component.py
```

Le mode interactif propose les valeurs contrôlées. Le mode non interactif accepte `--id`, `--label`,
`--job`, `--products`, `--surface`, `--scope` et `--industries`. `--dry-run` n'écrit rien. Le script
annule ses écritures si le registre final ne passe pas la validation. Les étapes suivantes restent
nécessaires pour transformer le squelette en composant métier et l'exposer dans un écran.

### 1. Choisir sa source

- Ajoute le composant à un fichier métier existant, par exemple
  `assets/lightning-kit/field-service-components.js`, s'il appartient clairement à ce domaine.
- Crée `assets/lightning-kit/<domaine>-components.js` si le domaine est nouveau. Le builder découvre
  automatiquement tous les fichiers `*.js` du kit.
- `lightning-components.js` reste le fichier de base : il définit `JsonComponent`, `escapeHtml` et `lcIcon`.

### 2. Respecter le contrat JSON-driven

Un composant étend `JsonComponent`, lit `this.data` et produit son rendu dans `render()` :

```js
class LcExampleSummary extends JsonComponent {
  render() {
    const data = this.data;
    const rows = (data.items || []).map(item => `
      <li><strong>${escapeHtml(item.label)}</strong></li>`).join('');

    this.innerHTML = `
      <section class="lc-panel" aria-labelledby="${this.id || 'example'}-title">
        <h2 id="${this.id || 'example'}-title">${escapeHtml(data.title || 'Summary')}</h2>
        <ul>${rows}</ul>
      </section>`;
  }
}
```

Règles :

- échappe toute donnée avec `escapeHtml` ;
- utilise des éléments natifs (`button`, `input`, `table`, `ol`) avant ARIA ;
- donne un nom accessible à chaque contrôle icon-only ;
- conserve des cibles tactiles d'au moins 44 × 44 px sur mobile ;
- n'utilise pas uniquement la couleur pour exprimer un statut ;
- expose les états interactifs (`aria-pressed`, `aria-selected`, `aria-expanded`) et synchronise-les ;
- envoie les interactions avec `this.emitAction('nom-action', detail)` ;
- ne charge aucun asset réseau : le build doit fonctionner en `file://`.

### 3. Enregistrer le custom element

Ajoute la classe à la map de définitions du fichier :

```js
const newDefinitions = {
  'lc-example-summary': LcExampleSummary,
};
```

Le nom doit commencer par `lc-`, être unique et correspondre exactement à la balise utilisée dans les templates.

### 4. Ajouter les styles

Ajoute la balise à la liste `display: block` en tête de
`assets/lightning-kit/lightning-components.css`, puis ajoute les classes CSS nécessaires.

- Réutilise les tokens `--lc-*` et les primitives `.lc-panel`, `.lc-button`, `.lc-badge`.
- Pour une identité produit verrouillée, utilise des variables locales au composant plutôt que
  `--accent`, qui représente la marque cliente.
- Ajoute un état `:focus-visible` quand le focus natif est remplacé.
- Respecte `prefers-reduced-motion` pour toute animation.

### 5. Cataloguer le composant

Ajoute une entrée à `registry/components.json` :

```json
{
  "id": "lc-example-summary",
  "source": "assets/lightning-kit/example-components.js",
  "label": "Example summary",
  "job": "assistance",
  "products": ["agentforce"],
  "status": "uncatalogued-screen"
}
```

Utilise `uncatalogued-screen` tant qu'aucun template ne contient la balise. Dès qu'un écran l'expose,
le statut attendu devient `available`. `validate_registry.py` vérifie cette règle automatiquement.

`job` doit exister dans `registry/taxonomy.json` et être couvert par au moins un produit de
`products`. Ajoute une nouvelle valeur de taxonomie seulement quand aucune intention existante ne
convient ; documente alors la décision dans la PR.

Pour un composant sectoriel, ajoute aussi :

```json
"cross_industry": false,
"industries": ["manufacturing"]
```

## Créer un écran à partir de composants existants

### 1. Copier la chrome la plus proche

Pars d'un template existant du même format :

- mobile : un `fieldservice-mobile-*`, `client-app`, `instagram` ou `whatsapp` ;
- Lightning desktop : un `lightning-*` ou un écran sectoriel proche ;
- site externe : un portail ou un template commerce proche.

Ne copie pas un dossier généré `*-story/`. Copie uniquement un fichier de `templates/`.

### 2. Définir les SLOTs

Chaque zone modifiable est entourée de commentaires :

```html
<!-- SLOT: summary ─ ajuste uniquement le JSON. -->
<lc-example-summary>
  <script type="application/json">
  {"title":"Résumé","items":[{"label":"Valeur"}]}
  </script>
</lc-example-summary>
<!-- /SLOT: summary -->
```

Le commentaire SLOT doit entourer la balise et le `<script>`. Ne mets jamais un commentaire HTML
dans le JSON : `JSON.parse` échouerait.

### 3. Cataloguer l'écran

Ajoute l'écran à `registry/screens.json` avec :

- `id` identique au nom du template sans `.html` ;
- `template` égal à `templates/<id>.html` ;
- `format` (`mobile` ou `desktop`) ;
- `job` et `products` ;
- `components` dans l'ordre exact d'apparition dans le HTML ;
- `slots` dans l'ordre exact d'apparition dans le HTML ;
- `status: "available"`.

Si le template dessine déjà sa coque `.phone`, ajoute son ID à `PHONE_TEMPLATES` dans
`scripts/build_site.py`. Sinon le hub le cadrera comme un navigateur desktop.

### 4. Documenter le contrat

Ajoute l'écran à `references/screens.md` :

- ligne dans la table canal → template ;
- liste de ses SLOTs ;
- composant associé et règles de données importantes.

### 5. Ajouter un exemple de story

Crée ou complète `registry/examples/<parcours>.json`. Un exemple doit couvrir :

- le nouveau template ;
- une narration avec `trigger`, `result` et `transition` ;
- les produits réellement utilisés ;
- `license_selection` si un produit sectoriel est impliqué.

## Ajouter une icône produit

1. Copie le SVG officiel dans `assets/product-icons/<product-id>.svg`.
2. Ajoute `"icon": "<product-id>.svg"` dans `registry/products.json`.
3. Le builder copiera uniquement les icônes des produits présents dans la story.

Une icône absente provoque une erreur de build explicite.

## Ajouter ou modifier des traductions

Les fichiers du kit gardent leurs libellés source. Les traductions françaises codées en dur vivent
dans `KIT_I18N`, dans `scripts/build_site.py`.

Quand un nouveau composant exposé contient des libellés anglais non configurables :

1. ajoute un remplacement contextuel `(EN, FR)` à `KIT_I18N` ;
2. préfère une chaîne suffisamment spécifique pour éviter un remplacement accidentel ;
3. lance `python3 scripts/build_site.py --selfcheck`.

Le self-check échoue si une clé de traduction n'existe plus dans le kit.

## Validation obligatoire

Depuis le dossier `plugins/salesforce-holodeck-creator/skills/salesforce-holodeck-creator` :

```bash
python3 scripts/validate_registry.py
python3 scripts/create_component.py --selfcheck
python3 scripts/build_component_catalog.py --selfcheck
python3 scripts/build_site.py --selfcheck
python3 scripts/build_site.py registry/examples/<exemple>.json
python3 scripts/review_site.py ./<slug>-story
```

Vérifie ensuite :

- `review/review-report.json` contient `"issue_count": 0` ;
- `review/contact-sheet.html` montre un cadrage lisible ;
- le composant fonctionne au clavier ;
- le rendu autonome s'ouvre directement en `file://` ;
- `git diff --check` ne remonte rien.

Pour inspecter la bibliothèque complète avant une revue, exécute
`python3 scripts/build_component_catalog.py`, puis ouvre `component-catalog/index.html`. Le catalogue
est une sortie locale `file://` reconstruite depuis les registres et exemples de templates ; ne
modifie jamais ses fichiers à la main.

La CI exécute les validations sans navigateur sur chaque PR. Le contributeur reste responsable de
la revue Chromium et des captures, car une charte visuelle ne peut pas être validée uniquement par
analyse statique.

Pour un re-sync complet du kit amont, consulte `assets/lightning-kit/SOURCE.md`.
