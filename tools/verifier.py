#!/usr/bin/env python3
"""
Vérification du portfolio avant publication.

Utilisation (depuis le dossier du site) :
    python tools/verifier.py                     vérifie tout, ne modifie rien
    python tools/verifier.py --corriger          met à jour les tailles du CV
                                                 et les dates de modification
    python tools/verifier.py --changer-adresse https://exemple.com/
                                                 remplace l'adresse du site partout

Le script n'utilise que Python 3.8 ou plus récent, sans module à installer.
Code de sortie : 0 s'il n'y a aucune erreur, 1 sinon.
"""

import argparse
import datetime
import json
import os
import re
import sys
import zipfile
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["index.html", "404.html"]

# Fichiers et dossiers qui ne doivent pas partir en ligne.
INTERDITS = [".env", "Thumbs.db", "desktop.ini", ".DS_Store"]
# Dossiers utiles en local mais à garder hors du dépôt public (voir MAINTENANCE.md).
PRIVES = ["documentation"]

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # anciennes consoles Windows
    pass


class Rapport:
    def __init__(self):
        self.erreurs = 0
        self.alertes = 0

    def ok(self, texte):
        print("  [OK]        " + texte)

    def erreur(self, texte):
        self.erreurs += 1
        print("  [ERREUR]    " + texte)

    def alerte(self, texte):
        self.alertes += 1
        print("  [ATTENTION] " + texte)

    def titre(self, texte):
        print("\n" + texte)


def lire(chemin):
    with open(os.path.join(RACINE, chemin), encoding="utf-8") as f:
        return f.read()


def ecrire(chemin, contenu):
    with open(os.path.join(RACINE, chemin), "w", encoding="utf-8", newline="") as f:
        f.write(contenu)


def existe_casse_exacte(chemin_relatif):
    """GitHub Pages distingue les majuscules : Photo.JPG n'est pas photo.jpg.
    Windows ne fait pas la différence, d'où cette vérification nom par nom."""
    courant = RACINE
    for morceau in chemin_relatif.replace("\\", "/").split("/"):
        if morceau in ("", "."):
            continue
        try:
            noms = os.listdir(courant)
        except (FileNotFoundError, NotADirectoryError):
            return False
        if morceau not in noms:
            return False
        courant = os.path.join(courant, morceau)
    return True


class Analyse(HTMLParser):
    """Relève les balises utiles d'une page HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.balises = []          # (nom, attributs, ligne)
        self.ids = {}
        self.jsonld = []
        self._dans_jsonld = False
        self._tampon = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        ligne = self.getpos()[0]
        self.balises.append((tag, a, ligne))
        if "id" in a:
            self.ids.setdefault(a["id"], []).append(ligne)
        if tag == "script" and a.get("type") == "application/ld+json":
            self._dans_jsonld = True
            self._tampon = []

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "script" and self._dans_jsonld:
            self.jsonld.append("".join(self._tampon))
            self._dans_jsonld = False

    def handle_data(self, data):
        if self._dans_jsonld:
            self._tampon.append(data)


def adresse_du_site(index):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', index)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Contrôles
# ---------------------------------------------------------------------------

def controler_coordonnees(r, index):
    r.titre("1. Coordonnées (doivent être identiques partout)")
    script = lire("assets/js/script.js")
    textes = {"index.html": index, "404.html": lire("404.html"), "assets/js/script.js": script}

    emails = {}
    for nom, t in textes.items():
        for e in re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", t):
            if e.endswith((".png", ".jpg", ".webp", ".svg")):
                continue
            emails.setdefault(e, set()).add(nom)
    if len(emails) == 1:
        r.ok("Une seule adresse e-mail : " + next(iter(emails)))
    elif not emails:
        r.erreur("Aucune adresse e-mail trouvée")
    else:
        for e, ou in emails.items():
            r.erreur("Adresses e-mail différentes : " + e + " dans " + ", ".join(sorted(ou)))

    # Numéros : forme internationale dans les liens (tel:, wa.me, constante du script).
    numeros = {}
    for nom, t in textes.items():
        for n in re.findall(r"tel:\+?(\d{8,15})|wa\.me/(\d{8,15})|WHATSAPP = \"(\d{8,15})\"", t):
            numero = next(x for x in n if x)
            numeros.setdefault(numero, set()).add(nom)
    if len(numeros) == 1:
        r.ok("Un seul numéro dans les liens téléphone et WhatsApp : +" + next(iter(numeros)))
    else:
        for n, ou in numeros.items():
            r.erreur("Numéros différents dans les liens : +" + n + " dans " + ", ".join(sorted(ou)))

    # Le numéro affiché doit correspondre au numéro des liens.
    if len(numeros) == 1:
        chiffres = next(iter(numeros))[-8:]
        affiches = set()
        for m in re.finditer(r"\+235(?:&nbsp;|\s| )*((?:\d{2}(?:&nbsp;|\s| )*){4})", index):
            affiches.add(re.sub(r"\D", "", m.group(1)))
        autres = sorted(a for a in affiches if a != chiffres)
        if autres:
            r.erreur("Numéro affiché différent des liens : " + ", ".join(autres))
        else:
            r.ok("Le numéro affiché correspond aux liens")

    # Le CV Word contient-il les mêmes coordonnées ?
    for nom in os.listdir(os.path.join(RACINE, "assets", "documents")):
        if nom.lower().endswith(".docx"):
            try:
                xml = zipfile.ZipFile(os.path.join(RACINE, "assets", "documents", nom)).read("word/document.xml").decode("utf-8")
                texte = re.sub(r"<[^>]+>", "", xml)
                absents = [e for e in emails if e not in texte]
                if absents:
                    r.alerte(nom + " ne contient pas " + ", ".join(absents) + " : pense à mettre le CV à jour")
                else:
                    r.ok(nom + " contient la même adresse e-mail")
            except Exception as exc:
                r.alerte("Impossible de lire " + nom + " (" + str(exc) + ")")


def controler_adresse(r, index):
    r.titre("2. Adresse du site (canonical, partage, sitemap, robots.txt, page 404)")
    base = adresse_du_site(index)
    if not base:
        r.erreur("Balise canonical absente de index.html")
        return
    if not base.endswith("/"):
        r.erreur("L'adresse canonical doit finir par / : " + base)
    r.ok("Adresse de référence : " + base)

    hote = urlparse(base).netloc
    trouvees = set(re.findall(r"https://" + re.escape(hote) + r"[^\s\"'<)]*", index))
    hors_base = sorted(u for u in trouvees if not u.startswith(base))
    if hors_base:
        for u in hors_base:
            r.erreur("Adresse qui ne commence pas par l'adresse de référence : " + u)
    else:
        r.ok("index.html : %d adresses absolues, toutes cohérentes" % len(trouvees))

    for fichier in ["sitemap.xml", "robots.txt"]:
        t = lire(fichier)
        if fichier == "sitemap.xml":
            urls = re.findall(r"<(?:image:)?loc>([^<]+)</", t)
        else:
            urls = re.findall(r"Sitemap:\s*(\S+)", t)
        mauvaises = [u for u in urls if not u.startswith(base)]
        if mauvaises:
            r.erreur(fichier + " : adresse différente : " + ", ".join(mauvaises))
        else:
            r.ok(fichier + " : cohérent")

    chemin = urlparse(base).path
    page404 = lire("404.html")
    liens = re.findall(r'(?:href|src)="(/[^"]*)"', page404)
    mauvais = [l for l in liens if not l.startswith(chemin)]
    if mauvais:
        r.erreur("404.html : liens qui ne commencent pas par " + chemin + " : " + ", ".join(mauvais))
    else:
        r.ok("404.html : liens cohérents avec " + chemin)

    for nom in os.listdir(os.path.join(RACINE, "assets", "documents")):
        if nom.lower().endswith(".docx"):
            try:
                xml = zipfile.ZipFile(os.path.join(RACINE, "assets", "documents", nom)).read("word/document.xml").decode("utf-8")
                adresse_courte = hote + chemin.rstrip("/")
                if adresse_courte not in re.sub(r"<[^>]+>", "", xml):
                    r.alerte(nom + " ne mentionne pas " + adresse_courte + " : mets à jour l'adresse du portfolio dans le CV")
                else:
                    r.ok(nom + " mentionne la bonne adresse du portfolio")
            except Exception:
                pass


def controler_cv(r, index, corriger):
    r.titre("3. CV : fichiers présents et tailles affichées")
    motif = re.compile(r'(href="(assets/documents/[^"]+)"[^>]*>[^<]*<span class="file-size">\([^)]*?)(\d+)( ko\))')
    nouveau = index
    for m in motif.finditer(index):
        fichier = unquote(m.group(2))
        if not existe_casse_exacte(fichier):
            r.erreur("Fichier introuvable : " + fichier)
            continue
        reel = max(1, round(os.path.getsize(os.path.join(RACINE, fichier)) / 1024))
        affiche = int(m.group(3))
        if reel == affiche:
            r.ok("%s : %d ko, taille affichée exacte" % (os.path.basename(fichier), reel))
        elif corriger:
            nouveau = nouveau.replace(m.group(0), m.group(1) + str(reel) + m.group(4), 1)
            r.ok("%s : taille corrigée, %d ko au lieu de %d ko" % (os.path.basename(fichier), reel, affiche))
        else:
            r.erreur("%s : la page affiche %d ko, le fichier fait %d ko (lance --corriger)" % (os.path.basename(fichier), affiche, reel))
    if nouveau != index:
        ecrire("index.html", nouveau)
    return nouveau


def controler_references(r, page, analyse, base):
    r.titre("4. Liens, images et ancres de " + page)
    erreurs_avant = r.erreurs
    vus = set()
    for tag, a, ligne in analyse.balises:
        valeurs = []
        for attr in ("href", "src", "poster"):
            if a.get(attr):
                valeurs.append(a[attr])
        for attr in ("srcset", "imagesrcset"):
            if a.get(attr):
                valeurs += [p.strip().split(" ")[0] for p in a[attr].split(",") if p.strip()]
        if tag == "meta" and a.get("content", "").startswith(base or "§"):
            valeurs.append(a["content"])
        for v in valeurs:
            if v.startswith(("mailto:", "tel:", "data:", "javascript:")) or v == "#":
                continue
            if v.startswith("#"):
                if v[1:] not in analyse.ids:
                    r.erreur("ligne %d : ancre %s sans id correspondant" % (ligne, v))
                continue
            if v.startswith("http"):
                if base and v.startswith(base):
                    v = v[len(base):]
                else:
                    continue
            chemin = unquote(v.split("#")[0].split("?")[0])
            if page == "404.html" and base:
                prefixe = urlparse(base).path
                if chemin.startswith(prefixe):
                    chemin = chemin[len(prefixe):]
            chemin = chemin.lstrip("/") or "index.html"
            if chemin.endswith("/"):
                chemin += "index.html"
            if chemin in vus:
                continue
            vus.add(chemin)
            if not existe_casse_exacte(chemin):
                r.erreur("ligne %d : fichier introuvable (ou majuscules différentes) : %s" % (ligne, chemin))

        if tag == "img":
            for attr in ("alt", "width", "height"):
                if attr not in a:
                    r.erreur("ligne %d : image %s sans attribut %s" % (ligne, a.get("src", "?"), attr))
        # La politique de sécurité (CSP) du site bloque les styles et scripts écrits dans la page
        # et toute ressource chargée depuis un autre site : ils ne fonctionneraient pas en ligne.
        if "style" in a:
            r.erreur("ligne %d : attribut style=\"…\" bloqué par la sécurité du site ; mettre le style dans style.css" % ligne)
        for attr in a:
            if attr.startswith("on"):
                r.erreur("ligne %d : attribut %s bloqué par la sécurité du site ; mettre le code dans script.js" % (ligne, attr))
        if tag == "script" and not a.get("src") and a.get("type") != "application/ld+json":
            r.erreur("ligne %d : script écrit dans la page, bloqué par la sécurité du site ; le mettre dans script.js" % ligne)
        if tag == "style":
            r.erreur("ligne %d : balise <style> bloquée par la sécurité du site ; utiliser style.css" % ligne)
        externe = a.get("src", "") if tag in ("img", "script", "source", "iframe") else ""
        if tag == "link" and a.get("rel") in ("stylesheet", "preload"):
            externe = a.get("href", "")
        if externe.startswith(("http://", "https://", "//")):
            r.erreur("ligne %d : ressource chargée depuis un autre site (%s), bloquée par la sécurité du site ; copier le fichier dans assets/" % (ligne, externe))
        if tag == "a" and a.get("target") == "_blank" and "noopener" not in a.get("rel", ""):
            r.erreur("ligne %d : lien externe sans rel=\"noopener\"" % ligne)

    for ident, lignes in analyse.ids.items():
        if len(lignes) > 1:
            r.erreur("id « %s » utilisé plusieurs fois (lignes %s)" % (ident, ", ".join(map(str, lignes))))

    if r.erreurs == erreurs_avant:
        r.ok("%d références vérifiées, aucune erreur" % len(vus))


def controler_css(r):
    css = lire("assets/css/style.css")
    manquants = []
    for u in re.findall(r"url\(\"?([^\")]+)\"?\)", css):
        if u.startswith("data:"):
            continue
        chemin = os.path.normpath(os.path.join("assets/css", u)).replace("\\", "/")
        if not existe_casse_exacte(chemin):
            manquants.append(chemin)
    if manquants:
        for m in manquants:
            r.erreur("style.css : fichier introuvable : " + m)
    else:
        r.ok("style.css : polices et images trouvées")


def controler_donnees(r, analyses, corriger, index):
    r.titre("5. Données structurées, manifeste et sitemap")
    for page, analyse in analyses.items():
        for bloc in analyse.jsonld:
            try:
                json.loads(bloc)
                r.ok(page + " : JSON-LD valide")
            except ValueError as exc:
                r.erreur(page + " : JSON-LD invalide (" + str(exc) + ")")
    try:
        manifeste = json.loads(lire("site.webmanifest"))
        for icone in manifeste.get("icons", []):
            if not existe_casse_exacte(icone["src"]):
                r.erreur("site.webmanifest : icône introuvable : " + icone["src"])
        r.ok("site.webmanifest : valide")
    except ValueError as exc:
        r.erreur("site.webmanifest invalide (" + str(exc) + ")")

    # Dates de dernière modification : sitemap.xml (date seule) et "dateModified" des données
    # pour Google, qui exige une date avec l'heure et le fuseau horaire (2026-11-27T08:45:00+01:00).
    horodatage = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(RACINE, "index.html"))).astimezone()
    modif = horodatage.date()
    cibles = [("sitemap.xml", r"<lastmod>([^<]+)</lastmod>", "<lastmod>%s</lastmod>", modif.isoformat()),
              ("index.html", r'"dateModified": "([^"]+)"', '"dateModified": "%s"',
               horodatage.replace(microsecond=0).isoformat())]
    for fichier, motif, gabarit, valeur in cibles:
        texte = lire(fichier)
        m = re.search(motif, texte)
        if not m:
            r.alerte(fichier + " : date de modification absente")
            continue
        nom = "sitemap.xml (lastmod)" if fichier == "sitemap.xml" else "index.html (dateModified)"
        brut = m.group(1)
        format_ok = True
        if fichier == "index.html" and not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?([+-]\d{2}:\d{2}|Z)$", brut):
            format_ok = False
        try:
            date = datetime.date.fromisoformat(brut[:10])
        except ValueError:
            date, format_ok = None, False
        if format_ok and date >= modif:
            r.ok("%s : date à jour (%s)" % (nom, brut))
        elif corriger:
            ecrire(fichier, texte.replace(m.group(0), gabarit % valeur, 1))
            r.ok("%s : date mise à jour (%s)" % (nom, valeur))
        elif not format_ok:
            r.erreur("%s : « %s » n'est pas au format attendu par Google (date, heure et fuseau, par exemple 2026-11-27T08:45:00+01:00) ; lance --corriger" % (nom, brut))
        else:
            r.alerte("%s : %s, antérieure à la dernière modification de la page (%s) ; lance --corriger" % (nom, brut, modif))


def controler_dossier(r, index):
    r.titre("6. Fichiers à ne pas publier")
    trouves = [n for n in INTERDITS if os.path.exists(os.path.join(RACINE, n))]
    trouves += [n for n in os.listdir(RACINE) if n.lower().endswith((".zip", ".rar", ".bak", ".tmp"))]
    for n in trouves:
        r.erreur("À retirer du dossier avant publication : " + n)
    if not trouves:
        r.ok("Aucun fichier de travail oublié")
    ignores = ""
    if os.path.exists(os.path.join(RACINE, ".gitignore")):
        ignores = "\n".join(l.strip() for l in lire(".gitignore").splitlines() if not l.strip().startswith("#"))
    for n in PRIVES:
        if os.path.isdir(os.path.join(RACINE, n)):
            if re.search(r"^/?%s/?$" % re.escape(n), ignores, re.M):
                r.ok("Le dossier « %s » est exclu par .gitignore (publier avec Git ou GitHub Desktop)" % n)
            else:
                r.alerte("Le dossier « %s » sera public avec le dépôt ; voir MAINTENANCE.md, section Publier" % n)
    for mot in ("lorem ipsum", "TODO", "À COMPLÉTER", "XXX"):
        if mot.lower() in index.lower():
            r.erreur("Texte provisoire trouvé dans index.html : « %s »" % mot)


def changer_adresse(nouvelle):
    if not re.match(r"^https://[^/\s]+/([^\s]*/)?$", nouvelle):
        sys.exit("L'adresse doit commencer par https:// et finir par / (exemple : https://motou-98.github.io/portfolio/)")
    index = lire("index.html")
    ancienne = adresse_du_site(index)
    if not ancienne:
        sys.exit("Adresse actuelle introuvable (balise canonical absente)")
    if ancienne == nouvelle:
        sys.exit("C'est déjà l'adresse du site.")
    ancien_chemin, nouveau_chemin = urlparse(ancienne).path, urlparse(nouvelle).path
    for fichier in ["index.html", "sitemap.xml", "robots.txt", "README.md"]:
        t = lire(fichier)
        if ancienne in t:
            ecrire(fichier, t.replace(ancienne, nouvelle))
            print("  modifié : " + fichier)
    p = lire("404.html")
    p2 = re.sub(r'((?:href|src)=")' + re.escape(ancien_chemin), r"\g<1>" + nouveau_chemin, p)
    if p2 != p:
        ecrire("404.html", p2)
        print("  modifié : 404.html")
    print("\nAdresse remplacée : %s -> %s" % (ancienne, nouvelle))
    print("À faire à la main : l'adresse du portfolio dans le CV (Word, puis export PDF).")


def main():
    parser = argparse.ArgumentParser(description="Vérifie le portfolio avant publication.")
    parser.add_argument("--corriger", action="store_true", help="met à jour les tailles du CV et les dates de modification")
    parser.add_argument("--changer-adresse", metavar="URL", help="remplace l'adresse du site partout")
    args = parser.parse_args()

    if args.changer_adresse:
        changer_adresse(args.changer_adresse)
        print()

    r = Rapport()
    print("Vérification du portfolio : " + RACINE)
    index = lire("index.html")
    base = adresse_du_site(index)

    controler_coordonnees(r, index)
    controler_adresse(r, index)
    index = controler_cv(r, index, args.corriger)

    analyses = {}
    for page in PAGES:
        analyse = Analyse()
        analyse.feed(lire(page))
        analyses[page] = analyse
        controler_references(r, page, analyse, base)
    controler_css(r)
    controler_donnees(r, analyses, args.corriger, index)
    controler_dossier(r, index)

    print("\nRésultat : %d erreur(s), %d point(s) d'attention." % (r.erreurs, r.alertes))
    if r.erreurs == 0:
        print("Le site peut être publié" + (" (relis les points d'attention)." if r.alertes else "."))
    sys.exit(1 if r.erreurs else 0)


if __name__ == "__main__":
    main()
