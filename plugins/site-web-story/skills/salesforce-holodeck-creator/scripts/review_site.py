#!/usr/bin/env python3
"""Capture et contrôle visuellement un site généré par site-web-story.

Usage :
    python3 scripts/review_site.py ./nova-story
    python3 scripts/review_site.py ./nova-story --selfcheck

Sorties dans <story>/review/ : captures PNG, contact-sheet.html et review-report.json.
La revue vise les défauts de démo : erreurs navigateur, assets cassés, débordements
horizontaux, restes de marque d'exemple et écrans difficiles à inspecter.
"""
import argparse
import html
import json
import tempfile
from pathlib import Path


VIEWPORT = {"width": 1440, "height": 900}


def _contact_sheet(items: list, report: dict) -> str:
    cards = []
    for item in items:
        issues = item.get("issues", [])
        badge = (
            f'<span class="badge bad">{len(issues)} alerte(s)</span>'
            if issues else '<span class="badge ok">OK</span>'
        )
        issue_markup = "".join(f"<li>{html.escape(issue)}</li>" for issue in issues)
        cards.append(
            '<article class="card">'
            f'<header><div><b>{html.escape(item["title"])}</b><small>{html.escape(item["file"])}</small></div>{badge}</header>'
            f'<a href="{html.escape(item["screenshot"])}"><img src="{html.escape(item["screenshot"])}" alt="Capture {html.escape(item["title"])}"></a>'
            + (f'<ul>{issue_markup}</ul>' if issues else "")
            + '</article>'
        )
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Planche contact — revue de démo</title>
<style>
body{{font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:0;background:#f4f5f7;color:#181818}}
main{{max-width:1500px;margin:auto;padding:32px}} h1{{margin:0 0 6px}} .summary{{color:#5c5c5c;margin-bottom:28px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:24px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:12px;overflow:hidden;box-shadow:0 4px 18px #0000000d}}
.card header{{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;gap:16px}}
.card small{{display:block;color:#666;margin-top:2px}} .card img{{display:block;width:100%;height:auto;border-top:1px solid #eee}}
.card ul{{margin:0;padding:12px 32px 18px;color:#8e030f}} .badge{{padding:4px 9px;border-radius:999px;font-size:12px;font-weight:700;white-space:nowrap}}
.ok{{background:#e6f6ec;color:#176b35}} .bad{{background:#fce8e6;color:#8e030f}}
</style></head><body><main><h1>Planche contact</h1>
<p class="summary">{len(items)} page(s) · {report["issue_count"]} alerte(s). Ouvrir les captures pour vérifier le cadrage et la lisibilité en condition de pitch.</p>
<section class="grid">{''.join(cards)}</section></main></body></html>"""


def review(site: Path) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("Playwright manque : pip install -r requirements.txt && playwright install chromium") from exc

    site = site.resolve()
    index = site / "index.html"
    if not index.is_file():
        raise SystemExit(f"index.html introuvable dans {site}")
    review_dir = site / "review"
    review_dir.mkdir(exist_ok=True)

    manifest_path = site / "build-manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        screen_pages = [
            (screen.get("title", screen["file"]), screen["file"],
             f'{index:02d}-{Path(screen["file"]).stem}.png')
            for index, screen in enumerate(manifest.get("screens", []), 1)
        ]
        # Les captures d'actes existent avant celle du hub, qui les utilise comme
        # doublures visuelles pour contourner le lazy painting de Chromium.
        pages = screen_pages + [("Hub", "index.html", "00-index.png")]
    else:
        screen_pages = [
            (path.stem.replace("-", " ").title(), path.name, f'{index:02d}-{path.stem}.png')
            for index, path in enumerate(
                (path for path in sorted(site.glob("*.html")) if path.name != "index.html"), 1
            )
        ]
        pages = screen_pages + [("Hub", "index.html", "00-index.png")]

    items = []
    with sync_playwright() as playwright:
        launch = {"headless": True}
        try:
            browser = playwright.chromium.launch(channel="chrome", **launch)
        except Exception:
            browser = playwright.chromium.launch(**launch)
        context = browser.new_context(viewport=VIEWPORT, device_scale_factor=1, reduced_motion="reduce")
        for title, filename, screenshot in pages:
            page = context.new_page()
            console_errors = []
            page_errors = []
            failed_requests = []
            page.on("console", lambda msg, bag=console_errors: bag.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda error, bag=page_errors: bag.append(str(error)))
            page.on("requestfailed", lambda request, bag=failed_requests: bag.append(
                f'{request.url}: {request.failure or "échec réseau"}'
            ))
            target = site / filename
            issues = []
            if not target.is_file():
                issues.append("Fichier HTML absent")
                items.append({"title": title, "file": filename, "screenshot": "", "issues": issues})
                page.close()
                continue
            page.goto(target.as_uri(), wait_until="load", timeout=30000)
            if filename == "index.html":
                # La capture full_page de Chromium ne peint pas fiablement des iframes
                # transformées plusieurs écrans plus bas. La revue capture donc chaque
                # écran séparément et remplace, dans le hub de revue uniquement, l'iframe
                # par cette capture. Le site livré reste inchangé.
                page.evaluate("""async () => {
                    const scenes = [...document.querySelectorAll('.intro, .chapter, .act')];
                    for (const scene of scenes) {
                        scene.scrollIntoView({ block: 'center' });
                        await new Promise(resolve => setTimeout(resolve, 220));
                    }
                    window.scrollTo(0, 0);
                }""")
                page.wait_for_timeout(1800)
                page.evaluate("""() => {
                    document.querySelectorAll('.frame iframe').forEach((frame, index) => {
                        const src = (frame.getAttribute('src') || '').split('/').pop().replace(/[.]html$/i, '');
                        if (!src) return;
                        const shot = document.createElement('img');
                        const number = String(index + 1).padStart(2, '0');
                        const isPhone = frame.closest('.frame')?.classList.contains('phone');
                        shot.src = isPhone ? `review/preview-${number}-${src}.png` : `review/${number}-${src}.png`;
                        shot.alt = frame.title || src;
                        shot.style.cssText = isPhone
                            ? 'position:absolute;inset:0;width:100%;height:100%;max-width:none;object-fit:cover'
                            : 'position:absolute;left:var(--screen-left,0);top:var(--screen-top,0);width:var(--screen-w,1440px);max-width:none;transform:scale(var(--screen-scale,0.5));transform-origin:top left';
                        frame.replaceWith(shot);
                    });
                }""")
            # Les templates animés doivent être capturés dans leur état final, pas pendant
            # une fusion/transition qui ressemble à un défaut de mise en page.
            page.wait_for_timeout(5200)
            metrics = page.evaluate("""() => ({
                scrollWidth: document.documentElement.scrollWidth,
                clientWidth: document.documentElement.clientWidth,
                scrollHeight: document.documentElement.scrollHeight,
                bodyBounds: (() => {
                    const nodes = [...document.body.children].filter(el => {
                        const s = getComputedStyle(el), r = el.getBoundingClientRect();
                        return s.position !== 'fixed' && r.width > 20 && r.height > 20;
                    });
                    if (!nodes.length) return { top: 0, bottom: 0, occupiedHeight: 0 };
                    const top = Math.min(...nodes.map(el => el.getBoundingClientRect().top));
                    const bottom = Math.max(...nodes.map(el => el.getBoundingClientRect().bottom));
                    return { top, bottom, occupiedHeight: bottom - top };
                })(),
                brokenImages: [...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.getAttribute('src') || ''),
                novaText: document.body.innerText.includes('Nova'),
                emptyIframes: [...document.querySelectorAll('iframe')].filter(i => !i.getAttribute('src')).length,
                invisibleActs: [...document.querySelectorAll('.act')].filter(el => {
                    const s = getComputedStyle(el.querySelector('.story') || el);
                    return Number(s.opacity) < 0.95 || s.visibility === 'hidden';
                }).length
            })""")
            if metrics["scrollWidth"] > metrics["clientWidth"] + 4:
                issues.append(f'Débordement horizontal : {metrics["scrollWidth"]} px pour {metrics["clientWidth"]} px')
            if metrics["brokenImages"]:
                issues.append("Images cassées : " + ", ".join(metrics["brokenImages"]))
            if metrics["novaText"]:
                issues.append("Marque d'exemple « Nova » visible")
            if metrics["emptyIframes"]:
                issues.append(f'{metrics["emptyIframes"]} iframe(s) sans source')
            if metrics["invisibleActs"]:
                issues.append(f'{metrics["invisibleActs"]} acte(s) invisible(s) pendant la capture')
            if filename != "index.html" and metrics["bodyBounds"]["occupiedHeight"] < VIEWPORT["height"] * 0.48:
                issues.append(
                    f'Page anormalement vide : contenu sur {metrics["bodyBounds"]["occupiedHeight"]:.0f} px '
                    f'pour une fenêtre de {VIEWPORT["height"]} px'
                )
            issues += [f'Console : {message}' for message in console_errors]
            issues += [f'Page : {message}' for message in page_errors]
            issues += [f'Réseau : {message}' for message in failed_requests]
            page.screenshot(path=str(review_dir / screenshot), full_page=True)
            phone = page.locator('.phone').first
            if filename != "index.html" and phone.count():
                phone.screenshot(path=str(review_dir / f'preview-{screenshot}'))
            items.append({
                "title": title,
                "file": filename,
                "screenshot": screenshot,
                "metrics": metrics,
                "issues": issues,
            })
            page.close()
        browser.close()

    items.sort(key=lambda item: (item["file"] != "index.html", item["file"]))

    report = {
        "site": str(site),
        "viewport": VIEWPORT,
        "issue_count": sum(len(item["issues"]) for item in items),
        "pages": items,
    }
    (review_dir / "review-report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (review_dir / "contact-sheet.html").write_text(_contact_sheet(items, report), encoding="utf-8")
    print(f'✓ revue visuelle : {len(items)} page(s), {report["issue_count"]} alerte(s)')
    print(f'  - {review_dir / "contact-sheet.html"}')
    print(f'  - {review_dir / "review-report.json"}')
    return report


def selfcheck() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        site = Path(tmp) / "demo-story"
        site.mkdir()
        (site / "index.html").write_text(
            '<!doctype html><html lang="fr"><head><meta charset="utf-8"></head><body><h1>Démo</h1></body></html>',
            encoding="utf-8",
        )
        report = review(site)
        assert report["issue_count"] == 0, report
        assert (site / "review" / "00-index.png").is_file()
        assert (site / "review" / "contact-sheet.html").is_file()
        assert (site / "review" / "review-report.json").is_file()
    print("selfcheck OK")


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture et contrôle un site site-web-story généré.")
    parser.add_argument("site", nargs="?", help="dossier <slug>-story")
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()
    if args.selfcheck:
        selfcheck()
        return
    if not args.site:
        parser.error("fournis le dossier <slug>-story (ou --selfcheck)")
    review(Path(args.site))


if __name__ == "__main__":
    main()
