#!/usr/bin/env python3
"""Assemble un site de démo `salesforce-holodeck-creator` à partir d'un manifest JSON.

Claude ne recopie plus le HTML : il produit un manifest {marque, tokens, écrans}
où chaque écran mappe des noms de SLOT à leur contenu. Ce script copie chaque
template, injecte les SLOTs (str.replace entre marqueurs), réécrit les tokens
:root de shared.css, et génère le hub. Déterministe, stdlib pure, zéro IA.

Usage :
    python3 scripts/build_site.py manifest.json     # ou '-' pour stdin
    python3 scripts/build_site.py --selfcheck
"""
import argparse
import html
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from validate_registry import RegistryError, validate_registry

ROOT = Path(__file__).resolve().parent.parent  # dossier de la skill
TPL = ROOT / "templates"
ASSETS = ROOT / "assets"
KIT = ASSETS / "lightning-kit"
KIT_BASE = "lightning-components.js"                      # définit JsonComponent : DOIT passer en 1er
KIT_SKIP = {"scenario-loader.js"}                         # fetch() → bloqué en file://, exclu

# Franc­isation au build (shim). Le kit vendoré reste IDENTIQUE à la source amont de l'utilisateur
# (un re-sync ne casse donc jamais le français) ; on traduit ses libellés EN codés en dur au moment
# du bundle. Chaque clé porte son CONTEXTE (`>`, `</span>`, guillemets) → unique et sûre, pas de
# remplacement de mot sauvage. Remplacements SANS apostrophe droite (' casse une string JS) : on
# utilise l'apostrophe typographique ’ (U+2019), valide dans une string JS et plus jolie en FR.
# ponytail: quand l'utilisateur AJOUTE un composant avec de nouveaux libellés EN, on étend ce dico
# (une ligne par libellé) — c'est le seul endroit du français, testé au --selfcheck.
KIT_I18N = [
    # — statusClass() : les badges/pastilles se colorent d'après le STATUT (données du manifest, en FR).
    #   Sans ça, un statut français ("Terminé", "Critique"…) n'est pas reconnu → tout tombe en bleu par
    #   défaut au lieu de vert/rouge/orange. On étend les 3 listes avec les termes FR des templates. —
    ("['completed', 'available', 'on-site', 'success'].includes(normalized)",
     "['completed', 'available', 'on-site', 'success', 'terminé', 'terminée', 'disponible', 'sur-site', 'en-ligne', 'livré', 'livrée', 'actif', 'active'].includes(normalized)"),
    ("['late', 'critical', 'blocked', 'error'].includes(normalized)",
     "['late', 'critical', 'blocked', 'error', 'en-retard', 'critique', 'bloqué', 'bloquée', 'urgent', 'urgente'].includes(normalized)"),
    ("['en-route', 'travel', 'warning', 'at-risk'].includes(normalized)",
     "['en-route', 'travel', 'warning', 'at-risk', 'trajet', 'à-risque', 'en-attente', 'en-cours'].includes(normalized)"),
    # — Field Service : libellés VRAIMENT codés en dur (non pilotables par le JSON) —
    (">Optimize Schedule<", ">Optimiser la tournée<"),
    (">New Appointment<", ">Nouveau rendez-vous<"),
    (">View Details<", ">Voir le détail<"),
    (">Request Restock<", ">Demander un réappro.<"),
    ("<th>SKU</th><th>Part</th><th>Required</th><th>Van Stock</th><th>Status</th>",
     "<th>SKU</th><th>Pièce</th><th>Requis</th><th>Stock camion</th><th>Statut</th>"),
    ("? 'Available' : 'Restock'", "? 'Disponible' : 'À réappro.'"),
    ("<h3>Checklist</h3>", "<h3>Liste de contrôle</h3>"),
    ("Use my location", "Utiliser ma position"),
    (">Open appointment<", ">Ouvrir le rendez-vous<"),
    ('aria-label="Locations"', 'aria-label="Lieux"'),
    (">Reset<", ">Réinitialiser<"),
    # légendes carte + dispatch (mêmes clés → traduction cohérente des deux)
    ("> Scheduled</span>", "> Planifié</span>"),
    ("> Travel</span>", "> Trajet</span>"),
    ("> Completed</span>", "> Terminé</span>"),
    ("> Conflict</span>", "> Conflit</span>"),
    # filtre carte : sentinelle logique ET affichage → traduits ENSEMBLE (sinon le filtre casse)
    ("['All', ...statuses]", "['Tous', ...statuses]"),
    ("filter === 'All'", "filter === 'Tous'"),
    # — panneau IA (Agentforce/Einstein) : "Draft" codé en dur —
    ("<strong>Draft</strong>", "<strong>Brouillon</strong>"),
    # — modale / toast : libellés d'action codés en dur —
    (">Cancel<", ">Annuler<"),
    ('aria-label="Close"', 'aria-label="Fermer"'),
    ('aria-label="Close notification"', 'aria-label="Fermer la notification"'),
    # — valeurs par DÉFAUT (fuient si le manifest omet le champ ; on les francise par sécurité) —
    ("'Service Map'", "'Carte du service'"),
    ("} locations`", "} lieux`"),
    ("'Map showing service locations'", "'Carte des interventions'"),
    ("'Unassigned'", "'Non assigné'"),
    ("'Dispatch Console'", "'Console de répartition'"),
    ("} technicians</div>", "} techniciens</div>"),
    ("'Technicians'", "'Techniciens'"),
    ("} resources`", "} ressources`"),
    ("'Technician Route'", "'Tournée technicien'"),
    ("} stops`", "} arrêts`"),
    ("'Service Appointment'", "'Rendez-vous de service'"),
    ("'Start Travel'", "'Démarrer le trajet'"),
    ("'Work Order'", "'Ordre de travail'"),
    ("'Parts Inventory'", "'Pièces & stock'"),
    ("'Technician van stock'", "'Stock du camion'"),
    ("'Dashboard Filters'", "'Filtres du tableau de bord'"),
    ("'Bar chart'", "'Diagramme en barres'"),
    ("'Donut chart'", "'Diagramme en anneau'"),
    ("'Line chart'", "'Courbe'"),
    ("'Gauge'", "'Jauge'"),
    ("|| 'Chart'", "|| 'Graphique'"),
    ("'Untitled record'", "'Enregistrement sans titre'"),
    ("'Customer 360'", "'Vue client 360'"),
    ("'Unified profile'", "'Profil unifié'"),
    ("'Related records'", "'Enregistrements liés'"),
    ("} items`", "} éléments`"),
    ("'Engagement Feed'", "'Flux d’engagement'"),
    ("'All time · All activities'", "'Tout · Toutes activités'"),
    ("|| 'Status'", "|| 'Statut'"),
    ("'Key performance indicators'", "'Indicateurs clés'"),
    ("'Agentforce recommendation'", "'Recommandation Agentforce'"),
    ("'Suggested next action'", "'Meilleure action suivante'"),
    ("|| 'Apply'", "|| 'Appliquer'"),
    ("|| 'Edit'", "|| 'Modifier'"),
    ("'Recalculated in real time'", "'Recalculé en temps réel'"),
    ("'Nothing here yet'", "'Rien pour l’instant'"),
    ("'Edit record'", "'Modifier l’enregistrement'"),
    ("|| 'Save'", "|| 'Enregistrer'"),
    # — Marketing Cloud (marketing-components.js) : câblé par lightning-marketing.html —
    # campaign-workspace
    (">Open Flow</button>", ">Ouvrir le flux</button>"),
    (">Activate</button>", ">Activer</button>"),
    ("<span>Status</span>", "<span>Statut</span>"),
    ("<span>Owner</span>", "<span>Propriétaire</span>"),
    ("<span>Flow Type</span>", "<span>Type de flux</span>"),
    ("<h3>Start: Segments (", "<h3>Départ : segments ("),
    (" people</small>", " personnes</small>"),
    # statut du message → couleur "Ready" ; le manifest FR utilise "Prêt", on aligne la sentinelle
    ("message.status === 'Ready'", "message.status === 'Prêt'"),
    # journey-builder
    (">Debug</button>", ">Déboguer</button>"),
    (">Save As New Version</button>", ">Enregistrer comme nouvelle version</button>"),
    (">Save</button>", ">Enregistrer</button>"),        # aussi email-studio (2 occurrences)
    ("<strong>Add Element</strong>", "<strong>Ajouter un élément</strong>"),
    ('placeholder="Search..."', 'placeholder="Rechercher..."'),
    ('aria-label="Add element after ', 'aria-label="Ajouter un élément après '),
    ('aria-label="Search journey elements"', 'aria-label="Rechercher des éléments de parcours"'),
    ('aria-label="Close element picker"', 'aria-label="Fermer le sélecteur d’éléments"'),
    ('aria-label="Zoom out"', 'aria-label="Dézoomer"'),
    ('aria-label="Fit journey"', 'aria-label="Ajuster le parcours"'),
    ('aria-label="Zoom in"', 'aria-label="Zoomer"'),
    # email-studio (panneau Agentforce = clin d'œil produit)
    ("<span>Last saved a few seconds ago</span>", "<span>Enregistré il y a quelques secondes</span>"),
    ("View Mode <select", "Mode d’affichage <select"),
    ("<h2>Components</h2>", "<h2>Composants</h2>"),
    ('placeholder="Search"', 'placeholder="Rechercher"'),
    ('aria-label="Search email components"', 'aria-label="Rechercher des composants email"'),
    ("<span>Subject Line</span>", "<span>Objet</span>"),
    ("<span>Preheader</span>", "<span>Pré-en-tête</span>"),
    (">Apply</button>", ">Appliquer</button>"),
    (">Try Again</button>", ">Réessayer</button>"),
    ('placeholder="Describe your task or ask a question..."', 'placeholder="Décrivez votre tâche ou posez une question..."'),
    (">Ask Agentforce</span>", ">Demander à Agentforce</span>"),
    # segment-builder (panneau Einstein = clin d'œil produit)
    ("<span>Segment On</span>", "<span>Segmenter sur</span>"),
    (">Save Segment</button>", ">Enregistrer le segment</button>"),
    (">Attributes</button>", ">Attributs</button>"),
    ('aria-label="Search segment attributes"', 'aria-label="Rechercher des attributs de segment"'),
    ("<h3>Related Attributes</h3>", "<h3>Attributs liés</h3>"),
    ('aria-label="Refresh segment population"', 'aria-label="Actualiser la population du segment"'),
    ("<span>Segment Population</span>", "<span>Population du segment</span>"),
    ("% of ${Number(data.totalPopulation)", "% de ${Number(data.totalPopulation)"),
    (" total population</small>", " de population totale</small>"),
    (".toLocaleString('en-US')", ".toLocaleString('fr-FR')"),   # nombres au format FR (espaces)
    (">+ Add condition</button>", ">+ Ajouter une condition</button>"),
    ("<span>Count</span>", "<span>Nombre</span>"),
    (">Include</button>", ">Inclure</button>"),
    (">Exclude</button>", ">Exclure</button>"),
    (">Regenerate</button>", ">Régénérer</button>"),
    (">Explain Attributes</button>", ">Expliquer les attributs</button>"),
    (">Ask Einstein about this segment</span>", ">Demander à Einstein à propos de ce segment</span>"),
    # marketing-performance
    ("Content <select", "Contenu <select"),
    ("<option>All</option>", "<option>Tout</option>"),
    ("<option>Campaign</option>", "<option>Campagne</option>"),
    ("<option>Transactional</option>", "<option>Transactionnel</option>"),
    ("<h3>Successful Send Details</h3>", "<h3>Détail des envois réussis</h3>"),
    ("<th>Campaign Name</th><th>Channel</th><th>Sent</th><th>Delivered</th><th>Opens</th><th>Clicks</th><th>CTR</th><th>Revenue</th>",
     "<th>Nom de la campagne</th><th>Canal</th><th>Envoyés</th><th>Délivrés</th><th>Ouvertures</th><th>Clics</th><th>Taux de clic</th><th>Revenu</th>"),
    # valeurs par DÉFAUT (fuient si le manifest omet le champ)
    ("|| 'Campaign'", "|| 'Campagne'"),
    ("|| 'Marketing Campaign'", "|| 'Campagne marketing'"),
    # — Sales Cloud + Revenue Cloud (sales-components.js) —
    # badges d'approbation : le manifest est en français, on conserve les couleurs métier
    ("value.includes('approved') || value.includes('won') || value === 'low'",
     "value.includes('approved') || value.includes('won') || value.includes('approuvé') || value.includes('gagné') || value === 'low' || value === 'faible'"),
    ("value.includes('pending') || value.includes('risk') || value.includes('review')",
     "value.includes('pending') || value.includes('risk') || value.includes('review') || value.includes('attente') || value.includes('risque') || value.includes('revue')"),
    ("value.includes('rejected') || value.includes('blocked')",
     "value.includes('rejected') || value.includes('blocked') || value.includes('rejeté') || value.includes('refusé') || value.includes('bloqué')"),
    # vue commerciale, pipeline et inspection des affaires
    ("'Revenue Command Center'", "'Centre de pilotage commercial'"),
    ("'Forecast Summary'", "'Synthèse des prévisions'"),
    ("'On target'", "'Objectif atteint'"),
    ("} gap`", "} d’écart`"),
    ("<span>of quota</span>", "<span>du quota</span>"),
    ("<span>Quota</span>", "<span>Quota</span>"),
    ("<span>Closed Won</span>", "<span>Gagné</span>"),
    ("<span>Commit</span>", "<span>Engagé</span>"),
    ("<span>Best Case</span>", "<span>Meilleur cas</span>"),
    ("<span>Pipeline Coverage</span>", "<span>Couverture du pipeline</span>"),
    ('aria-label="Forecast range"', 'aria-label="Fourchette de prévision"'),
    ("<b>Quota</b>", "<b>Quota</b>"),
    (" opportunities</small>", " opportunités</small>"),
    ("'Forecast by Category'", "'Prévisions par catégorie'"),
    ("'Forecast Hierarchy'", "'Hiérarchie des prévisions'"),
    (">Expand All</button>", ">Tout développer</button>"),
    ("<th scope=\"col\">Forecast Owner</th><th scope=\"col\">Quota</th><th scope=\"col\">Closed</th><th scope=\"col\">Commit</th><th scope=\"col\">Best Case</th><th scope=\"col\">Coverage</th>",
     "<th scope=\"col\">Responsable</th><th scope=\"col\">Quota</th><th scope=\"col\">Gagné</th><th scope=\"col\">Engagé</th><th scope=\"col\">Meilleur cas</th><th scope=\"col\">Couverture</th>"),
    (">+ Add opportunity</button>", ">+ Ajouter une opportunité</button>"),
    ("'Opportunity Pipeline'", "'Pipeline des opportunités'"),
    (">Filters</button>", ">Filtres</button>"),
    (">New Opportunity</button>", ">Nouvelle opportunité</button>"),
    ("<small>Risk</small>", "<small>Risque</small>"),
    ("<small>Next best action</small>", "<small>Meilleure action suivante</small>"),
    ("'Deal Inspection'", "'Inspection des affaires'"),
    ("'Recent Deal Activity'", "'Activité commerciale récente'"),
    # devis et approbation Revenue Cloud
    ('aria-label="Quantity for ', 'aria-label="Quantité pour '),
    ('aria-label="Unit price for ', 'aria-label="Prix unitaire pour '),
    ("} months</td>", "} mois</td>"),
    ('aria-label="Remove ', 'aria-label="Retirer '),
    ("'Quote'", "'Devis'"),
    (">Preview</button>", ">Aperçu</button>"),
    (">Send Quote</button>", ">Enregistrer le devis</button>"),
    ("<span>Valid Until</span>", "<span>Valide jusqu’au</span>"),
    ("<span>Discount</span>", "<span>Remise</span>"),
    ('aria-label="Discount percentage"', 'aria-label="Pourcentage de remise"'),
    ("<span>Currency</span>", "<span>Devise</span>"),
    ("<th scope=\"col\">Product</th><th scope=\"col\">Qty</th><th scope=\"col\">Unit Price</th><th scope=\"col\">Term</th><th scope=\"col\">Net Total</th>",
     "<th scope=\"col\">Produit</th><th scope=\"col\">Qté</th><th scope=\"col\">Prix unitaire</th><th scope=\"col\">Durée</th><th scope=\"col\">Total net</th>"),
    (">+ Add Product</button>", ">+ Ajouter un produit</button>"),
    ("<span>Subtotal</span>", "<span>Sous-total</span>"),
    ("<span>Estimated Tax (", "<span>Taxes estimées ("),
    ("<span>Grand Total</span>", "<span>Total général</span>"),
    ("'Approval Journey'", "'Parcours d’approbation'"),
    (">Send Reminder</button>", ">Envoyer un rappel</button>"),
    # — Pipeline Inspection (dashboard-components.js) —
    (">Target</span>", ">Objectif</span>"),
    ("'Revenue waterfall'", "'Évolution du pipeline'"),
    (">Increase</span>", ">Augmentation</span>"),
    (">Decrease</span>", ">Diminution</span>"),
    (">Total</span>", ">Total</span>"),
    ("'Deals Requiring Attention'", "'Affaires nécessitant votre attention'"),
    (">View All</button>", ">Tout afficher</button>"),
    ("<th scope=\"col\">Opportunity</th><th scope=\"col\">Owner</th><th scope=\"col\">Amount</th><th scope=\"col\">Stage</th><th scope=\"col\">Score</th><th scope=\"col\">Primary Risk</th><th scope=\"col\">Close Date</th>",
     "<th scope=\"col\">Opportunité</th><th scope=\"col\">Responsable</th><th scope=\"col\">Montant</th><th scope=\"col\">Étape</th><th scope=\"col\">Score</th><th scope=\"col\">Risque principal</th><th scope=\"col\">Date de clôture</th>"),
]


def kit_js_files() -> list:
    """Fichiers JS du kit à bundler, base d'abord. Découverte auto → quand l'utilisateur AJOUTE
    un fichier de composants au kit, il est pris sans toucher au code (cf. son workflow « j'en
    ajoute, on récupère petit à petit »). Ordre : lightning-components.js (base JsonComponent dont
    tout hérite → sinon `class X extends JsonComponent` casse à l'évaluation) puis le reste, trié."""
    others = sorted(f.name for f in KIT.glob("*.js") if f.name not in KIT_SKIP and f.name != KIT_BASE)
    return ([KIT_BASE] if (KIT / KIT_BASE).is_file() else []) + others


def _top_level_dupes(js: str) -> list:
    """Noms déclarés PLUSIEURS fois au top-level du bundle (colonne 0 = même portée globale).
    En file:// tout est concaténé dans un seul <script> → un double `const X` lève une
    SyntaxError qui tue TOUT le kit (aucun composant n'hydrate). Garde-fou du re-sync."""
    names = re.findall(r"^(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)", js, re.M)
    seen, dupes = set(), []
    for n in names:
        (dupes.append(n) if n in seen else seen.add(n))
    return sorted(set(dupes))


def bundle_kit_js() -> str:
    """Concatène les modules du kit <lc-*> en UN script CLASSIQUE (chargeable en file://).
    Les ES modules (import/export) et fetch() sont bloqués en file:// ; le contrat de la skill
    est le double-clic. On retire donc `import`/`export` : une fois concaténés, les fichiers
    partagent la même portée globale. `escapeHtml`/`JsonComponent`/`lcIcon` sont définis UNE fois
    (dans le fichier base) → aucune collision. Mais chaque fichier de composants a sa propre map
    d'enregistrement `const definitions = {…}` (convention du kit) : au top-level partagé, ces
    homonymes lèveraient `Identifier 'definitions' has already been declared`. On la renomme donc
    par fichier (elle n'est jamais partagée entre fichiers). Toute AUTRE collision → on lève."""
    parts = []
    for name in kit_js_files():
        src = (KIT / name).read_text(encoding="utf-8")
        src = re.sub(r"^\s*import\s.*?;\s*$", "", src, flags=re.M)  # lignes `import … ;`
        src = re.sub(r"^export\s+", "", src, flags=re.M)            # mot-clé `export`
        slug = re.sub(r"[^A-Za-z0-9]", "_", name)                   # map d'enregistrement → unique/fichier
        src = re.sub(r"\bdefinitions\b", f"definitions__{slug}", src)
        parts.append(f"/* {name} */\n{src}")
    js = translate_kit("\n\n".join(parts))
    dupes = _top_level_dupes(js)
    if dupes:
        raise SystemExit(
            "ERREUR : collision de noms top-level dans le bundle du kit (casse tout le kit en "
            "file://) :\n  " + ", ".join(dupes) + "\n→ un fichier de composants ré-emploie un nom "
            "global ; renomme-le à la source ou traite-le comme `definitions` dans bundle_kit_js()."
        )
    return js


def translate_kit(js: str) -> str:
    """Applique KIT_I18N au bundle. Chaque clé DOIT exister (sinon un libellé a bougé à la source
    et le shim ne traduirait plus en silence → on lève, c'est justement le risque à couvrir)."""
    missing = [en for en, _ in KIT_I18N if en not in js]
    if missing:
        raise SystemExit(
            "ERREUR : libellés à traduire absents du kit (déplacés à la source ?) :\n  "
            + "\n  ".join(missing)
            + "\n→ mets à jour KIT_I18N dans build_site.py (ou re-sync le kit)."
        )
    for en, fr in KIT_I18N:
        js = js.replace(en, fr)
    return js


def _first_tag(s: str) -> str | None:
    """1er tag ouvrant d'un fragment HTML (None si le fragment commence par du texte)."""
    m = re.match(r"\s*(<[a-zA-Z][^>]*?>)", s)
    return m.group(1) if m else None


def inject_slots(markup: str, slots: dict, template_name: str) -> list:
    """Remplace le contenu de chaque SLOT nommé (mutation en place via la variable markup).
    SLOT inconnu → erreur bruyante. Retourne la liste des avertissements « wrapper avalé »."""
    warnings = []
    for name, content in slots.items():
        # <!-- SLOT: nom [─ description] --> (corps) <!-- /SLOT
        # ouverture inline (`nom -->`) ou bloc (`nom ─ desc -->`) ; 2 fermetures possibles.
        # `.*?-->` (non-greedy, DOTALL) borne l'ouverture au 1er `-->` : c'est forcément la
        # fermeture du commentaire d'ouverture (un commentaire HTML ne peut pas contenir `--`).
        # → le libellé peut contenir des `>` (« garde le <script JSON> ») ET tenir sur plusieurs lignes.
        # groupe 2 = corps d'origine (l'exemple), pour comparer le wrapper de tête.
        pat = re.compile(
            r"(<!-- SLOT: " + re.escape(name) + r"(?![\w-]).*?-->)(.*?)(<!-- /SLOT)",
            re.DOTALL,
        )
        m = pat.search(markup)
        if m is None:
            raise SystemExit(
                f"ERREUR : SLOT '{name}' introuvable dans template '{template_name}'. "
                f"Vérifie le nom (voir references/screens.md)."
            )
        # ponytail: garde-fou « wrapper de tête avalé ». Si l'exemple du template ouvre sur
        # un <div class="…"> et que le contenu fourni démarre par autre chose, l'auteur a
        # recopié l'intérieur du SLOT sans son conteneur → DOM valide mais style perdu.
        exp = _first_tag(m.group(2))
        if content.strip() and exp and exp.startswith("<div") and _first_tag(content) != exp:
            warnings.append(f"{template_name} · SLOT '{name}' : devrait commencer par {exp}")
        markup = markup[: m.start()] + m.group(1) + content + markup[m.end(2):]
    return warnings, markup


def inject_story_avatar(markup: str, screen: dict, intro: dict) -> str:
    """Injecte dans `sf-avatar` le portrait du personnage connecté pour cet acte."""
    if 'SLOT: sf-avatar' not in markup:
        return markup
    persona = screen.get("persona")
    if not persona:
        return markup
    character = next((p for p in intro.get("cast", []) if p.get("name") == persona), None)
    if character is None:
        raise SystemExit(
            f"ERREUR : persona '{persona}' de l'écran '{screen['file']}' absente de intro.cast."
        )
    image = character.get("image")
    if not image:
        raise SystemExit(
            f"ERREUR : le personnage '{persona}' doit avoir une image pour alimenter sf-avatar "
            f"dans '{screen['file']}'."
        )
    avatar = f'<img class="ln-avatar" src="{html.escape(image, quote=True)}" alt="">'
    _, markup = inject_slots(markup, {"sf-avatar": avatar}, screen["template"])
    return markup


def rewrite_tokens(css: str, tokens: dict, font_import: str | None) -> str:
    """Réécrit les valeurs de tokens dans :root, et la 1ère ligne @import si fournie."""
    for name, value in tokens.items():
        pat = re.compile(r"(" + re.escape(name) + r":\s*)[^;]+")
        css, n = pat.subn(lambda m: m.group(1) + value, css, count=1)
        if n == 0:  # token pas encore présent → l'ajouter en tête de :root
            css = re.sub(r"(:root\s*\{)", r"\1\n    " + name + ": " + value + ";", css, count=1)
    if font_import:
        css = re.sub(r"@import url\([^)]*\);", font_import, css, count=1)
    return css


# Templates qui dessinent DÉJÀ leur propre coque de téléphone (.phone) → cadre .frame.phone,
# sinon cadre navigateur .frame.desktop. (cf. references/screens.md)
PHONE_TEMPLATES = {
    "instagram", "whatsapp", "landing-capture", "client-app", "mobile-card-scan",
    "fieldservice-mobile-work-order", "fieldservice-mobile-work-plan",
    "fieldservice-mobile-coverage", "fieldservice-mobile-part-return",
    "fieldservice-mobile-agent-summary",
}


def _intro_block(intro: dict, screens: list) -> str:
    """Section .intro : kicker + titre + lede, cartes personnages (cast[]), frise du parcours (1 pas/écran)."""
    if not intro:
        return ""
    cast = []
    for p in intro.get("cast", []):
        img = p.get("image")
        face = (f'<img class="face" src="{html.escape(img)}" alt="{html.escape(p.get("name",""))}">'
                if img else f'<span class="face letter">{html.escape(p.get("name","?")[:1])}</span>')
        cast.append(
            f'        <div class="who">{face}<div>'
            f'<div class="nm">{html.escape(p.get("name",""))}</div>'
            f'<div class="rl">{html.escape(p.get("role",""))}</div>'
            f'<div class="bio">{html.escape(p.get("bio",""))}</div></div></div>'
        )
    steps = []
    for n, s in enumerate(screens, 1):
        steps.append(
            f'        <div class="step"><span class="dot"></span>'
            f'<div class="sn">{n:02d}</div><div class="sl">{html.escape(s.get("title",""))}</div></div>'
        )
    return (
        '<section class="intro">\n'
        f'    <div class="kicker">{html.escape(intro.get("kicker", "L\'histoire"))}</div>\n'
        f'    <h2>{html.escape(intro.get("title", ""))}</h2>\n'
        f'    <p class="lede">{html.escape(intro.get("lede", ""))}</p>\n'
        + ('    <div class="cast">\n' + "\n".join(cast) + "\n    </div>\n" if cast else "")
        + '    <div class="journey">\n' + "\n".join(steps) + "\n    </div>\n"
        "</section>\n\n"
    )


def _chapter_section(title: str, number: int) -> str:
    """Séparateur narratif quand la story change de persona, de marché ou de temporalité."""
    return (
        '<section class="chapter">\n'
        f'    <div class="chapter-num">Chapitre {number:02d}</div>\n'
        f'    <h2>{html.escape(title)}</h2>\n'
        '</section>\n'
    )


def _desktop_frame_style(screen: dict) -> str:
    """Variables CSS du cadrage hub. Les valeurs restent facultatives et ont des défauts pitch-friendly."""
    display = screen.get("display") or {}
    mode = display.get("mode", "full")
    scale = float(display.get("scale", 0.5))
    x = float(display.get("x", 0))
    y = float(display.get("y", 0))
    source_width = float(display.get("source_width", 1440))
    source_height = float(display.get("source_height", 1100))
    crop_width = float(display.get("width", source_width if mode == "crop" else 1440))
    crop_height = float(display.get("height", 900 if mode == "crop" else 900))
    frame_width = float(display.get("frame_width", min(820, crop_width * scale)))
    frame_height = float(display.get("frame_height", crop_height * scale))
    values = {
        "--frame-w": f"{frame_width:g}px",
        "--frame-h": f"{frame_height:g}px",
        "--screen-left": f"{-x * scale:g}px",
        "--screen-top": f"{-13 - y * scale:g}px",
        "--screen-w": f"{source_width:g}px",
        "--screen-h": f"{source_height:g}px",
        "--screen-scale": f"{scale:g}",
    }
    return ";".join(f"{name}:{value}" for name, value in values.items())


def _act_section(s: dict, index: int) -> str:
    """Une section .act : récit (num/titre/desc/lien) + écran réel en iframe (cadre phone ou desktop)."""
    side = " right" if index % 2 else ""
    f = html.escape(s["file"])
    phone = s["template"] in PHONE_TEMPLATES
    open_link = f'<a class="open" href="{f}" target="_blank" aria-label="Ouvrir en plein écran"></a>'
    iframe = f'<div class="vp"><iframe src="{f}" loading="lazy" scrolling="no" title="{html.escape(s.get("title",""))}"></iframe></div>'
    if phone:
        frame = f'<div class="frame phone">{open_link}{iframe}</div>'
    else:
        url = html.escape(s.get("url", s.get("channel", "")))
        bar = f'<div class="bar"><i></i><i></i><i></i><span class="url">{url}</span></div>'
        frame = f'<div class="frame desktop" style="{_desktop_frame_style(s)}">{open_link}{bar}{iframe}</div>'
    transition = s.get("transition", "")
    transition_block = (
        f'        <div class="transition"><b>Et maintenant</b>{html.escape(transition)}</div>\n'
        if transition else ""
    )
    return (
        f'<section class="act{side}">\n'
        '    <div class="story">\n'
        f'        <div class="num">{html.escape(s.get("act",""))}</div>\n'
        f'        <h2>{html.escape(s.get("title",""))}</h2>\n'
        f'        <p class="desc">{html.escape(s.get("desc",""))}</p>\n'
        + transition_block
        +
        f'        <a class="go" href="{f}" target="_blank">Ouvrir l\'écran '
        '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">'
        '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg></a>\n'
        '    </div>\n'
        f'    <div class="stage">{frame}</div>\n'
        '</section>\n'
    )


def _story_products(root: Path, screens: list) -> list:
    """Produits utilisés par les templates de la story, dans l'ordre du registre."""
    registry = json.loads((root / "registry" / "products.json").read_text(encoding="utf-8"))
    screen_registry = json.loads((root / "registry" / "screens.json").read_text(encoding="utf-8"))
    template_ids = {screen["template"] for screen in screens}
    product_ids = {
        product_id
        for registered_screen in screen_registry.get("screens", [])
        if registered_screen["id"] in template_ids
        for product_id in registered_screen.get("products", [])
    }
    return [item for item in registry.get("products", []) if item["id"] in product_ids]


def _license_block(products: list, selection: dict | None = None) -> str:
    """Mention discrète des produits et licences mobilisés par la story."""
    selection = selection or {}
    items = []
    for product in products:
        license_info = product.get("license") or {}
        notice = html.escape(license_info.get("notice", "Produit mobilisé dans cette story."))
        icon = product.get("icon")
        visual = (
            f'<img src="product-icons/{html.escape(icon)}" alt="">'
            if icon else
            f'<span class="license-monogram" aria-hidden="true">{html.escape(product["label"][:2].upper())}</span>'
        )
        items.append('<li class="license-product">' + visual
                     + f'<b>{html.escape(product["label"])}</b><small>{notice}</small></li>')
    if not items:
        return ""
    return (
        '<aside class="license-notice" aria-label="Produits et licences Salesforce utilisés">'
        '<span>Produits Salesforce :</span><ul class="license-products">' + "".join(items) + '</ul></aside>'
    )


def build_hub(template: str, brand: str, story_title: str, screens: list,
              tagline: str = "", intro: dict | None = None, thesis: str = "",
              products: list | None = None, license_selection: dict | None = None) -> str:
    """Assemble la page story : hero (placeholders) + intro + une section .act par écran."""
    sections = []
    previous_chapter = None
    chapter_number = 0
    for index, screen in enumerate(screens):
        chapter = screen.get("chapter")
        if chapter and chapter != previous_chapter:
            chapter_number += 1
            sections.append(_chapter_section(chapter, chapter_number))
            previous_chapter = chapter
        sections.append(_act_section(screen, index))
    body = _intro_block(intro or {}, screens) + "\n".join(sections)
    head, _, _ = template.partition("<!-- BUILD:")
    hub = head + body + "\n</body>\n</html>\n"
    thesis_block = f'<p class="thesis">{html.escape(thesis)}</p>' if thesis else ""
    license_block = _license_block(products or [], license_selection)
    return (hub.replace("{{BRAND}}", html.escape(brand))
               .replace("{{STORY_TITLE}}", html.escape(story_title))
               .replace("{{TAGLINE}}", html.escape(tagline or ""))
               .replace("{{THESIS_BLOCK}}", thesis_block)
               .replace("{{LICENSE_BLOCK}}", license_block))


def build_presenter_notes(manifest: dict) -> str:
    """Notes internes prêtes à pitcher, dérivées du même contrat causal que le hub."""
    lines = [
        f'# Notes présentateur — {manifest.get("brand", "")}',
        "",
        f'## {manifest.get("story_title", "Story")}',
        "",
    ]
    if manifest.get("thesis"):
        lines += [f'**Thèse de démo :** {manifest["thesis"]}', ""]
    products = _story_products(ROOT, manifest.get("screens", []))
    if products:
        lines += ["## Produits et licences", ""]
        selection = manifest.get("license_selection") or {}
        if selection.get("label"):
            lines += [f'**Choix de configuration :** {selection["label"]}', ""]
        for product in products:
            notice = (product.get("license") or {}).get("notice")
            lines.append(f'- **{product["label"]}**' + (f' — {notice}' if notice else ''))
        lines.append("")
    brief = manifest.get("brief") or {}
    if brief:
        labels = {
            "audience": "Audience",
            "objective": "Objectif",
            "duration_minutes": "Durée cible",
            "business_tension": "Tension métier",
            "salesforce_focus": "Produits Salesforce",
        }
        lines += ["## Brief validé", ""]
        for key, label in labels.items():
            value = brief.get(key)
            if value in (None, "", []):
                continue
            if isinstance(value, list):
                value = ", ".join(str(item) for item in value)
            suffix = " min" if key == "duration_minutes" else ""
            lines.append(f'- **{label} :** {value}{suffix}')
        lines.append("")
    current_chapter = None
    total_seconds = 0
    for index, screen in enumerate(manifest.get("screens", []), 1):
        chapter = screen.get("chapter")
        if chapter and chapter != current_chapter:
            lines += [f'## Chapitre — {chapter}', ""]
            current_chapter = chapter
        presenter = screen.get("presenter") or {}
        duration = int(presenter.get("duration_seconds", 45))
        total_seconds += duration
        lines += [
            f'### {screen.get("act", f"Acte {index}")} — {screen.get("title", "")}',
            "",
            f'**Durée indicative :** {duration} s',
            "",
        ]
        fields = [
            ("Déclencheur", screen.get("trigger")),
            ("Message clé", presenter.get("message") or screen.get("result")),
            ("À montrer", presenter.get("show")),
            ("Résultat visible", screen.get("result")),
            ("Transition", screen.get("transition")),
            ("Question client", presenter.get("question")),
        ]
        for label, value in fields:
            if value:
                lines += [f'**{label} :** {value}', ""]
    lines += ["---", "", f'**Durée commentée estimée :** {total_seconds // 60} min {total_seconds % 60:02d} s', ""]
    assumptions = manifest.get("assumptions") or []
    facts = manifest.get("facts") or []
    if facts or assumptions:
        lines += ["## Faits et hypothèses", ""]
        for fact in facts:
            statement = fact.get("statement", "") if isinstance(fact, dict) else str(fact)
            source = fact.get("source") if isinstance(fact, dict) else None
            lines.append(f'- **Vérifié :** {statement}' + (f' — {source}' if source else ""))
        for assumption in assumptions:
            statement = assumption.get("statement", "") if isinstance(assumption, dict) else str(assumption)
            lines.append(f'- **Hypothèse de démo :** {statement}')
        lines.append("")
    return "\n".join(lines)


def build(manifest: dict, root: Path = ROOT) -> Path:
    try:
        validate_registry(root)
    except RegistryError as exc:
        raise SystemExit(f"ERREUR registre : {exc}") from exc
    slug = manifest["slug"]
    out = Path.cwd() / f"{slug}-story"
    out.mkdir(exist_ok=True)
    written = []

    # 1. shared.css avec tokens de marque
    css = (root / "assets" / "shared.css").read_text(encoding="utf-8")
    css = rewrite_tokens(css, manifest.get("tokens", {}), manifest.get("font_import"))
    (out / "shared.css").write_text(css, encoding="utf-8")
    written.append("shared.css")

    # Icônes produit officielles utilisées par l'encart licences du hub.
    story_products = _story_products(root, manifest["screens"])
    product_icons = sorted({product.get("icon") for product in story_products if product.get("icon")})
    if product_icons:
        icon_output = out / "product-icons"
        icon_output.mkdir(exist_ok=True)
        for icon in product_icons:
            source = root / "assets" / "product-icons" / icon
            if not source.is_file():
                raise SystemExit(f"ERREUR : icône produit introuvable : assets/product-icons/{icon}")
            shutil.copy(source, icon_output / icon)
            written.append(f"product-icons/{icon}")

    # 1b. assets fournis (logo + photos produit, quand le crawl échoue) : copiés tels quels.
    # manifest["assets"] = liste de chemins ; les écrans y réfèrent par basename (src="logo.png").
    for src in manifest.get("assets", []):
        p = Path(src).expanduser()
        if not p.is_file():
            raise SystemExit(f"ERREUR : asset introuvable : {src}")
        shutil.copy(p, out / p.name)
        written.append(p.name)

    # 2. un écran par acte
    leaks, wrap_warn = [], []
    rendered = {}  # file -> markup, pour scanner les portraits people/ après coup
    for s in manifest["screens"]:
        markup = (root / "templates" / f'{s["template"]}.html').read_text(encoding="utf-8")
        warns, markup = inject_slots(markup, s.get("slots", {}), s["template"])
        if "sf-avatar" not in s.get("slots", {}):
            markup = inject_story_avatar(markup, s, manifest.get("intro", {}))
        wrap_warn += [f"{s['file']} · {w.split(' · ',1)[1]}" for w in warns]
        # ponytail: garde-fou marque d'exemple. Un wordmark "Nova" restant = un SLOT
        # structuré (nav/pdp/landing/email) omis dans le manifest → marque d'exemple qui fuite.
        if "Nova" in markup:
            leaks.append(s["file"])
        if 'class="lightning"' in markup and "lightning-header.js" not in markup:
            markup = markup.replace("</body>", '<script src="lightning-header.js"></script>\n</body>')
        (out / s["file"]).write_text(markup, encoding="utf-8")
        rendered[s["file"]] = markup
        written.append(s["file"])

    # 2a. kit de composants Lightning : copié UNIQUEMENT si un écran pose des <lc-*>.
    # Bundle JS classique + CSS → chargés en <script>/<link> par les templates lightning-* (file:// OK).
    if any("<lc-" in mk for mk in rendered.values()):
        (out / "lightning-kit.js").write_text(bundle_kit_js(), encoding="utf-8")
        shutil.copy(KIT / "lightning-components.css", out / "lightning-kit.css")
        written += ["lightning-kit.js", "lightning-kit.css"]

    # 2a bis. Chrome Salesforce commune : ordre et icônes globales identiques sur tout écran Lightning.
    if any('class="lightning"' in mk for mk in rendered.values()):
        shutil.copy(root / "assets" / "lightning-header.js", out / "lightning-header.js")
        written.append("lightning-header.js")

    # 2b. portraits fictifs de la banque assets/people/ RÉELLEMENT référencés (src="people/xxx").
    # On ne copie que ceux utilisés → aucun poids mort dans le site généré. Le hub (cast[].image)
    # peut aussi y pointer, donc on scanne écrans + manifest sérialisé.
    haystack = "".join(rendered.values()) + json.dumps(manifest, ensure_ascii=False)
    used = set(re.findall(r'people/([\w.-]+\.(?:jpg|jpeg|png|webp))', haystack))
    if used:
        (out / "people").mkdir(exist_ok=True)
        for name in sorted(used):
            src = root / "assets" / "people" / name
            if not src.is_file():
                raise SystemExit(f"ERREUR : portrait people/{name} introuvable (voir assets/people/).")
            shutil.copy(src, out / "people" / name)
            written.append(f"people/{name}")

    # 3. hub
    hub_tpl = (root / "assets" / "index.template.html").read_text(encoding="utf-8")
    hub = build_hub(hub_tpl, manifest.get("brand", ""), manifest.get("story_title", ""),
                    manifest["screens"], manifest.get("tagline", ""), manifest.get("intro"),
                    manifest.get("thesis", ""), story_products,
                    manifest.get("license_selection"))
    (out / "index.html").write_text(hub, encoding="utf-8")
    written.append("index.html")

    # 4. notes présentateur : livrable interne séparé, jamais affiché au client dans le hub.
    (out / "presenter-notes.md").write_text(build_presenter_notes(manifest), encoding="utf-8")
    written.append("presenter-notes.md")
    (out / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    written.append("build-manifest.json")

    # Les champs narratifs restent rétrocompatibles, mais leur absence doit être visible :
    # ils ont un impact direct sur le pitch, contrairement à une simple validation technique.
    narrative_warnings = []
    if not manifest.get("thesis"):
        narrative_warnings.append("thèse de démo absente")
    licensed_products = [product["label"] for product in _story_products(root, manifest["screens"])
                         if (product.get("license") or {}).get("category") in {"industry-cloud", "add-on"}]
    selection = manifest.get("license_selection") or {}
    if licensed_products and not selection.get("confirmed"):
        narrative_warnings.append(
            "choix de licence ou add-on non confirmé : " + ", ".join(licensed_products)
        )
    for index, screen in enumerate(manifest.get("screens", []), 1):
        missing = [key for key in ("trigger", "result", "transition") if not screen.get(key)]
        if missing:
            narrative_warnings.append(
                f'acte {index} « {screen.get("title", "sans titre")} » : ' + ", ".join(missing) + " absent(s)"
            )

    print(f"✓ {len(written)} fichiers écrits dans {out}/")
    for f in written:
        print(f"  - {f}")
    if leaks:
        print(f"\n⚠ marque d'exemple « Nova » encore présente dans : {', '.join(leaks)}")
        print("  → renseigne les SLOTs structurés (nav/pdp/landing/email) de ces écrans dans le manifest.")
    if wrap_warn:
        print("\n⚠ wrapper de tête avalé (le style du conteneur sera perdu) :")
        for w in wrap_warn:
            print(f"  - {w}")
        print("  → reprends le bloc d'exemple du template : garde son <div class=\"…\"> d'ouverture.")
    if narrative_warnings:
        print("\n⚠ contrat narratif incomplet (le build reste autorisé) :")
        for warning in narrative_warnings:
            print(f"  - {warning}")
        print("  → complète thesis + trigger/result/transition pour obtenir une démo plus facile à pitcher.")
    print(f"\nOuvre {out}/index.html dans un navigateur.")
    return out


def selfcheck():
    """Manifest minimal → assert injection + tokens + hub. Nettoie derrière lui."""
    m = {
        "brand": "TestCo", "slug": "__selfcheck", "story_title": "Parcours test",
        "tokens": {"--accent": "#ff0000"},
        "tagline": "TAGLINE_INJECTEE",
        "thesis": "THESE_INJECTEE",
        "license_selection": {"mode": "industry-cloud", "label": "CONFIGURATION_TEST", "confirmed": True},
        "brief": {"audience": "Direction", "duration_minutes": 5,
                  "salesforce_focus": ["Data Cloud", "Agentforce"]},
        "intro": {"title": "INTRO_TITRE", "lede": "intro lede",
                  "cast": [{"name": "Camille", "role": "La cliente", "bio": "bio", "image": "people/femme-1.jpg"},
                           {"name": "Alex", "role": "Agent de service", "bio": "bio", "image": "people/homme-1.jpg"}]},
        "screens": [
            {"file": "acte1-instagram.html", "template": "instagram", "channel": "Instagram",
             "chapter": "CHAPITRE_TEST", "act": "Acte 1 · Test", "title": "Pub test", "desc": "desc test",
             "trigger": "DECLENCHEUR_TEST", "result": "RESULTAT_TEST", "transition": "TRANSITION_TEST",
             "presenter": {"duration_seconds": 30, "show": "MONTRER_TEST"}, "animated": True,
             "slots": {"title": "TITRE_INJECTE", "why": "POURQUOI_INJECTE"}},
            {"file": "acte2-site.html", "template": "site-ecommerce", "channel": "sezane.com",
             "act": "Acte 2 · Test", "title": "Fiche", "desc": "desc2", "url": "test.com/produit",
             "trigger": "trigger2", "result": "result2", "transition": "transition2",
             "display": {"mode": "crop", "scale": 0.6, "x": 100, "y": 50, "height": 600},
              "slots": {}},
            {"file": "acte3-salesforce.html", "template": "consumer-service-account", "channel": "Salesforce",
             "act": "Acte 3 · Test", "title": "Compte", "desc": "desc3",
             "trigger": "trigger3", "result": "result3", "transition": "transition3",
             "persona": "Alex", "slots": {}},
        ],
    }
    prev = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        import os
        os.chdir(tmp)
        (Path(tmp) / "logo.png").write_bytes(b"\x89PNG\r\n")  # faux asset à copier
        m["assets"] = ["logo.png"]
        try:
            out = build(m, root=ROOT)
            assert (out / "logo.png").is_file(), "asset fourni non copié"
            assert (out / "people" / "femme-1.jpg").is_file(), "portrait people/ référencé non copié"
            assert (out / "people" / "homme-1.jpg").is_file(), "portrait du persona Salesforce non copié"
            css = (out / "shared.css").read_text(encoding="utf-8")
            assert "#ff0000" in css, "token accent non réécrit"
            screen = (out / "acte1-instagram.html").read_text(encoding="utf-8")
            assert "TITRE_INJECTE" in screen, "SLOT title non injecté"
            assert "POURQUOI_INJECTE" in screen, "SLOT why non injecté"
            hub = (out / "index.html").read_text(encoding="utf-8")
            assert "TAGLINE_INJECTEE" in hub, "tagline hero non injectée"
            assert "THESE_INJECTEE" in hub, "thèse hero non injectée"
            assert "Produits Salesforce" in hub and "Consumer Goods Cloud" in hub, \
                "produits/licences absents du hub"
            assert "INTRO_TITRE" in hub and 'src="people/femme-1.jpg"' in hub, "section intro/personnage manquante"
            assert "CHAPITRE_TEST" in hub and "Chapitre 01" in hub, "séparateur de chapitre manquant"
            assert "TRANSITION_TEST" in hub, "transition narrative manquante du hub"
            assert '<span class="sl">Pub test</span>' or "Pub test" in hub, "titre écran absent du récit"
            # écran 1 (instagram) = cadre téléphone ; écran 2 (site-ecommerce) = cadre desktop, côté alterné
            assert 'class="frame phone"' in hub, "cadre téléphone manquant"
            assert 'class="frame desktop"' in hub and 'class="act right"' in hub, "cadre desktop / alternance manquant"
            assert "--screen-scale:0.6" in hub and "--screen-left:-60px" in hub, "cadrage desktop non appliqué"
            assert 'src="acte1-instagram.html"' in hub, "iframe de l'écran manquante dans la story"
            salesforce = (out / "acte3-salesforce.html").read_text(encoding="utf-8")
            assert '<img class="ln-avatar" src="people/homme-1.jpg" alt="">' in salesforce, \
                "avatar du persona Salesforce non injecté"
            assert 'src="lightning-header.js"' in salesforce, "header Lightning non injecté"
            notes = (out / "presenter-notes.md").read_text(encoding="utf-8")
            assert "THESE_INJECTEE" in notes and "MONTRER_TEST" in notes, "notes présentateur incomplètes"
            assert "0 min 120 s" not in notes and "2 min 00 s" in notes, "durée présentateur mal calculée"
            saved_manifest = json.loads((out / "build-manifest.json").read_text(encoding="utf-8"))
            assert saved_manifest["thesis"] == "THESE_INJECTEE", "manifest de build absent ou altéré"
            # SLOT inconnu → doit lever
            try:
                inject_slots("<x/>", {"nope": "y"}, "instagram")
                raise AssertionError("SLOT inconnu aurait dû lever")
            except SystemExit:
                pass
            # libellé de SLOT avec un `>` (« garde le <script JSON> ») ET sur plusieurs lignes → match
            _, m2 = inject_slots(
                "<!-- SLOT: x ─ garde le <script JSON>\n     sur 2 lignes -->OLD<!-- /SLOT: x -->",
                {"x": "NEW"}, "t")
            assert "NEW" in m2 and "OLD" not in m2, "SLOT à libellé multi-ligne avec `>` non injecté"
            # garde-fou wrapper avalé : `why` sans <div class="why"> → warning
            tpl = (ROOT / "templates" / "instagram.html").read_text(encoding="utf-8")
            warns, _ = inject_slots(tpl, {"why": "<b>texte nu sans wrapper</b>"}, "instagram")
            assert any("why" in w for w in warns), "wrapper avalé non détecté"
            # à l'inverse, avec le bon wrapper → aucun warning
            warns2, _ = inject_slots(tpl, {"why": '<div class="why">ok</div>'}, "instagram")
            assert not warns2, "faux positif : wrapper correct signalé"
            # kit Lightning : le bundle retire import/export et NE copie que si un écran pose des <lc-*>
            js = bundle_kit_js()
            assert "export " not in js and not re.search(r"^\s*import\s", js, re.M), "import/export non retiré du bundle"
            assert "customElements.define" in js, "définitions de composants absentes du bundle"
            assert (out / "lightning-kit.js").exists(), "kit absent avec un écran qui utilise <lc-*>"
            assert (out / "lightning-header.js").exists(), "header Lightning absent avec un écran Salesforce"
            # franc­isation : le FR est là, l'EN codé en dur a disparu, ET le filtre carte reste cohérent
            assert ">Optimiser la tournée<" in js and ">Voir le détail<" in js, "libellés FS non traduits"
            assert ">Optimize Schedule<" not in js and ">View Details<" not in js, "libellé EN encore présent"
            assert "['Tous', ...statuses]" in js and "filter === 'Tous'" in js, "filtre carte non traduit (cohérence affichage/logique)"
            assert "'All'" not in js, "sentinelle 'All' orpheline → filtre carte cassé"
            assert "'terminé'" in js and "'critique'" in js and "'trajet'" in js, "statusClass ne reconnaît pas les statuts FR (badges tous bleus)"
            # re-sync : aucune collision de noms top-level (sinon SyntaxError → tout le kit tombe en file://)
            assert not _top_level_dupes(js), f"collision top-level dans le bundle : {_top_level_dupes(js)}"
            assert "const definitions =" not in js, "map d'enregistrement `definitions` non isolée par fichier"
            assert "lc-revenue-quote-pricing" in js, "composants Revenue Cloud absents du bundle"
            assert 'data-revenue-config-total' in js, "total du configurateur non pilotable"
            assert 'aria-pressed="${index === activeCategory}"' in js, "état des catégories Revenue non exposé"
        finally:
            os.chdir(prev)
    print("selfcheck OK")


def main():
    ap = argparse.ArgumentParser(description="Assemble un site salesforce-holodeck-creator depuis un manifest JSON.")
    ap.add_argument("manifest", nargs="?", help="chemin du manifest JSON, ou '-' pour stdin")
    ap.add_argument("--selfcheck", action="store_true", help="lance l'auto-vérification et quitte")
    args = ap.parse_args()
    if args.selfcheck:
        selfcheck()
        return
    if not args.manifest:
        ap.error("fournis un manifest JSON (ou --selfcheck)")
    raw = sys.stdin.read() if args.manifest == "-" else Path(args.manifest).read_text(encoding="utf-8")
    build(json.loads(raw))


if __name__ == "__main__":
    main()
