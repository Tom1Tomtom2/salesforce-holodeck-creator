# site-web-story

Skill Claude Code qui construit un **site de démo narratif** : un parcours client de
marque raconté en plusieurs « actes » (pub Instagram → configurateur → landing →
WhatsApp → Data Cloud → console SAV…), en HTML/CSS artisanal. Zéro serveur, zéro clé API.

Elle crawle le site de la marque avec un vrai navigateur (logo, images produit HD,
palette, typo), puis génère un site statique navigable depuis un manifest JSON.

## Installation (pour tes collègues)

```
/plugin marketplace add <URL-du-repo-git>
/plugin install site-web-story
```

Puis, **une fois par machine**, pour activer le crawler de marque :

```
pip install -r ~/.claude/plugins/**/site-web-story/requirements.txt
playwright install chromium
```

> Le crawler utilise Google Chrome système s'il est présent, sinon le Chromium ci-dessus.
> Sans cette étape, la **génération** du site fonctionne quand même (stdlib pure) ; seul le
> crawl automatique de la marque est indisponible — on remplit alors le manifest à la main.

## Utilisation

Demande à Claude : « fais-moi un site-web-story pour la marque X, url https://… ».
La skill est conversationnelle en 3 phases (ambiance → story validée en chat → génération).

## Contenu

| Composant | Rôle | Dépendances |
|---|---|---|
| `scripts/build_site.py` | génère le site depuis un manifest | aucune (stdlib, Python 3.10+) |
| `scripts/crawl_brand.py` | crawle logo + images + palette | playwright + un navigateur |
| `templates/*.html` | bibliothèque d'écrans à chrome verrouillée | — |

Vérification rapide après install :
```
python3 <chemin>/scripts/build_site.py --selfcheck   # doit afficher "selfcheck OK"
```
