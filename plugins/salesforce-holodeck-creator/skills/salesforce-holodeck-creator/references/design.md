# Design par défaut des composants Salesforce

Cette référence est **obligatoire** avant de créer ou modifier un composant `<lc-*>` destiné à une
surface Salesforce (`lightning` ou `mobile`). Elle complète `component-charter.md` : la charte décrit
le contrat général ; ce fichier fixe la grammaire visuelle par défaut.

Toute nouvelle entrée de `registry/components.json` déclare sa `surface` et son `design_profile` :
`"slds"` pour `lightning`/`mobile`, `"brand"` pour `external`/`channel`. Le validateur utilise ce
profil pour appliquer les garde-fous adaptés sans imposer rétroactivement la nouvelle charte aux
composants historiques.

## Règle impérative

Un composant Salesforce doit ressembler à Salesforce avant toute personnalisation client :

- appliquer la grammaire **Salesforce Lightning Design System (SLDS)** avec les primitives du kit
  (`.lc-panel`, `.lc-panel__header`, `.lc-panel__heading`, `.lc-panel__title`, `.lc-panel__meta`,
  `.lc-button`, `.lc-button--brand`, `.lc-badge`, `.lc-table`, `.lc-input`, `.lc-select`) ;
- utiliser les tokens `--lc-*` disponibles pour les couleurs, bordures, rayons, ombres et
  typographie ; conserver l'échelle d'espacement compacte des primitives du kit lorsqu'aucun token
  d'espacement n'existe ;
- utiliser `lcIcon()` pour les pictogrammes fonctionnels et les icônes d'objet ;
- ne jamais dessiner une icône avec un emoji, un caractère Unicode décoratif, une image distante,
  une bibliothèque externe ou un SVG ad hoc dans le composant ;
- ne jamais appliquer la couleur client `--accent` à une surface Salesforce ;
- conserver la densité Lightning : contrôles desktop proches de 32 px, lignes de tableau 36-40 px,
  surfaces blanches sur fond gris, bordures fines et une seule action primaire par groupe ;
- préférer les patterns existants du kit avant de créer une nouvelle classe visuelle.

Pour une surface `external` ou `channel`, la marque client peut piloter l'expérience et la grammaire
SLDS n'est pas imposée. Si un composant `<lc-*>` externe réutilise le Lightning kit, il doit néanmoins
continuer à employer `lcIcon()` et les primitives accessibles du kit plutôt que réinventer des icônes.

## Icônes autorisées

La source unique est `iconPaths` dans
`assets/lightning-kit/lightning-components.js`, appelée avec `lcIcon(name, label?)`.

Icônes de base disponibles :

| Nom | Usage par défaut |
|---|---|
| `account` | compte, organisation, bâtiment |
| `contact` | contact, personne, client |
| `case` | dossier, intervention, ordre de travail |
| `activity` | activité générique, historique |
| `task` | tâche, checklist |
| `email` | email |
| `phone` | appel |
| `event` | rendez-vous, calendrier |
| `spark` | Agentforce, recommandation IA |
| `trend` | analytics, prévisions, performance |
| `chevron` | navigation, détail |
| `close` | fermeture, erreur |
| `check` | réussite, validation |
| `plus` | création |
| `search` | recherche |
| `location` | carte, géolocalisation |

Si aucune icône ne convient, ajoute d'abord un tracé SVG à `iconPaths` avec un nom sémantique,
réutilisable et documenté dans ce tableau. Le composant appelle ensuite `lcIcon('nom')`. Ne colle pas
le SVG directement dans sa méthode `render()`.

## Anatomie par défaut

Le squelette recommandé pour une carte Salesforce est :

```js
class LcExampleSummary extends JsonComponent {
  render() {
    const data = this.data;
    const titleId = `${this.id || 'example-summary'}-title`;
    this.innerHTML = `
      <section class="lc-panel lc-example-summary" aria-labelledby="${titleId}">
        <div class="lc-panel__header">
          <div class="lc-panel__heading">
            <span class="lc-object-icon lc-object-icon--activity" aria-hidden="true">
              ${lcIcon(data.icon || 'activity')}
            </span>
            <div>
              <h2 class="lc-panel__title" id="${titleId}">${escapeHtml(data.title)}</h2>
              <div class="lc-panel__meta">${escapeHtml(data.meta || '')}</div>
            </div>
          </div>
          <div class="lc-panel__actions">
            <button class="lc-button lc-button--brand" type="button" data-action="continue">
              ${escapeHtml(data.actionLabel || 'Continuer')}
            </button>
          </div>
        </div>
      </section>`;
  }
}
```

L'icône d'objet est décorative ici, donc `aria-hidden="true"`. Une icône qui porte seule une
information utilise `lcIcon(name, label)` ou un bouton avec un `aria-label` spécifique.

## Relecture obligatoire

Avant de considérer le composant terminé, vérifier :

1. aucune classe marketing générique ou couleur client n'a remplacé les primitives `lc-*` ;
2. chaque pictogramme vient de `lcIcon()` ;
3. aucun emoji ou symbole textuel ne joue le rôle d'icône ;
4. le composant reste crédible dans le shell Lightning décrit par `fidelite-salesforce.md` ;
5. le rendu fonctionne en `file://`, au clavier et avec focus visible ;
6. l'état ne dépend pas uniquement de la couleur ou de l'icône.
