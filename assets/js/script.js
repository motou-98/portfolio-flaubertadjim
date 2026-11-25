/* Portfolio Allah-adjim Flaubert — interactions (v5.0)
   1. Menu replié accessible (Échap, piège de focus, verrouillage du défilement)
   2. Apparitions au défilement (préparées avant toute mesure)
   3. Fil rouge : progression de lecture et section active (mesures en cache)
   4. Copie de l'adresse e-mail
   5. Formulaire « Discuter d'un projet » : validation et message prérempli
   6. Ancres, invitation à défiler, année
   Aucun contenu saisi n'est injecté en HTML : tout passe par textContent ou encodeURIComponent. */
(function () {
  "use strict";

  var root = document.documentElement;
  root.classList.remove("no-js");
  root.classList.add("js");

  var mobileQuery = window.matchMedia("(max-width: 820px)");
  var menuQuery = window.matchMedia("(max-width: 1100px)");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var each = function (list, fn) { Array.prototype.forEach.call(list, fn); };

  /* ---------- 1. Menu replié ---------- */
  var menuButton = document.querySelector(".menu-button");
  var nav = document.getElementById("menu");

  function setMenu(open, returnFocus) {
    nav.classList.toggle("is-open", open);
    document.body.classList.toggle("menu-open", open);
    menuButton.setAttribute("aria-expanded", String(open));
    menuButton.textContent = open ? "Fermer" : "Menu";
    if (open) {
      var first = nav.querySelector("a");
      if (first) first.focus();
    } else if (returnFocus) {
      menuButton.focus();
    }
  }

  if (menuButton && nav) {
    menuButton.addEventListener("click", function () {
      setMenu(menuButton.getAttribute("aria-expanded") !== "true", true);
    });
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a") && menuQuery.matches) setMenu(false, false);
    });
    document.addEventListener("keydown", function (event) {
      if (!nav.classList.contains("is-open")) return;
      if (event.key === "Escape") { setMenu(false, true); return; }
      if (event.key === "Tab") {
        var items = [menuButton].concat(Array.prototype.slice.call(nav.querySelectorAll("a")));
        var first = items[0], last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    });
    var onBreakpoint = function (e) { if (!e.matches) setMenu(false, false); };
    if (menuQuery.addEventListener) menuQuery.addEventListener("change", onBreakpoint);
    else menuQuery.addListener(onBreakpoint);
  }

  /* ---------- 2. Apparitions au défilement (écritures uniquement) ---------- */
  var revealGroups = [
    ".section__title", ".statement", ".lede", ".prose > p", ".facts > div",
    ".domain", ".sub-heading", ".extra", ".ledger__year", ".aside-project", ".education > div",
    ".project", ".work", ".offer", ".specialty", ".offer__actions",
    ".email", ".contact-list > div", ".project-form", ".pillar"
  ];
  var revealEls = [];
  revealGroups.forEach(function (selector) {
    each(document.querySelectorAll("main " + selector), function (el) {
      var index = 0, sib = el.previousElementSibling;
      while (sib) { if (sib.matches(selector)) index++; sib = sib.previousElementSibling; }
      el.style.setProperty("--delay", Math.min(index, 4) * 0.09 + "s");
      revealEls.push(el);
    });
  });
  each(document.querySelectorAll(".domain, .offer, .specialty"), function (group) {
    each(group.querySelectorAll(".tags li, .offer__list li, .specialty__steps li"), function (li, i) {
      li.style.setProperty("--i", String(Math.min(i, 12)));
    });
  });

  var revealObserver = null;
  function revealWithin(target) {
    if (!target) return;
    var owner = target.closest(".reveal");
    if (owner) owner.classList.add("is-visible");
    if (target.classList.contains("reveal")) target.classList.add("is-visible");
    each(target.querySelectorAll(".reveal"), function (el) { el.classList.add("is-visible"); });
  }
  if (!reduceMotion && "IntersectionObserver" in window) {
    revealEls.forEach(function (el) { el.classList.add("reveal"); });
    revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
    revealEls.forEach(function (el) { revealObserver.observe(el); });
  }
  function hashTarget() {
    return location.hash.length > 1 ? document.getElementById(decodeURIComponent(location.hash.slice(1))) : null;
  }
  revealWithin(hashTarget());
  window.addEventListener("hashchange", function () { revealWithin(hashTarget()); });

  /* ---------- 3. Fil rouge ---------- */
  var main = document.querySelector("main");
  var fil = document.querySelector(".fil");
  var hero = document.querySelector(".hero");
  var photoImg = document.querySelector(".hero__photo img");
  var sections = Array.prototype.slice.call(document.querySelectorAll("main section.section[id]"));
  var navLinks = {};
  each(document.querySelectorAll(".nav__list a"), function (a) { navLinks[a.getAttribute("href").slice(1)] = a; });

  var mainTop = 0, filTop = 0, filHeight = 1, sectionTops = [], docHeight = 0, ticking = false, measurePending = false;
  var currentId = null;

  function absTop(el) { return el.getBoundingClientRect().top + window.pageYOffset; }

  function measure() {
    measurePending = false;
    // Lectures groupées
    mainTop = absTop(main);
    var start = mobileQuery.matches
      ? absTop(hero) + hero.offsetHeight
      : photoImg.getBoundingClientRect().bottom + window.pageYOffset;
    filTop = start - mainTop;
    filHeight = Math.max(1, main.offsetHeight - filTop);
    sectionTops = sections.map(function (s) { return absTop(s.querySelector(".section__title") || s); });
    docHeight = document.documentElement.scrollHeight;
    // Écriture
    fil.style.setProperty("--fil-top", filTop + "px");
    update();
  }
  function requestMeasure() {
    if (measurePending) return;
    measurePending = true;
    window.requestAnimationFrame(measure);
  }

  function update() {
    ticking = false;
    var y = window.pageYOffset;
    var marker = y + window.innerHeight * 0.55;
    var atEnd = y + window.innerHeight >= docHeight - 4;
    var progress = atEnd ? 1 : Math.min(1, Math.max(0, (marker - mainTop - filTop) / filHeight));
    fil.style.setProperty("--fil-progress", progress.toFixed(4));

    var current = null;
    sections.forEach(function (s, i) {
      var reached = marker >= sectionTops[i];
      s.classList.toggle("is-reached", reached);
      if (reached) current = s.id;
    });
    if (atEnd && sections.length) current = sections[sections.length - 1].id;
    if (current !== currentId) {
      currentId = current;
      Object.keys(navLinks).forEach(function (id) {
        if (id === current) navLinks[id].setAttribute("aria-current", "true");
        else navLinks[id].removeAttribute("aria-current");
      });
    }
  }
  function requestUpdate() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(update);
  }

  if (fil && main && photoImg && hero) {
    requestMeasure();
    window.addEventListener("scroll", requestUpdate, { passive: true });
    window.addEventListener("resize", requestMeasure);
    window.addEventListener("load", requestMeasure);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(requestMeasure);
    if (!photoImg.complete) photoImg.addEventListener("load", requestMeasure);
    // Les images différées changent la hauteur de page en se chargeant
    each(document.querySelectorAll("img[loading=lazy]"), function (img) {
      if (!img.complete) img.addEventListener("load", requestMeasure, { once: true });
    });
  }

  /* ---------- 4. Copier l'adresse e-mail ---------- */
  var copyButton = document.querySelector(".copy-button");
  var copyStatus = document.querySelector(".copy-status");
  if (copyButton && navigator.clipboard && window.isSecureContext) {
    copyButton.hidden = false;
    var resetTimer;
    copyButton.addEventListener("click", function () {
      navigator.clipboard.writeText(copyButton.getAttribute("data-copy")).then(function () {
        copyButton.textContent = "Adresse copiée";
        if (copyStatus) copyStatus.textContent = "L'adresse e-mail a été copiée dans le presse-papiers.";
      }, function () {
        if (copyStatus) copyStatus.textContent = "La copie a échoué. Sélectionnez l'adresse pour la copier.";
      });
      clearTimeout(resetTimer);
      resetTimer = setTimeout(function () {
        copyButton.textContent = "Copier l'adresse";
        if (copyStatus) copyStatus.textContent = "";
      }, 4000);
    });
  }

  /* ---------- 5. Formulaire « Discuter d'un projet » ---------- */
  // Coordonnées utilisées par le formulaire : les garder identiques à celles de index.html
  // (python tools/verifier.py le contrôle).
  var EMAIL = "flaubertallah@gmail.com";
  var WHATSAPP = "23563459298";
  var form = document.getElementById("projet");

  if (form) {
    var fields = {
      name: form.querySelector("#f-name"),
      need: form.querySelector("#f-need"),
      message: form.querySelector("#f-message")
    };
    var summary = form.querySelector(".form-errors");
    var status = form.querySelector(".form-status");
    var counter = form.querySelector("#f-message-count");
    var submitted = false;
    var lastChannel = "email";

    var rules = {
      name: function (v) { return v.trim().length >= 2 ? "" : "Indiquez votre nom (au moins 2 caractères)."; },
      need: function (v) { return v ? "" : "Choisissez le type de besoin."; },
      message: function (v) {
        var n = v.trim().length;
        return n >= 20 ? "" : "Décrivez votre besoin en au moins 20 caractères (" + n + " pour l'instant).";
      }
    };

    function setFieldError(key, message) {
      var input = fields[key];
      var error = form.querySelector("#" + input.id + "-error");
      if (message) {
        input.setAttribute("aria-invalid", "true");
        error.textContent = message;
        error.hidden = false;
      } else {
        input.removeAttribute("aria-invalid");
        error.textContent = "";
        error.hidden = true;
      }
    }

    function validate() {
      var errors = [];
      Object.keys(rules).forEach(function (key) {
        var message = rules[key](fields[key].value);
        setFieldError(key, message);
        if (message) errors.push({ key: key, message: message });
      });
      return errors;
    }

    function showSummary(errors) {
      while (summary.firstChild) summary.removeChild(summary.firstChild);
      if (!errors.length) { summary.hidden = true; return; }
      var title = document.createElement("p");
      title.textContent = errors.length === 1 ? "Un champ est à corriger :" : errors.length + " champs sont à corriger :";
      var list = document.createElement("ul");
      errors.forEach(function (err) {
        var item = document.createElement("li");
        var link = document.createElement("a");
        link.href = "#" + fields[err.key].id;
        link.textContent = err.message;
        link.addEventListener("click", function (e) { e.preventDefault(); fields[err.key].focus(); });
        item.appendChild(link);
        list.appendChild(item);
      });
      summary.appendChild(title);
      summary.appendChild(list);
      summary.hidden = false;
    }

    function updateCount() {
      counter.textContent = fields.message.value.length + " / " + fields.message.maxLength;
    }

    function buildText() {
      var needLabel = fields.need.options[fields.need.selectedIndex].text;
      return "Bonjour Flaubert,\n\n" + fields.message.value.trim() +
        "\n\nBesoin : " + needLabel + "\nNom : " + fields.name.value.trim() +
        "\n\n(Message préparé depuis votre portfolio)";
    }

    form.addEventListener("click", function (event) {
      var btn = event.target.closest("button[type=submit]");
      if (btn) lastChannel = btn.value;
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      submitted = true;
      status.textContent = "";
      var channel = (event.submitter && event.submitter.value) || lastChannel;
      var errors = validate();
      showSummary(errors);
      if (errors.length) {
        summary.setAttribute("tabindex", "-1");
        summary.focus();
        return;
      }
      var needLabel = fields.need.options[fields.need.selectedIndex].text;
      var text = buildText();
      if (channel === "whatsapp") {
        var link = document.createElement("a");
        link.href = "https://wa.me/" + WHATSAPP + "?text=" + encodeURIComponent(text);
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        form.setAttribute("data-last-action", link.href);
        document.body.appendChild(link);
        link.click();
        link.remove();
        showResult("whatsapp", text, link.href);
        status.textContent = "WhatsApp s'ouvre dans un nouvel onglet avec votre message. Il ne part que lorsque vous appuyez sur Envoyer dans WhatsApp.";
      } else {
        var subject = "Projet : " + needLabel + " (" + fields.name.value.trim() + ")";
        var mailto = "mailto:" + EMAIL + "?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(text);
        form.setAttribute("data-last-action", mailto);
        showResult("email", "À : " + EMAIL + "\nObjet : " + subject + "\n\n" + text,
          "https://mail.google.com/mail/?view=cm&fs=1&to=" + encodeURIComponent(EMAIL) +
          "&su=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(text));
        window.location.href = mailto;
        status.textContent = "Message prêt. Votre messagerie devrait s'ouvrir ; sinon, utilisez Gmail ou copiez le message.";
      }
    });

    /* Panneau affiché après la préparation : il reste utile quand aucune
       application de messagerie n'est configurée (le lien mailto ne fait alors rien). */
    var result = form.querySelector(".form-result");
    var resultCopy = form.querySelector(".form-result__copy");
    var resultCopied = form.querySelector(".form-result__copied");
    var preparedText = "";

    function showResult(channel, copyText, url) {
      preparedText = copyText;
      result.querySelectorAll("[data-channel]").forEach(function (el) {
        el.hidden = el.getAttribute("data-channel") !== channel;
      });
      var link = result.querySelector(channel === "email" ? ".form-result__gmail" : ".form-result__wa");
      link.href = url;
      resultCopied.textContent = "";
      result.hidden = false;
      result.focus({ preventScroll: true });
      // Amène le panneau à l'écran, sans animation : l'ouverture du lien mailto
      // interromprait un défilement animé.
      var box = result.getBoundingClientRect();
      var siteHeader = document.querySelector(".site-header");
      var headerH = siteHeader ? siteHeader.offsetHeight : 0;
      var delta = 0;
      if (box.bottom > window.innerHeight - 16) delta = box.bottom - window.innerHeight + 24;
      if (box.top - delta < headerH + 16) delta = box.top - headerH - 24;
      if (delta) window.scrollTo({ top: window.pageYOffset + delta, behavior: "instant" });
    }

    function fallbackCopy(text) {
      var area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.className = "visually-hidden";
      document.body.appendChild(area);
      area.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      area.remove();
      return ok;
    }

    resultCopy.addEventListener("click", function () {
      function done(ok) {
        resultCopied.textContent = ok
          ? "Message copié. Collez-le dans votre messagerie et envoyez-le à " + EMAIL + "."
          : "La copie a échoué. Écrivez directement à " + EMAIL + ".";
      }
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(preparedText).then(function () { done(true); }, function () { done(fallbackCopy(preparedText)); });
      } else {
        done(fallbackCopy(preparedText));
      }
    });

    Object.keys(fields).forEach(function (key) {
      var evt = key === "need" ? "change" : "input";
      fields[key].addEventListener(evt, function () {
        if (key === "message") updateCount();
        if (submitted) {
          setFieldError(key, rules[key](fields[key].value));
          var remaining = Object.keys(rules).map(function (k) { return { key: k, message: rules[k](fields[k].value) }; })
            .filter(function (e) { return e.message; });
          if (!remaining.length) showSummary([]);
        }
      });
    });
    updateCount();

    // Les boutons « Demander un devis » préremplissent le besoin
    each(document.querySelectorAll("a[data-need]"), function (link) {
      link.addEventListener("click", function () {
        var need = link.getAttribute("data-need");
        if (need) fields.need.value = need;
        if (link.getAttribute("data-intent") === "devis" && !fields.message.value.trim()) {
          fields.message.value = "Je souhaite obtenir un devis pour ";
          updateCount();
        }
        revealWithin(form);
        window.setTimeout(function () { fields.name.focus({ preventScroll: true }); }, 450);
      });
    });
  }

  /* ---------- 6. Ancres, invitation à défiler, année ---------- */
  if (location.hash.length > 1) {
    window.addEventListener("load", function () {
      var ready = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
      ready.then(function () {
        var userScrolled = false;
        var markUser = function () { userScrolled = true; };
        ["wheel", "touchstart", "keydown"].forEach(function (evt) { window.addEventListener(evt, markUser, { once: true, passive: true }); });
        var realign = function () {
          var target = hashTarget();
          if (target && !userScrolled) target.scrollIntoView({ behavior: "instant", block: "start" });
        };
        // Deux recalages : après les polices, puis après les dernières images chargées
        window.setTimeout(realign, 50);
        window.setTimeout(realign, 700);
      });
    });
  }

  var scrolled = null;
  var onScrolledState = function () {
    var now = window.pageYOffset > 120;
    if (now !== scrolled) { scrolled = now; root.classList.toggle("is-scrolled", now); }
  };
  window.addEventListener("scroll", onScrolledState, { passive: true });
  window.requestAnimationFrame(onScrolledState);

  var year = document.querySelector(".js-year");
  if (year) year.textContent = String(new Date().getFullYear());
})();
