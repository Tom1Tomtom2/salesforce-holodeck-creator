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
    return found


def _template_slots(text: str) -> list:
    return list(dict.fromkeys(re.findall(r"<!--\s*SLOT:\s*([\w-]+)", text)))


def _template_components(text: str) -> list:
    return list(dict.fromkeys(re.findall(r"<(lc-[a-z0-9-]+)\b", text)))


def validate_registry(root: Path = ROOT) -> dict:
    products_data = _load("products.json", root)
    industries_data = _load("industries.json", root)
    components_data = _load("components.json", root)
    screens_data = _load("screens.json", root)

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
        if not component.get("products"):
            raise RegistryError(f"composant {component_id} : au moins un produit est obligatoire")
        unknown_products = sorted(set(component.get("products", [])) - set(products))
        if unknown_products:
            raise RegistryError(f"composant {component_id} : produits inconnus {unknown_products}")
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
        if not screen.get("products"):
            raise RegistryError(f"écran {screen_id} : au moins un produit est obligatoire")
        unknown_products = sorted(set(screen.get("products", [])) - set(products))
        if unknown_products:
            raise RegistryError(f"écran {screen_id} : produits inconnus {unknown_products}")
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
