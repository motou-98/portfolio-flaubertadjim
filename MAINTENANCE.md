# Mettre à jour le portfolio

Ce guide explique comment modifier le site sans rien casser. Le site est fait de fichiers simples, sans outil de construction : on modifie un fichier, on vérifie, on publie.

## Les quatre règles

1. **Avant chaque publication, lance la vérification** : `python tools/verifier.py` (voir [Vérifier](#vérifier-avant-de-publier)). Elle signale les oublis : coordonnées différentes d'un endroit à l'autre, image introuvable, taille du CV fausse, etc.
2. **Pas de style ni de script dans `index.html`.** La sécurité du site (en-tête `Content-Security-Policy`) les bloque en ligne. Le style va dans `assets/css/style.css`, le code dans `assets/js/script.js`, et tout fichier (image, police) dans `assets/`, jamais chargé depuis un autre site.
3. **Noms de fichiers en minuscules, sans espace ni accent** (`agro-almountas-1200.jpg`). GitHub Pages distingue `Photo.jpg` de `photo.jpg`, contrairement à Windows.
4. **N'écrire que ce qui est vrai et vérifiable.** Un projet en cours reste « en développement » ; une étape n'est marquée terminée que lorsqu'elle l'est.

## Où se trouve quoi

| Fichier | Contenu |
| --- | --- |
| `index.html` | Tout le contenu de la page. Chaque section commence par un repère `<!-- ═══ NOM ═══ … -->` qui explique comment la modifier |
| `assets/css/style.css` | L'apparence. Le sommaire est en tête du fichier ; les couleurs sont dans `:root` |
| `assets/js/script.js` | Le menu, les animations, le fil rouge et le formulaire |
| `assets/documents/` | Le CV en PDF et en Word |
| `assets/images/` | Portrait, logos et écrans des projets (`projets/`), captures des réalisations (`realisations/`) |
| `404.html` | Page affichée pour une adresse inexistante |
| `sitemap.xml`, `robots.txt`, `site.webmanifest` | Référencement et installation sur téléphone |
| `tools/verifier.py` | Vérification avant publication |
| `tools/images.py` | Préparation des captures d'écran |
| `googlec9043d34cc53f428.html` | Preuve de propriété pour Google Search Console : **ne pas supprimer ni renommer**, sinon la validation est perdue |

Pour trouver un texte dans `index.html` : ouvre-le dans VS Code et cherche avec **Ctrl+F** la phrase visible sur le site.

## Voir le résultat sur ton ordinateur

Dans VS Code, avec l'extension **Live Server** : clic droit sur `index.html` → **Open with Live Server**. La page se recharge à chaque enregistrement.

Sans VS Code : ouvre un terminal dans le dossier **parent** du site et lance `python -m http.server 8000`, puis va sur http://localhost:8000/portfolio-adjimflaubert/ (nom de ton dossier local ; en ligne, l'adresse est https://motou-98.github.io/portfolio-flaubertadjim/).

Un double-clic sur `index.html` affiche la page, mais sans les bonnes polices (Chrome les bloque en `file://`). Ce n'est pas une erreur du site.

## Tâches courantes

### Mettre à jour le CV

1. Modifie le CV dans Word, puis **Fichier → Exporter → PDF**.
2. Remplace les deux fichiers dans `assets/documents/`, **en gardant exactement les mêmes noms** : `CV_ALLAH-ADJIM_Flaubert.pdf` et `CV_ALLAH-ADJIM_Flaubert.docx`.
3. Lance `python tools/verifier.py --corriger` : les tailles affichées sur le site (« 75 ko ») se mettent à jour toutes seules.

### Changer l'adresse e-mail ou le numéro de téléphone

Ils sont écrits à plusieurs endroits, voulus pour le visiteur (accueil, contact, pied de page, données pour Google) :

1. Dans VS Code : **Ctrl+Maj+H** (remplacer dans tous les fichiers), ancienne valeur → nouvelle valeur. Pour le téléphone, remplace aussi la forme sans espaces (`23563459298`).
2. Vérifie `assets/js/script.js`, en haut de la rubrique 5 : les constantes `EMAIL` et `WHATSAPP`.
3. Lance `python tools/verifier.py` : il signale toute valeur oubliée, y compris si le CV Word ne contient pas la nouvelle adresse.

### Changer de poste

Le poste actuel figure dans : l'accueil (`hero__current`), le profil (« Poste actuel »), le parcours (nouvel `<article class="job">`), le pied de page (`site-footer__role`) et les données pour Google (`"jobTitle"`, en haut de `index.html`). Cherche l'ancien intitulé avec **Ctrl+F** pour n'en oublier aucun. Pense aussi au CV.

### Faire avancer un projet

Dans la section Projets, chaque projet a une liste d'étapes `<ol class="stages">` :

```html
<li class="is-done">Suivi GPS<span class="visually-hidden"> (terminé)</span></li>
<li class="is-current" aria-current="step">Phase pilote<span class="visually-hidden"> (prochaine étape)</span></li>
<li>Application mobile</li>
```

Quand une étape est finie : passe-la en `is-done` avec « (terminé) », et passe la suivante en `is-current` avec `aria-current="step"` et « (prochaine étape) ». Il ne doit y avoir **qu'une seule** étape en cours.

Le statut affiché au-dessus du nom (« En développement », « En finalisation ») se change dans `<p class="project__status">`. Quand un projet est publié, remplace aussi « aucun n'est encore publié » dans l'introduction de la section.

Un chiffre (nombre de tests, par exemple) ne se met à jour qu'avec la source : le nombre réellement compté dans le dépôt, et sa date.

### Ajouter un site dans « Sites en ligne »

1. Fais une capture de la page d'accueil du site (au moins 1200 px de large), puis prépare les images :
   ```
   python tools/images.py ma-capture.png assets/images/realisations/nom-du-site
   ```
   Le script crée les quatre fichiers attendus (720 et 1200 px, en `.jpg` et `.webp`), recadrés au bon format, sans métadonnées. La première fois : `python -m pip install pillow`.
2. Dans `index.html`, cherche (Ctrl+F) **AJOUTER UN NOUVEAU SITE ICI**, colle ce modèle juste au-dessus de cette ligne, puis remplace chaque `…` :

```html
<li class="work">
  <a class="work__link" href="https://…" target="_blank" rel="noopener noreferrer">
    <picture class="work__shot">
      <source type="image/webp" srcset="assets/images/realisations/nom-du-site-720.webp 720w, assets/images/realisations/nom-du-site-1200.webp 1200w" sizes="(max-width: 820px) 92vw, 62vw">
      <img src="assets/images/realisations/nom-du-site-1200.jpg" width="1200" height="800" loading="lazy" decoding="async" alt="Page d'accueil du site … : …">
    </picture>
    <span class="work__name">Nom du site<span class="visually-hidden"> (ouvrir le site dans un nouvel onglet)</span></span>
    <span class="work__type">Site vitrine (WordPress)</span>
  </a>
  <dl class="work__facts work__facts--key">
    <div class="work__contribution"><dt>Ma contribution</dt><dd>…</dd></div>
  </dl>
  <details class="project__more work__more">
    <summary>Voir l'objectif, le contenu et les technologies</summary>
    <dl class="work__facts">
      <div><dt>Objectif</dt><dd>…</dd></div>
      <div><dt>Contenu du site</dt><dd>…</dd></div>
      <div><dt>Technologies</dt><dd>…</dd></div>
    </dl>
  </details>
</li>
```

Le texte `alt` décrit ce que montre la capture, pour les personnes qui ne voient pas l'image. La grille passe automatiquement à la ligne au-delà de trois sites.

Pour une capture d'un outil interne : uniquement sur une installation de test, avec des données fictives, et avec l'accord de l'entreprise. Masque les numéros de téléphone et toute donnée qui pourrait correspondre à une vraie personne.

### Ajouter une expérience

Dans la section Parcours, ajoute un `<article class="job">` dans l'année concernée (ou crée une année en copiant un bloc `<li class="ledger__year">` entier) :

```html
<article class="job">
  <h3>Intitulé du poste</h3>
  <p class="job__meta">Employeur <span class="job__date">mois année à mois année</span></p>
  <ul>
    <li>Une responsabilité, commençant par un nom ou un verbe d'action.</li>
  </ul>
</article>
```

Les deux années les plus récentes sont visibles ; les plus anciennes sont dans le bloc replié `ledger--older`. Quand une nouvelle année arrive, déplace la plus ancienne des années visibles dans ce bloc.

### Ajouter une compétence ou un service

- Compétence : un `<li>` de plus dans la liste `<ul class="tags">` du domaine concerné (section Compétences).
- Service : un `<li>` de plus dans `<ul class="offer__list">` (section Services).
- Besoin proposé dans le formulaire : une `<option>` de plus dans `<select id="f-need">` (section Contact).

### Remplacer le portrait

Le portrait existe en quatre largeurs (340, 440, 520 et 663 px), en `.jpg` et `.webp`, recadré pour que le liseré rouge de la chemise reste aligné avec le fil rouge du site. Le plus simple est de me le demander : le recadrage se règle dans `style.css` (`.hero__grid`).

### Changer une couleur

Toutes les couleurs sont des variables au début de `style.css`, dans `:root` : `--banco` (bleu de fond), `--sable` (texte clair), `--fil` (rouge du fil). Modifier la variable change la couleur partout. Vérifie ensuite le contraste du texte (au moins 4,5:1), par exemple avec l'outil Lighthouse de Chrome.

### Changer l'adresse du site

Par exemple après l'achat d'un nom de domaine :

```
python tools/verifier.py --changer-adresse https://adjimflaubert.com/
```

La commande remplace l'adresse dans `index.html`, `sitemap.xml`, `robots.txt`, `README.md` et les liens de `404.html`. Il reste à mettre à jour l'adresse du portfolio dans le CV, et pour un domaine personnel, à ajouter le fichier `CNAME` (voir `documentation/06-deploiement.md`).

## Vérifier avant de publier

Dans un terminal ouvert dans le dossier du site :

```
python tools/verifier.py
```

(Sous Windows, si `python` n'est pas reconnu, essaie `py tools/verifier.py`. Python s'installe depuis python.org ou le Microsoft Store.)

Le script contrôle, sans rien modifier :

1. que l'e-mail et le numéro sont identiques partout, dans la page, le formulaire et le CV Word ;
2. que l'adresse du site est la même dans la page, le sitemap, robots.txt et la page 404 ;
3. que les fichiers du CV existent et que les tailles affichées sont exactes ;
4. que chaque lien interne, image et ancre existe, avec les bonnes majuscules, et que chaque image a un texte alternatif et des dimensions ;
5. qu'aucun style, script ou fichier externe ne sera bloqué par la sécurité du site ;
6. que les données pour Google, le manifeste et le sitemap sont valides ;
7. qu'aucun fichier de travail (archives .zip, sauvegardes .bak, fichiers système de Windows…) ne traîne dans le dossier.

Chaque ligne commence par `[OK]`, `[ATTENTION]` (à relire) ou `[ERREUR]` (à corriger avant de publier). Option `--corriger` : met à jour les tailles du CV et les dates de dernière modification (sitemap et données pour Google).

Pour un contrôle complet du rendu (5 tailles d'écran, accessibilité, menu, formulaire), la suite `tests/run_tests.py` est décrite dans le README ; elle demande l'installation de Playwright.

## Publier

Le plus simple : **GitHub Desktop**.

1. Une seule fois : dans GitHub Desktop, **File → Add local repository** → `D:\portfolio-adjimflaubert` (ou **Create a repository** s'il n'est pas encore suivi par Git), puis **Publish repository** sur le compte `motou-98`. Dans la fenêtre de publication, **remplace le nom proposé par `portfolio-flaubertadjim`** (c'est le nom du dépôt qui donne l'adresse `https://motou-98.github.io/portfolio-flaubertadjim/`) et **décoche « Keep this code private »** : GitHub Pages gratuit exige un dépôt public. Sur github.com : **Settings → Pages → Deploy from a branch → main / (root)**.
   *Si le dépôt a déjà été créé sur github.com (vide)*, GitHub Desktop ne peut pas le « publier » une seconde fois. Deux solutions : supprimer ce dépôt vide (**Settings → Danger Zone → Delete this repository**) puis publier depuis GitHub Desktop, ou utiliser Git en ligne de commande dans le dossier du site :
   ```
   git init -b main
   git add .
   git status
   git commit -m "Première publication du portfolio"
   git remote add origin https://github.com/motou-98/portfolio-flaubertadjim.git
   git push -u origin main
   ```
   `git status` liste ce qui sera publié : `documentation/` ne doit pas y figurer.
2. À chaque mise à jour : lance la vérification, puis dans GitHub Desktop écris un résumé (« Ajout du site X »), clique sur **Commit to main**, puis **Push origin**. Le site est à jour en une à deux minutes.

GitHub Desktop respecte le fichier `.gitignore`, qui écarte les fichiers de travail. **Le dossier `documentation/` décrit le code interne de DAK-VISION PLUS** : pour le garder sur ton ordinateur sans le publier, retire le `#` devant `documentation/` à la fin de `.gitignore`. L'envoi par glisser-déposer sur github.com, lui, publie tout ce qu'on dépose : n'y mets que les fichiers du site.

Pour revenir en arrière après une erreur : dans GitHub Desktop, onglet **History**, clic droit sur la modification → **Revert changes in commit**, puis **Push origin**.
