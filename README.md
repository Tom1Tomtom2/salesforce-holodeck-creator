# Salesforce Holodeck Creator

Skill Claude `salesforce-holodeck-creator` qui construit un **site de démo Salesforce narratif** : un parcours client de
marque raconté en plusieurs « actes » (pub Instagram → configurateur → landing →
WhatsApp → Data Cloud → console SAV…), en HTML/CSS artisanal. Zéro serveur, zéro clé API.

Elle crawle le site de la marque avec le navigateur intégré de l'app Claude (logo, images
produit HD, palette, typo), puis génère un site statique navigable depuis un manifest JSON.
Un brief complémentaire peut préciser l'audience, l'objectif, la durée et les produits
Salesforce ; il reste facultatif. Le build produit aussi des notes présentateur et une
planche de revue visuelle.

## Installation

### Option A — Cowork, sans GitHub ni terminal (recommandé)

C'est le chemin par défaut pour un utilisateur non développeur. **Aucune connexion GitHub,
aucun marketplace, aucune ligne de commande.**

1. Récupère le fichier **`salesforce-holodeck-creator.skill`** (partagé sur Slack, Drive ou
   en pièce jointe — c'est une simple archive).
2. Dans l'app Claude : **Personnaliser → Compétences → `+` → Importer une compétence**,
   puis sélectionne le fichier `.skill`.
3. C'est terminé. Demande par exemple :
   `Prépare-moi un holodeck pour Acme, https://www.example.com.`

Tout fonctionne immédiatement : les templates, le registre, le Lightning kit, le crawl de
marque et la génération du site ne dépendent que de Python 3.10+ (déjà présent sur macOS) et
du navigateur intégré de l'app Claude. Seule la **revue visuelle automatisée** demande une
installation — voir l'Option C.

> Pour régénérer le bundle après une modification du skill :
> ```bash
> cd plugins/salesforce-holodeck-creator/skills
> zip -r ../../../salesforce-holodeck-creator.skill salesforce-holodeck-creator -x "*.DS_Store" "*__pycache__*"
> ```
> L'archive doit contenir **un seul dossier racine** `salesforce-holodeck-creator/`
> avec `SKILL.md` directement dedans.

### Option B — Claude Code, via le marketplace (développeurs)

```
/plugin marketplace add https://github.com/Tom1Tomtom2/salesforce-holodeck-creator
/plugin install salesforce-holodeck-creator@salesforce-holodeck-creator-marketplace
/reload-plugins
```

Le plugin, le marketplace et la skill portent le même nom `salesforce-holodeck-creator`.
Si tu avais installé l'ancienne version `site-web-story`, désinstalle-la puis réinstalle avec les
commandes ci-dessus, et exécute `/reload-plugins` (ou redémarre Claude Code) pour vider l'ancien cache.

> **Si une demande d'authentification GitHub apparaît** : elle vient du clone en SSH, pas du dépôt
> (qui est public). Deux contournements :
> - utilise l'URL `https://…` complète comme ci-dessus plutôt que la forme courte `owner/repo` ;
> - ou force le HTTPS : `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` avant la commande.
>
> Si tu veux simplement éviter le sujet, passe par l'**Option A**.

### Option C — Playwright (facultatif, uniquement pour la revue visuelle)

**Le crawl de marque n'a plus besoin de Playwright.** Il passe par le **navigateur intégré de
l'app Claude** : Claude ouvre lui-même le site, exécute le script d'extraction dans la page,
et `crawl_brand.py --from-browser` transforme le résultat en `brand.json` — téléchargement du
logo et des visuels compris, en stdlib pure.

Il reste **un seul script** qui ne peut pas s'en passer : `review_site.py`, la revue visuelle.
Elle ouvre le site généré en `file://`, un protocole que le navigateur intégré n'ouvre pas.

Si tu veux la planche contact automatique, une seule fois par machine :

```bash
pip install playwright
playwright install chromium
```

> `playwright install chromium` télécharge le **navigateur** lui-même ; `pip install playwright`
> seul n'installe que la lib Python. Chrome système est utilisé en priorité s'il est présent.
>
> Sans Playwright, la génération du site fonctionne intégralement : seule la revue visuelle
> automatisée manque, et Claude te le dit explicitement au lieu de prétendre avoir relu le rendu.

#### Comment marche le crawl par le navigateur intégré

```bash
# 1. le JS à exécuter dans la page (forme auto-appelée, collable telle quelle)
python3 scripts/crawl_brand.py --print-extract-js

# 2. Claude ouvre la marque, scrolle pour hydrater les visuels, exécute ce JS,
#    enregistre la valeur brute dans acme-extract.json, puis :
python3 scripts/crawl_brand.py --from-browser acme-extract.json \
        --brand "Acme" --slug acme --source-url https://www.example.com

# 3. après validation de la story, les visuels produit exacts :
python3 scripts/crawl_brand.py --print-extract-js product   # JS de page produit
python3 scripts/crawl_brand.py --fetch <image1> <image2> --slug acme
```

Le champ `brand.json.engine` indique quel moteur a produit le fichier. Le fallback Playwright
(`crawl_brand.py <url> --brand … --slug …`) reste disponible si le navigateur intégré est
indisponible ou si l'accès au site est refusé.

## Démarrage rapide

La façon normale d'utiliser le plugin est de demander la démo à Claude. Il orchestre le crawl,
la sélection des écrans, le manifest, le build et la revue visuelle.

La skill se déclenche pour toute demande explicite de **démo pour un client ou prospect** et de
**holodeck pour un client ou prospect**, même si la demande ne mentionne pas Salesforce.

Exemple minimal :

```text
Prépare-moi un holodeck pour Acme, https://www.example.com.
```

Exemple avec un brief :

```text
Prépare une démo client Salesforce pour Acme, https://www.example.com.
Audience : direction service et IT.
Objectif : montrer le parcours d'un technicien de la réception de l'ordre de travail
jusqu'au compte rendu Agentforce.
Durée : 8 minutes.
Produits : Field Service et Agentforce.
```

La skill fonctionne en trois validations :

1. **Ambiance** : marque, palette, assets et hypothèses du brief.
2. **Story** : thèse, personnages, actes, écrans et produits Salesforce.
3. **Génération** : manifest JSON, site statique, notes présentateur et revue visuelle.

Le brief est facultatif. En son absence, Claude propose des hypothèses et demande leur validation.
Un cahier des charges PDF, Word ou texte peut aussi servir de point de départ.

### Livrables

Le build écrit un dossier `<slug>-story/` dans le dossier depuis lequel il est lancé :

- `index.html` : page story à présenter ;
- `acte*.html` : écrans autonomes ouvrables individuellement ;
- `presenter-notes.md` : fil de présentation, transitions et durée indicative ;
- `build-manifest.json` : copie du manifest ayant produit le site ;
- `review/contact-sheet.html` : planche de contrôle visuel ;
- `review/review-report.json` : erreurs de console, assets cassés et débordements.

Le site est autonome et s'ouvre directement en `file://` : aucun serveur n'est nécessaire.

### Utilisation manuelle

Pour repartir d'un exemple sans passer par le workflow conversationnel :

```bash
cd plugins/salesforce-holodeck-creator/skills/salesforce-holodeck-creator
cp registry/examples/field-service-technician-mobile.json /tmp/ma-story.json
# Éditer /tmp/ma-story.json, puis :
python3 scripts/build_site.py /tmp/ma-story.json
python3 scripts/review_site.py ./field-service-technician-mobile-story
```

Autres exemples disponibles :

- `registry/examples/financial-services-lending.json`
- `registry/examples/consumer-goods-commerce-service.json`
- `registry/examples/manufacturing-sales-service.json`
- `registry/examples/field-service-technician-mobile.json`
- `registry/examples/core-sales-revenue.json`
- `registry/examples/revenue-cloud-advanced-quotes.json`

Ces deux derniers exemples couvrent les parcours commerciaux avancés : le premier relie Sales Cloud
et Revenue Cloud ; le second détaille configuration, tarification multi-devises, approbation et
pipeline des devis dans Revenue Cloud Advanced.

Pour choisir un écran, consulte d'abord `registry/screens.json`, puis `references/screens.md`
pour son contrat JSON et ses SLOTs. Ne modifie jamais directement un dossier `*-story/` : c'est une
sortie générée qui sera écrasée au prochain build.

## Étendre la bibliothèque

Les trois niveaux d'extension ne coûtent pas la même chose :

1. **Nouvelles données seulement** : adapte le JSON d'un composant dans le manifest. C'est le choix par défaut.
2. **Nouvel écran** : compose un nouveau template à partir de composants `<lc-*>` existants.
3. **Nouveau composant** : ajoute une nouvelle primitive JSON-driven au Lightning kit, puis expose-la dans un écran.

Le guide complet est dans
[`references/extending.md`](plugins/salesforce-holodeck-creator/skills/salesforce-holodeck-creator/references/extending.md).
Pour tout composant Salesforce, la référence
[`references/design.md`](plugins/salesforce-holodeck-creator/skills/salesforce-holodeck-creator/references/design.md)
impose par défaut la grammaire SLDS, les primitives `lc-*` et les icônes `lcIcon()` centralisées.
Pour contribuer via une pull request, commence par [`CONTRIBUTING.md`](CONTRIBUTING.md) : la charte
visuelle, la classification et les preuves de rendu y sont obligatoires.

Trois outils accélèrent le workflow contributeur :

```bash
cd plugins/salesforce-holodeck-creator/skills/salesforce-holodeck-creator
python3 scripts/create_component.py          # assistant interactif classifié
python3 scripts/create_screen.py             # template + registre + story d'exemple
python3 scripts/build_component_catalog.py   # catalogue filtrable en file://
```

Le catalogue est reconstruit depuis `registry/components.json`, les sources JavaScript et les
exemples des templates. Il ne constitue pas une deuxième source de vérité.

Commande de validation obligatoire après une extension :

```bash
cd plugins/salesforce-holodeck-creator/skills/salesforce-holodeck-creator
python3 scripts/validate_registry.py
python3 scripts/create_component.py --selfcheck
python3 scripts/create_screen.py --selfcheck
python3 scripts/build_component_catalog.py --selfcheck
python3 scripts/build_site.py --selfcheck
python3 scripts/build_site.py registry/examples/<exemple>.json
python3 scripts/review_site.py ./<slug>-story
```

Après toute modification du skill, **régénère aussi le bundle `.skill`** (voir Option A) pour que
les utilisateurs Cowork reçoivent la mise à jour.

## Dépannage

Commence toujours par ces commandes depuis le dossier de la skill :

```bash
python3 scripts/validate_registry.py
python3 scripts/build_site.py --selfcheck
python3 scripts/review_site.py --selfcheck
```

Le guide [`references/troubleshooting.md`](plugins/salesforce-holodeck-creator/skills/salesforce-holodeck-creator/references/troubleshooting.md)
couvre notamment :

- Playwright ou Chromium absent ;
- crawl de marque bloqué ;
- SLOT inconnu ou wrapper avalé ;
- registre désynchronisé ;
- composant non hydraté ou bundle JavaScript cassé ;
- écran blanc, asset manquant ou débordement ;
- problème de cadrage téléphone/desktop ;
- marque d'exemple `Nova` encore visible.

## Contenu

| Composant | Rôle | Dépendances |
|---|---|---|
| `scripts/build_site.py` | génère le site depuis un manifest | aucune (stdlib, Python 3.10+) |
| `scripts/crawl_brand.py` | crawle logo + images + palette | navigateur intégré de l'app Claude (aucune installation) ; playwright en fallback |
| `scripts/review_site.py` | capture le hub et contrôle le rendu | playwright obligatoire (ouvre des `file://`) |
| `scripts/validate_registry.py` | valide catalogue, taxonomie, classification et contrat statique des composants | aucune (stdlib) |
| `scripts/create_component.py` | génère un squelette de composant classifié et sa fixture | aucune (stdlib) |
| `scripts/create_screen.py` | compose un écran, le catalogue et une story d'exemple | aucune (stdlib) |
| `scripts/build_component_catalog.py` | génère le catalogue filtrable depuis les assets réels | aucune (stdlib) |
| `templates/*.html` | bibliothèque d'écrans à chrome verrouillée | — |
| `registry/*.json` | taxonomie machine-readable des assets | — |

La CI GitHub exécute le registre, la taxonomie et le self-check déterministe sur chaque pull request.
La revue visuelle Chromium reste une preuve obligatoire fournie par le contributeur.

Vérification rapide après install :

```bash
python3 <chemin>/scripts/build_site.py --selfcheck
python3 <chemin>/scripts/validate_registry.py
python3 <chemin>/scripts/create_component.py --selfcheck
python3 <chemin>/scripts/create_screen.py --selfcheck
python3 <chemin>/scripts/build_component_catalog.py --selfcheck
python3 <chemin>/scripts/crawl_brand.py --selfcheck
python3 <chemin>/scripts/review_site.py --selfcheck
```

Pour les mainteneurs : `SKILL.md` contient le workflow conversationnel complet,
`references/registry.md` décrit la taxonomie et `assets/lightning-kit/SOURCE.md` explique le bundling.
