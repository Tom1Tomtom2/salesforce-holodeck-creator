# Charte des composants Holodeck

Cette charte définit le contrat commun des composants `<lc-*>`. Elle sert à la création et à la
revue. Les règles automatisables sont vérifiées par `validate_registry.py` ; les règles perceptuelles
restent une responsabilité de revue humaine.

## 1. Anatomie

Un composant représente **une primitive métier**, pas une page entière. Il étend `JsonComponent`,
lit `this.data`, rend une racine sémantique et expose ses actions :

```js
class LcExampleSummary extends JsonComponent {
  render() {
    const data = this.data;
    this.innerHTML = `
      <section class="lc-panel" aria-labelledby="${this.id || 'example'}-title">
        <div class="lc-panel__header">
          <h2 class="lc-panel__title" id="${this.id || 'example'}-title">
            ${escapeHtml(data.title || 'Résumé')}
          </h2>
        </div>
      </section>`;
  }
}
```

Le JSON est le contrat public. Les clés doivent être stables, documentées par un exemple dans un
template et contenir des valeurs brutes plutôt que du HTML arbitraire.

## 2. Grammaire visuelle

- **Couleurs** : bleu d'action `--lc-brand`, titres `--lc-heading`, états via `--lc-success`,
  `--lc-warning` et `--lc-error`. La couleur cliente `--accent` ne repeint jamais Lightning.
- **Surfaces** : `--lc-page`, `--lc-surface`, `--lc-surface-subtle`, bordures `--lc-border*`.
- **Typographie** : `--lc-font`, base compacte, titres hiérarchisés sans hero marketing dans Lightning.
- **Densité** : contrôles autour de 32 px en desktop ; 44 px minimum pour les cibles mobiles.
- **Formes** : `--lc-radius` et `--lc-shadow`; ombres faibles, pas de glassmorphism.
- **Actions** : une action primaire par groupe ; les actions secondaires restent neutres.
- **Layout** : rangées 1/1, 2/3-1/3 ou 1/3-1/3-1/3. Le composant remplit sa colonne et ne
  décide pas seul de la grille de page.

Les couleurs de graphiques déterministes peuvent utiliser la palette Salesforce du kit. Une couleur
configurable doit être échappée et ne peut pas être le seul moyen d'exprimer un statut.

## 3. Accessibilité

- Utilise `button`, `a`, `input`, `select`, `table`, `ol` et `ul` selon leur sens natif.
- Tout contrôle icon-only possède un `aria-label` spécifique.
- Tout état sélectionné, déplié ou pressé est exposé (`aria-selected`, `aria-expanded`,
  `aria-pressed`) et mis à jour avec l'état visuel.
- Les tableaux ont des en-têtes avec `scope`; les graphiques ont un nom et un résumé textuel utile.
- Le clavier donne accès à toute fonctionnalité. Aucun `tabindex` positif.
- Le focus est visible. Les animations respectent `prefers-reduced-motion`.
- Les mises à jour de prix, statut ou progression importantes sont annoncées avec une région live
  mesurée, sans rendre toute la page bavarde.

## 4. Sécurité et autonomie

- Passe toute valeur interpolée dans `escapeHtml`.
- Aucun `innerHTML` provenant directement du JSON.
- Aucun gestionnaire HTML inline, URL `javascript:` ou script distant.
- Aucun nouvel accès réseau. Le site généré reste utilisable en `file://`.
- Les bibliothèques déjà approuvées dans un composant historique ne constituent pas une autorisation
  d'en ajouter de nouvelles.

## 5. Classification

La classification suit cet ordre :

1. `job` : ce que l'utilisateur accomplit ;
2. `products` : les produits Salesforce qui rendent cette capacité crédible ;
3. `cross_industry` : `true` par défaut ;
4. `industries` : seulement lorsque le composant est réellement sectoriel ;
5. `status` : `available` si un template l'expose, sinon `uncatalogued-screen`.

La liste des jobs autorisés et les surfaces de revue sont dans `registry/taxonomy.json`. Un composant
ne devient pas sectoriel parce que son exemple contient un nom de banque, d'usine ou de magasin.

## 6. Preuve attendue

Une contribution est prête quand elle fournit : rendu desktop ou mobile selon sa surface, état
initial, état après interaction, navigation clavier, exemple JSON, classification et story de
démonstration. La planche contact vérifie la composition ; une interaction importante doit aussi
faire l'objet d'un test Playwright ciblé ou d'une vérification manuelle décrite dans la PR.
