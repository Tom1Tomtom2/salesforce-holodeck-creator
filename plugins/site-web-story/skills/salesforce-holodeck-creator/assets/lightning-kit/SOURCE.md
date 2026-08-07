# Instantané vendoré du Lightning Demo Component Kit

Ces fichiers sont un **instantané autonome** du kit de composants `<lc-*>` utilisé
par la skill. Le plugin Claude n'a besoin d'aucun chemin externe pour les charger.

Ils sont vendorés ici pour que la skill soit **distribuable via le marketplace Git**
(un chemin hors-repo ne se partagerait pas). `build_site.py` les bundle (retire
`import`/`export`, concatène) en `lightning-kit.js` + copie `lightning-kit.css`
dans le site généré → chargés en <script>/<link> classiques (marchent en file://).

Fichiers actuels : `lightning-components.{js,css}` (base : `JsonComponent`, `escapeHtml`,
`lcIcon` + composants CRM/charts), `field-service-components.js`, `dashboard-components.js`,
`sales-components.js`, `marketing-components.js`. `kit_js_files()` fait de la **découverte
auto par glob** → un nouveau `*-components.js` déposé ici est bundlé sans toucher au code.

## Re-sync pour les mainteneurs quand le kit source évolue

Depuis une copie locale du kit amont :

    KIT=/chemin/vers/lightning-component-kit
    cp "$KIT"/*-components.js ./          # tous les fichiers de composants
    cp "$KIT/lightning-components.js" ./   # + le fichier base (pas suffixé -components)
    cp "$KIT/lightning-components.css" ./

Après un re-sync, **lance `python3 scripts/build_site.py --selfcheck`** : il bundle réellement
le kit et vérifie 3 pièges connus —
1. **Collision de noms top-level** : chaque `*-components.js` déclare `const definitions` (sa map
   d'enregistrement) → renommée par fichier au bundle ; toute AUTRE collision fait lever le build.
2. **Libellés EN disparus** : `translate_kit()` lève si une clé de `KIT_I18N` n'existe plus (libellé
   déplacé à la source) → mets `KIT_I18N` à jour.
3. Les **nouveaux** libellés EN d'un fichier fraîchement ajouté ne sont PAS francisés tant qu'aucun
   template ne câble ses composants (cf. sales/dashboard/marketing : dispos mais non exposés). Quand
   tu crées le template qui les utilise, ajoute leurs libellés EN à `KIT_I18N` (voir screens.md § B2B).

La copie vendorée peut contenir de petits ajustements d'intégration propres à la skill. Actuellement,
`sales-components.js` accepte `data.eyebrow` dans `lc-sales-overview` afin qu'un écran pipeline ne soit
pas étiqueté « Forecast ». Un re-sync brut peut écraser cet ajustement : réapplique-le avant le self-check.
`pipeline-inspection-components.js` est propre à la skill et ne vient pas du kit amont : ne le supprime pas
lors d'un re-sync.

On NE vendorise PAS scenario-loader.js (il utilise fetch(), bloqué en file://) :
la config passe en JSON inline dans un SLOT, pas par un scénario chargé au runtime.
