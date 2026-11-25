# Portfolio · Allah-adjim Flaubert — version 5.0

Portfolio professionnel d'Allah-adjim Flaubert, à N'Djaména (Tchad) : **solutions numériques, gestion de projets et données**.

Site statique en HTML, CSS et JavaScript, sans framework ni dépendance externe, prêt pour GitHub Pages.

- Adresse prévue : https://motou-98.github.io/portfolio-flaubertadjim/
- Lighthouse en local : performance 99 à 100, accessibilité 100, bonnes pratiques 100 (mobile et ordinateur)
- 68 tests automatisés réussis, 0 violation d'accessibilité axe-core (WCAG 2.2 AA)

**Pour modifier le site : voir [MAINTENANCE.md](MAINTENANCE.md)** (tâches courantes, modèles de blocs, vérification avant publication).

## Contenu de la page

| Section | Rôle |
| --- | --- |
| Accueil | Accroche, poste actuel, boutons « Découvrir mes projets » et « Discuter d'un projet », lien vers le CV, trois piliers |
| Profil | Parcours, profil hybride, informations clés |
| Compétences | 3 domaines principaux (développement, gestion de projets, données) et expertises complémentaires (formation, maintenance, vidéosurveillance) |
| Projets | DJAOU (moto-taxi, Laravel), JANJAN (Android, Kotlin), ADJIM INNOV, en études de cas tirées de leur code, avec suivi d'avancement |
| Réalisations | Plateforme de gestion interne de DAK-VISION PLUS et 3 sites en ligne : objectif, contenu, technologies, contribution |
| Parcours | Expériences par année, formation et langues |
| Services | Solutions numériques et services informatiques |
| Contact | Coordonnées directes et formulaire « Discuter d'un projet » |

## Identité visuelle

- **Concept « fil rouge » :** le liseré rouge de la chemise du portrait se prolonge en une ligne verticale qui traverse le site, se remplit au fil de la lecture et sépare titres et contenus.
- **Couleurs :** bleu nuit `#112f57`, texte `#f6f2eb`, rouge `#f0465d`. Chaque projet reprend les couleurs de son logo.
- **Polices :** Poppins (400 à 700) et Newsreader italique, auto-hébergées (licence SIL OFL).

## Structure

```
index.html              page unique
404.html                page d'erreur (chemins prévus pour /portfolio-flaubertadjim/)
site.webmanifest        manifeste d'application (icônes, couleurs)
robots.txt, sitemap.xml référencement
_headers                en-têtes de sécurité pour Netlify ou Cloudflare Pages (ignoré par GitHub Pages)
.nojekyll               désactive Jekyll sur GitHub Pages
assets/
  css/style.css         styles (variables en tête, bloc « Version 5.0 » pour les ajouts)
  js/script.js          menu, apparitions, fil rouge, copie de l'e-mail, formulaire
  fonts/                polices woff2 et licences
  images/               portrait (340 à 663 px, webp et jpg), icônes, image de partage
  images/projets/       logos, écrans de DJAOU et de JANJAN
  images/realisations/  captures des sites et de la plateforme interne (données fictives)
  documents/            CV en PDF et en Word
tests/run_tests.py      suite de tests automatisés (Playwright)
tools/verifier.py       vérification avant publication (Python seul, sans installation)
tools/images.py         préparation des captures d'écran (Pillow)
MAINTENANCE.md          mode d'emploi pour mettre le site à jour
documentation/          rapports (voir ci-dessous)
```

## Prévisualiser

```
cd ..                        # dossier qui contient portfolio-adjimflaubert/
python3 -m http.server 8000
```

Puis ouvrir http://localhost:8000/portfolio-adjimflaubert/. Ouvrir directement `index.html` depuis l'explorateur de fichiers (adresse en `file://`) affiche la page, mais Chrome y bloque les polices : le texte s'affiche alors dans une police de remplacement et la console signale des erreurs CORS. Ces erreurs disparaissent avec un serveur local (ci-dessus, ou l'extension Live Server de VS Code) et en ligne.

## Formulaire de contact

Le formulaire « Discuter d'un projet » **n'envoie rien par lui-même**. Il prépare le message dans la messagerie du visiteur (lien `mailto:`) ou dans WhatsApp (`wa.me`), et le visiteur l'envoie lui-même. Aucun service externe, aucune donnée stockée. Pour un envoi direct, voir `documentation/07-ameliorations-futures.md` (point 12).

## Tests

```
pip install playwright && playwright install chromium
python3 tests/run_tests.py http://localhost:8000/portfolio-adjimflaubert/
```

Options : `--axe chemin/vers/axe.min.js` pour l'audit d'accessibilité, `--chrome chemin/vers/chrome` pour choisir le navigateur.

## Déploiement

Résumé : envoyer le contenu de ce dossier sur la branche `main` du dépôt, puis activer **Settings → Pages → Deploy from a branch → main / (root)**. Le détail, la limite du robots.txt, Google Search Console et le changement d'adresse sont dans [documentation/06-deploiement.md](documentation/06-deploiement.md).

## Documentation

Le dossier `documentation/` reste sur l'ordinateur de l'auteur : il est exclu du dépôt public par `.gitignore`. Les liens ci-dessous ne fonctionnent donc qu'en local.

| Fichier | Contenu |
| --- | --- |
| [01-audit-technique.md](documentation/01-audit-technique.md) | Diagnostic de la version 4.7 |
| [02-ameliorations.md](documentation/02-ameliorations.md) | Plan et améliorations réalisées, mesures avant/après |
| [03-cv-et-documents.md](documentation/03-cv-et-documents.md) | Écarts entre le CV et le site, propositions |
| [04-informations-a-valider.md](documentation/04-informations-a-valider.md) | Informations à confirmer ou à fournir |
| [05-tests.md](documentation/05-tests.md) | Tests exécutés et résultats |
| [06-deploiement.md](documentation/06-deploiement.md) | Mise en ligne, Search Console, en-têtes |
| [07-ameliorations-futures.md](documentation/07-ameliorations-futures.md) | Pistes recommandées |
| [08-analyse-des-depots.md](documentation/08-analyse-des-depots.md) | Faits tirés des dépôts DJAOU, JANJAN et dakvision |
| [09-rapport-de-validation.md](documentation/09-rapport-de-validation.md) | Rapport de validation avant publication : bloquants, importants, facultatifs |

## Règles de contenu

Aucune expérience, compétence, réalisation, statistique ou témoignage n'est inventé. Les projets en développement sont présentés comme tels. Tout élément déduit plutôt que fourni est listé dans `documentation/04-informations-a-valider.md`.
