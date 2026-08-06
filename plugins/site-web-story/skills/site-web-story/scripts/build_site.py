#!/usr/bin/env python3
"""Assemble un site de démo `site-web-story` à partir d'un manifest JSON.

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
PHONE_TEMPLATES = {"instagram", "whatsapp", "landing-capture", "client-app"}


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


def build_hub(template: str, brand: str, story_title: str, screens: list,
              tagline: str = "", intro: dict | None = None, thesis: str = "") -> str:
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
    return (hub.replace("{{BRAND}}", html.escape(brand))
               .replace("{{STORY_TITLE}}", html.escape(story_title))
               .replace("{{TAGLINE}}", html.escape(tagline or ""))
               .replace("{{THESIS_BLOCK}}", thesis_block))


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
    slug = manifest["slug"]
    out = Path.cwd() / f"{slug}-story"
    out.mkdir(exist_ok=True)
    written = []

    # 1. shared.css avec tokens de marque
    css = (root / "assets" / "shared.css").read_text(encoding="utf-8")
    css = rewrite_tokens(css, manifest.get("tokens", {}), manifest.get("font_import"))
    (out / "shared.css").write_text(css, encoding="utf-8")
    written.append("shared.css")

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
        wrap_warn += [f"{s['file']} · {w.split(' · ',1)[1]}" for w in warns]
        # ponytail: garde-fou marque d'exemple. Un wordmark "Nova" restant = un SLOT
        # structuré (nav/pdp/landing/email) omis dans le manifest → marque d'exemple qui fuite.
        if "Nova" in markup:
            leaks.append(s["file"])
        (out / s["file"]).write_text(markup, encoding="utf-8")
        rendered[s["file"]] = markup
        written.append(s["file"])

    # 2a. kit de composants Lightning : copié UNIQUEMENT si un écran pose des <lc-*>.
    # Bundle JS classique + CSS → chargés en <script>/<link> par les templates lightning-* (file:// OK).
    if any("<lc-" in mk for mk in rendered.values()):
        (out / "lightning-kit.js").write_text(bundle_kit_js(), encoding="utf-8")
        shutil.copy(KIT / "lightning-components.css", out / "lightning-kit.css")
        written += ["lightning-kit.js", "lightning-kit.css"]

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
                    manifest.get("thesis", ""))
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
        "brief": {"audience": "Direction", "duration_minutes": 5,
                  "salesforce_focus": ["Data Cloud", "Agentforce"]},
        "intro": {"title": "INTRO_TITRE", "lede": "intro lede",
                  "cast": [{"name": "Camille", "role": "La cliente", "bio": "bio", "image": "people/femme-1.jpg"}]},
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
            css = (out / "shared.css").read_text(encoding="utf-8")
            assert "#ff0000" in css, "token accent non réécrit"
            screen = (out / "acte1-instagram.html").read_text(encoding="utf-8")
            assert "TITRE_INJECTE" in screen, "SLOT title non injecté"
            assert "POURQUOI_INJECTE" in screen, "SLOT why non injecté"
            hub = (out / "index.html").read_text(encoding="utf-8")
            assert "TAGLINE_INJECTEE" in hub, "tagline hero non injectée"
            assert "THESE_INJECTEE" in hub, "thèse hero non injectée"
            assert "INTRO_TITRE" in hub and 'src="people/femme-1.jpg"' in hub, "section intro/personnage manquante"
            assert "CHAPITRE_TEST" in hub and "Chapitre 01" in hub, "séparateur de chapitre manquant"
            assert "TRANSITION_TEST" in hub, "transition narrative manquante du hub"
            assert '<span class="sl">Pub test</span>' or "Pub test" in hub, "titre écran absent du récit"
            # écran 1 (instagram) = cadre téléphone ; écran 2 (site-ecommerce) = cadre desktop, côté alterné
            assert 'class="frame phone"' in hub, "cadre téléphone manquant"
            assert 'class="frame desktop"' in hub and 'class="act right"' in hub, "cadre desktop / alternance manquant"
            assert "--screen-scale:0.6" in hub and "--screen-left:-60px" in hub, "cadrage desktop non appliqué"
            assert 'src="acte1-instagram.html"' in hub, "iframe de l'écran manquante dans la story"
            notes = (out / "presenter-notes.md").read_text(encoding="utf-8")
            assert "THESE_INJECTEE" in notes and "MONTRER_TEST" in notes, "notes présentateur incomplètes"
            assert "0 min 75 s" not in notes and "1 min 15 s" in notes, "durée présentateur mal calculée"
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
            assert not (out / "lightning-kit.js").exists(), "kit copié alors qu'aucun écran n'utilise <lc-*>"
            # franc­isation : le FR est là, l'EN codé en dur a disparu, ET le filtre carte reste cohérent
            assert ">Optimiser la tournée<" in js and ">Voir le détail<" in js, "libellés FS non traduits"
            assert ">Optimize Schedule<" not in js and ">View Details<" not in js, "libellé EN encore présent"
            assert "['Tous', ...statuses]" in js and "filter === 'Tous'" in js, "filtre carte non traduit (cohérence affichage/logique)"
            assert "'All'" not in js, "sentinelle 'All' orpheline → filtre carte cassé"
            assert "'terminé'" in js and "'critique'" in js and "'trajet'" in js, "statusClass ne reconnaît pas les statuts FR (badges tous bleus)"
            # re-sync : aucune collision de noms top-level (sinon SyntaxError → tout le kit tombe en file://)
            assert not _top_level_dupes(js), f"collision top-level dans le bundle : {_top_level_dupes(js)}"
            assert "const definitions =" not in js, "map d'enregistrement `definitions` non isolée par fichier"
        finally:
            os.chdir(prev)
    print("selfcheck OK")


def main():
    ap = argparse.ArgumentParser(description="Assemble un site site-web-story depuis un manifest JSON.")
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
