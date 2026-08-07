## Besoin couvert

Décris le moment de démonstration et pourquoi les composants ou écrans existants ne suffisent pas.

## Niveau d'extension

- [ ] Données seulement
- [ ] Nouvel écran avec composants existants
- [ ] Nouveau composant `<lc-*>`

## Classification

- Job :
- Produit(s) Salesforce :
- Surface : `lightning` / `mobile` / `external` / `channel`
- Scope : `cross-industry` / `industry`
- Industrie(s), si sectoriel :
- Licence ou add-on à signaler :

Si une valeur de taxonomie est nouvelle, explique pourquoi une valeur existante ne convient pas.

## Charte et accessibilité

- [ ] Données JSON échappées avec `escapeHtml`
- [ ] Tokens et primitives `--lc-*` réutilisés
- [ ] HTML natif privilégié et états ARIA synchronisés
- [ ] Navigation clavier et focus visible vérifiés
- [ ] Cibles mobiles de 44 px si applicable
- [ ] Aucun nouvel accès réseau ; fonctionnement `file://`
- [ ] Animation compatible `prefers-reduced-motion`

## Preuves

- Story d'exemple :
- Planche contact / captures :
- États interactifs testés :
- Assistance IA utilisée et relue : oui / non

## Validation

- [ ] `python3 scripts/validate_registry.py`
- [ ] `python3 scripts/build_site.py --selfcheck`
- [ ] `python3 scripts/review_site.py --selfcheck`
- [ ] Build et revue de la story d'exemple
- [ ] `review-report.json` contient `"issue_count": 0`
