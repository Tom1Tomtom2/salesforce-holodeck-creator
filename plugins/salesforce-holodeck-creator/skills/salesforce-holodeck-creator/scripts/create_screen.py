#!/usr/bin/env python3
"""Crée un écran Holodeck classifié, composé et immédiatement buildable."""
import argparse
import html
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from validate_registry import validate_registry


ROOT = Path(__file__).resolve().parent.parent


def _component_surfaces(root: Path, screen_data: dict) -> dict[str, set[str]]:
    surfaces = {}
    for screen in screen_data["screens"]:
        template_text = (root / screen["template"]).read_text(encoding="utf-8")
        screen_surface = screen.get("surface") or (
            "mobile" if screen["format"] == "mobile" else "lightning" if 'class="lightning"' in template_text else "external"
        )
        for component_id in screen.get("components", []):
            surfaces.setdefault(component_id, set()).add(screen_surface)
    return surfaces


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _kebab(value: str, label: str) -> str:
    value = value.strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", value):
        raise ValueError(f"{label} doit être en kebab-case : {value!r}")
    return value


def _choose(prompt: str, values: list[str], supplied: str | None) -> str:
    if supplied:
        return supplied
    print(f"{prompt} :")
    for index, value in enumerate(values, 1):
        print(f"  {index}. {value}")
    answer = input("> ").strip()
    if answer.isdigit() and 1 <= int(answer) <= len(values):
        return values[int(answer) - 1]
    return answer


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def _restore(path: Path, text: str) -> None:
    try:
        _atomic_write(path, text)
    except Exception:
        path.write_text(text, encoding="utf-8")


def _insert_registry_entry(text: str, entry: dict) -> str:
    marker = "\n  ]\n}"
    if marker not in text:
        raise ValueError("format inattendu de registry/screens.json")
    serialized = json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
    return text.replace(marker, f",\n    {serialized}{marker}", 1)


def _component_examples(root: Path) -> dict[str, str]:
    examples = {}
    for template in sorted((root / "templates").glob("*.html")):
        text = template.read_text(encoding="utf-8")
        for component_id in re.findall(r"<(lc-[a-z0-9-]+)\b", text):
            if component_id in examples:
                continue
            match = re.search(
                rf"<{re.escape(component_id)}\b[^>]*>.*?</{re.escape(component_id)}\s*>",
                text,
                re.DOTALL,
            )
            if match:
                markup = match.group(0).strip()
                nested = [item for item in _actual_components(markup) if item != component_id]
                if not nested:
                    examples[component_id] = markup
    fixture_dir = root / "registry" / "component-examples"
    for fixture in sorted(fixture_dir.glob("*.json")) if fixture_dir.exists() else []:
        component_id = fixture.stem
        if component_id in examples:
            continue
        data = json.loads(fixture.read_text(encoding="utf-8"))
        payload = re.sub(r"</", r"<\/", json.dumps(data, ensure_ascii=False), flags=re.IGNORECASE)
        examples[component_id] = (
            f'<{component_id}>\n  <script type="application/json">{payload}</script>\n</{component_id}>'
        )
    return examples


def _slot(name: str, content: str, description: str = "ajuste uniquement les données JSON") -> str:
    return (
        f"<!-- SLOT: {name} - {description}. -->\n"
        f"{content}\n"
        f"<!-- /SLOT: {name} -->"
    )


def _lightning_shell(screen_id: str, label: str, components: list[str], examples: dict[str, str]) -> str:
    label = html.escape(label)
    blocks = []
    for component_id in components:
        slot_name = component_id[3:]
        blocks.append(_slot(slot_name, examples[component_id]))
    content = "\n\n    ".join(blocks) if blocks else _slot(
        "content", '<section class="screen-placeholder"><h1>Écran à composer</h1><p>Ajoute les composants métier de cet écran.</p></section>',
        "remplace le contenu de démonstration",
    )
    kit_css = '<link rel="stylesheet" href="lightning-kit.css">\n' if components else ""
    kit_js = '<script src="lightning-kit.js"></script>\n' if components else ""
    return f"""<!DOCTYPE html>
<!-- TEMPLATE - {label} (généré par create_screen.py). -->
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title><!-- SLOT: title -->{label}<!-- /SLOT: title --></title>
<link rel="stylesheet" href="shared.css">
{kit_css}<style>
body {{ background: var(--lc-page); min-height: 100vh; }}
.generated-page {{ width: min(1500px,100%); margin:auto; padding:18px 20px 72px; display:grid; gap:16px; }}
.screen-placeholder {{ min-height:320px; padding:32px; background:var(--lc-surface); border:1px solid var(--lc-border); border-radius:var(--lc-radius); }}
</style></head><body>
<div class="act-tag"><!-- SLOT: act-tag -->Acte 1 - {label}<!-- /SLOT: act-tag --></div>
<div class="lightning">
  <div class="ln-top">
    <!-- SLOT: sf-logo --><span class="ln-logo"><span class="brand"><span class="brand-mark">H</span> Holodeck</span></span><!-- /SLOT: sf-logo -->
    <div class="ln-search">Rechercher dans Salesforce...</div>
    <div class="ln-icons"><span aria-hidden="true">?</span><!-- SLOT: sf-avatar --><span class="ln-avatar"></span><!-- /SLOT: sf-avatar --></div>
  </div>
  <div class="ln-nav"><span class="ln-waffle" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></span><!-- SLOT: sf-app --><span class="ln-app">Salesforce</span><!-- /SLOT: sf-app --><!-- SLOT: sf-tabs --><div class="ln-tabs"><span class="ln-tab on">{label}</span></div><!-- /SLOT: sf-tabs --></div>
</div>
<main class="generated-page" data-screen="{screen_id}">
    {content}
</main>
{kit_js}</body></html>
"""


def _mobile_shell(screen_id: str, label: str, components: list[str], examples: dict[str, str]) -> str:
    label = html.escape(label)
    component_markup = "\n      ".join(examples[item] for item in components)
    content = component_markup or '<section class="mobile-placeholder"><h1>Écran mobile à composer</h1><p>Ajoute le parcours métier.</p></section>'
    kit_css = '<link rel="stylesheet" href="lightning-kit.css">\n' if components else ""
    kit_js = '<script src="lightning-kit.js"></script>\n' if components else ""
    return f"""<!DOCTYPE html>
<!-- TEMPLATE - {label} (généré par create_screen.py). -->
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title><!-- SLOT: title -->{label}<!-- /SLOT: title --></title>
<link rel="stylesheet" href="shared.css">
{kit_css}<style>
body {{ min-height:100vh; display:grid; place-items:center; background:#e8edf4; }}
.mobile-placeholder {{ min-height:520px; padding:28px 20px; background:#fff; }}
</style></head><body>
<div class="act-tag"><!-- SLOT: act-tag -->Acte 1 - {label}<!-- /SLOT: act-tag --></div>
<div class="phone" data-screen="{screen_id}"><div class="phone-notch"></div><div class="screen">
  {_slot('app', content, 'application mobile complète')}
</div></div>
{kit_js}</body></html>
"""


def _external_shell(screen_id: str, label: str, components: list[str], examples: dict[str, str]) -> str:
    label = html.escape(label)
    blocks = []
    for component_id in components:
        blocks.append(_slot(component_id[3:], examples[component_id]))
    content = "\n\n  ".join(blocks) if blocks else _slot(
        "content", '<section class="external-placeholder"><h1>Écran à composer</h1><p>Décris ici le moment du parcours.</p></section>',
        "remplace le contenu de démonstration",
    )
    kit_css = '<link rel="stylesheet" href="lightning-kit.css">\n' if components else ""
    kit_js = '<script src="lightning-kit.js"></script>\n' if components else ""
    return f"""<!DOCTYPE html>
<!-- TEMPLATE - {label} (généré par create_screen.py). -->
<html lang="fr"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title><!-- SLOT: title -->{label}<!-- /SLOT: title --></title>
<link rel="stylesheet" href="shared.css">
{kit_css}<style>
body {{ min-height:100vh; background:#f4f6f9; }}
.external-page {{ width:min(1180px,100%); margin:auto; padding:64px 24px; }}
.external-placeholder {{ min-height:520px; padding:48px; background:#fff; border-radius:18px; box-shadow:0 18px 48px #10213a18; }}
</style></head><body>
<div class="act-tag"><!-- SLOT: act-tag -->Acte 1 - {label}<!-- /SLOT: act-tag --></div>
<main class="external-page" data-screen="{screen_id}">
  {content}
</main>
{kit_js}</body></html>
"""


def _actual_slots(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"<!--\s*SLOT:\s*([\w-]+)", text)))


def _actual_components(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"<(lc-[a-z0-9-]+)\b", text)))


def _promote_components(text: str, component_ids: list[str]) -> str:
    updated = text
    for component_id in component_ids:
        pattern = re.compile(
            rf'(\{{[^{{}}]*"id"\s*:\s*"{re.escape(component_id)}"[^{{}}]*"status"\s*:\s*")uncatalogued-screen(")'
        )
        updated, count = pattern.subn(r"\1available\2", updated, count=1)
        if count == 0 and f'"id":"{component_id}"' not in updated:
            raise ValueError(f"entrée composant introuvable : {component_id}")
    json.loads(updated)
    return updated


def _example(screen_id: str, label: str, products: list[dict]) -> dict:
    result = {
        "brand": "Exemple Holodeck",
        "slug": f"{screen_id}-example",
        "story_title": label,
        "thesis": "Cet exemple vérifie que le nouvel écran peut être construit et présenté dans une story autonome.",
        "screens": [{
            "file": f"acte1-{screen_id}.html",
            "template": screen_id,
            "channel": label,
            "chapter": "Exemple",
            "act": "Acte 1 · Exemple",
            "title": label,
            "desc": "Exemple autonome du nouvel écran et de ses composants.",
            "trigger": "Le parcours atteint l'étape couverte par le nouvel écran.",
            "result": "La valeur métier principale est visible dans un écran buildable.",
            "transition": "Le parcours peut continuer avec le contexte produit conservé.",
            "slots": {},
        }],
    }
    if any(product.get("license", {}).get("category") in {"industry-cloud", "add-on"} for product in products):
        result["license_selection"] = {
            "mode": "unconfirmed",
            "label": "Configuration de licence à confirmer",
            "confirmed": False,
        }
    return result


def create_screen(root: Path, *, screen_id: str, label: str, format_name: str, surface: str,
                  job: str, products: list[str], scope: str, industries: list[str],
                  components: list[str], dry_run: bool = False) -> dict:
    validate_registry(root)
    screen_id = _kebab(screen_id, "id")
    if not label.strip():
        raise ValueError("label est obligatoire")
    if format_name not in {"mobile", "desktop"}:
        raise ValueError(f"format inconnu : {format_name}")
    taxonomy = _load(root / "registry" / "taxonomy.json")
    product_data = _load(root / "registry" / "products.json")["products"]
    industry_data = _load(root / "registry" / "industries.json")["industries"]
    component_data = _load(root / "registry" / "components.json")
    screen_data = _load(root / "registry" / "screens.json")
    known_component_surfaces = _component_surfaces(root, screen_data)
    known_products = {item["id"]: item for item in product_data}
    known_industries = {item["id"] for item in industry_data}
    known_components = {item["id"]: item for item in component_data["components"]}
    surfaces = {item["id"] for item in taxonomy["surfaces"]}
    if surface not in surfaces:
        raise ValueError(f"surface inconnue : {surface}")
    if surface == "lightning" and format_name != "desktop":
        raise ValueError("une surface lightning doit utiliser le format desktop")
    if surface == "mobile" and format_name != "mobile":
        raise ValueError("une surface mobile doit utiliser le format mobile")
    if job not in taxonomy["jobs"]:
        raise ValueError(f"job inconnu : {job}")
    if not products or sorted(set(products) - set(known_products)):
        raise ValueError("au moins un produit connu est obligatoire")
    if not any(job in known_products[item]["jobs"] for item in products):
        raise ValueError(f"le job {job} n'est couvert par aucun produit sélectionné")
    if scope not in {"cross-industry", "industry"}:
        raise ValueError(f"scope inconnu : {scope}")
    if sorted(set(industries) - known_industries):
        raise ValueError("une industrie sélectionnée est inconnue")
    if scope == "industry" and not industries:
        raise ValueError("un écran sectoriel doit déclarer une industrie")
    if scope == "cross-industry" and industries:
        raise ValueError("un écran transverse ne peut pas déclarer d'industrie")
    if len(components) != len(set(components)):
        raise ValueError("les composants ne peuvent pas être dupliqués")
    unknown_components = sorted(set(components) - set(known_components))
    if unknown_components:
        raise ValueError(f"composants inconnus : {unknown_components}")
    for component_id in components:
        component = known_components[component_id]
        component_cross_industry = component.get("cross_industry", component_data.get("defaults", {}).get("cross_industry", True))
        component_industries = set(component.get("industries", component_data.get("defaults", {}).get("industries", [])))
        if scope == "cross-industry" and not component_cross_industry:
            raise ValueError(f"composant sectoriel incompatible avec un écran transverse : {component_id}")
        if not component_cross_industry and not component_industries.intersection(industries):
            raise ValueError(f"industrie incompatible pour le composant {component_id}")
        component_surfaces = known_component_surfaces.get(component_id)
        if not component_surfaces:
            if component_id.startswith("lc-fs-mobile-"):
                component_surfaces = {"mobile"}
            elif any(product in {"commerce-cloud", "experience-cloud"} for product in component["products"]):
                component_surfaces = {"external"}
            else:
                component_surfaces = {component.get("surface", "lightning")}
        if surface not in component_surfaces:
            raise ValueError(f"surface incompatible pour le composant {component_id}")
        if not set(component["products"]).intersection(products):
            raise ValueError(f"aucun produit de l'écran ne couvre le composant {component_id}")
    if any(item["id"] == screen_id for item in screen_data["screens"]):
        raise ValueError(f"écran déjà catalogué : {screen_id}")

    template_path = root / "templates" / f"{screen_id}.html"
    example_path = root / "registry" / "examples" / f"{screen_id}.json"
    if template_path.exists() or example_path.exists():
        raise ValueError(f"fichier déjà présent pour {screen_id}")
    examples = _component_examples(root)
    missing_examples = sorted(set(components) - set(examples))
    if missing_examples:
        raise ValueError(f"composants sans exemple réutilisable : {missing_examples}")

    if surface == "lightning":
        template = _lightning_shell(screen_id, label.strip(), components, examples)
    elif format_name == "mobile":
        template = _mobile_shell(screen_id, label.strip(), components, examples)
    else:
        template = _external_shell(screen_id, label.strip(), components, examples)
    actual_components = _actual_components(template)
    entry = {
        "id": screen_id,
        "template": f"templates/{screen_id}.html",
        "label": label.strip(),
        "format": format_name,
        "surface": surface,
        "job": job,
        "products": products,
        "components": actual_components,
        "slots": _actual_slots(template),
        "status": "available",
    }
    if scope == "industry":
        entry["cross_industry"] = False
        entry["industries"] = industries
    example = _example(screen_id, label.strip(), [known_products[item] for item in products])
    result = {"screen": entry, "template": str(template_path.relative_to(root)), "example": str(example_path.relative_to(root))}
    if dry_run:
        return result

    screens_path = root / "registry" / "screens.json"
    components_path = root / "registry" / "components.json"
    original_screens = screens_path.read_text(encoding="utf-8")
    original_components = components_path.read_text(encoding="utf-8")
    written_screens = _insert_registry_entry(original_screens, entry)
    written_components = _promote_components(original_components, actual_components)
    try:
        _atomic_write(template_path, template)
        _atomic_write(example_path, json.dumps(example, indent=2, ensure_ascii=False) + "\n")
        _atomic_write(components_path, written_components)
        _atomic_write(screens_path, written_screens)
        validate_registry(root)
    except Exception:
        if template_path.exists() and template_path.read_text(encoding="utf-8") == template:
            template_path.unlink()
        if example_path.exists() and example_path.read_text(encoding="utf-8") == json.dumps(example, indent=2, ensure_ascii=False) + "\n":
            example_path.unlink()
        if components_path.read_text(encoding="utf-8") == written_components:
            _restore(components_path, original_components)
        if screens_path.read_text(encoding="utf-8") == written_screens:
            _restore(screens_path, original_screens)
        raise
    return result


def selfcheck() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "skill"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("*-story", "*-brand", "component-catalog", "__pycache__", "*.pyc"))
        result = create_screen(
            root,
            screen_id="community-summary",
            label="Synthèse communautaire",
            format_name="desktop",
            surface="lightning",
            job="forecasting",
            products=["sales-cloud"],
            scope="cross-industry",
            industries=[],
            components=["lc-forecast-summary"],
        )
        template = (root / result["template"]).read_text(encoding="utf-8")
        assert _actual_slots(template) == ["title", "act-tag", "sf-logo", "sf-avatar", "sf-app", "sf-tabs", "forecast-summary"]
        assert _actual_components(template) == ["lc-forecast-summary"]
        assert "Synthèse communautaire" in template
        escaped_result = create_screen(
            root,
            screen_id="escaped-label",
            label="Prévision <T4> & croissance",
            format_name="desktop",
            surface="external",
            job="forecasting",
            products=["sales-cloud"],
            scope="cross-industry",
            industries=[],
            components=[],
        )
        escaped_template = (root / escaped_result["template"]).read_text(encoding="utf-8")
        assert "Prévision &lt;T4&gt; &amp; croissance" in escaped_template
        assert "Prévision <T4>" not in escaped_template
        registry = _load(root / "registry" / "components.json")
        assert next(item for item in registry["components"] if item["id"] == "lc-forecast-summary")["status"] == "available"
        validate_registry(root)
        cwd = Path.cwd()
        try:
            os.chdir(tmp)
            from build_site import build
            output = build(_load(root / result["example"]), root=root)
            assert (output / "index.html").is_file()
            assert (output / "acte1-community-summary.html").is_file()
            assert (output / "lightning-kit.js").is_file()
            escaped_output = build(_load(root / escaped_result["example"]), root=root)
            assert (escaped_output / "acte1-escaped-label.html").is_file()
        finally:
            os.chdir(cwd)
        try:
            create_screen(
                root,
                screen_id="invalid-industry",
                label="Invalide <secteur>",
                format_name="desktop",
                surface="external",
                job="loan-origination",
                products=["financial-services-cloud"],
                scope="cross-industry",
                industries=[],
                components=["lc-loan-product-catalog"],
            )
        except ValueError as exc:
            assert "sectoriel" in str(exc)
        else:
            raise AssertionError("un composant sectoriel ne doit pas être exposé comme transverse")
    print("screen creator selfcheck OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crée un écran Holodeck classifié et buildable.")
    parser.add_argument("--id", dest="screen_id")
    parser.add_argument("--label")
    parser.add_argument("--format", dest="format_name", choices=("mobile", "desktop"))
    parser.add_argument("--surface")
    parser.add_argument("--job")
    parser.add_argument("--products")
    parser.add_argument("--scope", choices=("cross-industry", "industry"))
    parser.add_argument("--industries", default="")
    parser.add_argument("--components", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()
    if args.selfcheck:
        selfcheck()
        return
    taxonomy = _load(ROOT / "registry" / "taxonomy.json")
    product_data = _load(ROOT / "registry" / "products.json")["products"]
    screen_id = args.screen_id or input("Id de l'écran : ").strip()
    label = args.label or input("Libellé humain : ").strip()
    format_name = _choose("Format", ["desktop", "mobile"], args.format_name)
    surface = _choose("Surface", [item["id"] for item in taxonomy["surfaces"]], args.surface)
    job = _choose("Job métier", taxonomy["jobs"], args.job)
    products = args.products or input("Produits (" + ", ".join(item["id"] for item in product_data) + ") : ").strip()
    scope = _choose("Scope", ["cross-industry", "industry"], args.scope)
    industries = _csv(args.industries)
    if scope == "industry" and not industries:
        industries = _csv(input("Industries séparées par des virgules : ").strip())
    result = create_screen(
        ROOT,
        screen_id=screen_id,
        label=label,
        format_name=format_name,
        surface=surface,
        job=job,
        products=_csv(products),
        scope=scope,
        industries=industries,
        components=_csv(args.components),
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not args.dry_run:
        print("\nProchaine étape : adapte les SLOTs et documente l'écran dans references/screens.md.")


if __name__ == "__main__":
    main()
