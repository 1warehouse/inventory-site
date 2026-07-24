(function () {
  "use strict";

  // Sticky header shadow on scroll
  var header = document.querySelector(".site-header");
  function onScroll() {
    if (!header) return;
    header.classList.toggle("scrolled", window.scrollY > 8);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Mobile menu toggle
  var toggle = document.querySelector(".nav-toggle");
  var menu = document.querySelector(".nav-menu");
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      var open = menu.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    menu.addEventListener("click", function (e) {
      if (e.target.closest("a")) menu.classList.remove("open");
    });
  }

  // Reveal on scroll
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
    revealables.forEach(function (el) { io.observe(el); });
    // Safety net: force-reveal anything still hidden shortly after load
    // (covers edge cases where the observer never fires for an element).
    window.addEventListener("load", function () {
      setTimeout(function () {
        revealables.forEach(function (el) { el.classList.add("in"); });
      }, 1500);
    });
  } else {
    revealables.forEach(function (el) { el.classList.add("in"); });
  }

  // Current year in footer
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });
})();
