#!/usr/bin/env python3
"""Pré-remplit la Phase 1 de salesforce-holodeck-creator : logo, images produit, palette, typo.

Pourquoi un navigateur et pas WebFetch/curl : les sites de marque (audi.fr…) sont
derrière un anti-bot de CDN qui renvoie 503 à tout client sans JS. Un vrai navigateur
exécute le JS → il passe.

DEUX MOTEURS, dans cet ordre de préférence :

  1. **Navigateur intégré de l'app Claude** (par défaut — AUCUNE installation).
     Claude ouvre le site lui-même, exécute le JS d'extraction, enregistre le résultat
     brut dans un fichier JSON, puis appelle ce script en mode `--from-browser`.
     Le script fait toute la post-production en stdlib pure : cascade logo, téléchargement
     des visuels, choix de l'accent, écriture de brand.json.

  2. **Playwright/Chromium** (fallback) : le script pilote lui-même un navigateur headless.
     Nécessite `pip install playwright && playwright install chromium`.

Dans les deux cas le script PROPOSE (couleurs, produits) et TÉLÉCHARGE (logo + images) ;
c'est toujours l'utilisateur qui valide l'ambiance en chat (Phase 1).

Sortie dans ./<slug>-brand/ :
    brand.json     — couleurs proposées, typo, secteur/produits détectés, images, logo_source
    logo.(svg|png) — logo de la marque, cascade : DOM → SVG inline → Wikidata/Commons → icon.horse
    product-N.*    — les plus grandes images produit rendues (og:image en premier)

Le logo passe par une cascade de sources : même quand un site bloque le crawl, son vrai
logo officiel est souvent récupérable via Wikidata (propriété P154), non bloqué par anti-bot.

Usage :
    # 1. navigateur intégré de l'app Claude (par défaut, zéro installation)
    python3 scripts/crawl_brand.py --print-extract-js            # le JS à exécuter dans la page
    python3 scripts/crawl_brand.py --from-browser extract.json \
            --brand Audi --slug audi --source-url https://www.audi.fr

    # 2. fallback Playwright (pilote son propre Chromium)
    python3 scripts/crawl_brand.py https://www.audi.fr --brand Audi --slug audi

    # utilitaires (stdlib pure, aucun navigateur)
    python3 scripts/crawl_brand.py --fetch <url…> --slug audi    # images produit par URL directe
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
  // --- catalogue de liens produit : <a> qui enveloppe une image (cartes produit) ---
  // On ne DEVINE jamais d'URL : on récolte les liens RÉELS de la page (URL + libellé), à
  // matcher plus tard (produit de la story → lien réel) puis re-crawler via --pages pour la
  // vraie photo. Même origine seulement (écarte réseaux sociaux/paiement) ; en test (origin
  // 'null' pour about:blank/data:) on ne filtre pas l'origine → parser vérifiable hors ligne.
  const origin = location.origin && location.origin !== 'null' ? location.origin : null;
  const seenH = new Set();
  const productLinks = [];
  for (const a of document.querySelectorAll('a[href]')) {
    if (!a.querySelector('img')) continue;                       // carte produit = lien AVEC visuel
    const href = abs(a.getAttribute('href'));
    if (!href || (origin && !href.startsWith(origin)) || seenH.has(href)) continue;
    const label = ((a.querySelector('img').alt || a.textContent || '')
                    .trim().replace(/\s+/g, ' ')).slice(0, 80);
    if (!label) continue;
    seenH.add(href);
    productLinks.push({ href, label });
    if (productLinks.length >= 24) break;
  }
  return {
    title: document.title,
    description: document.querySelector('meta[name=description]')?.content || '',
    logo, logoSvg,
    ogImages: og,
    images: imgs.slice(0, 12),
    productLinks,
    theme,
    bg: rgb2hex(bodyCS.backgroundColor),
    text: rgb2hex(bodyCS.color),
    ctaColors: [...new Set(ctas)].slice(0, 10),
    bodyFont: bodyCS.fontFamily,
    titleFont: titleEl ? getComputedStyle(titleEl).fontFamily : bodyCS.fontFamily,
  };
}
"""

# JS de 2e passe : exécuté sur UNE page produit (Phase 3), renvoie son visuel exact.
# Même logique que crawl_pages() mais côté navigateur intégré : Claude récolte les URL
# puis les télécharge d'un coup avec --fetch (stdlib, aucun navigateur).
PRODUCT_JS = r"""
() => {
  const abs = (u) => { try { return new URL(u, location.href).href } catch { return null } };
  const og = document.querySelector('meta[property="og:image"], meta[name="twitter:image"]');
  const biggest = [...document.querySelectorAll('img')]
    .map(i => ({ url: abs(i.currentSrc || i.src), a: i.naturalWidth * i.naturalHeight }))
    .filter(x => x.url && !x.url.startsWith('data:') && !/\.svg($|\?)/i.test(x.url))
    .sort((a, b) => b.a - a.a)[0];
  return {
    page: location.href,
    title: document.title,
    image: (og && abs(og.content)) || (biggest && biggest.url) || null,
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
    def as_hex(c):
        """theme-color accepte des mots-clés CSS (« white », « rebeccapurple ») et la forme
        courte #abc. Le manifest, lui, attend un hex à 7 caractères : on normalise ce qu'on
        peut et on rejette le reste, plutôt que d'écrire --accent: white dans brand.json."""
        if not isinstance(c, str):
            return None
        c = c.strip().lower()
        if re.fullmatch(r"#[0-9a-f]{6}", c):
            return c
        if re.fullmatch(r"#[0-9a-f]{3}", c):
            return "#" + "".join(ch * 2 for ch in c[1:])
        return {"white": "#ffffff", "black": "#000000"}.get(c)

    for c in data.get("ctaColors", []):
        if not is_neutral(c):
            return c
    for candidate in (data.get("theme"), data.get("bg")):
        h = as_hex(candidate)
        if h and not is_neutral(h):
            return h
    return "#1c2b4a"


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


def _require_playwright():
    """Absence de Playwright = message d'action, pas de stack trace.

    Le crawl est la SEULE partie du skill qui a besoin d'un navigateur.
    build_site.py est en stdlib pure et fonctionne sans rien installer.
    """
    try:
        from playwright.sync_api import sync_playwright as _sp
    except ModuleNotFoundError:
        import sys
        print("\u2717 Playwright n'est pas install\u00e9 \u2014 le crawl automatique de la marque est indisponible.")
        print("")
        print("  Ce n'est PAS bloquant : la g\u00e9n\u00e9ration du site fonctionne sans navigateur.")
        print("  \u2192 continue sans crawl : fournis le logo et 2 \u00e0 4 photos produit en local,")
        print("    ou des URL d'images, et r\u00e9f\u00e9rence-les dans la cl\u00e9 `assets` du manifest.")
        print("")
        print("  Pour activer le crawl plus tard (une seule fois par machine) :")
        print("    pip install playwright && playwright install chromium")
        sys.exit(3)
    return _sp


def crawl(url: str, brand: str, slug: str, max_images: int = 6) -> Path:
    sync_playwright = _require_playwright()

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

    return build_brand_json(data, url, brand, slug, max_images, engine="Playwright")


def build_brand_json(data: dict, url: str, brand: str, slug: str,
                     max_images: int = 6, engine: str = "Playwright") -> Path:
    """Post-production commune aux deux moteurs — STDLIB PURE, aucun navigateur requis.

    `data` = le dictionnaire renvoyé par EXTRACT_JS, d'où qu'il vienne : évalué par
    Playwright (mode fallback) ou par le navigateur intégré de l'app Claude (mode
    `--from-browser`). Écrit <slug>-brand/ : brand.json, logo.*, product-N.*
    """
    out = Path.cwd() / f"{slug}-brand"
    out.mkdir(exist_ok=True)
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
        "engine": engine,
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
        # liens produit RÉELS de la home, à re-crawler après la story validée (--pages) pour
        # les visuels exacts. Claude matche produit-de-la-story → href, ne DEVINE aucune URL.
        "product_links": data.get("productLinks", []),
    }
    (out / "brand.json").write_text(json.dumps(brand_json, indent=2, ensure_ascii=False), encoding="utf-8")

    if failure:
        print(f"✗ crawl {brand} ÉCHOUÉ : {failure}")
        print(f"  (brand.json écrit avec status=failed dans {out}/)")
        if logo_source == "Wikidata/Commons":
            print(f"  ✓ logo tout de même récupéré via Wikidata → {logo_file}")
        print("\n→ Fallback, dans cet ordre :")
        print("  1. re-tente avec le NAVIGATEUR INTÉGRÉ de l'app Claude (aucune installation) :")
        print("     ouvre la page, scrolle par paliers pour hydrater les visuels, exécute le JS")
        print("     de --print-extract-js, enregistre le résultat, puis :")
        print(f"       python3 scripts/crawl_brand.py --from-browser <fichier>.json --brand \"{brand}\" --slug {slug}")
        print("  2. site trop protégé, même dans un vrai navigateur :")
        print("     · logo → déjà tenté via Wikidata (ci-dessus) ;")
        print("     · images produit → demande à l'utilisateur les URL + noms, puis :")
        print(f"       python3 scripts/crawl_brand.py --fetch <url1> <url2>… --slug {slug}")
        print("     · ou déduis l'ambiance du nom + secteur et signale-le à l'utilisateur.")
        return out

    print(f"✓ crawl {brand} → {out}/   (moteur : {engine})")
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


def crawl_pages(urls: list, slug: str) -> Path:
    """2e passe (après story validée) : visite chaque PAGE produit avec le vrai navigateur et
    télécharge son visuel exact (og:image en priorité, sinon la plus grande image rendue) en
    product-N.*. Contrairement à --fetch (URL d'images DIRECTES), ici on donne des URL de PAGES
    — typiquement des `href` du catalogue `product_links` de brand.json (jamais devinées). Passe
    l'anti-bot comme crawl() (même furtivité). Les échecs sont best-effort : on saute et on continue."""
    sync_playwright = _require_playwright()

    out = Path.cwd() / f"{slug}-brand"
    out.mkdir(exist_ok=True)
    saved = []
    launch = dict(args=["--disable-blink-features=AutomationControlled"])
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", **launch)
        except Exception:
            browser = p.chromium.launch(**launch)
        ctx = browser.new_context(user_agent=UA, viewport={"width": 1440, "height": 900}, locale="fr-FR")
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        for u in urls:
            img_url = None
            try:
                page = ctx.new_page()
                page.goto(u, wait_until="domcontentloaded", timeout=45000)
                try:
                    page.wait_for_selector("img[src]:not([src^='data:'])", timeout=8000)
                except Exception:
                    pass
                page.evaluate("scrollTo(0, document.body.scrollHeight*0.4)")
                page.wait_for_timeout(600)
                d = page.evaluate(EXTRACT_JS)
                page.close()
                imgs = [i["url"] for i in d.get("images", [])]  # déjà triées par surface
                img_url = (d.get("ogImages") or imgs or [None])[0]
            except Exception as e:
                print(f"  ⚠ page non chargée ({u}) : {e}")
            if not img_url:
                print(f"  ✗ pas de visuel trouvé sur {u}")
                continue
            name = f"product-{len(saved)+1}{_ext(img_url)}"
            if download(img_url, out / name, u):        # referer = la page produit (passe le CDN)
                saved.append(name)
                print(f"  ✓ {name}  ← {u}")
            else:
                print(f"  ✗ échec téléchargement du visuel de {u}")
        browser.close()
    print(f"\n{len(saved)}/{len(urls)} visuel(s) dans {out}/ — référence-les dans le manifest "
          f"(clé assets, par basename).")
    return out


def from_browser(payload_path: str, brand: str, slug: str,
                 source_url: str | None = None, max_images: int = 6) -> Path:
    """Mode PAR DÉFAUT : le navigateur intégré de l'app Claude a déjà fait le rendu.

    `payload_path` = un fichier JSON contenant EXACTEMENT ce que EXTRACT_JS a renvoyé
    dans la page (Claude l'exécute via l'outil JavaScript du navigateur intégré, puis
    enregistre le résultat). On accepte aussi un enveloppage {"result": {...}} ou
    {"value": {...}}, parce que les outils navigateur emballent parfois la valeur.

    Aucune dépendance : tout le reste (logo, images, accent) est du stdlib.
    """
    raw = Path(payload_path)
    if not raw.exists():
        print(f"✗ fichier introuvable : {payload_path}")
        sys.exit(2)
    try:
        data = json.loads(raw.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"✗ JSON invalide dans {payload_path} : {e}")
        print("  → enregistre la valeur BRUTE renvoyée par EXTRACT_JS, sans texte autour.")
        sys.exit(2)
    for key in ("result", "value", "data"):          # déballage tolérant
        if isinstance(data, dict) and key in data and isinstance(data[key], dict):
            data = data[key]
    if not isinstance(data, dict):
        print(f"✗ le payload doit être un objet JSON, reçu : {type(data).__name__}")
        sys.exit(2)
    expected = {"title", "logo", "ogImages", "images", "productLinks", "ctaColors"}
    if not expected & set(data):
        print("✗ payload non reconnu : aucune clé d'EXTRACT_JS trouvée.")
        print(f"  clés reçues : {sorted(data)[:12]}")
        print("  → récupère le JS avec : python3 scripts/crawl_brand.py --print-extract-js")
        sys.exit(2)

    url = source_url or data.get("sourceUrl") or ""
    if not url:
        print("⚠ pas de --source-url : le referer des téléchargements sera vide et")
        print("  certains CDN refuseront les images. Passe --source-url <url de la page>.")
    return build_brand_json(data, url, brand, slug, max_images,
                            engine="navigateur intégré (app Claude)")


def selfcheck():
    """Sans réseau ni navigateur pour l'essentiel.

    Partie A (toujours) : parsing du payload --from-browser, post-production, helpers.
    Partie B (seulement si Playwright est installé) : extraction DOM réelle par EXTRACT_JS.
    """
    _selfcheck_stdlib()
    try:
        from playwright.sync_api import sync_playwright
    except ModuleNotFoundError:
        print("selfcheck OK (partie stdlib ; Playwright absent → extraction DOM non testée,")
        print("  c'est normal : le moteur par défaut est le navigateur intégré de l'app Claude)")
        return
    html = """<!doctype html><html><head><title>ACME — Voitures</title>
      <meta name=description content="desc test">
      <meta name=theme-color content="#0a5">
      <meta property="og:image" content="https://ex.test/hero.jpg"></head>
      <body style="background:#111;color:#eee;font-family:Georgia">
        <header><img class=logo alt="ACME logo" src="https://ex.test/logo.png"></header>
        <h1 style="font-family:'Brand Sans'">Titre</h1>
        <a style="background:#cc0022;width:120px;height:40px;display:inline-block">CTA</a>
        <a style="background:#333;width:120px;height:40px;display:inline-block">gris</a>
        <a href="https://ex.test/p/manteau-will"><img alt="Le manteau Will" src="https://ex.test/m.jpg"></a>
        <a href="https://ex.test/mentions-legales">texte sans image</a>
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
    # catalogue product_links : le <a> AVEC image est capté (href absolu + libellé = alt),
    # le <a> sans image est écarté. Origine non filtrée en test (about:blank → origin null).
    assert d["productLinks"] == [{"href": "https://ex.test/p/manteau-will",
                                  "label": "Le manteau Will"}], d["productLinks"]
    assert d["theme"] == "#0a5", d["theme"]  # meta content brut, non normalisé
    assert "#cc0022" in d["ctaColors"] and "Brand Sans" in d["titleFont"], d
    # pick_accent doit sauter le gris #333 et prendre le rouge saturé
    assert pick_accent(d) == "#cc0022", pick_accent(d)
    print("selfcheck OK (stdlib + extraction DOM Playwright)")


def _selfcheck_stdlib():
    """Tout ce qui ne demande aucun navigateur — dont le mode --from-browser."""
    import tempfile, os
    # fallback quand aucun CTA coloré → theme-color
    # theme-color en forme courte → normalisé en hex 7 caractères
    assert pick_accent({"ctaColors": ["#333333"], "theme": "#0a5"}) == "#00aa55"
    # theme-color en mot-clé CSS neutre → jamais écrit tel quel dans brand.json
    assert pick_accent({"ctaColors": ["#000000"], "theme": "white"}) == "#1c2b4a"
    assert pick_accent({"ctaColors": [], "theme": "rebeccapurple"}) == "#1c2b4a"
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

    # --- mode --from-browser : payload d'EXTRACT_JS → brand.json, sans navigateur ---
    payload = {
        "title": "ACME — Voitures", "description": "desc",
        "logo": None, "logoSvg": "<svg xmlns='http://www.w3.org/2000/svg'><rect/></svg>",
        "ogImages": [], "images": [], "productLinks": [{"href": "https://ex.test/p/1",
                                                        "label": "Manteau"}],
        "theme": "#0a5", "bg": "#111111", "text": "#eeeeee",
        "ctaColors": ["#333333", "#cc0022"],
        "bodyFont": "Georgia", "titleFont": "Brand Sans",
    }
    cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        try:
            Path("payload.json").write_text(json.dumps({"result": payload}), encoding="utf-8")
            out = from_browser("payload.json", "ACME", "acme", "https://ex.test/")
            bj = json.loads((out / "brand.json").read_text(encoding="utf-8"))
            assert bj["engine"] == "navigateur intégré (app Claude)", bj["engine"]
            assert bj["proposed_tokens"]["--accent"] == "#cc0022", bj["proposed_tokens"]
            assert bj["logo"] == "logo.svg" and bj["logo_source"] == "site (SVG inline)", bj
            assert bj["product_links"][0]["label"] == "Manteau", bj["product_links"]
            assert (out / "logo.svg").exists()
        finally:
            os.chdir(cwd)


def main():
    ap = argparse.ArgumentParser(
        description="Pré-remplit la Phase 1 d'un holodeck. Moteur par défaut : le navigateur "
                    "intégré de l'app Claude (--print-extract-js puis --from-browser). "
                    "Playwright n'est qu'un fallback.")
    ap.add_argument("url", nargs="?", help="[fallback Playwright] URL du site de la marque")
    ap.add_argument("--brand", help="nom de la marque")
    ap.add_argument("--slug", help="slug (dossier de sortie <slug>-brand/)")
    ap.add_argument("--max-images", type=int, default=6)
    ap.add_argument("--print-extract-js", nargs="?", const="home", choices=["home", "product"],
                    metavar="home|product",
                    help="imprime le JS à exécuter dans le navigateur intégré de l'app Claude : "
                         "'home' (défaut) pour la page d'accueil, 'product' pour une page produit")
    ap.add_argument("--from-browser", metavar="PAYLOAD.json",
                    help="MODE PAR DÉFAUT : construit brand.json depuis le résultat brut du JS "
                         "exécuté par le navigateur intégré (avec --brand, --slug, --source-url)")
    ap.add_argument("--source-url", metavar="URL",
                    help="URL de la page d'où vient le payload --from-browser (referer des "
                         "téléchargements ; sans elle certains CDN refusent les images)")
    ap.add_argument("--fetch", nargs="+", metavar="URL",
                    help="télécharge ces URL d'images DIRECTES (avec --slug). Stdlib pure : "
                         "c'est le compagnon de --print-extract-js product.")
    ap.add_argument("--pages", nargs="+", metavar="URL",
                    help="[fallback Playwright] visite ces PAGES produit et prend leur visuel "
                         "(avec --slug). URL = href du catalogue product_links (jamais devinées).")
    ap.add_argument("--selfcheck", action="store_true")
    a = ap.parse_args()
    if a.print_extract_js:
        # Forme IIFE : c'est ce qu'attend l'outil JavaScript du navigateur intégré, qui
        # renvoie la valeur de la DERNIÈRE EXPRESSION. (page.evaluate de Playwright, lui,
        # veut la fonction nue — il la reçoit via EXTRACT_JS directement, pas par ici.)
        body = PRODUCT_JS if a.print_extract_js == "product" else EXTRACT_JS
        print("(" + body.strip() + ")()")
        return
    if a.selfcheck:
        selfcheck(); return
    if a.from_browser:
        if not (a.brand and a.slug):
            ap.error("--from-browser nécessite --brand et --slug")
        from_browser(a.from_browser, a.brand, a.slug, a.source_url, a.max_images); return
    if a.pages:
        if not a.slug:
            ap.error("--pages nécessite --slug (dossier <slug>-brand/)")
        crawl_pages(a.pages, a.slug); return
    if a.fetch:
        if not a.slug:
            ap.error("--fetch nécessite --slug (dossier <slug>-brand/)")
        fetch_urls(a.fetch, a.slug); return
    if not (a.url and a.brand):
        ap.error("fournis une URL et --brand.\n"
                 "  Chemin recommandé (aucune installation) : --print-extract-js puis --from-browser.\n"
                 "  Autres modes : --fetch, --selfcheck.")
    crawl(a.url, a.brand, a.slug or urlparse(a.url).netloc.split(".")[-2], a.max_images)


if __name__ == "__main__":
    main()
