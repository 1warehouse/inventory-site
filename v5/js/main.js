/* =========================================================================
   1inventory v5

   The v4 audit found 331 lines of JS containing no gtag, no dataLayer and no
   handler bound to [data-cta] — the five data-cta values and the scroll hook
   were inert markup. This file makes them real, and adds the platform
   detection that turns every "Get the app" into a store link instead of a
   scroll anchor that throws a phone user 5,700px down the page.

   No dependencies. Degrades to a working page with JS off.
   ========================================================================= */
(function () {
  'use strict';

  var IOS = 'https://apps.apple.com/app/id6747425128';
  var PLAY = 'https://play.google.com/store/apps/details?id=com.sparkybit.oneinventory';

  /* ---------------------------------------------------------- platform */

  function platform() {
    var ua = navigator.userAgent || '';
    if (/iPhone|iPad|iPod/i.test(ua)) return 'ios';
    if (/Android/i.test(ua)) return 'android';
    // iPadOS 13+ reports as Mac; touch points disambiguate.
    if (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1) return 'ios';
    return 'desktop';
  }

  var PLAT = platform();
  document.documentElement.setAttribute('data-platform', PLAT);

  /* Every in-page CTA pointing at #get becomes a real store link on mobile.
     On desktop it stays an anchor to the install block, which carries both
     badges — a desktop user cannot install from a deep link anyway. */
  function resolveCtas() {
    if (PLAT === 'desktop') return;
    var href = PLAT === 'ios' ? IOS : PLAY;
    var links = document.querySelectorAll('a[href="#get"]');
    for (var i = 0; i < links.length; i++) {
      links[i].setAttribute('href', href);
      links[i].setAttribute('rel', 'noopener');
    }
  }

  /* ------------------------------------------------------- measurement */

  /* Fires into whatever is present. Nothing is installed yet, so this is
     deliberately defensive rather than assuming gtag exists. */
  function track(name, params) {
    try {
      if (typeof window.gtag === 'function') window.gtag('event', name, params || {});
      if (Array.isArray(window.dataLayer)) window.dataLayer.push(Object.assign({ event: name }, params || {}));
    } catch (e) { /* measurement must never break the page */ }
  }

  function bindCtas() {
    document.addEventListener('click', function (ev) {
      var el = ev.target.closest ? ev.target.closest('[data-cta]') : null;
      if (!el) return;
      track('cta_click', {
        cta_id: el.getAttribute('data-cta'),
        platform: PLAT,
        destination: el.getAttribute('href') || ''
      });
    }, { passive: true });
  }

  /* Scroll depth — the only evidence that anyone reaches the long beats. */
  function bindScrollDepth() {
    var marks = [25, 50, 75, 100];
    var hit = {};
    var ticking = false;
    function check() {
      ticking = false;
      var doc = document.documentElement;
      var max = doc.scrollHeight - window.innerHeight;
      if (max <= 0) return;
      var pct = Math.min(100, Math.round((window.scrollY / max) * 100));
      for (var i = 0; i < marks.length; i++) {
        if (pct >= marks[i] && !hit[marks[i]]) {
          hit[marks[i]] = true;
          track('scroll_depth', { percent: marks[i] });
        }
      }
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(check); }
    }, { passive: true });
  }

  /* --------------------------------------------------------- sticky cta */

  function bindSticky() {
    var bar = document.getElementById('sticky');
    var hero = document.getElementById('top');
    if (!bar || !hero || !('IntersectionObserver' in window)) return;
    new IntersectionObserver(function (entries) {
      bar.classList.toggle('is-on', !entries[0].isIntersecting);
    }, { rootMargin: '-40% 0px 0px 0px' }).observe(hero);
  }

  /* ------------------------------------------------------------ reveals */

  function bindReveals() {
    if (!('IntersectionObserver' in window)) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var els = document.querySelectorAll('.reveal');
    if (!els.length) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    for (var i = 0; i < els.length; i++) io.observe(els[i]);
  }

  function init() {
    resolveCtas();
    bindCtas();
    bindScrollDepth();
    bindSticky();
    bindReveals();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
