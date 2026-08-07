# Salesforce Holodeck Creator

Skill Claude Code `salesforce-holodeck-creator` qui construit un **site de démo Salesforce narratif** : un parcours client de
marque raconté en plusieurs « actes » (pub Instagram → configurateur → landing →
WhatsApp → Data Cloud → console SAV…), en HTML/CSS artisanal. Zéro serveur, zéro clé API.

Elle crawle le site de la marque avec un vrai navigateur (logo, images produit HD,
palette, typo), puis génère un site statique navigable depuis un manifest JSON.
Un brief complémentaire peut préciser l'audience, l'objectif, la durée et les produits
Salesforce ; il reste facultatif. Le build produit aussi des notes présentateur et une
planche de revue visuelle.

## Installation sur une nouvelle machine

**1. Installer le plugin** (dans Claude Code) :

```
/plugin marketplace add https://github.com/Tom1Tomtom2/site-web-story-plugin
/plugin install site-web-story@site-web-story-marketplace
/reload-plugins
```

Le package du plugin conserve l'identifiant d'installation `site-web-story`, tandis que la skill
chargée par Claude s'appelle `salesforce-holodeck-creator`. Après une mise à jour qui introduit ce
nouveau nom, exécute `/reload-plugins` ou redémarre Claude Code pour retirer l'ancien nom du cache.

**2. Installer le navigateur du crawler** — **une seule fois par machine**, dans un terminal :

```
pip install playwright
playwright install chromium
```

> ⚠️ Ne saute pas la 2ᵉ commande : `playwright install chromium` télécharge le **navigateur**
> lui-même (le moteur de crawl). `pip install playwright` seul n'installe que la lib Python — le
> crawl échouera sans navigateur. Chrome système est utilisé en priorité s'il est présent.
>
> Sans cette étape, la **génération** du site fonctionne quand même (stdlib pure) ; seul le
> crawl automatique de la marque est indisponible — on remplit alors le manifest à la main.

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
cd plugins/site-web-story/skills/salesforce-holodeck-creator
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

Ce dernier exemple couvre le nouveau parcours transverse Sales Cloud + Revenue Cloud : pipeline
d'opportunités en Kanban, inspection Einstein, configuration de devis, calcul temps réel et
approbation de marge avec Agentforce.

Pour choisir un écran, consulte d'abord `registry/screens.json`, puis `references/screens.md`
pour son contrat JSON et ses SLOTs. Ne modifie jamais directement un dossier `*-story/` : c'est une
sortie générée qui sera écrasée au prochain build.

## Étendre la bibliothèque

Les trois niveaux d'extension ne coûtent pas la même chose :

1. **Nouvelles données seulement** : adapte le JSON d'un composant dans le manifest. C'est le choix par défaut.
2. **Nouvel écran** : compose un nouveau template à partir de composants `<lc-*>` existants.
3. **Nouveau composant** : ajoute une nouvelle primitive JSON-driven au Lightning kit, puis expose-la dans un écran.

Le guide complet est dans
[`references/extending.md`](plugins/site-web-story/skills/salesforce-holodeck-creator/references/extending.md).

Commande de validation obligatoire après une extension :

```bash
cd plugins/site-web-story/skills/salesforce-holodeck-creator
python3 scripts/validate_registry.py
python3 scripts/build_site.py --selfcheck
python3 scripts/build_site.py registry/examples/<exemple>.json
python3 scripts/review_site.py ./<slug>-story
```

## Dépannage

Commence toujours par ces commandes depuis le dossier de la skill :

```bash
python3 scripts/validate_registry.py
python3 scripts/build_site.py --selfcheck
python3 scripts/review_site.py --selfcheck
```

Le guide [`references/troubleshooting.md`](plugins/site-web-story/skills/salesforce-holodeck-creator/references/troubleshooting.md)
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
| `scripts/crawl_brand.py` | crawle logo + images + palette | playwright + un navigateur |
| `scripts/review_site.py` | capture le hub et contrôle le rendu | playwright + un navigateur |
| `scripts/validate_registry.py` | valide le catalogue composants/écrans/produits/industries | aucune (stdlib) |
| `templates/*.html` | bibliothèque d'écrans à chrome verrouillée | — |
| `registry/*.json` | taxonomie machine-readable des assets | — |

Vérification rapide après install :
```bash
python3 <chemin>/scripts/build_site.py --selfcheck
python3 <chemin>/scripts/validate_registry.py
python3 <chemin>/scripts/crawl_brand.py --selfcheck
python3 <chemin>/scripts/review_site.py --selfcheck
```

Pour les mainteneurs : `SKILL.md` contient le workflow conversationnel complet,
`references/registry.md` décrit la taxonomie et `assets/lightning-kit/SOURCE.md` explique le bundling.
