# Dépannage

Ce guide suit l'ordre le plus rapide pour isoler une panne : environnement, registre, build, puis rendu.

## Diagnostic rapide

Place-toi dans `plugins/salesforce-holodeck-creator/skills/salesforce-holodeck-creator` et lance :

```bash
python3 scripts/validate_registry.py
python3 scripts/build_site.py --selfcheck
python3 scripts/review_site.py --selfcheck
```

Ensuite reproduis avec le manifest concerné :

```bash
python3 scripts/build_site.py /chemin/manifest.json
python3 scripts/review_site.py ./<slug>-story
```

Lis d'abord `review/review-report.json`, puis ouvre `review/contact-sheet.html`.

## Playwright ou Chromium absent

Symptômes :

- `ModuleNotFoundError: playwright` ;
- message demandant `playwright install chromium` ;
- le crawl ou la revue visuelle ne démarre pas.

Correction :

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 scripts/review_site.py --selfcheck
```

`build_site.py` et `validate_registry.py` n'ont aucune dépendance externe et doivent continuer à fonctionner.

## Le crawl de marque échoue

Vérifie `<slug>-brand/brand.json` :

- `status: "ok"` : utilise les assets récupérés ;
- `status: "failed"` : lis `error`, ne réutilise pas les couleurs par défaut comme si elles venaient du client ;
- `logo_source: "Wikidata/Commons"` : le logo peut être valide même si les images produit manquent.

Solutions :

1. fournir des fichiers locaux via `manifest.assets` ;
2. télécharger des URL d'images directes avec :

```bash
python3 scripts/crawl_brand.py --fetch <url1> <url2> --slug <slug>
```

3. conserver des visuels en dégradé si aucun asset fiable n'est disponible.

N'invente jamais une URL produit.

## `SLOT inconnu`

Cause : une clé de `screens[].slots` n'existe pas dans le template.

Correction :

1. ouvre `registry/screens.json` ou `references/screens.md` ;
2. utilise exactement le nom déclaré ;
3. vérifie le commentaire `<!-- SLOT: nom -->` dans `templates/<template>.html`.

Les noms sont sensibles aux tirets et doivent correspondre exactement.

## `wrapper de tête avalé`

Cause : un SLOT structuré a remplacé le conteneur racine attendu, par exemple un bloc `.why`, une
carte ou un composant `<lc-*>`.

Correction : reprends le bloc d'exemple complet dans le template et modifie uniquement son contenu
ou son JSON. Ne remplace pas un SLOT structuré par du texte nu.

## `JSON.parse` ou composant vide

Vérifie le `<script type="application/json">` du composant :

- JSON valide, sans virgule finale ;
- guillemets doubles ;
- aucun commentaire HTML dans le script ;
- balise `<script>` bien incluse dans le SLOT ;
- clés attendues identiques à celles lues dans `render()`.

Tu peux valider un manifest avec :

```bash
python3 -m json.tool /chemin/manifest.json >/dev/null
```

Les erreurs du JSON inline apparaissent aussi dans `review/review-report.json` sous `Console`.

## Registre désynchronisé

Messages fréquents :

- `composant non catalogué` ;
- `écran non catalogué` ;
- `SLOTs désynchronisés` ;
- `composants désynchronisés` ;
- `statut attendu available/uncatalogued-screen`.

Correction :

1. lance `python3 scripts/validate_registry.py` ;
2. aligne `registry/components.json` sur les maps de définitions JavaScript ;
3. aligne `registry/screens.json.components` et `.slots` sur l'ordre réel du template ;
4. passe le composant à `available` s'il apparaît dans un template, sinon à `uncatalogued-screen`.

Ne contourne pas le validateur : il protège le catalogue utilisé par la skill.

## Le kit JavaScript ne s'hydrate pas

Symptômes : balises `<lc-*>` vides, erreur JavaScript au chargement, plusieurs composants cassés à la fois.

Lance :

```bash
python3 scripts/build_site.py --selfcheck
```

Causes possibles :

- collision d'un nom top-level entre deux fichiers du bundle ;
- `import` ou `export` non retiré ;
- map `definitions` non isolée ;
- syntaxe JavaScript invalide ;
- traduction `KIT_I18N` devenue obsolète après un re-sync.

Pour un fichier modifié, vérifie aussi :

```bash
node --check assets/lightning-kit/<fichier>.js
```

Consulte `assets/lightning-kit/SOURCE.md` avant un re-sync du kit.

## L'écran est blanc ou incomplet

Cherche dans `review/review-report.json` :

- `Page` : exception JavaScript ;
- `Console` : JSON invalide ou ressource absente ;
- `Réseau` : fichier local non copié ;
- `Images cassées` : mauvais chemin ou asset absent.

Vérifie ensuite que :

- le template charge `lightning-kit.js` et `lightning-kit.css` s'il contient des `<lc-*>` ;
- le composant est enregistré avec le même nom que sa balise ;
- l'asset figure dans `manifest.assets` ou dans une banque gérée par le builder ;
- aucun fichier généré n'a été édité à la place du template source.

## Mauvais cadrage dans l'index

### Mobile

- Le template doit avoir `format: "mobile"` dans `registry/screens.json`.
- S'il dessine sa propre `.phone`, son ID doit être présent dans `PHONE_TEMPLATES`.
- Corrige la coque ou le composant dans `templates/` / `assets/lightning-kit/`, jamais dans `<slug>-story/`.

### Desktop

Utilise `screens[].display` dans le manifest :

```json
{"mode":"full","scale":0.5,"height":900}
```

ou :

```json
{"mode":"crop","scale":0.65,"x":120,"y":60,"height":560}
```

Un débordement horizontal est remonté automatiquement par `review_site.py`.

## La marque d'exemple `Nova` reste visible

Cause : un SLOT structuré de marque n'a pas été renseigné et le contenu d'exemple du template est resté.

Correction : remplis les SLOTs `brand`, `nav`, `pdp`, `landing`, `email` ou équivalents du template.
Le builder liste les fichiers concernés après génération.

## Une icône produit manque

Si le build affiche `icône produit introuvable` :

1. vérifie `registry/products.json.icon` ;
2. vérifie que le même nom existe dans `assets/product-icons/` ;
3. conserve un SVG local, sans URL distante.

Le builder ne copie que les icônes réellement utilisées par les écrans de la story.

## Les couleurs produit changent avec la marque

`--accent` appartient à la marque cliente. Une couleur produit qui doit rester fixe doit être portée
par des variables locales au composant, par exemple `--lc-fs-mobile-brand`, et non par `--accent`.

Vérifie aussi les contrastes après changement avec la planche contact.

## Le build semble bon mais le rendu ne l'est pas

Ne te fie pas uniquement au code retour. Exige les quatre preuves suivantes :

```bash
python3 scripts/validate_registry.py
python3 scripts/build_site.py --selfcheck
python3 scripts/review_site.py ./<slug>-story
git diff --check
```

Puis confirme :

- `issue_count` vaut `0` ;
- le hub et chaque écran ont été regardés ;
- aucun texte important n'est coupé ;
- les contrôles clavier et les états de focus restent utilisables.
