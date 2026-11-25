"""Tests automatisés du portfolio (version 1.0).

Usage :
    pip install playwright && playwright install chromium
    python3 -m http.server 8000            # depuis le dossier parent du dépôt
    python3 tests/run_tests.py http://localhost:8000/portfolio-adjimflaubert/

Options : --chrome /chemin/vers/chrome   (navigateur à utiliser)
          --axe /chemin/vers/axe.min.js  (active l'audit d'accessibilité axe-core)

Le script vérifie les fichiers (références, ancres, images, métadonnées) puis le
comportement dans un vrai navigateur à 320, 375, 768, 1024 et 1440 px.
Code de sortie 0 si tout passe, 1 sinon.
"""
import argparse
import asyncio
import json
import os
import re
import sys
from urllib.parse import unquote, urlparse, parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("  OK   " if ok else "  ÉCHEC ") + name + (f" — {detail}" if detail and not ok else ""))


def static_tests():
    print("\n[1] Fichiers et métadonnées")
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

    # Références locales
    missing = []
    for ref in re.findall(r'(?:href|src|srcset)="([^"]+)"', html):
        for part in ref.split(","):
            url = part.strip().split(" ")[0]
            if not url or url.startswith(("http", "mailto:", "tel:", "#", "data:")):
                continue
            if not os.path.exists(os.path.join(ROOT, unquote(url))):
                missing.append(url)
    for url in re.findall(r'url\("\.\./([^"]+)"\)', open(os.path.join(ROOT, "assets/css/style.css"), encoding="utf-8").read()):
        if not os.path.exists(os.path.join(ROOT, "assets", url)):
            missing.append(url)
    manifest = json.load(open(os.path.join(ROOT, "site.webmanifest"), encoding="utf-8"))
    for icon in manifest["icons"]:
        if not os.path.exists(os.path.join(ROOT, icon["src"])):
            missing.append(icon["src"])
    check("Toutes les ressources locales existent", not missing, ", ".join(missing))

    # Ancres internes
    ids = set(re.findall(r'\sid="([^"]+)"', html))
    broken = [a for a in re.findall(r'href="#([^"]*)"', html) if a and a not in ids]
    check("Toutes les ancres internes ont une cible", not broken, ", ".join(broken))
    dup = [i for i in ids if len(re.findall(r'\sid="%s"' % re.escape(i), html)) > 1]
    check("Aucun identifiant en double", not dup, ", ".join(dup))

    # Images
    imgs = re.findall(r"<img\b[^>]*>", html)
    no_alt = [i for i in imgs if not re.search(r'\salt="[^"]+"', i)]
    no_dim = [i for i in imgs if not (re.search(r'\swidth="\d+"', i) and re.search(r'\sheight="\d+"', i))]
    check(f"{len(imgs)} images avec un texte alternatif", not no_alt, str(len(no_alt)) + " sans alt")
    check("Images avec dimensions déclarées (pas de décalage de mise en page)", not no_dim, str(len(no_dim)))

    # Titres
    h1 = re.findall(r"<h1\b", html)
    check("Un seul titre H1", len(h1) == 1, str(len(h1)))

    # Métadonnées
    title = re.search(r"<title>(.*?)</title>", html).group(1)
    desc = re.search(r'<meta name="description" content="([^"]+)"', html).group(1)
    check("Titre de 30 à 65 caractères", 30 <= len(title) <= 65, f"{len(title)} caractères")
    check("Description de 120 à 230 caractères", 120 <= len(desc) <= 230, f"{len(desc)} caractères")
    for needle in ['rel="canonical"', 'property="og:title"', 'property="og:image"', 'name="twitter:card"', 'rel="manifest"', 'http-equiv="Content-Security-Policy"']:
        check(f"Présence de {needle}", needle in html)
    ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    try:
        data = json.loads(ld.group(1))
        types = sorted(n["@type"] for n in data["@graph"])
        check("Données structurées JSON-LD valides (WebSite, ProfilePage, Person)", types == ["Person", "ProfilePage", "WebSite"], str(types))
    except Exception as exc:  # noqa: BLE001
        check("Données structurées JSON-LD valides", False, str(exc))

    # Liens externes
    ext = re.findall(r'<a\b[^>]*href="https?://[^"]+"[^>]*>', html)
    unsafe = [a for a in ext if 'target="_blank"' in a and "noopener" not in a]
    check(f"{len(ext)} liens externes protégés par noopener", not unsafe, str(len(unsafe)))

    # Sécurité du script
    js = open(os.path.join(ROOT, "assets/js/script.js"), encoding="utf-8").read()
    check("Aucun innerHTML / eval / document.write dans le script", not re.search(r"innerHTML|eval\(|document\.write", js))
    check("Aucun script en ligne exécutable dans la page", not re.search(r"<script(?![^>]*(src=|application/ld\+json))", html))


async def browser_tests(url, chrome, axe_path):
    from playwright.async_api import async_playwright

    print("\n[2] Navigateur")
    hidden_js = """() => [...document.querySelectorAll('main *')].filter(e => {
        if (!e.textContent.trim() || e.children.length || e.closest('.visually-hidden') || e.closest('[hidden]') || e.closest('details:not([open])')) return false;
        let n = e; while (n && n !== document.body) { const cs = getComputedStyle(n);
          if (cs.opacity === '0' || cs.visibility === 'hidden' || cs.display === 'none') return true; n = n.parentElement; }
        return false; }).map(e => e.textContent.trim().slice(0, 40))"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else await p.chromium.launch()
        for w, h, mob in [(320, 640, True), (375, 812, True), (768, 1024, True), (1024, 768, False), (1440, 900, False)]:
            ctx = await browser.new_context(viewport={"width": w, "height": h}, is_mobile=mob, has_touch=mob)
            page = await ctx.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.on("console", lambda m: m.type == "error" and errors.append(m.text))
            failed = []
            page.on("requestfailed", lambda r: (r.url.startswith(url) and failed.append(r.url)))
            await page.goto(url, wait_until="networkidle")
            height = await page.evaluate("document.body.scrollHeight")
            for y in range(0, height, 300):
                await page.evaluate(f"scrollTo({{top:{y},behavior:'instant'}})")
                await page.wait_for_timeout(30)
            await page.wait_for_timeout(1500)
            overflow = await page.evaluate("document.documentElement.scrollWidth - innerWidth")
            hidden = await page.evaluate(hidden_js)
            small_targets = await page.evaluate("""() => [...document.querySelectorAll('main a.button, main button, .menu-button, .project-form input, .project-form select')]
                .filter(e => e.offsetParent && e.getBoundingClientRect().height < 44).map(e => e.textContent.trim() || e.id)""")
            check(f"{w}px : aucune erreur JavaScript", not errors, "; ".join(errors[:3]))
            check(f"{w}px : aucune ressource locale en échec", not failed, ", ".join(failed[:3]))
            check(f"{w}px : pas de défilement horizontal", overflow <= 0, f"{overflow}px")
            check(f"{w}px : aucun texte resté invisible après défilement", not hidden, ", ".join(hidden[:5]))
            check(f"{w}px : cibles tactiles d'au moins 44 px", not small_targets, ", ".join(small_targets[:5]))
            await ctx.close()

        # Aucun texte ne doit croiser le fil rouge (largeurs où il est au tiers de la page)
        cross_js = """() => {
          const fil = document.querySelector('.fil'); if (!fil || getComputedStyle(fil).display === 'none') return [];
          const fr = fil.getBoundingClientRect(); const x = fr.left + fr.width / 2;
          const out = []; const walker = document.createTreeWalker(document.querySelector('main'), NodeFilter.SHOW_TEXT);
          let n; while ((n = walker.nextNode())) {
            if (!n.textContent.trim()) continue;
            const el = n.parentElement; if (el.closest('.visually-hidden, details:not([open]), [aria-hidden=true]')) continue;
            const r = document.createRange(); r.selectNodeContents(n);
            for (const b of r.getClientRects()) {
              const top = b.top + window.scrollY;
              if (b.width && b.left < x - 2 && b.right > x + 2 && top > fr.top + window.scrollY) { out.push(n.textContent.trim().slice(0, 40)); break; }
            } }
          return [...new Set(out)]; }"""
        for w in (900, 1000, 1080, 1280, 1440):
            ctx = await browser.new_context(viewport={"width": w, "height": 900})
            page = await ctx.new_page()
            await page.goto(url, wait_until="networkidle")
            height = await page.evaluate("document.body.scrollHeight")
            for y in range(0, height, 400):
                await page.evaluate(f"scrollTo({{top:{y},behavior:'instant'}})")
                await page.wait_for_timeout(25)
            await page.wait_for_timeout(1200)
            crossing = await page.evaluate(cross_js)
            check(f"{w}px : aucun texte ne croise le fil rouge", not crossing, " | ".join(crossing[:5]))
            await ctx.close()

        # Accessibilité axe-core (le CSP de la page est contourné pour l'outil de test uniquement)
        if axe_path:
            axe = open(axe_path, encoding="utf-8").read()
            for w, h in [(1440, 900), (375, 812)]:
                ctx = await browser.new_context(viewport={"width": w, "height": h}, bypass_csp=True)
                page = await ctx.new_page()
                await page.goto(url, wait_until="networkidle")
                height = await page.evaluate("document.body.scrollHeight")
                for y in range(0, height, 400):
                    await page.evaluate(f"scrollTo({{top:{y},behavior:'instant'}})")
                    await page.wait_for_timeout(30)
                await page.wait_for_timeout(1500)
                await page.evaluate(axe)
                res = await page.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']})")
                v = [f"{x['id']} ({len(x['nodes'])})" for x in res["violations"]]
                check(f"axe-core {w}px : aucune violation ({len(res['passes'])} règles respectées)", not v, ", ".join(v))
                await ctx.close()

        # Menu replié
        ctx = await browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
        page = await ctx.new_page()
        await page.goto(url, wait_until="networkidle")
        await page.click(".menu-button")
        await page.wait_for_timeout(300)
        check("Menu : s'ouvre et annonce aria-expanded=true", await page.get_attribute(".menu-button", "aria-expanded") == "true")
        check("Menu : le focus passe sur le premier lien", (await page.evaluate("document.activeElement.textContent")).strip() == "Profil")
        for _ in range(12):
            await page.keyboard.press("Tab")
        inside = await page.evaluate("!!document.activeElement.closest('.site-header')")
        check("Menu : le focus reste piégé dans le menu", inside)
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
        check("Menu : Échap ferme le menu et rend le focus au bouton",
              await page.get_attribute(".menu-button", "aria-expanded") == "false" and await page.evaluate("document.activeElement.classList.contains('menu-button')"))
        await page.click(".menu-button")
        await page.click('.nav__list a[href="#projets"]')
        await page.wait_for_timeout(2500)  # laisser finir le défilement fluide
        check("Menu : un lien ferme le menu et mène à la section", await page.get_attribute(".menu-button", "aria-expanded") == "false" and await page.evaluate("Math.abs(document.getElementById('projets').getBoundingClientRect().top) < 120"))
        await ctx.close()

        # Détail repliable des projets
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()
        await page.goto(url + "#projets", wait_until="networkidle")
        closed = await page.evaluate("[...document.querySelectorAll('.project__more')].every(d => !d.open)")
        await page.click(".project--djaou .project__more > summary")
        opened = await page.evaluate("document.querySelector('.project--djaou .project__more').open")
        visible = await page.is_visible(".project--djaou .project__more .case")
        check("Projets : détail replié par défaut, s'ouvre au clic et devient visible", closed and opened and visible)
        await ctx.close()

        # Formulaire
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()
        await page.goto(url + "#contact", wait_until="networkidle")
        await page.click(".project-form button[value=email]")
        await page.wait_for_timeout(200)
        n_err = await page.evaluate("document.querySelectorAll('.project-form [aria-invalid=true]').length")
        summary_visible = await page.evaluate("!document.querySelector('.form-errors').hidden")
        check("Formulaire vide : 3 champs signalés et résumé des erreurs affiché", n_err == 3 and summary_visible, f"{n_err} erreurs")
        check("Formulaire vide : le focus va sur le résumé des erreurs", await page.evaluate("document.activeElement.classList.contains('form-errors')"))
        await page.fill("#f-name", "Test <b>Client</b>")
        await page.select_option("#f-need", "site")
        await page.fill("#f-message", "Bonjour, j'ai besoin d'un site vitrine & d'une boutique.")
        await page.wait_for_timeout(100)
        check("Formulaire corrigé : erreurs effacées en direct", await page.evaluate("document.querySelectorAll('.project-form [aria-invalid=true]').length") == 0)
        await page.click(".project-form button[value=email]")
        await page.wait_for_timeout(300)
        mail = await page.get_attribute("#projet", "data-last-action") or ""
        q = parse_qs(urlparse(mail).query)
        check("E-mail : lien mailto vers la bonne adresse, sujet et message encodés",
              mail.startswith("mailto:flaubertallah@gmail.com?") and "Client" in q.get("subject", [""])[0] and "boutique" in q.get("body", [""])[0])
        res = await page.evaluate("""(() => { const r = document.querySelector('.form-result'); const b = r.getBoundingClientRect();
            return { shown: !r.hidden, inView: b.top >= 0 && b.bottom <= innerHeight,
                     gmail: r.querySelector('.form-result__gmail').href, gmailShown: !!r.querySelector('.form-result__gmail').offsetParent,
                     copy: !!r.querySelector('.form-result__copy').offsetParent, text: r.textContent }; })()""")
        gq = parse_qs(urlparse(res["gmail"]).query)
        check("E-mail : panneau de secours visible à l'écran (Gmail et copie), message honnête",
              res["shown"] and res["inView"] and res["gmailShown"] and res["copy"]
              and gq.get("to", [""])[0] == "flaubertallah@gmail.com" and "boutique" in gq.get("body", [""])[0]
              and "Si rien ne s'ouvre" in res["text"], str({k: v for k, v in res.items() if k != "text"}))
        check("Saisie non interprétée comme HTML", await page.evaluate("document.querySelectorAll('.project-form b').length") == 0)
        async with ctx.expect_page() as popup_info:
            await page.click(".project-form button[value=whatsapp]")
        popup = await popup_info.value
        wa = await page.get_attribute("#projet", "data-last-action") or ""
        check("WhatsApp : ouverture dans un nouvel onglet vers wa.me avec le message", wa.startswith("https://wa.me/23563459298?text=") and "boutique" in unquote(wa))
        await popup.close()
        await ctx.close()

        # Bouton « Demander un devis »
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await ctx.new_page()
        await page.goto(url, wait_until="networkidle")
        await page.click('a[data-intent="devis"]')
        await page.wait_for_timeout(1200)
        check("Demander un devis : message amorcé, besoin laissé au choix du visiteur",
              await page.input_value("#f-need") == "" and (await page.input_value("#f-message")).startswith("Je souhaite obtenir un devis"))
        check("Demander un devis : le focus est placé dans le formulaire", await page.evaluate("document.activeElement.id") == "f-name")
        await ctx.close()

        # Ancre directe et sans JavaScript
        ctx = await browser.new_context(viewport={"width": 390, "height": 844})
        page = await ctx.new_page()
        await page.goto(url + "#realisations", wait_until="networkidle")
        await page.wait_for_timeout(2000)
        top = await page.evaluate("document.getElementById('realisations').getBoundingClientRect().top")
        check("Arrivée directe sur #realisations : section en haut de l'écran", 0 <= top < 140, f"{top:.0f}px")
        await ctx.close()
        ctx = await browser.new_context(viewport={"width": 390, "height": 844}, java_script_enabled=False)
        page = await ctx.new_page()
        await page.goto(url, wait_until="networkidle")
        hidden = await page.evaluate(hidden_js)
        check("Sans JavaScript : tout le contenu reste visible", not hidden, ", ".join(hidden[:5]))
        await ctx.close()

        # Mouvement réduit
        ctx = await browser.new_context(reduced_motion="reduce")
        page = await ctx.new_page()
        await page.goto(url, wait_until="networkidle")
        check("Mouvement réduit : aucune animation d'apparition", await page.evaluate("document.querySelectorAll('.reveal').length") == 0)
        await ctx.close()
        await browser.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--chrome")
    ap.add_argument("--axe")
    args = ap.parse_args()
    url = args.url if args.url.endswith("/") else args.url + "/"
    static_tests()
    asyncio.run(browser_tests(url, args.chrome, args.axe))
    failed = [r for r in RESULTS if not r[1]]
    print(f"\nRésultat : {len(RESULTS) - len(failed)} / {len(RESULTS)} tests réussis.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
