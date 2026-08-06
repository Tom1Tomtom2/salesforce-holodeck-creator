# site-web-story

Skill Claude Code qui construit un **site de démo Salesforce narratif** : un parcours client de
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

## Utilisation

Demande à Claude : « fais-moi un site-web-story pour la marque X, url https://… ».
La skill est conversationnelle en 3 phases (ambiance → story validée en chat → génération).
Elle s'active aussi automatiquement pour des demandes comme « prépare un holodeck pour
le client X » ou « fais-moi une démo client Salesforce pour X ».

## Contenu

| Composant | Rôle | Dépendances |
|---|---|---|
| `scripts/build_site.py` | génère le site depuis un manifest | aucune (stdlib, Python 3.10+) |
| `scripts/crawl_brand.py` | crawle logo + images + palette | playwright + un navigateur |
| `scripts/review_site.py` | capture le hub et contrôle le rendu | playwright + un navigateur |
| `templates/*.html` | bibliothèque d'écrans à chrome verrouillée | — |

Vérification rapide après install :
```
python3 <chemin>/scripts/build_site.py --selfcheck
python3 <chemin>/scripts/crawl_brand.py --selfcheck
python3 <chemin>/scripts/review_site.py --selfcheck
```
