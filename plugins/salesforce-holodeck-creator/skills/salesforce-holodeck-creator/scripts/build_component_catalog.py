#!/usr/bin/env python3
"""Génère un catalogue filtrable à partir des registres et templates réels."""
import argparse
import html
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from build_site import bundle_kit_js
from validate_registry import validate_registry


ROOT = Path(__file__).resolve().parent.parent
CATALOG_MARKER = ".holodeck-component-catalog"
CATALOG_SIGNATURE = "salesforce-holodeck-component-catalog-v1\n"


def _load(root: Path, name: str) -> dict:
    return json.loads((root / "registry" / name).read_text(encoding="utf-8"))


def _examples(root: Path) -> dict[str, dict]:
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
                examples[component_id] = {
                    "markup": match.group(0).strip(),
                    "template": template.name,
                }
    fixture_dir = root / "registry" / "component-examples"
    for fixture in sorted(fixture_dir.glob("*.json")) if fixture_dir.exists() else []:
        component_id = fixture.stem
        if component_id in examples:
            continue
        data = json.loads(fixture.read_text(encoding="utf-8"))
        payload = re.sub(r"</", r"<\/", json.dumps(data, ensure_ascii=False), flags=re.IGNORECASE)
        examples[component_id] = {
            "markup": f'<{component_id}><script type="application/json">{payload}</script></{component_id}>',
            "template": f"fixture {fixture.name}",
        }
    return examples


def _options(items: list[dict], selected_label: str) -> str:
    return f'<option value="">{html.escape(selected_label)}</option>' + "".join(
        f'<option value="{html.escape(item["id"])}">{html.escape(item["label"])}</option>'
        for item in items
    )


def _catalog_html(root: Path) -> tuple[str, dict]:
    counts = validate_registry(root)
    components_data = _load(root, "components.json")
    products = _load(root, "products.json")["products"]
    industries = _load(root, "industries.json")["industries"]
    taxonomy = _load(root, "taxonomy.json")
    examples = _examples(root)
    defaults = components_data.get("defaults", {})
    product_labels = {item["id"]: item["label"] for item in products}
    industry_labels = {item["id"]: item["label"] for item in industries}
    cards = []
    available_without_example = []

    for component in sorted(components_data["components"], key=lambda item: (item["label"].casefold(), item["id"])):
        component_id = component["id"]
        example = examples.get(component_id)
        if component["status"] == "available" and not example:
            available_without_example.append(component_id)
        cross_industry = component.get("cross_industry", defaults.get("cross_industry", True))
        component_industries = component.get("industries", defaults.get("industries", []))
        scope = "cross-industry" if cross_industry else "industry"
        search = " ".join([
            component_id,
            component["label"],
            component["job"],
            *component["products"],
            *component_industries,
        ]).casefold()
        product_badges = "".join(
            f'<span class="badge">{html.escape(product_labels[item])}</span>'
            for item in component["products"]
        )
        industry_badges = (
            '<span class="badge badge--scope">Transverse</span>' if cross_industry else "".join(
                f'<span class="badge badge--industry">{html.escape(industry_labels[item])}</span>'
                for item in component_industries
            )
        )
        if example:
            preview = (
                '<details class="preview">'
                '<summary>Aperçu interactif</summary>'
                f'<div class="preview__canvas">{example["markup"]}</div>'
                f'<p class="preview__source">Exemple extrait de <code>{html.escape(example["template"])}</code></p>'
                '</details>'
            )
        else:
            preview = (
                '<div class="preview preview--missing">'
                '<strong>Aperçu à composer</strong>'
                '<span>Ce composant réel n’est encore exposé par aucun template.</span>'
                '</div>'
            )
        cards.append(f"""
        <article class="component-card" data-component-card
          data-search="{html.escape(search)}" data-job="{html.escape(component['job'])}"
          data-products="{' '.join(component['products'])}" data-industry="{html.escape(scope + ' ' + ' '.join(component_industries))}"
          data-status="{html.escape(component['status'])}">
          <header class="component-card__header">
            <div><p class="eyebrow">{html.escape(component['job'])}</p><h2>{html.escape(component['label'])}</h2>
            <code>{html.escape(component_id)}</code></div>
            <span class="status status--{html.escape(component['status'])}">{'Disponible' if component['status'] == 'available' else 'Sans écran'}</span>
          </header>
          <div class="badges">{product_badges}{industry_badges}</div>
          {preview}
        </article>""")

    if available_without_example:
        raise ValueError("composants disponibles sans exemple dans un template : " + ", ".join(available_without_example))
    jobs = [{"id": job, "label": job} for job in taxonomy["jobs"]]
    catalog_data = {
        **counts,
        "previews": sum(component["id"] in examples for component in components_data["components"]),
        "without_screen": sum(item["status"] == "uncatalogued-screen" for item in components_data["components"]),
    }
    markup = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Catalogue des composants Holodeck</title><link rel="stylesheet" href="lightning-kit.css">
<style>
:root{{--catalog-ink:#10213a;--catalog-muted:#5d6b7f;--catalog-line:#d9e1ec;--catalog-wash:#f4f7fb;--catalog-accent:#0b5cab}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--catalog-wash);color:var(--catalog-ink);font:15px/1.45 var(--lc-font)}}
.catalog-header{{padding:48px max(24px,calc((100vw - 1500px)/2));background:linear-gradient(125deg,#071d39,#0b5cab);color:#fff}}
.catalog-header p{{max-width:760px;color:#dbeaff}} .catalog-header h1{{font-size:clamp(30px,5vw,56px);line-height:1;margin:0 0 12px}}
.catalog-header code{{color:#fff}} .catalog-main{{max-width:1500px;margin:auto;padding:24px}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin:0 0 20px}} .stat{{background:#fff;border:1px solid var(--catalog-line);border-radius:999px;padding:7px 12px}}
.filters{{position:sticky;top:0;z-index:20;display:grid;grid-template-columns:minmax(220px,2fr) repeat(4,minmax(145px,1fr)) auto;gap:10px;padding:14px;background:#fff;border:1px solid var(--catalog-line);border-radius:12px;box-shadow:0 8px 24px #10213a12}}
.filters label{{font-size:12px;font-weight:700;color:var(--catalog-muted)}} .filters input,.filters select{{display:block;width:100%;min-height:42px;margin-top:4px;border:1px solid #8c9bad;border-radius:7px;padding:8px;background:#fff;color:var(--catalog-ink)}}
.filters button{{align-self:end;min-height:42px;border:1px solid var(--catalog-accent);border-radius:7px;padding:8px 14px;background:#fff;color:var(--catalog-accent);font-weight:700;cursor:pointer}}
.result-count{{margin:20px 2px 12px;color:var(--catalog-muted)}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:16px;align-items:start}}
.component-card{{min-width:0;background:#fff;border:1px solid var(--catalog-line);border-radius:12px;padding:18px;box-shadow:0 2px 10px #10213a0a}}
.component-card[hidden]{{display:none}} .component-card__header{{display:flex;align-items:start;justify-content:space-between;gap:16px}}
.component-card h2{{margin:1px 0 4px;font-size:21px}} .component-card code{{font-size:12px;color:var(--catalog-muted)}} .eyebrow{{margin:0;color:var(--catalog-accent);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.08em}}
.status,.badge{{display:inline-flex;border-radius:999px;padding:4px 8px;font-size:11px;font-weight:700}} .status{{white-space:nowrap}} .status--available{{background:#e7f7ed;color:#176b35}} .status--uncatalogued-screen{{background:#fff3d8;color:#704d00}}
.badges{{display:flex;flex-wrap:wrap;gap:6px;margin:14px 0}} .badge{{background:#eef4ff;color:#164d82}} .badge--scope{{background:#edf2f7;color:#45566c}} .badge--industry{{background:#f3eefe;color:#5b35a0}}
.preview{{margin-top:14px;border-top:1px solid var(--catalog-line);padding-top:14px}} .preview summary{{cursor:pointer;color:var(--catalog-accent);font-weight:750}} .preview__canvas{{min-width:0;max-height:650px;overflow:auto;margin-top:14px;padding:10px;background:var(--lc-page);border:1px solid var(--catalog-line);border-radius:8px}}
.preview__source{{margin:8px 0 0;color:var(--catalog-muted);font-size:12px}} .preview--missing{{display:grid;gap:3px;color:var(--catalog-muted)}}
:focus-visible{{outline:3px solid #1b96ff;outline-offset:2px}} @media(max-width:1050px){{.filters{{position:static;grid-template-columns:repeat(2,1fr)}}}} @media(max-width:620px){{.catalog-header{{padding:34px 20px}}.catalog-main{{padding:14px}}.filters{{grid-template-columns:1fr}}}}
</style></head><body>
<header class="catalog-header"><h1>Composants Holodeck</h1><p>Catalogue généré depuis les registres, les définitions JavaScript et les exemples intégrés aux templates. Aucun composant ni exemple parallèle n’est maintenu ici.</p><code>file:// compatible</code></header>
<main class="catalog-main"><div class="stats" aria-label="Statistiques"><span class="stat"><strong>{catalog_data['components']}</strong> composants</span><span class="stat"><strong>{catalog_data['components_in_screens']}</strong> exposés</span><span class="stat"><strong>{catalog_data['without_screen']}</strong> sans écran</span></div>
<form class="filters" id="filters">
<label>Rechercher<input type="search" name="query" placeholder="Nom, id, job…"></label>
<label>Job<select name="job">{_options(jobs, 'Tous les jobs')}</select></label>
<label>Produit<select name="product">{_options(products, 'Tous les produits')}</select></label>
<label>Industrie<select name="industry"><option value="">Toutes les industries</option><option value="cross-industry">Transverse</option>{''.join(f'<option value="{html.escape(item["id"])}">{html.escape(item["label"])}</option>' for item in industries)}</select></label>
<label>Statut<select name="status"><option value="">Tous les statuts</option><option value="available">Disponible</option><option value="uncatalogued-screen">Sans écran</option></select></label>
<button type="reset">Réinitialiser</button></form>
<p class="result-count" id="result-count" aria-live="polite">{catalog_data['components']} composants</p>
<section class="grid" aria-label="Composants">{''.join(cards)}</section></main>
<script src="lightning-kit.js"></script><script>
const form=document.querySelector('#filters');const cards=[...document.querySelectorAll('[data-component-card]')];const count=document.querySelector('#result-count');
function applyFilters(){{const data=new FormData(form);const query=String(data.get('query')||'').trim().toLocaleLowerCase('fr');let visible=0;for(const card of cards){{const show=(!query||card.dataset.search.includes(query))&&(!data.get('job')||card.dataset.job===data.get('job'))&&(!data.get('product')||card.dataset.products.split(' ').includes(data.get('product')))&&(!data.get('industry')||card.dataset.industry.split(' ').includes(data.get('industry')))&&(!data.get('status')||card.dataset.status===data.get('status'));card.hidden=!show;if(show)visible++}}count.textContent=`${{visible}} composant${{visible>1?'s':''}}`}}
form.addEventListener('input',applyFilters);form.addEventListener('reset',()=>requestAnimationFrame(applyFilters));
</script></body></html>"""
    return markup, catalog_data


def build_catalog(root: Path, output: Path) -> dict:
    root = root.resolve()
    output = output.resolve()
    if output == root or output in root.parents:
        raise ValueError(f"sortie de catalogue non sûre : {output}")
    if root in output.parents and output != root / "component-catalog":
        raise ValueError(f"un sous-dossier source ne peut pas servir de sortie : {output}")
    if output.exists() and not output.is_dir():
        raise ValueError(f"la sortie de catalogue doit être un dossier : {output}")
    if output.exists():
        marker = output / CATALOG_MARKER
        if not marker.is_file() or marker.read_text(encoding="utf-8") != CATALOG_SIGNATURE:
            raise ValueError(f"refus de remplacer un dossier non généré : {output}")
    markup, report = _catalog_html(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    backup = output.with_name(f".{output.name}.{os.getpid()}.backup")
    try:
        (staging / "index.html").write_text(markup, encoding="utf-8")
        shutil.copy2(root / "assets" / "lightning-kit" / "lightning-components.css", staging / "lightning-kit.css")
        (staging / "lightning-kit.js").write_text(
            bundle_kit_js(root / "assets" / "lightning-kit"), encoding="utf-8"
        )
        (staging / "catalog-report.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (staging / CATALOG_MARKER).write_text(CATALOG_SIGNATURE, encoding="utf-8")
        if backup.exists():
            raise ValueError(f"sauvegarde temporaire déjà présente : {backup}")
        if output.exists():
            output.replace(backup)
        staging.replace(output)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if not output.exists() and backup.exists():
            backup.replace(output)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return report


def selfcheck() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        temporary = Path(tmp)
        output = temporary / "catalog"
        report = build_catalog(ROOT, output)
        markup = (output / "index.html").read_text(encoding="utf-8")
        assert markup.count('<article class="component-card" data-component-card') == report["components"]
        assert report["previews"] >= report["components_in_screens"]
        assert "fetch(" not in (output / "lightning-kit.js").read_text(encoding="utf-8")
        fixture_root = temporary / "fixture-root"
        (fixture_root / "templates").mkdir(parents=True)
        fixture_dir = fixture_root / "registry" / "component-examples"
        fixture_dir.mkdir(parents=True)
        (fixture_dir / "lc-fixture-smoke.json").write_text(
            '{"title":"Fixture smoke","description":"</SCRIPT> reste sûr"}\n', encoding="utf-8"
        )
        fixture_example = _examples(fixture_root)["lc-fixture-smoke"]
        assert "fixture lc-fixture-smoke.json" == fixture_example["template"]
        assert "<\\/SCRIPT>" in fixture_example["markup"]
        try:
            build_catalog(ROOT, ROOT)
        except ValueError as exc:
            assert "non sûre" in str(exc)
        else:
            raise AssertionError("la racine de la skill ne doit jamais être une sortie valide")
        protected_output = temporary / "protected"
        protected_output.mkdir()
        (protected_output / "sentinel.txt").write_text("keep", encoding="utf-8")
        (protected_output / "catalog-report.json").write_text("{}", encoding="utf-8")
        try:
            build_catalog(ROOT, protected_output)
        except ValueError as exc:
            assert "non généré" in str(exc)
            assert (protected_output / "sentinel.txt").read_text(encoding="utf-8") == "keep"
        else:
            raise AssertionError("un dossier utilisateur non marqué ne doit jamais être remplacé")
        source_output = ROOT / "assets"
        try:
            build_catalog(ROOT, source_output)
        except ValueError as exc:
            assert "sous-dossier source" in str(exc)
        else:
            raise AssertionError("un sous-dossier source ne doit jamais être remplacé")
        copied_root = temporary / "copied-root"
        shutil.copytree(
            ROOT,
            copied_root,
            ignore=shutil.ignore_patterns("component-catalog", ".component-catalog.*", "__pycache__", "*.pyc"),
        )
        copied_source = copied_root / "assets" / "lightning-kit" / "fixture-only-components.js"
        copied_source.write_text(
            "class LcFixtureOnly extends JsonComponent { render() { this.innerHTML = '<p>ok</p>'; } }\n"
            "const definitions = {\n  'lc-fixture-only': LcFixtureOnly,\n};\n"
            "for (const [name, constructor] of Object.entries(definitions)) {\n"
            "  if (!customElements.get(name)) customElements.define(name, constructor);\n}\n",
            encoding="utf-8",
        )
        copied_css = copied_root / "assets" / "lightning-kit" / "lightning-components.css"
        copied_css.write_text(copied_css.read_text(encoding="utf-8") + "\nlc-fixture-only { display: block; }\n", encoding="utf-8")
        registry_path = copied_root / "registry" / "components.json"
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        registry["components"].append({
            "id": "lc-fixture-only",
            "source": "assets/lightning-kit/fixture-only-components.js",
            "label": "Fixture only",
            "job": "assistance",
            "products": ["agentforce"],
            "surface": "lightning",
            "status": "uncatalogued-screen",
        })
        registry_path.write_text(json.dumps(registry, ensure_ascii=False), encoding="utf-8")
        copied_fixture = copied_root / "registry" / "component-examples" / "lc-fixture-only.json"
        copied_fixture.parent.mkdir(exist_ok=True)
        copied_fixture.write_text('{"title":"Fixture only"}\n', encoding="utf-8")
        copied_output = temporary / "copied-catalog"
        build_catalog(copied_root, copied_output)
        assert "lc-fixture-only" in (copied_output / "lightning-kit.js").read_text(encoding="utf-8")
    print("catalog selfcheck OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère le catalogue local des composants Holodeck.")
    parser.add_argument("output", nargs="?", type=Path, default=ROOT / "component-catalog")
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()
    if args.selfcheck:
        selfcheck()
        return
    output = args.output.resolve()
    report = build_catalog(ROOT, output)
    print(f"catalogue OK · {report['components']} composants · {report['previews']} aperçus · {output / 'index.html'}")


if __name__ == "__main__":
    main()
