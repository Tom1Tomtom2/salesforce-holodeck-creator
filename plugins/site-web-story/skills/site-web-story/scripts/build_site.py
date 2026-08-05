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
        frame = f'<div class="frame desktop">{open_link}{bar}{iframe}</div>'
    return (
        f'<section class="act{side}">\n'
        '    <div class="story">\n'
        f'        <div class="num">{html.escape(s.get("act",""))}</div>\n'
        f'        <h2>{html.escape(s.get("title",""))}</h2>\n'
        f'        <p class="desc">{html.escape(s.get("desc",""))}</p>\n'
        f'        <a class="go" href="{f}" target="_blank">Ouvrir l\'écran '
        '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">'
        '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg></a>\n'
        '    </div>\n'
        f'    <div class="stage">{frame}</div>\n'
        '</section>\n'
    )


def build_hub(template: str, brand: str, story_title: str, screens: list,
              tagline: str = "", intro: dict | None = None) -> str:
    """Assemble la page story : hero (placeholders) + intro + une section .act par écran."""
    body = _intro_block(intro or {}, screens) + "\n".join(_act_section(s, i) for i, s in enumerate(screens))
    head, _, _ = template.partition("<!-- BUILD:")
    hub = head + body + "\n</body>\n</html>\n"
    return (hub.replace("{{BRAND}}", html.escape(brand))
               .replace("{{STORY_TITLE}}", html.escape(story_title))
               .replace("{{TAGLINE}}", html.escape(tagline or "")))


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
                    manifest["screens"], manifest.get("tagline", ""), manifest.get("intro"))
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
        "tagline": "TAGLINE_INJECTEE",
        "intro": {"title": "INTRO_TITRE", "lede": "intro lede",
                  "cast": [{"name": "Camille", "role": "La cliente", "bio": "bio", "image": "people/femme-1.jpg"}]},
        "screens": [
            {"file": "acte1-instagram.html", "template": "instagram", "channel": "Instagram",
             "act": "Acte 1 · Test", "title": "Pub test", "desc": "desc test", "animated": True,
             "slots": {"title": "TITRE_INJECTE", "why": "POURQUOI_INJECTE"}},
            {"file": "acte2-site.html", "template": "site-ecommerce", "channel": "sezane.com",
             "act": "Acte 2 · Test", "title": "Fiche", "desc": "desc2", "url": "test.com/produit",
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
            assert "INTRO_TITRE" in hub and 'src="people/femme-1.jpg"' in hub, "section intro/personnage manquante"
            assert '<span class="sl">Pub test</span>' or "Pub test" in hub, "titre écran absent du récit"
            # écran 1 (instagram) = cadre téléphone ; écran 2 (site-ecommerce) = cadre desktop, côté alterné
            assert 'class="frame phone"' in hub, "cadre téléphone manquant"
            assert 'class="frame desktop"' in hub and 'class="act right"' in hub, "cadre desktop / alternance manquant"
            assert 'src="acte1-instagram.html"' in hub, "iframe de l'écran manquante dans la story"
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
