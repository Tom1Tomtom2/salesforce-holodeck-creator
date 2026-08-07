#!/usr/bin/env python3
"""Valide les registres d'assets contre les sources réellement livrées."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class RegistryError(ValueError):
    pass


def _load(name: str, root: Path) -> dict:
    path = root / "registry" / name
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryError(f"registre absent : {path.relative_to(root)}") from exc
    except json.JSONDecodeError as exc:
        raise RegistryError(f"JSON invalide dans {path.relative_to(root)} : {exc}") from exc
    if data.get("schema_version") != 1:
        raise RegistryError(f"{name} : schema_version doit valoir 1")
    return data


def _indexed(items: list, kind: str) -> dict:
    indexed = {}
    for item in items:
        asset_id = item.get("id")
        if not isinstance(asset_id, str) or not asset_id:
            raise RegistryError(f"{kind} sans id valide")
        if asset_id in indexed:
            raise RegistryError(f"{kind} dupliqué : {asset_id}")
        indexed[asset_id] = item
    return indexed


def _effective_industry(asset: dict, defaults: dict, kind: str) -> tuple[bool, list]:
    cross_industry = asset.get("cross_industry", defaults.get("cross_industry"))
    industries = asset.get("industries", defaults.get("industries", []))
    if not isinstance(cross_industry, bool):
        raise RegistryError(f"{kind} {asset['id']} : cross_industry doit être booléen")
    if not isinstance(industries, list) or not all(isinstance(value, str) for value in industries):
        raise RegistryError(f"{kind} {asset['id']} : industries doit être une liste d'identifiants")
    if cross_industry and industries:
        raise RegistryError(f"{kind} {asset['id']} : un asset cross-industry ne porte pas d'industries")
    if not cross_industry and not industries:
        raise RegistryError(f"{kind} {asset['id']} : un asset sectoriel doit déclarer au moins une industrie")
    return cross_industry, industries


def _source_components(root: Path) -> dict:
    found = {}
    kit = root / "assets" / "lightning-kit"
    for source in sorted(kit.glob("*.js")):
        if source.name == "scenario-loader.js":
            continue
        text = source.read_text(encoding="utf-8")
        for component_id in re.findall(r"^\s*['\"](lc-[a-z0-9-]+)['\"]\s*:", text, re.MULTILINE):
            if component_id in found:
                raise RegistryError(f"composant défini dans plusieurs sources : {component_id}")
            found[component_id] = source.relative_to(root).as_posix()
        classes = set(re.findall(r"\bclass\s+(Lc[A-Za-z0-9]+)\s+extends\s+(?:JsonComponent|HTMLElement)\b", text))
        registered_classes = set(re.findall(
            r"^\s*['\"]lc-[a-z0-9-]+['\"]\s*:\s*(Lc[A-Za-z0-9]+)\b", text, re.MULTILINE
        ))
        orphan_classes = sorted(classes - registered_classes)
        if orphan_classes:
            raise RegistryError(
                f"classes de composant non enregistrées dans {source.name} : " + ", ".join(orphan_classes)
            )
    return found


def _template_slots(text: str) -> list:
    return list(dict.fromkeys(re.findall(r"<!--\s*SLOT:\s*([\w-]+)", text)))


def _template_components(text: str) -> list:
    return list(dict.fromkeys(re.findall(r"<(lc-[a-z0-9-]+)\b", text)))


def _validate_component_contract(root: Path, source_components: dict) -> None:
    """Garde-fous statiques minimaux de la charte pour les contributions au kit."""
    sources = {
        source: (root / source).read_text(encoding="utf-8")
        for source in set(source_components.values())
    }
    css = (root / "assets" / "lightning-kit" / "lightning-components.css").read_text(encoding="utf-8")
    css_header = css[:css.find("}", css.find(":root")) + 1] if ":root" in css else ""
    required_tokens = {
        "--lc-brand", "--lc-heading", "--lc-text", "--lc-text-secondary", "--lc-page",
        "--lc-surface", "--lc-border", "--lc-success", "--lc-warning", "--lc-error",
        "--lc-radius", "--lc-shadow", "--lc-font",
    }
    missing_tokens = sorted(token for token in required_tokens if token not in css_header)
    if missing_tokens:
        raise RegistryError("charte CSS : tokens de base absents " + ", ".join(missing_tokens))

    for component_id, source in source_components.items():
        text = sources[source]
        if component_id != "lc-toast-region" and not re.search(
            r"class\s+\w+\s+extends\s+JsonComponent\b", text
        ):
            raise RegistryError(
                f"composant {component_id} : la source doit exposer un composant JSON-driven"
            )
        if not re.search(rf"['\"]{re.escape(component_id)}['\"]\s*:", text):
            raise RegistryError(f"composant {component_id} : définition custom element introuvable")
        if not re.search(rf"\b{re.escape(component_id)}\b", css):
            raise RegistryError(
                f"composant {component_id} : ajoute la balise à lightning-components.css"
            )

    for source, text in sources.items():
        relative = Path(source).name
        if re.search(r"\b(?:fetch|XMLHttpRequest)\s*\(", text):
            raise RegistryError(f"charte {relative} : accès réseau interdit, le kit doit fonctionner en file://")
        if re.search(r"\btabindex\s*=\s*['\"][1-9]\d*['\"]", text):
            raise RegistryError(f"charte {relative} : tabindex positif interdit")
        if re.search(r"\bon(?:click|change|input|keydown|keyup)\s*=", text, re.IGNORECASE):
            raise RegistryError(f"charte {relative} : gestionnaires inline interdits")
        if re.search(r"javascript\s*:", text, re.IGNORECASE):
            raise RegistryError(f"charte {relative} : URL javascript: interdite")


def validate_registry(root: Path = ROOT) -> dict:
    products_data = _load("products.json", root)
    industries_data = _load("industries.json", root)
    components_data = _load("components.json", root)
    screens_data = _load("screens.json", root)
    taxonomy_data = _load("taxonomy.json", root)

    products = _indexed(products_data.get("products", []), "produit")
    industries = _indexed(industries_data.get("industries", []), "industrie")
    components = _indexed(components_data.get("components", []), "composant")
    screens = _indexed(screens_data.get("screens", []), "écran")
    source_components = _source_components(root)
    if set(components) != set(source_components):
        missing = sorted(set(source_components) - set(components))
        stale = sorted(set(components) - set(source_components))
        details = []
        if missing:
            details.append("non catalogués : " + ", ".join(missing))
        if stale:
            details.append("absents des sources : " + ", ".join(stale))
        raise RegistryError("couverture composants incomplète (" + " ; ".join(details) + ")")
    _validate_component_contract(root, source_components)

    taxonomy_jobs = taxonomy_data.get("jobs", [])
    if not isinstance(taxonomy_jobs, list) or not taxonomy_jobs or len(taxonomy_jobs) != len(set(taxonomy_jobs)):
        raise RegistryError("taxonomy.json : jobs doit être une liste non vide sans doublon")
    if taxonomy_jobs != sorted(taxonomy_jobs):
        raise RegistryError("taxonomy.json : jobs doit être trié pour limiter les doublons en revue")
    jobs = set(taxonomy_jobs)
    for collection_name, collection in (("scopes", taxonomy_data.get("scopes")),
                                        ("surfaces", taxonomy_data.get("surfaces"))):
        if not isinstance(collection, list) or not collection:
            raise RegistryError(f"taxonomy.json : {collection_name} doit être une liste non vide")
        _indexed(collection, collection_name[:-1])

    product_jobs = {job for product in products.values() for job in product.get("jobs", [])}
    unknown_product_jobs = sorted(product_jobs - jobs)
    if unknown_product_jobs:
        raise RegistryError(f"taxonomy.json : jobs produit non classifiés {unknown_product_jobs}")

    for component in components.values():
        component_id = component["id"]
        if component.get("source") != source_components[component_id]:
            raise RegistryError(
                f"composant {component_id} : source attendue {source_components[component_id]}"
            )
        if component.get("status") not in {"available", "uncatalogued-screen"}:
            raise RegistryError(f"composant {component_id} : statut invalide")
        if not component.get("job") or not component.get("label"):
            raise RegistryError(f"composant {component_id} : label et job sont obligatoires")
        if component.get("job") not in jobs:
            raise RegistryError(f"composant {component_id} : job non classifié {component.get('job')}")
        if not component.get("products"):
            raise RegistryError(f"composant {component_id} : au moins un produit est obligatoire")
        unknown_products = sorted(set(component.get("products", [])) - set(products))
        if unknown_products:
            raise RegistryError(f"composant {component_id} : produits inconnus {unknown_products}")
        if not any(component["job"] in products[product_id].get("jobs", [])
                   for product_id in component["products"]):
            raise RegistryError(
                f"composant {component_id} : le job {component['job']} n'est couvert par aucun "
                f"produit déclaré {component['products']}"
            )
        _, asset_industries = _effective_industry(
            component, components_data.get("defaults", {}), "composant"
        )
        unknown_industries = sorted(set(asset_industries) - set(industries))
        if unknown_industries:
            raise RegistryError(f"composant {component_id} : industries inconnues {unknown_industries}")

    template_ids = {path.stem for path in (root / "templates").glob("*.html")}
    if set(screens) != template_ids:
        missing = sorted(template_ids - set(screens))
        stale = sorted(set(screens) - template_ids)
        details = []
        if missing:
            details.append("non catalogués : " + ", ".join(missing))
        if stale:
            details.append("sans template : " + ", ".join(stale))
        raise RegistryError("couverture écrans incomplète (" + " ; ".join(details) + ")")

    used_components = set()
    for screen in screens.values():
        screen_id = screen["id"]
        template = root / screen.get("template", "")
        if template != root / "templates" / f"{screen_id}.html" or not template.is_file():
            raise RegistryError(f"écran {screen_id} : template incohérent ou absent")
        if screen.get("format") not in {"mobile", "desktop"}:
            raise RegistryError(f"écran {screen_id} : format invalide")
        if screen.get("status") != "available" or not screen.get("job") or not screen.get("label"):
            raise RegistryError(f"écran {screen_id} : label, job et statut available sont obligatoires")
        if screen.get("job") not in jobs:
            raise RegistryError(f"écran {screen_id} : job non classifié {screen.get('job')}")
        if not screen.get("products"):
            raise RegistryError(f"écran {screen_id} : au moins un produit est obligatoire")
        unknown_products = sorted(set(screen.get("products", [])) - set(products))
        if unknown_products:
            raise RegistryError(f"écran {screen_id} : produits inconnus {unknown_products}")
        if not any(screen["job"] in products[product_id].get("jobs", [])
                   for product_id in screen["products"]):
            raise RegistryError(
                f"écran {screen_id} : le job {screen['job']} n'est couvert par aucun "
                f"produit déclaré {screen['products']}"
            )
        _, asset_industries = _effective_industry(screen, screens_data.get("defaults", {}), "écran")
        unknown_industries = sorted(set(asset_industries) - set(industries))
        if unknown_industries:
            raise RegistryError(f"écran {screen_id} : industries inconnues {unknown_industries}")

        text = template.read_text(encoding="utf-8")
        actual_slots = _template_slots(text)
        if screen.get("slots") != actual_slots:
            raise RegistryError(
                f"écran {screen_id} : SLOTs désynchronisés, attendu {actual_slots}"
            )
        actual_components = _template_components(text)
        if screen.get("components") != actual_components:
            raise RegistryError(
                f"écran {screen_id} : composants désynchronisés, attendu {actual_components}"
            )
        unknown_components = sorted(set(actual_components) - set(components))
        if unknown_components:
            raise RegistryError(f"écran {screen_id} : composants inconnus {unknown_components}")
        used_components.update(actual_components)

    for component_id, component in components.items():
        expected_status = "available" if component_id in used_components else "uncatalogued-screen"
        if component["status"] != expected_status:
            raise RegistryError(
                f"composant {component_id} : statut attendu {expected_status}, trouvé {component['status']}"
            )

    return {
        "products": len(products),
        "industries": len(industries),
        "components": len(components),
        "screens": len(screens),
        "components_in_screens": len(used_components),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Valide les registres site-web-story.")
    parser.add_argument("--root", type=Path, default=ROOT, help="dossier racine de la skill")
    args = parser.parse_args()
    try:
        counts = validate_registry(args.root.resolve())
    except RegistryError as exc:
        raise SystemExit(f"ERREUR registre : {exc}") from exc
    print(
        "registry OK · "
        f"{counts['products']} produits · {counts['industries']} industries · "
        f"{counts['components']} composants · {counts['screens']} écrans · "
        f"{counts['components_in_screens']} composants exposés"
    )


if __name__ == "__main__":
    main()
