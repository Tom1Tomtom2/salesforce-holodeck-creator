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
        # [^>]* borne l'ouverture au 1er `-->` (pas de `>` dans le libellé d'un SLOT).
        # groupe 2 = corps d'origine (l'exemple), pour comparer le wrapper de tête.
        pat = re.compile(
            r"(<!-- SLOT: " + re.escape(name) + r"(?![\w-])[^>]*-->)(.*?)(<!-- /SLOT)",
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


def build_hub(template: str, brand: str, story_title: str, screens: list) -> str:
    """Regénère les blocs .act/.screen depuis screens[], groupés par libellé d'acte."""
    blocks, i = [], 0
    while i < len(screens):
        act = screens[i].get("act", "")
        cards = []
        while i < len(screens) and screens[i].get("act", "") == act:
            s = screens[i]
            gif = '<span class="gif">▶ animé</span>' if s.get("animated") else ""
            cards.append(
                f'<a class="screen" href="{html.escape(s["file"])}">'
                f'<div class="n">{html.escape(s.get("channel", s.get("template", "")))}</div>'
                f'<div class="t">{html.escape(s.get("title", ""))}</div>'
                f'<div class="d">{html.escape(s.get("desc", ""))}</div>{gif}</a>'
            )
            i += 1
        blocks.append(
            f'    <div class="act">\n        <h2>{html.escape(act)}</h2>\n'
            f'        <div class="screens">\n            '
            + "\n            ".join(cards)
            + "\n        </div>\n    </div>"
        )
    # remplace le bloc .act d'exemple (entre le commentaire repère et </div></body>)
    head = template.split('<!-- Répéter ce bloc .act par acte de la story -->')[0]
    hub = head + "\n".join(blocks) + "\n\n</div>\n</body>\n</html>\n"
    hub = hub.replace("{{BRAND}}", html.escape(brand)).replace("{{STORY_TITLE}}", html.escape(story_title))
    return hub


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

    # 2. un écran par acte
    leaks, wrap_warn = [], []
    for s in manifest["screens"]:
        markup = (root / "templates" / f'{s["template"]}.html').read_text(encoding="utf-8")
        warns, markup = inject_slots(markup, s.get("slots", {}), s["template"])
        wrap_warn += [f"{s['file']} · {w.split(' · ',1)[1]}" for w in warns]
        # ponytail: garde-fou marque d'exemple. Un wordmark "Nova" restant = un SLOT
        # structuré (nav/pdp/landing/email) omis dans le manifest → marque d'exemple qui fuite.
        if "Nova" in markup:
            leaks.append(s["file"])
        (out / s["file"]).write_text(markup, encoding="utf-8")
        written.append(s["file"])

    # 3. hub
    hub_tpl = (root / "assets" / "index.template.html").read_text(encoding="utf-8")
    hub = build_hub(hub_tpl, manifest.get("brand", ""), manifest.get("story_title", ""), manifest["screens"])
    (out / "index.html").write_text(hub, encoding="utf-8")
    written.append("index.html")

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
    print(f"\nOuvre {out}/index.html dans un navigateur.")
    return out


def selfcheck():
    """Manifest minimal → assert injection + tokens + hub. Nettoie derrière lui."""
    m = {
        "brand": "TestCo", "slug": "__selfcheck", "story_title": "Parcours test",
        "tokens": {"--accent": "#ff0000"},
        "screens": [{
            "file": "acte1-instagram.html", "template": "instagram", "channel": "Instagram",
            "act": "Acte 1 · Test", "title": "Pub test", "desc": "desc test", "animated": True,
            "slots": {"title": "TITRE_INJECTE", "why": "POURQUOI_INJECTE"},
        }],
    }
    prev = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        import os
        os.chdir(tmp)
        try:
            out = build(m, root=ROOT)
            css = (out / "shared.css").read_text(encoding="utf-8")
            assert "#ff0000" in css, "token accent non réécrit"
            screen = (out / "acte1-instagram.html").read_text(encoding="utf-8")
            assert "TITRE_INJECTE" in screen, "SLOT title non injecté"
            assert "POURQUOI_INJECTE" in screen, "SLOT why non injecté"
            hub = (out / "index.html").read_text(encoding="utf-8")
            assert "acte1-instagram.html" in hub and "Pub test" in hub, "carte hub manquante"
            assert "▶ animé" in hub, "badge animé manquant"
            # SLOT inconnu → doit lever
            try:
                inject_slots("<x/>", {"nope": "y"}, "instagram")
                raise AssertionError("SLOT inconnu aurait dû lever")
            except SystemExit:
                pass
            # garde-fou wrapper avalé : `why` sans <div class="why"> → warning
            tpl = (ROOT / "templates" / "instagram.html").read_text(encoding="utf-8")
            warns, _ = inject_slots(tpl, {"why": "<b>texte nu sans wrapper</b>"}, "instagram")
            assert any("why" in w for w in warns), "wrapper avalé non détecté"
            # à l'inverse, avec le bon wrapper → aucun warning
            warns2, _ = inject_slots(tpl, {"why": '<div class="why">ok</div>'}, "instagram")
            assert not warns2, "faux positif : wrapper correct signalé"
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
