/* =========================================================================
   1inventory.io — main.js
   Vanilla, no dependencies, no build step. Everything here is progressive
   enhancement: with JS off the page is fully readable, every link works,
   the sticky CTA bar is visible and the frame rows still scroll natively.

   CONTENTS
     01  Sticky header shadow
     02  Mobile menu toggle
     03  Smooth scroll for in-page anchors (reduced-motion aware)
     04  Sticky mobile CTA bar — show past the hero, hide over the final CTA
     05  Horizontal snap-scroll affordances for the frame rows
     06  Reveal on scroll
     07  Current year in footer
   ========================================================================= */
(function () {
  "use strict";

  var reduceMotion = window.matchMedia
    ? window.matchMedia("(prefers-reduced-motion: reduce)")
    : null;
  function prefersReducedMotion() {
    return !!(reduceMotion && reduceMotion.matches);
  }

  /* ---------------------------------------------------------------------
     01  STICKY HEADER SHADOW
     --------------------------------------------------------------------- */
  var header = document.querySelector(".site-header");
  function onHeaderScroll() {
    if (!header) return;
    header.classList.toggle("scrolled", window.scrollY > 8);
  }
  window.addEventListener("scroll", onHeaderScroll, { passive: true });
  onHeaderScroll();

  /* ---------------------------------------------------------------------
     02  MOBILE MENU TOGGLE
     --------------------------------------------------------------------- */
  var toggle = document.querySelector(".nav-toggle");
  var menu = document.querySelector(".nav-menu");
  if (toggle && menu) {
    var FOCUSABLE =
      'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])';

    function menuIsOpen() {
      return menu.classList.contains("open");
    }

    // Body scroll lock. The plan's §0 names it explicitly, alongside
    // Escape-to-close and the focus trap, as the three things the old
    // mobile menu did not have.
    function setMenu(open, returnFocus) {
      menu.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      document.documentElement.classList.toggle("menu-open", open);
      if (open) {
        var first = menu.querySelector(FOCUSABLE);
        if (first) first.focus();
      } else if (returnFocus) {
        toggle.focus();
      }
    }

    toggle.addEventListener("click", function () {
      setMenu(!menuIsOpen(), false);
    });

    menu.addEventListener("click", function (e) {
      if (e.target.closest("a")) setMenu(false, false);
    });

    document.addEventListener("keydown", function (e) {
      if (!menuIsOpen()) return;

      if (e.key === "Escape") {
        setMenu(false, true);
        return;
      }

      // Focus trap: Tab cycles between the toggle and the menu's own links.
      if (e.key !== "Tab") return;
      var items = [toggle].concat(
        Array.prototype.slice.call(menu.querySelectorAll(FOCUSABLE))
      );
      if (!items.length) return;
      var first = items[0];
      var last = items[items.length - 1];
      var active = document.activeElement;
      if (e.shiftKey && (active === first || !menu.contains(active) && active !== toggle)) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      }
    });

    // A viewport that grows past the mobile breakpoint leaves the menu open
    // and the body locked; unlock rather than trapping a desktop visitor.
    window.addEventListener("resize", function () {
      if (menuIsOpen() && window.innerWidth > 960) setMenu(false, false);
    }, { passive: true });
  }

  /* ---------------------------------------------------------------------
     03  SMOOTH SCROLL FOR IN-PAGE ANCHORS

     CSS already sets html { scroll-behavior: smooth } with a reduced-motion
     override, so this handler exists for the one thing CSS cannot do: move
     keyboard focus to the destination.

     v2: the email-field focus branch is gone with the email form. Every CTA
     on this page now jumps to #get-the-app, whose content is two links to
     the real store listings — moving focus to the section is the correct and
     only behaviour.

     Still deliberately does NOT preventDefault when the target does not
     exist, so an unresolved href stays inert rather than throwing.
     --------------------------------------------------------------------- */
  var HEADER_OFFSET = 90; // --header-h (74) + 16, matching scroll-margin-top

  function scrollToEl(el) {
    if (!prefersReducedMotion() && "scrollBehavior" in document.documentElement.style) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      var y = el.getBoundingClientRect().top + window.pageYOffset - HEADER_OFFSET;
      window.scrollTo(0, y < 0 ? 0 : y);
    }
  }

  // Move keyboard focus with the viewport. Without this a smooth scroll
  // leaves screen-reader and keyboard users where they started.
  function focusEl(el) {
    var hadTabindex = el.hasAttribute("tabindex");
    if (!hadTabindex) el.setAttribute("tabindex", "-1");
    el.focus({ preventScroll: true });
    if (!hadTabindex) {
      el.addEventListener("blur", function once() {
        el.removeAttribute("tabindex");
        el.removeEventListener("blur", once);
      });
    }
  }

  document.addEventListener("click", function (e) {
    var link = e.target.closest('a[href^="#"]');
    if (!link) return;
    if (link.classList.contains("skip-link")) return; // native behaviour is correct

    var id = link.getAttribute("href").slice(1);
    if (!id) return;

    var target = document.getElementById(id);
    if (!target) return; // placeholder hrefs stay inert

    e.preventDefault();
    scrollToEl(target);
    focusEl(target);

    // Keep the URL shareable without a second jump.
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, "", "#" + id);
    }
  });

  /* ---------------------------------------------------------------------
     04  STICKY MOBILE CTA BAR

     Visible by default in CSS so it works with JS off. With JS it hides
     while the hero or the final band is on screen — both already show the
     two store badges, and a bar over the top of them is noise — and while
     the mobile menu is open.
     --------------------------------------------------------------------- */
  var sticky = document.getElementById("sticky-cta");
  if (sticky) {
    var dismiss = sticky.querySelector("[data-sticky-dismiss]");
    if (dismiss) {
      dismiss.addEventListener("click", function () {
        sticky.classList.add("is-dismissed");
      });
    }

    var hero = document.getElementById("top");
    // v2: the final band was renamed #get-started -> #get-the-app.
    var finalCta = document.getElementById("get-the-app");

    function onScreen(el) {
      if (!el) return false;
      var r = el.getBoundingClientRect();
      return r.bottom > 0 && r.top < (window.innerHeight || 0);
    }

    function syncSticky() {
      if (sticky.classList.contains("is-dismissed")) return;
      var hide =
        onScreen(hero) ||
        onScreen(finalCta) ||
        !!(menu && menu.classList.contains("open"));
      sticky.classList.toggle("is-hidden", hide);
      // A translated-away bar is still focusable, so take it out of the tree.
      sticky.setAttribute("aria-hidden", hide ? "true" : "false");
    }

    // Measured on scroll rather than observed, so the bar's state is always
    // a function of where the page actually is. IntersectionObserver batches
    // its callbacks and can lag a fast programmatic jump by a frame or two.
    var stickyTick = false;
    function queueSticky() {
      // Leading edge, unconditionally: syncSticky is two getBoundingClientRect
      // calls, and running it here means the bar's state never depends on a
      // frame callback arriving. requestAnimationFrame is suspended whenever
      // the document is hidden (background tab, some embedded viewers), and an
      // rAF-only throttle leaves the bar stuck in whatever state it had.
      syncSticky();
      if (stickyTick) return;
      stickyTick = true;
      window.requestAnimationFrame(function () {
        stickyTick = false;
        syncSticky();
      });
    }
    window.addEventListener("scroll", queueSticky, { passive: true });
    window.addEventListener("resize", queueSticky, { passive: true });
    window.addEventListener("load", syncSticky);
    if (toggle) toggle.addEventListener("click", queueSticky);
    syncSticky();
  }

  /* ---------------------------------------------------------------------
     05  HORIZONTAL SNAP-SCROLL AFFORDANCES

     Below 960px each .frame-row becomes one horizontal snap-scroll strip.
     Native scrolling already works; this only adds the signal that there
     is more to the right (.can-scroll-start / .can-scroll-end drive the
     edge fades) and lets the keyboard drive the strip once it has focus.
     --------------------------------------------------------------------- */
  var rows = document.querySelectorAll(".frame-row");
  Array.prototype.forEach.call(rows, function (row) {
    function syncEdges() {
      var overflow = row.scrollWidth - row.clientWidth;
      if (overflow < 4) {
        row.classList.remove("can-scroll-start", "can-scroll-end", "is-scrollable");
        // Not scrollable (desktop): a focus stop that does nothing is noise
        // for a keyboard user. The attribute ships in the HTML so the row is
        // still reachable with JS off.
        row.removeAttribute("tabindex");
        return;
      }
      row.classList.add("is-scrollable");
      row.setAttribute("tabindex", "0");
      row.classList.toggle("can-scroll-start", row.scrollLeft > 4);
      row.classList.toggle("can-scroll-end", row.scrollLeft < overflow - 4);
    }

    row.addEventListener("scroll", syncEdges, { passive: true });
    window.addEventListener("resize", syncEdges, { passive: true });
    window.addEventListener("load", syncEdges);
    syncEdges();

    // Arrow keys page the strip one frame at a time once it has focus.
    row.addEventListener("keydown", function (e) {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      var item = row.querySelector(".frame-row__item");
      if (!item) return;
      var step = item.getBoundingClientRect().width + 18;
      e.preventDefault();
      row.scrollBy({
        left: e.key === "ArrowRight" ? step : -step,
        behavior: prefersReducedMotion() ? "auto" : "smooth"
      });
    });
  });

  /* ---------------------------------------------------------------------
     06  REVEAL ON SCROLL
     --------------------------------------------------------------------- */
  var revealables = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealables.length) {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px 0px 0px", threshold: 0.1 }
    );
    Array.prototype.forEach.call(revealables, function (el) { io.observe(el); });
    // Safety net: force-reveal anything still hidden shortly after load
    // (covers edge cases where the observer never fires for an element).
    window.addEventListener("load", function () {
      window.setTimeout(function () {
        Array.prototype.forEach.call(revealables, function (el) { el.classList.add("in"); });
      }, 1500);
    });
  } else {
    Array.prototype.forEach.call(revealables, function (el) { el.classList.add("in"); });
  }

  /* ---------------------------------------------------------------------
     07  CURRENT YEAR IN FOOTER
     --------------------------------------------------------------------- */
  Array.prototype.forEach.call(document.querySelectorAll("[data-year]"), function (el) {
    el.textContent = new Date().getFullYear();
  });
})();

/* 8. v3 — scroll reveals. Sections after the hero fade-and-rise as they
      enter the viewport. Gated on prefers-reduced-motion; no-JS pages and
      reduced-motion users see everything immediately. */
(function () {
  "use strict";
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (!("IntersectionObserver" in window)) return;
  var targets = Array.prototype.slice.call(
    document.querySelectorAll("main > section:not(.hero) > .container")
  );
  targets.forEach(function (el) { el.classList.add("reveal"); });
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-in");
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: "0px 0px -8% 0px" });
  targets.forEach(function (el) { io.observe(el); });
})();

/* =========================================================================
   EMAIL DE-OBFUSCATION

   No address on this site appears in the served HTML as a readable string,
   and no mailto: appears either. Each one ships as:

     <a class="eml" data-u="…" data-d="…" data-t="…">…</a>

   with the user, domain and TLD held separately, every character written as a
   numeric entity. A browser decodes the entities, so the visible text is
   exactly the address whether or not this script runs. A harvester grepping
   the raw HTML for an @ or a mailto: finds neither, and even one that reads
   data attributes has to know to join three of them.

   This is deliberately not encryption. It stops the bulk automated harvesting
   that produces most address spam; it will not stop somebody who targets this
   site specifically. Which is the right trade for a published legal contact:
   the address must stay readable to a human with JavaScript off, because on
   the Impressum and the privacy policy it is a regulatory obligation.
   ========================================================================= */
(function () {
  'use strict';

  function reveal() {
    var links = document.querySelectorAll('a.eml');
    for (var i = 0; i < links.length; i++) {
      var a = links[i];
      var u = a.getAttribute('data-u'),
          d = a.getAttribute('data-d'),
          t = a.getAttribute('data-t');
      if (!u || !d || !t) continue;
      var addr = u + '@' + d + '.' + t;
      a.setAttribute('href', 'mailto:' + addr);
      // Only normalise the label when it is the address itself; links whose
      // text is a phrase keep their wording.
      if (a.textContent.trim() === addr) a.textContent = addr;
      a.removeAttribute('data-u');
      a.removeAttribute('data-d');
      a.removeAttribute('data-t');
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', reveal);
  } else {
    reveal();
  }
})();
