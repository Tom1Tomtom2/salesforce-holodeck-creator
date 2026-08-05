# Grille de fidélité — écrans Salesforce Lightning

Checklist de relecture pour les écrans **desktop Salesforce** de la skill
(`datacloud-profil`, `datacloud-pipeline`, `datacloud-segment`, `service-console`).
À passer en tête avant de générer, et à l'œil sur le rendu.

> Source : design system interne « Salesforce Lightning Holodeck » (calibré sur SLDS + captures).
> **Adapté au contrat de cette skill** : narratif, statique, zéro JS, zéro serveur.
> Tout ce qui touche au routing `#/`, aux toasts, aux modales cliquables ou au scénario JSON
> **ne s'applique pas ici** (nos écrans sont figés dans des iframes, on scrolle) — c'est le rôle du récit.

## Ce qui rend un faux écran SF crédible (à viser)

- **Shell d'abord.** Le header Lightning (`.lightning` dans `shared.css`) est la signature :
  header ~50px, context-bar ~40px, ligne bleue de 3px sous l'onglet actif. Un écran sans lui paraît faux.
- **Le bleu reste le bleu.** Liens, actions principales, sélection, focus = `#0176d3`. **On ne repeint jamais
  toute l'UI à la couleur du client** — seul le logo top-left (`sf-logo`) est à la marque. (C'est déjà la règle de la skill.)
- **Densité compacte.** Base 13px, lignes de tableau 36-40px, titres pas surdimensionnés, graisses pas toutes à 700.
  Une interface SF est structurée par les fonds/bordures/espacements, pas par de grosses ombres.
- **Surfaces blanches sur fond de page gris clair** (`#f3f2f2`). Bordures fines `#c9c9c9`, ombres faibles.
- **Icônes d'une seule famille**, grises et compactes ; l'avatar rond est l'élément le plus fort à droite du header.
- **Données cohérentes** entre les écrans : un contact vu dans un acte garde le même nom / poste / téléphone dans le suivant.
  Pas de valeurs rondes répétées, pas de Lorem ipsum, dates plausibles. Voir le contrat « données réelles ».
- **Un repère « démo » visible** : ici c'est le cartouche `.act-tag` en haut à gauche (repère de démo, assumé).

## Signaux qui trahissent un faux écran (à éviter)

- Header global absent, trop haut, ou repeint à la couleur client.
- Navigation sans onglet actif marqué.
- Police trop grosse / trop grasse partout ; espacements de 24-32px dans une zone censée être dense.
- Cartes toutes identiques avec de fortes ombres ; gradients décoratifs, glassmorphism, boutons géants.
- Tableau sans en-tête gris, sans séparateurs fins, sans liens bleus sur les noms.
- Trop de boutons bleus « principaux » (un seul par zone).
- Icônes de plusieurs styles mélangés.
- Couleur du client étalée sur toute l'interface (bordures, icônes…).
- Données qui se contredisent d'un écran à l'autre.

## Dimensions de référence (calibration, valeurs cibles)

| Élément | Cible bureau |
|---|---:|
| Global header | 48-52 px |
| Context-bar (nav d'app) | 40-44 px |
| Rail console gauche | 48-52 px |
| Bouton / champ de recherche | 32 px de haut |
| Ligne de tableau | 36-40 px |
| Icône d'objet | 32 px |
| Avatar header | 32-36 px |
| Colonne latérale (Activity / panneau) | ~31-33 % de la largeur |

## Couleurs (rappel)

La chrome SF porte **ses vraies couleurs en dur** dans `.lightning` (bleu action `#0176d3`, marine `#032d60`
pour les grands titres, bordures `#c9c9c9`). Les tokens `--green/--red/--amber` de `shared.css` sont **génériques
et partagés** avec les écrans non-SF (WhatsApp, e-commerce…) : **ne les repeins pas** aux valeurs SLDS, tu ferais
fuiter la palette Salesforce hors de Salesforce. Un profil visuel par écran, jamais mélangés.
