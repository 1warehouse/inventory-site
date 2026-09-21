/* =========================================================================
   1inventory.io — analytics.js
   GA4, cookieless. Vanilla, no dependencies, no build step.

   Deliberately separate from main.js: that file is the page working,
   this one is only measurement, and measurement must never be the reason
   something breaks. Every path here is wrapped; a throw in here costs a
   statistic, not a visitor.

   CONSENT — Sparkybit GmbH is German, so GA4's default cookies would need
   an opt-in under TTDSG §25. We don't set any. Consent Mode v2 is declared
   denied before the tag loads and is never upgraded, so gtag runs in
   cookieless ping mode: no _ga cookie, no client_id, no device storage,
   nothing to ask permission for. The cost is that "users" and "sessions"
   in GA4 become estimates — read event counts, not user counts.

   CONTENTS
     01  Bail-outs (app webview, local, preview folders)
     02  Page context (type, language, platform)
     03  Consent defaults + tag bootstrap
     04  Events — store_click, cta_click, anchor_click, lang_switch, scroll_depth

   Load order matters: this must sit AFTER the language detector in <head>,
   or we log a page_view for a page the visitor is being redirected away
   from before it ever paints.
   ========================================================================= */
(function () {
  "use strict";

  var MEASUREMENT_ID = "G-96ZNX5D52Q";

  /* ---------------------------------------------------------------------
     01  BAIL-OUTS
     Three kinds of traffic are not the marketing audience and would only
     make the real numbers harder to read.
     --------------------------------------------------------------------- */
  try {
    /* The app embeds the legal pages and the FAQ in a webview with
       ?mobile=1. Those are existing users, already measured by Firebase
       in this same property as app streams. Counting them here would
       inflate page views and crater every conversion rate on the site. */
    if (/[?&]mobile(=(1|true))?(&|$)/i.test(location.search)) return;

    /* Local work and the v2–v7 redesign previews, which GitHub Pages
       serves from the same domain but which are not the live site. */
    var host = location.hostname;
    if (host === "localhost" || host === "127.0.0.1" || host === "" ) return;
    if (/^\/v[2-9]\//.test(location.pathname)) return;
  } catch (e) { return; }

  /* ---------------------------------------------------------------------
     02  PAGE CONTEXT
     --------------------------------------------------------------------- */

  /* The site ships 8 pages in 5 languages. Without normalising, /plans.html
     and /de/plans.html and three more are five unrelated rows and no page
     ever looks like it has traffic. page_type is the thing you actually
     want to group by; page_language is the cut across it. */
  function pageType() {
    var p = location.pathname.replace(/^\/(de|es|fr|pt)\//, "/");
    if (p === "/" || /\/index\.html$/.test(p)) return "home";
    if (/\/plans\.html$/.test(p)) return "plans";
    if (/\/faq\.html$/.test(p)) return "faq";
    if (/\/support\.html$/.test(p)) return "support";
    if (/\/(privacy|terms|impressum)\.html$/.test(p)) return "legal";
    if (/\/404\.html$/.test(p)) return "404";
    return "other";
  }

  function pageLanguage() {
    return (document.documentElement.getAttribute("lang") || "en").toLowerCase();
  }

  /* Which store badge is even reachable. iPadOS 13+ reports as a Mac, so
     touch points disambiguate. Lifted from the v5 prototype. */
  function platform() {
    var ua = navigator.userAgent || "";
    if (/iPhone|iPad|iPod/i.test(ua)) return "ios";
    if (/Android/i.test(ua)) return "android";
    if (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1) return "ios";
    return "desktop";
  }

  var PAGE_TYPE = pageType();
  var PAGE_LANG = pageLanguage();
  var PLATFORM = platform();

  /* ---------------------------------------------------------------------
     03  CONSENT DEFAULTS + TAG BOOTSTRAP
     --------------------------------------------------------------------- */
  window.dataLayer = window.dataLayer || [];
  function gtag() { window.dataLayer.push(arguments); }
  window.gtag = gtag;

  /* Declared before the tag loads — that ordering is the whole point.
     Denied here means gtag never writes storage in the first place,
     rather than writing it and tidying up afterwards. */
  gtag("consent", "default", {
    ad_storage: "denied",
    ad_user_data: "denied",
    ad_personalization: "denied",
    analytics_storage: "denied",
    functionality_storage: "denied",
    personalization_storage: "denied",
    security_storage: "granted"
  });

  gtag("js", new Date());

  /* content_group is a GA4 built-in, so page_type shows up in the standard
     reports with no extra configuration. page_language and device_platform
     need registering as custom dimensions in Admin before they're
     reportable — the data arrives either way. */
  gtag("config", MEASUREMENT_ID, {
    content_group: PAGE_TYPE,
    page_language: PAGE_LANG,
    device_platform: PLATFORM
  });

  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + MEASUREMENT_ID;
  document.head.appendChild(s);

  function track(name, params) {
    try {
      var payload = params || {};
      payload.page_type = PAGE_TYPE;
      payload.page_language = PAGE_LANG;
      payload.device_platform = PLATFORM;
      gtag("event", name, payload);
    } catch (e) { /* measurement must never break the page */ }
  }

  /* ---------------------------------------------------------------------
     04  EVENTS
     All delegated on document, so nothing here depends on the DOM being
     ready and nothing needs rebinding if markup moves.
     --------------------------------------------------------------------- */

  var IOS_RE = /apps\.apple\.com/i;
  var PLAY_RE = /play\.google\.com/i;

  document.addEventListener("click", function (ev) {
    try {
      var t = ev.target;
      if (!t || !t.closest) return;
      var a = t.closest("a");
      if (!a) return;

      var href = a.getAttribute("href") || "";
      var cta = a.getAttribute("data-cta");
      var lang = a.getAttribute("data-lang");

      /* The conversion. The only action on this site that can end in an
         install, so it is the one event worth marking as a key event.
         placement is the data-cta already in the markup — it is what tells
         you whether the hero badges or the ones at the foot of the page
         are doing the work. */
      if (IOS_RE.test(href) || PLAY_RE.test(href)) {
        track("store_click", {
          store_name: IOS_RE.test(href) ? "app_store" : "google_play",
          placement: cta || "unmarked"
        });
        return;
      }

      /* Intent, not conversion: the header and sticky CTAs scroll to
         #get-the-app rather than leaving for a store. Counting these as
         conversions would roughly double the number and make the funnel
         a lie. Kept separate so the drop-off between them and
         store_click is visible — that gap is the install block's job. */
      if (cta) {
        track("cta_click", { placement: cta, destination: href });
        return;
      }

      /* The FAQ "Jump to" nav and any other in-page anchor. On the FAQ
         page this is the closest thing to a question-level signal, since
         the answers are all expanded rather than in an accordion: what
         people jump to is what they came to find out.

         The skip-link is excluded: it is accessibility furniture aimed at
         keyboard and screen-reader users, and counting it as topic
         interest would put "main" at the top of the report on every page. */
      if (href.charAt(0) === "#" && href.length > 1) {
        if (a.className && /\bskip-link\b/.test(a.className)) return;
        track("anchor_click", { target: href.slice(1) });
        return;
      }

      /* Validates the auto-redirect in the <head> detector. If this fires
         often, the detector is guessing wrong and sending people to a
         language they then have to correct. */
      if (lang) {
        track("lang_switch", { from: PAGE_LANG, to: lang });
      }
    } catch (e) { /* never break a click */ }
  }, { passive: true, capture: true });

  /* Scroll depth. The pages are long and most of the argument is below the
     fold, so this is the only evidence that anyone reaches the later beats.
     Each mark fires once. */
  (function bindScrollDepth() {
    var marks = [25, 50, 75, 100];
    var hit = {};
    var queued = false;

    function measure() {
      queued = false;
      try {
        var doc = document.documentElement;
        var scrollable = doc.scrollHeight - window.innerHeight;
        if (scrollable <= 0) return;
        var pct = ((window.scrollY || doc.scrollTop) / scrollable) * 100;
        for (var i = 0; i < marks.length; i++) {
          var m = marks[i];
          if (pct >= m && !hit[m]) {
            hit[m] = true;
            track("scroll_depth", { percent: m });
          }
        }
      } catch (e) { /* ignore */ }
    }

    window.addEventListener("scroll", function () {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame
        ? window.requestAnimationFrame(measure)
        : setTimeout(measure, 100);
    }, { passive: true });
  })();
})();
