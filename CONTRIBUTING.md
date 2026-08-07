# Contribuer à Salesforce Holodeck Creator

La bibliothèque est ouverte aux nouveaux composants, écrans et parcours. Une contribution doit
cependant rester **réutilisable, classifiée et démontrable**. L'objectif n'est pas d'accumuler des
variantes visuelles, mais d'enrichir un vocabulaire commun et crédible.

## Avant de coder

Choisis le plus petit niveau d'extension possible :

1. **Données** : adapte le JSON d'un composant existant.
2. **Écran** : compose un nouveau template avec des composants existants.
3. **Composant** : ajoute une primitive seulement si l'interaction ou la structure manque réellement.

Recherche d'abord dans `registry/screens.json`, puis `registry/components.json`. Décris dans la pull
request ce qui manque et pourquoi les assets existants ne suffisent pas.

## Classification obligatoire

`registry/taxonomy.json` est la liste contrôlée des axes de classement.

- **Job** : intention métier servie, par exemple `approval`, `dispatch` ou `customer-360`.
- **Produit** : produit Salesforce réellement matérialisé par le composant.
- **Scope** : transverse par défaut ; sectoriel uniquement si le workflow ou les objets le sont.
- **Industrie** : obligatoire avec `cross_industry:false`, interdite sinon.
- **Surface** : contexte de conception (`lightning`, `mobile`, `external`, `channel`) à préciser dans la PR.

Ne crée pas un nouveau job pour un changement de marque, de vocabulaire, de persona ou de données.
Si un job est vraiment nouveau, ajoute-le à `taxonomy.json`, relie-le au bon produit dans
`products.json` et explique la décision dans la PR.

## Charte des composants

Un composant `<lc-*>` doit :

- étendre `JsonComponent` et recevoir ses données via un `<script type="application/json">` ;
- échapper toute donnée utilisateur avec `escapeHtml` ;
- utiliser les primitives et tokens `--lc-*` de `lightning-components.css` ;
- conserver la densité Lightning : typographie compacte, bordures fines, surfaces blanches et une
  seule action principale par zone ;
- utiliser des éléments HTML natifs avant ARIA et exposer le nom, le rôle et l'état des contrôles ;
- fonctionner au clavier, afficher un focus visible et ne pas reposer sur la couleur seule ;
- respecter `prefers-reduced-motion` pour toute animation ;
- émettre les interactions avec `emitAction()` ;
- fonctionner directement en `file://`, sans dépendance réseau ajoutée par le composant.

La charte détaillée et les exemples se trouvent dans
`plugins/site-web-story/skills/salesforce-holodeck-creator/references/component-charter.md`.

## Livrables d'une contribution

Un nouveau composant comprend au minimum :

- sa classe dans `assets/lightning-kit/<domaine>-components.js` ;
- ses styles dans `assets/lightning-kit/lightning-components.css` ;
- son entrée dans `registry/components.json` ;
- un template qui l'expose, ou le statut `uncatalogued-screen` ;
- un exemple dans `registry/examples/` dès qu'un template est ajouté ;
- la mise à jour de `references/screens.md` et, si nécessaire, de `KIT_I18N`.

## Vérification avant PR

Depuis `plugins/site-web-story/skills/salesforce-holodeck-creator` :

```bash
python3 scripts/validate_registry.py
python3 scripts/build_site.py --selfcheck
python3 scripts/review_site.py --selfcheck
python3 scripts/build_site.py registry/examples/<exemple>.json
python3 scripts/review_site.py ./<slug>-story
```

La PR doit joindre la planche contact ou des captures des états importants et confirmer :

- `review-report.json` contient `"issue_count": 0` ;
- les interactions principales ont été testées au clavier ;
- la classification job / produit / scope / industrie a été relue ;
- aucune donnée réelle sensible ni asset sans droit d'usage n'a été ajouté ;
- l'assistance IA éventuelle a été relue et testée par le contributeur.

Les validations automatiques garantissent la structure et quelques règles objectives. Elles ne
remplacent pas la revue visuelle, métier et accessibilité.
