#!/usr/bin/env python3
"""Crawle le site d'une marque avec un vrai navigateur (Chromium headless) pour
pré-remplir la Phase 1 de site-web-story : logo, images produit, palette, typo.

Pourquoi un navigateur et pas WebFetch/curl : les sites de marque (audi.fr…) sont
derrière un anti-bot de CDN qui renvoie 503 à tout client sans JS. Chromium exécute
le JS → il passe. Le script PROPOSE (couleurs, produits) et TÉLÉCHARGE (logo + images) ;
c'est toujours l'utilisateur qui valide l'ambiance en chat (Phase 1).

Sortie dans ./<slug>-brand/ :
    brand.json     — couleurs proposées, typo, secteur/produits détectés, images, logo_source
    logo.(svg|png) — logo de la marque, cascade : DOM → SVG inline → Wikidata/Commons → icon.horse
    product-N.*    — les plus grandes images produit rendues (og:image en premier)

Le logo passe par une cascade de sources : même quand un site bloque le crawl, son vrai
logo officiel est souvent récupérable via Wikidata (propriété P154), non bloqué par anti-bot.

Usage :
    python3 scripts/crawl_brand.py https://www.audi.fr --brand Audi --slug audi
    python3 scripts/crawl_brand.py --fetch <url…> --slug audi   # backup : images produit par URL
    python3 scripts/crawl_brand.py --selfcheck
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlencode, urljoin, urlparse

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

# titres typiques d'une page anti-bot / maintenance servie à la place du vrai site
BLOCK_MARKERS = ("not available", "access denied", "just a moment", "attention required",
                 "captcha", "are you a robot", "unavailable", "forbidden", "blocked")


def diagnose(data: dict, products: list) -> str | None:
    """Renvoie un message d'échec si le crawl a manifestement échoué (anti-bot / page vide),
    sinon None. But : ne jamais écrire un brand.json trompeur en silence."""
    title = (data.get("title") or "").lower()
    if any(m in title for m in BLOCK_MARKERS):
        return f"page anti-bot/maintenance servie (titre : « {data.get('title')} »)"
    if not products and not data.get("logo") and not data.get("logoSvg"):
        return "aucune image ni logo récupéré (site JS-only non hydraté, ou blocage)"
    return None

# JS exécuté DANS la page rendue : renvoie tout ce dont la Phase 1 a besoin, d'un coup.
# Pur lecture du DOM calculé (getComputedStyle) → robuste au markup, pas de parsing CSS.
EXTRACT_JS = r"""
() => {
  const abs = (u) => { try { return new URL(u, location.href).href } catch { return null } };
  const rgb2hex = (c) => {
    const m = (c||'').match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const [r,g,b,a] = m[1].split(',').map(s => parseFloat(s));
    if (a === 0) return null;                        // transparent → ignore
    return '#' + [r,g,b].map(x => Math.round(x).toString(16).padStart(2,'0')).join('');
  };
  // --- logo : <img> "logo" dans l'en-tête, sinon 1er <svg> de l'en-tête ---
  const header = document.querySelector('header, [role=banner], nav');
  let logo = null, logoSvg = null;
  if (header) {
    const img = [...header.querySelectorAll('img')].find(i =>
      /logo|brand|wordmark/i.test(i.className + ' ' + (i.alt||'') + ' ' + (i.src||'')));
    if (img) logo = abs(img.currentSrc || img.src);
    // SVG logo : le plus large (≥ 40px) — écarte les icônes 24×24 (chevrons, loupe…)
    if (!logo) {
      const svg = [...header.querySelectorAll('svg')]
        .map(s => ({ s, w: s.getBoundingClientRect().width }))
        .filter(x => x.w >= 40)
        .sort((a,b) => b.w - a.w)[0];
      if (svg) logoSvg = svg.s.outerHTML;
    }
  }
  // --- images produit : og:image d'abord, puis les <img> rendues les plus grandes ---
  const og = [...document.querySelectorAll('meta[property="og:image"], meta[name="twitter:image"]')]
    .map(m => abs(m.content)).filter(Boolean);
  const imgs = [...document.querySelectorAll('img')]
    .map(i => ({ url: abs(i.currentSrc || i.src), w: i.naturalWidth, h: i.naturalHeight,
                 alt: i.alt || '' }))
    .filter(x => x.url && !x.url.startsWith('data:') && !/\.svg($|\?)/i.test(x.url)
                 && x.w >= 400 && x.h >= 300)
    .sort((a,b) => b.w*b.h - a.w*a.h);
  // --- couleurs : theme-color, fond/texte du body, backgrounds des CTA visibles ---
  const theme = document.querySelector('meta[name="theme-color"]')?.content || null;
  const bodyCS = getComputedStyle(document.body);
  const ctas = [...document.querySelectorAll('a,button')]
    .filter(el => { const r = el.getBoundingClientRect();
                    return r.width > 60 && r.height > 24 && r.top < innerHeight*2; })
    .map(el => rgb2hex(getComputedStyle(el).backgroundColor)).filter(Boolean);
  const titleEl = document.querySelector('h1, h2');
  return {
    title: document.title,
    description: document.querySelector('meta[name=description]')?.content || '',
    logo, logoSvg,
    ogImages: og,
    images: imgs.slice(0, 12),
    theme,
    bg: rgb2hex(bodyCS.backgroundColor),
    text: rgb2hex(bodyCS.color),
    ctaColors: [...new Set(ctas)].slice(0, 10),
    bodyFont: bodyCS.fontFamily,
    titleFont: titleEl ? getComputedStyle(titleEl).fontFamily : bodyCS.fontFamily,
  };
}
"""

# sélecteurs de "tout accepter" (best-effort ; le bandeau ne gêne que les captures, pas le DOM)
CONSENT = ["button:has-text('Tout accepter')", "button:has-text('Accepter')",
           "button:has-text('Accept all')", "button:has-text('Accept')",
           "[data-testid='uc-accept-all-button']", "#onetrust-accept-btn-handler"]


def pick_accent(data: dict) -> str:
    """Heuristique : couleur d'accent proposée = 1er CTA coloré non gris/noir/blanc,
    sinon theme-color, sinon le fond. L'utilisateur valide en Phase 1 (ne décide pas)."""
    def is_neutral(h):
        if not h or len(h) != 7:
            return True
        r, g, b = (int(h[i:i+2], 16) for i in (1, 3, 5))
        return max(r, g, b) - min(r, g, b) < 24  # gris/noir/blanc = faible saturation
    for c in data.get("ctaColors", []):
        if not is_neutral(c):
            return c
    return data.get("theme") or data.get("bg") or "#1c2b4a"


def _is_valid_download(body: bytes, suffix: str) -> bool:
    """Un SVG est un vecteur : souvent < 1 Ko et pourtant valide (logo Nike = 966 o) →
    on le valide sur la présence de la balise <svg, pas sur la taille. Un raster < 1 Ko
    est presque toujours un pixel espion ou une erreur déguisée → on le rejette."""
    if suffix.lower() == ".svg":
        return b"<svg" in body[:4096].lower()
    return len(body) > 1024


def download(url: str, dest: Path, referer: str) -> bool:
    """Télécharge une URL (UA navigateur + referer, sinon le CDN re-bloque). True si OK."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": referer})
        with urllib.request.urlopen(req, timeout=20) as r:
            if r.status != 200:
                return False
            body = r.read()
        dest.write_bytes(body)
        return _is_valid_download(body, dest.suffix)
    except Exception as e:
        print(f"  ⚠ échec téléchargement {url} : {e}")
        return False


def _ext(url: str, default: str = ".jpg") -> str:
    m = re.search(r"\.(jpe?g|png|webp|avif|gif|svg)", urlparse(url).path, re.I)
    return "." + m.group(1).lower().replace("jpeg", "jpg") if m else default


def _json_get(url: str):
    """GET JSON avec UA (Wikimedia exige un UA non vide). None si échec réseau/parse."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠ Wikidata : {e}")
        return None


def wikidata_logo_url(brand: str) -> str | None:
    """Cherche le logo officiel de la marque via Wikidata (propriété P154 « logo image »)
    hébergé sur Wikimedia Commons. Source robuste, légale, non bloquée par anti-bot —
    complément du crawl DOM quand le site de marque bloque. None si rien trouvé."""
    # 1. brand → entité Q… (wbsearchentities, biais 'fr' puis 'en')
    entity = None
    for lang in ("fr", "en"):
        q = urlencode({"action": "wbsearchentities", "search": brand, "language": lang,
                       "format": "json", "limit": "1", "type": "item"})
        d = _json_get("https://www.wikidata.org/w/api.php?" + q)
        if d and d.get("search"):
            entity = d["search"][0]["id"]
            break
    if not entity:
        return None
    # 2. entité → claims P154 → nom de fichier Commons
    d = _json_get(f"https://www.wikidata.org/wiki/Special:EntityData/{entity}.json")
    try:
        claim = d["entities"][entity]["claims"]["P154"][0]
        filename = claim["mainsnak"]["datavalue"]["value"]
    except (TypeError, KeyError, IndexError):
        return None
    # 3. nom de fichier → URL de téléchargement (Special:FilePath résout vers le binaire Commons)
    return "https://commons.wikimedia.org/wiki/Special:FilePath/" + quote(filename.replace(" ", "_"))


def crawl(url: str, brand: str, slug: str, max_images: int = 6) -> Path:
    from playwright.sync_api import sync_playwright

    out = Path.cwd() / f"{slug}-brand"
    out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        # Furtivité : les anti-bots CDN (Akamai sur audi.fr) bloquent Chromium headless nu
        # (navigator.webdriver, fingerprint). On lance le vrai Chrome si présent + on masque
        # les signaux les plus grossiers. ponytail: pas de plugin stealth, ces 3 mesures
        # suffisent pour un site marketing ; si un jour ça re-bloque, passer à playwright-stealth.
        launch = dict(args=["--disable-blink-features=AutomationControlled"])
        try:
            browser = p.chromium.launch(channel="chrome", **launch)
        except Exception:
            browser = p.chromium.launch(**launch)  # fallback Chromium si Chrome absent
        ctx = browser.new_context(user_agent=UA, viewport={"width": 1440, "height": 900},
                                  locale="fr-FR")
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        page = ctx.new_page()
        # ponytail: 'networkidle' ne se déclenche jamais sur un site à télémétrie continue
        # (audi.fr) → on attend le DOM, puis un <img> produit hydraté, plafonné par timeout.
        # Un blocage DUR (goto qui lève) ne doit PAS avorter le reste : on garde data={} et
        # on tombera sur les fallbacks (logo Wikidata, message d'échec) au lieu de crasher.
        data = {}
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            for sel in CONSENT:  # best-effort : ferme le bandeau si présent
                try:
                    page.locator(sel).first.click(timeout=1500)
                    break
                except Exception:
                    pass
            try:
                page.wait_for_selector("img[src]:not([src^='data:'])", timeout=8000)
            except Exception:
                pass
            # scroll par paliers : la home d'une marque lazy-load ses visuels produit ;
            # sans scroll leur naturalWidth reste à 0 et le filtre taille les écarte.
            for frac in (0.25, 0.5, 0.75, 1.0):
                page.evaluate("f => scrollTo(0, document.body.scrollHeight*f)", frac)
                page.wait_for_timeout(700)
            page.evaluate("scrollTo(0, 0)")
            page.wait_for_timeout(800)
            data = page.evaluate(EXTRACT_JS)
        except Exception as e:
            print(f"  ⚠ page non chargée ({e}) → fallbacks (logo Wikidata) et status=failed")
        browser.close()

    # --- logo : cascade DOM → SVG inline → Wikidata/Commons → icon.horse (favicon) ---
    # Wikidata AVANT le favicon : c'est le logo officiel de la marque, pas une icône d'onglet.
    logo_file, logo_source = None, None
    if data.get("logo") and download(data["logo"], out / ("logo" + _ext(data["logo"], ".png")), url):
        logo_file, logo_source = "logo" + _ext(data["logo"], ".png"), "site (DOM)"
    elif data.get("logoSvg"):
        (out / "logo.svg").write_text(data["logoSvg"], encoding="utf-8")
        logo_file, logo_source = "logo.svg", "site (SVG inline)"
    else:
        wd = wikidata_logo_url(brand)
        if wd and download(wd, out / ("logo" + _ext(wd, ".png")), "https://commons.wikimedia.org/"):
            logo_file, logo_source = "logo" + _ext(wd, ".png"), "Wikidata/Commons"
        else:
            host = urlparse(url).netloc
            if download(f"https://icon.horse/icon/{host}", out / "logo.png", url):
                logo_file, logo_source = "logo.png", "favicon (icon.horse)"

    # --- images produit : og:image en tête (dédupliquées), puis les plus grandes ---
    seen, candidates = set(), []
    for u in data.get("ogImages", []) + [i["url"] for i in data.get("images", [])]:
        if u not in seen:
            seen.add(u)
            candidates.append(u)
    products = []
    for u in candidates:
        if len(products) >= max_images:
            break
        name = f"product-{len(products)+1}{_ext(u)}"
        if download(u, out / name, url):
            products.append(name)

    accent = pick_accent(data)
    failure = diagnose(data, products)
    brand_json = {
        "brand": brand, "slug": slug, "source_url": url,
        "status": "failed" if failure else "ok",
        "error": failure,
        "detected": {
            "title": data.get("title"), "description": data.get("description"),
            "body_font": data.get("bodyFont"), "title_font": data.get("titleFont"),
            "theme_color": data.get("theme"), "bg": data.get("bg"), "text": data.get("text"),
            "cta_colors": data.get("ctaColors"),
        },
        "proposed_tokens": {"--accent": accent},
        "logo": logo_file,
        "logo_source": logo_source,
        "product_images": products,
    }
    (out / "brand.json").write_text(json.dumps(brand_json, indent=2, ensure_ascii=False), encoding="utf-8")

    if failure:
        print(f"✗ crawl {brand} ÉCHOUÉ : {failure}")
        print(f"  (brand.json écrit avec status=failed dans {out}/)")
        if logo_source == "Wikidata/Commons":
            print(f"  ✓ logo tout de même récupéré via Wikidata → {logo_file}")
        print("\n→ Fallback :")
        print("  1. navigateur manquant ?  → pip install -r requirements.txt && playwright install chromium")
        print("  2. site trop protégé :")
        print("     · logo → déjà tenté via Wikidata (ci-dessus) ;")
        print("     · images produit → demande à l'utilisateur les URL + noms, puis :")
        print(f"       python3 scripts/crawl_brand.py --fetch <url1> <url2>… --slug {slug}")
        print("     · ou déduis l'ambiance du nom + secteur et signale-le à l'utilisateur.")
        return out

    print(f"✓ crawl {brand} → {out}/")
    print(f"  logo           : {logo_file or '⚠ non trouvé'}")
    print(f"  images produit : {len(products)}  {products}")
    print(f"  accent proposé : {accent}   (CTA détectés : {data.get('ctaColors')})")
    print(f"  typo           : {data.get('titleFont','?')[:60]}")
    print(f"\n→ relis {out}/brand.json, propose l'ambiance en Phase 1, puis valide avec l'utilisateur.")
    return out


def fetch_urls(urls: list, slug: str) -> Path:
    """Backup manuel : télécharge des URL d'images fournies par l'utilisateur (produits) en
    product-N.* dans <slug>-brand/. Utile quand le site de marque bloque le crawl mais que
    l'utilisateur a les URL des visuels (marketplace, presse, réseaux). Referer neutralisé."""
    out = Path.cwd() / f"{slug}-brand"
    out.mkdir(exist_ok=True)
    saved = []
    for u in urls:
        ref = f"{urlparse(u).scheme}://{urlparse(u).netloc}/"  # referer = origine de l'image
        name = f"product-{len(saved)+1}{_ext(u)}"
        if download(u, out / name, ref):
            saved.append(name)
            print(f"  ✓ {name}  ← {u}")
        else:
            print(f"  ✗ échec : {u}")
    print(f"\n{len(saved)}/{len(urls)} image(s) dans {out}/ — référence-les dans le manifest "
          f"(clé assets, par basename) comme au Plan B.")
    return out


def selfcheck():
    """Sans réseau : charge un HTML en mémoire, vérifie l'extraction JS + pick_accent."""
    from playwright.sync_api import sync_playwright
    html = """<!doctype html><html><head><title>ACME — Voitures</title>
      <meta name=description content="desc test">
      <meta name=theme-color content="#0a5">
      <meta property="og:image" content="https://ex.test/hero.jpg"></head>
      <body style="background:#111;color:#eee;font-family:Georgia">
        <header><img class=logo alt="ACME logo" src="https://ex.test/logo.png"></header>
        <h1 style="font-family:'Brand Sans'">Titre</h1>
        <a style="background:#cc0022;width:120px;height:40px;display:inline-block">CTA</a>
        <a style="background:#333;width:120px;height:40px;display:inline-block">gris</a>
      </body></html>"""
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.set_content(html, wait_until="domcontentloaded")
        d = pg.evaluate(EXTRACT_JS)
        b.close()
    assert d["title"] == "ACME — Voitures", d["title"]
    assert d["logo"] == "https://ex.test/logo.png", d["logo"]
    assert d["ogImages"] == ["https://ex.test/hero.jpg"], d["ogImages"]
    assert d["theme"] == "#0a5", d["theme"]  # meta content brut, non normalisé
    assert "#cc0022" in d["ctaColors"] and "Brand Sans" in d["titleFont"], d
    # pick_accent doit sauter le gris #333 et prendre le rouge saturé
    assert pick_accent(d) == "#cc0022", pick_accent(d)
    # fallback quand aucun CTA coloré → theme-color
    assert pick_accent({"ctaColors": ["#333333"], "theme": "#0a5"}) == "#0a5"
    assert _ext("https://x/a.JPEG?v=2") == ".jpg" and _ext("https://x/b") == ".jpg"
    # _is_valid_download : SVG minuscule mais valide (logo Nike = 966 o) OK ; raster < 1 Ko rejeté
    assert _is_valid_download(b'<?xml version="1.0"?><svg xmlns="...">...</svg>', ".svg")
    assert not _is_valid_download(b"pas du svg", ".svg")
    assert not _is_valid_download(b"x" * 500, ".png") and _is_valid_download(b"x" * 2000, ".png")
    # _ext sur une URL Commons FilePath (extension dans le nom de fichier)
    assert _ext("https://commons.wikimedia.org/wiki/Special:FilePath/Audi_logo.svg") == ".svg"
    # diagnose : titre anti-bot → échec ; page vide → échec ; crawl normal → None
    assert diagnose({"title": "Site currently not available"}, [])
    assert diagnose({"title": "OK", "logo": None}, [])
    assert diagnose({"title": "Accueil | Audi", "logo": "x"}, ["product-1.jpg"]) is None

    # --- wikidata_logo_url sans réseau : on mocke _json_get selon l'URL demandée ---
    global _json_get
    real = _json_get
    def fake(url):
        if "wbsearchentities" in url:
            return {"search": [{"id": "Q123"}]}
        if "EntityData/Q123" in url:
            return {"entities": {"Q123": {"claims":
                {"P154": [{"mainsnak": {"datavalue": {"value": "ACME logo.svg"}}}]}}}}
        return None
    _json_get = fake
    try:
        u = wikidata_logo_url("ACME")
        assert u == "https://commons.wikimedia.org/wiki/Special:FilePath/ACME_logo.svg", u
        # pas d'entité trouvée → None
        _json_get = lambda url: {"search": []} if "wbsearchentities" in url else None
        assert wikidata_logo_url("Inconnue") is None
        # entité sans claim P154 → None
        _json_get = lambda url: ({"search": [{"id": "Q9"}]} if "wbsearchentities" in url
                                 else {"entities": {"Q9": {"claims": {}}}})
        assert wikidata_logo_url("SansLogo") is None
    finally:
        _json_get = real
    print("selfcheck OK")


def main():
    ap = argparse.ArgumentParser(description="Crawle une marque (Chromium headless) pour la Phase 1.")
    ap.add_argument("url", nargs="?", help="URL du site de la marque (https)")
    ap.add_argument("--brand", help="nom de la marque")
    ap.add_argument("--slug", help="slug (dossier de sortie <slug>-brand/)")
    ap.add_argument("--max-images", type=int, default=6)
    ap.add_argument("--fetch", nargs="+", metavar="URL",
                    help="backup manuel : télécharge ces URL d'images produit (avec --slug)")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.selfcheck:
        selfcheck(); return
    if a.fetch:
        if not a.slug:
            ap.error("--fetch nécessite --slug (dossier <slug>-brand/)")
        fetch_urls(a.fetch, a.slug); return
    if not (a.url and a.brand):
        ap.error("fournis une URL et --brand (ou --selfcheck, ou --fetch)")
    crawl(a.url, a.brand, a.slug or urlparse(a.url).netloc.split(".")[-2], a.max_images)


if __name__ == "__main__":
    main()
