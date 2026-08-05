# Instantané vendoré du Lightning Demo Component Kit

Ces 3 fichiers sont une **copie** du kit de composants `<lc-*>` maintenu ailleurs :
`~/.aisuite/notebook/.agents/artifacts/lightning-component-kit/`.

Ils sont vendorés ici pour que la skill soit **distribuable via le marketplace Git**
(un chemin hors-repo ne se partagerait pas). `build_site.py` les bundle (retire
`import`/`export`, concatène) en `lightning-kit.js` + copie `lightning-kit.css`
dans le site généré → chargés en <script>/<link> classiques (marchent en file://).

## Re-sync quand le kit source évolue
    KIT=~/.aisuite/notebook/.agents/artifacts/lightning-component-kit
    cp "$KIT/lightning-components.css"    ./lightning-components.css
    cp "$KIT/lightning-components.js"     ./lightning-components.js
    cp "$KIT/field-service-components.js" ./field-service-components.js

On NE vendorise PAS scenario-loader.js (il utilise fetch(), bloqué en file://) :
la config passe en JSON inline dans un SLOT, pas par un scénario chargé au runtime.
