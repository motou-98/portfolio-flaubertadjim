#!/usr/bin/env python3
"""
Prépare une capture d'écran pour le portfolio.

Utilisation :
    python tools/images.py ma-capture.png assets/images/realisations/nom-du-site

Crée, à partir de n'importe quelle image (PNG, JPG, WebP) :
    nom-du-site-1200.jpg   nom-du-site-1200.webp   (1200 x 800 px)
    nom-du-site-720.jpg    nom-du-site-720.webp    (720 x 480 px)

L'image est recadrée au format 3:2 en gardant le haut de la page (là où se
trouvent l'en-tête et le titre d'une capture de site), puis réduite.
Les métadonnées (appareil, position GPS, date) ne sont pas recopiées.

Nécessite le module Pillow, à installer une seule fois :
    python -m pip install pillow
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Le module Pillow manque. Installe-le avec : python -m pip install pillow")

TAILLES = [(1200, 800), (720, 480)]


def recadrer_3_2(image):
    largeur, hauteur = image.size
    if largeur / hauteur > 1.5:                      # trop large : on coupe les côtés
        nouvelle = round(hauteur * 1.5)
        gauche = (largeur - nouvelle) // 2
        return image.crop((gauche, 0, gauche + nouvelle, hauteur))
    return image.crop((0, 0, largeur, round(largeur / 1.5)))   # trop haute : on garde le haut


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    source, destination = sys.argv[1], sys.argv[2]
    if not os.path.isfile(source):
        sys.exit("Image introuvable : " + source)
    dossier = os.path.dirname(destination)
    if dossier and not os.path.isdir(dossier):
        sys.exit("Dossier introuvable : " + dossier)
    nom = os.path.basename(destination)
    if nom != nom.lower() or " " in nom or not nom.isascii():
        sys.exit("Utilise un nom en minuscules, sans espace ni accent (exemple : agro-almountas).")

    image = recadrer_3_2(Image.open(source).convert("RGB"))
    if image.width < 1200:
        print("Attention : l'image fait %d px de large ; elle sera agrandie et un peu floue." % image.width)
    for largeur, hauteur in TAILLES:
        reduite = image.resize((largeur, hauteur), Image.LANCZOS)
        base = "%s-%d" % (destination, largeur)
        reduite.save(base + ".jpg", quality=82, optimize=True, progressive=True)
        reduite.save(base + ".webp", quality=80, method=6)
        print("Créé : %s.jpg et %s.webp" % (base, base))


if __name__ == "__main__":
    main()
