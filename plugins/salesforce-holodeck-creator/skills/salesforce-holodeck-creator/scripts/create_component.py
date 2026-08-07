#!/usr/bin/env python3
"""Scaffolde un composant Holodeck classifié et conforme à la charte.

Le script crée une source JS isolée, un squelette CSS, une fixture de catalogue et
l'entrée registry/components.json. Il refuse toute taxonomie ou association
job/produit inconnue avant d'écrire.
"""
import argparse
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from validate_registry import RegistryError, validate_registry


ROOT = Path(__file__).resolve().parent.parent


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _kebab(value: str, label: str) -> str:
    value = value.strip().lower()
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", value):
        raise ValueError(f"{label} doit être en kebab-case : {value!r}")
    return value


def _class_name(component_id: str) -> str:
    return "".join(part.capitalize() for part in component_id.split("-"))


def _csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


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


def _component_source(component_id: str, class_name: str, label: str, surface: str) -> str:
    js_label = json.dumps(label, ensure_ascii=False)
    heading_start = (
        '<div class="lc-panel__heading"><span class="lc-object-icon lc-object-icon--activity" '
        'aria-hidden="true">${lcIcon(\'activity\')}</span><div>'
    )
    heading_end = "</div></div>"
    return f"""import {{ JsonComponent, escapeHtml, lcIcon }} from './lightning-components.js';

class {class_name} extends JsonComponent {{
  render() {{
    const data = this.data;
    const titleId = `${{this.id || '{component_id[3:]}'}}-title`;
    this.innerHTML = `
      <section class=\"lc-panel {component_id}\" aria-labelledby=\"${{titleId}}\">
        <div class=\"lc-panel__header\">
          {heading_start}
            <h2 class=\"lc-panel__title\" id=\"${{titleId}}\">${{escapeHtml(data.title || {js_label})}}</h2>
            <div class=\"lc-panel__meta\">${{escapeHtml(data.meta || '')}}</div>
          {heading_end}
          <div class=\"lc-panel__actions\">
            <button class=\"lc-button lc-button--brand\" type=\"button\" data-component-action>
              ${{escapeHtml(data.actionLabel || 'Continuer')}}
            </button>
          </div>
        </div>
        <div class=\"{component_id}__body\">
          <p>${{escapeHtml(data.description || 'Décris ici la valeur métier du composant.')}}</p>
        </div>
      </section>`;
    this.querySelector('[data-component-action]').addEventListener('click', () =>
      this.emitAction(data.action || '{component_id[3:]}-continue'));
  }}
}}

const definitions = {{
  '{component_id}': {class_name},
}};

for (const [name, constructor] of Object.entries(definitions)) {{
  if (!customElements.get(name)) customElements.define(name, constructor);
}}
"""


def _component_css(component_id: str) -> str:
    return f"""

/* Community component: {component_id} */
{component_id} {{ min-width: 0; display: block; }}
.{component_id}__body {{
  padding: 16px;
  color: var(--lc-text);
  background: var(--lc-surface);
}}
.{component_id}__body p {{ margin: 0; line-height: 1.5; }}
"""


def _insert_registry_entry(text: str, entry: dict) -> str:
    marker = "\n  ]\n}"
    if marker not in text:
        raise ValueError("format inattendu de registry/components.json")
    serialized = json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
    return text.replace(marker, f",\n    {serialized}{marker}", 1)


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
        # Une restauration de secours plus simple vaut mieux qu'un fichier partagé partiellement modifié.
        path.write_text(text, encoding="utf-8")


def create_component(root: Path, *, component_id: str, label: str, job: str,
                     products: list[str], surface: str, scope: str, industries: list[str],
                     description: str, dry_run: bool = False) -> dict:
    component_id = component_id if component_id.startswith("lc-") else f"lc-{component_id}"
    component_id = "lc-" + _kebab(component_id[3:], "id")
    if not label.strip():
        raise ValueError("label est obligatoire")
    taxonomy = _load(root / "registry" / "taxonomy.json")
    product_data = _load(root / "registry" / "products.json")["products"]
    industry_data = _load(root / "registry" / "industries.json")["industries"]
    component_data = _load(root / "registry" / "components.json")
    known_products = {item["id"]: item for item in product_data}
    known_industries = {item["id"] for item in industry_data}
    known_surfaces = {item["id"] for item in taxonomy["surfaces"]}

    if job not in taxonomy["jobs"]:
        raise ValueError(f"job inconnu : {job}")
    if surface not in known_surfaces:
        raise ValueError(f"surface inconnue : {surface}")
    if scope not in {"cross-industry", "industry"}:
        raise ValueError(f"scope inconnu : {scope}")
    unknown_products = sorted(set(products) - set(known_products))
    if unknown_products or not products:
        raise ValueError(f"produits inconnus ou absents : {unknown_products or products}")
    if not any(job in known_products[product]["jobs"] for product in products):
        raise ValueError(f"le job {job} n'est couvert par aucun produit sélectionné")
    unknown_industries = sorted(set(industries) - known_industries)
    if unknown_industries:
        raise ValueError(f"industries inconnues : {unknown_industries}")
    if scope == "industry" and not industries:
        raise ValueError("un composant sectoriel doit déclarer au moins une industrie")
    if scope == "cross-industry" and industries:
        raise ValueError("un composant transverse ne peut pas déclarer d'industrie")
    if any(item["id"] == component_id for item in component_data["components"]):
        raise ValueError(f"composant déjà catalogué : {component_id}")

    slug = component_id[3:]
    source_relative = f"assets/lightning-kit/community-{slug}-components.js"
    source = root / source_relative
    fixture_relative = f"registry/component-examples/{component_id}.json"
    fixture = root / fixture_relative
    if source.exists() or fixture.exists():
        raise ValueError(f"fichier déjà présent pour {component_id}")

    entry = {
        "id": component_id,
        "source": source_relative,
        "label": label.strip(),
        "job": job,
        "products": products,
        "surface": surface,
        "design_profile": "slds" if surface in {"lightning", "mobile"} else "brand",
        "status": "uncatalogued-screen",
    }
    if scope == "industry":
        entry["cross_industry"] = False
        entry["industries"] = industries
    fixture_data = {
        "title": label.strip(),
        "meta": f"{job} · {surface}",
        "description": description.strip() or "Décris ici la valeur métier du composant.",
        "actionLabel": "Continuer",
    }
    result = {
        "component": entry,
        "source": source_relative,
        "fixture": fixture_relative,
        "css": "assets/lightning-kit/lightning-components.css",
    }
    if dry_run:
        return result

    css_path = root / "assets" / "lightning-kit" / "lightning-components.css"
    registry_path = root / "registry" / "components.json"
    original_css = css_path.read_text(encoding="utf-8")
    original_registry = registry_path.read_text(encoding="utf-8")
    try:
        _atomic_write(source, _component_source(component_id, _class_name(component_id), label.strip(), surface))
        _atomic_write(css_path, original_css + _component_css(component_id))
        _atomic_write(fixture, json.dumps(fixture_data, indent=2, ensure_ascii=False) + "\n")
        _atomic_write(registry_path, _insert_registry_entry(original_registry, entry))
        validate_registry(root)
    except Exception:
        source.unlink(missing_ok=True)
        fixture.unlink(missing_ok=True)
        _restore(css_path, original_css)
        _restore(registry_path, original_registry)
        raise
    return result


def selfcheck() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "skill"
        shutil.copytree(
            ROOT,
            root,
            ignore=shutil.ignore_patterns(
                "*-story", "*-brand", "component-catalog", ".component-catalog.*", "__pycache__", "*.pyc"
            ),
        )
        result = create_component(
            root,
            component_id="lc-community-summary",
            label="Vue d'équipe\npartagée",
            job="assistance",
            products=["agentforce"],
            surface="lightning",
            scope="cross-industry",
            industries=[],
            description="Résumé contributif vérifié.",
        )
        assert (root / result["source"]).is_file()
        assert (root / result["fixture"]).is_file()
        registry = _load(root / "registry" / "components.json")
        assert any(item["id"] == "lc-community-summary" for item in registry["components"])
        generated_source = (root / result["source"]).read_text(encoding="utf-8")
        assert json.dumps("Vue d'équipe\npartagée", ensure_ascii=False) in generated_source
        assert "Vue d'équipe\npartagée" not in generated_source
        assert "lc-panel__heading" in generated_source
        assert "lcIcon('activity')" in generated_source
        assert "lc-object-icon" in generated_source
        validate_registry(root)
        source_path = root / result["source"]
        source_path.write_text(generated_source.replace("lcIcon('activity')", "'★'"), encoding="utf-8")
        try:
            validate_registry(root)
        except RegistryError as exc:
            assert "lcIcon" in str(exc) or "Unicode" in str(exc)
        else:
            raise AssertionError("un composant SLDS sans lcIcon() doit être rejeté")
    print("selfcheck OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="Crée un composant Holodeck classifié.")
    parser.add_argument("--id", dest="component_id")
    parser.add_argument("--label")
    parser.add_argument("--job")
    parser.add_argument("--products", help="identifiants séparés par des virgules")
    parser.add_argument("--surface")
    parser.add_argument("--scope", choices=("cross-industry", "industry"))
    parser.add_argument("--industries", default="", help="identifiants séparés par des virgules")
    parser.add_argument("--description", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()
    if args.selfcheck:
        selfcheck()
        return

    taxonomy = _load(ROOT / "registry" / "taxonomy.json")
    products = _load(ROOT / "registry" / "products.json")["products"]
    component_id = args.component_id or input("Id du composant (lc-...) : ").strip()
    label = args.label or input("Libellé humain : ").strip()
    job = _choose("Job métier", taxonomy["jobs"], args.job)
    product_value = args.products or input(
        "Produits, séparés par des virgules (" + ", ".join(item["id"] for item in products) + ") : "
    ).strip()
    surface = _choose("Surface", [item["id"] for item in taxonomy["surfaces"]], args.surface)
    scope = _choose("Scope", ["cross-industry", "industry"], args.scope)
    industries = _csv(args.industries)
    if scope == "industry" and not industries:
        industry_data = _load(ROOT / "registry" / "industries.json")["industries"]
        industries = _csv(input(
            "Industries, séparées par des virgules ("
            + ", ".join(item["id"] for item in industry_data) + ") : "
        ).strip())
    if scope == "cross-industry" and industries:
        parser.error("--industries est incompatible avec --scope cross-industry")
    result = create_component(
        ROOT,
        component_id=component_id,
        label=label,
        job=job,
        products=_csv(product_value),
        surface=surface,
        scope=scope,
        industries=industries,
        description=args.description,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not args.dry_run:
        print("\nProchaine étape : adapte le JS, le CSS et la fixture, puis crée un template qui expose le composant.")


if __name__ == "__main__":
    main()
