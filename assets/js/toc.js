// ToC: scroll-spy, mobile toggle, desktop positioning. CSS owns appearance
// through three hooks: .toc-open (mobile manual open), li > ul.expanded
// (scroll-spy branch), a.current (highlight). JS only toggles state; the sole
// inline style is the measured top offset.
(function () {
  "use strict";
  var toc = document.getElementById("TableOfContents");
  if (!toc) return;

  // Must match the single @media (min-width: 1280px) block in main.css.
  var DESKTOP = window.matchMedia("(min-width: 1280px)");
  var tocManuallyOpen = false;
  var ticking = false;

  function clearSpy() {
    toc.querySelectorAll("a.current").forEach(function (a) {
      a.classList.remove("current");
    });
    toc.querySelectorAll("li > ul.expanded").forEach(function (ul) {
      ul.classList.remove("expanded");
    });
  }

  function isVisible(el) {
    var rect = el.getBoundingClientRect();
    return (
      rect.bottom >= 0 &&
      rect.right >= 0 &&
      rect.top <= (window.innerHeight || document.documentElement.clientHeight) &&
      rect.left <= (window.innerWidth || document.documentElement.clientWidth)
    );
  }

  function updateSpy() {
    if (!DESKTOP.matches) return;
    var scope = document.querySelector("[data-toc-scope]");
    var article = document.getElementById("article-content");
    if (!scope || !article) return;

    // Last heading whose top has passed 100px below the viewport top.
    var id = "";
    scope.querySelectorAll("h1, h2, h3, h4, h5, h6").forEach(function (h) {
      if (h.getBoundingClientRect().top <= 100) id = h.id || "";
    });

    if (!isVisible(article)) {
      clearSpy();
      return;
    }

    var current = toc.querySelectorAll("a.current");
    if (
      current.length &&
      current[current.length - 1].getAttribute("href") === "#" + id
    )
      return;

    clearSpy();
    if (!id) return;
    var active = toc.querySelector('a[href="#' + CSS.escape(id) + '"]');
    if (!active) return;
    // Walk ancestor list items up to the ToC root: highlight each link on the
    // path and expand its nested list.
    for (var el = active.parentElement; el && el !== toc; el = el.parentElement) {
      if (el.tagName !== "LI") continue;
      var link = el.querySelector(":scope > a");
      if (link) link.classList.add("current");
      var sub = el.querySelector(":scope > ul");
      if (sub) sub.classList.add("expanded");
    }
  }

  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      ticking = false;
      updateSpy();
    });
  }

  // Desktop: align the fixed ToC's top with the page title.
  function positionToc() {
    if (!DESKTOP.matches) return;
    var title = document.querySelector("[data-toc-anchor]");
    if (title)
      toc.style.top = title.getBoundingClientRect().top + window.scrollY + "px";
  }

  function adjust() {
    if (DESKTOP.matches) {
      toc.classList.remove("toc-open");
      tocManuallyOpen = false;
      positionToc();
    }
    if (!tocManuallyOpen) clearSpy();
    updateSpy();
  }

  var btn = document.getElementById("toc-btn");
  if (btn) {
    btn.addEventListener("click", function () {
      tocManuallyOpen = toc.classList.toggle("toc-open");
      btn.setAttribute("aria-expanded", tocManuallyOpen ? "true" : "false");
      // CSS shows every nested list while manually open; drop stale highlights.
      if (tocManuallyOpen) clearSpy();
    });
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", adjust, { passive: true });
  DESKTOP.addEventListener("change", adjust);
  // The title's metrics can shift once webfonts arrive.
  if (document.fonts && document.fonts.ready)
    document.fonts.ready.then(positionToc);

  if (document.readyState !== "loading") adjust();
  else document.addEventListener("DOMContentLoaded", adjust);
})();
