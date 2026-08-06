# Registre des assets

Le dossier `registry/` est l'index machine-readable de la bibliothèque. Il ajoute une taxonomie
sans déplacer les fichiers sources : le bundler continue de lire `templates/` et
`assets/lightning-kit/` aux mêmes emplacements.

## Les quatre registres

- `products.json` décrit les produits Salesforce et les jobs qu'ils couvrent.
- `industries.json` décrit les secteurs autorisés. Le caractère transverse est porté uniquement par
  `cross_industry`, jamais par une fausse industrie `cross-industry`.
- `components.json` inventorie chaque `<lc-*>`, sa source, son job, ses produits et sa disponibilité.
- `screens.json` inventorie chaque template, son format, ses SLOTs et ses composants.

Les valeurs de `components[].status` signifient :

- `available` : le composant est déjà exposé dans au moins un template.
- `uncatalogued-screen` : le composant est livré et bundlé, mais aucun écran ne l'expose encore.

## Règle de sélection

1. Pars du job métier et du rôle de l'écran dans l'histoire.
2. Filtre ensuite sur les produits Salesforce attendus dans le brief.
3. Préfère un asset `cross_industry: true` et adapte uniquement ses données.
4. Applique un filtre industrie seulement si le parcours exige une structure ou une interaction
   réellement sectorielle.

Un changement de marque, de vocabulaire, de persona ou de données ne justifie pas un nouvel écran.
Il doit vivre dans le manifest ou dans un futur fixture/pack sectoriel. Crée un asset sectoriel
uniquement lorsque le workflow, les objets visibles ou l'interaction ne peuvent pas être représentés
crédiblement par un asset cross-industry.

## Ajouter un asset industrie

1. Vérifie d'abord qu'aucun composant ou écran cross-industry ne couvre le même job.
2. Réutilise les composants `<lc-*>` existants dès que possible.
3. Ajoute l'industrie à `industries.json` si elle n'existe pas.
4. Ajoute l'écran ou le composant avec `"cross_industry": false` et au moins une valeur dans
   `industries`.
5. Renseigne `job` et `products` indépendamment de l'industrie.
6. Si le besoin ne change que les données, crée un fixture/pack plutôt qu'un composant.
7. Lance `python3 scripts/validate_registry.py`, puis les trois selfchecks.

## Validation

`validate_registry.py` vérifie automatiquement :

- que tous les composants déclarés dans les fichiers JavaScript sont catalogués une seule fois ;
- que tous les templates sont catalogués ;
- que les sources, SLOTs et composants des écrans correspondent aux fichiers réels ;
- que les références produit et industrie existent ;
- que les règles `cross_industry` sont cohérentes ;
- que le statut d'un composant reflète son exposition réelle dans un écran.

Le builder appelle cette validation avant chaque génération. Une dérive du registre bloque donc le
build au lieu de produire silencieusement un catalogue faux.
