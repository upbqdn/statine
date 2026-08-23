(function () {
  "use strict";
  var darkMQ = window.matchMedia("(prefers-color-scheme: dark)");

  // Single source of truth for the color scheme; single.html reads it for Remark42.
  window.siteTheme = function () {
    return darkMQ.matches ? "dark" : "light";
  };

  // Remark42 must see the theme before its deferred embed boots — write at parse time.
  try {
    localStorage.remark42_theme = siteTheme();
  } catch (e) {}

  // ----- Plot iframes: light/dark variants ------------------------------
  function fixPlot(iframe, dark) {
    var src = iframe.getAttribute("src");
    if (!src) return;
    var url = new URL(src, location.href);
    if (!/\.html$/.test(url.pathname)) return;
    url.pathname = url.pathname.replace(/(?:-dark)?\.html$/, dark ? "-dark.html" : ".html");
    if (url.href !== iframe.src) iframe.src = url.href;
  }

  function fixAllPlots() {
    var dark = darkMQ.matches;
    document.querySelectorAll("iframe.plot").forEach(function (f) {
      fixPlot(f, dark);
    });
  }

  // Correct plot srcs as soon as the parser inserts them, so the wrong-theme
  // file is neither fetched nor flashed (some plot files are megabytes).
  var plotObserver = new MutationObserver(function (records) {
    var dark = darkMQ.matches;
    records.forEach(function (r) {
      r.addedNodes.forEach(function (n) {
        if (n.nodeType !== Node.ELEMENT_NODE) return;
        if (n.matches("iframe.plot")) fixPlot(n, dark);
        else if (n.querySelectorAll)
          n.querySelectorAll("iframe.plot").forEach(function (f) {
            fixPlot(f, dark);
          });
      });
    });
  });
  plotObserver.observe(document.documentElement, { childList: true, subtree: true });

  function applyColorScheme() {
    fixAllPlots();
    var theme = siteTheme();
    try {
      localStorage.remark42_theme = theme;
    } catch (e) {}
    if (window.REMARK42) window.REMARK42.changeTheme(theme);
  }

  // ----- Non-breaking hyphens ------------------------------------------
  // U+2011 prevents line breaks at hyphens in justified prose. Never touch
  // code (it must copy-paste as ASCII), raw TeX (the pagefind-ignore spans),
  // or MathJax output: MathJax silently drops U+2011, which would erase
  // minus signs if it typesets after this pass.
  var SKIP = "pre,code,kbd,samp,script,style,textarea,span[data-pagefind-ignore],mjx-container";

  function nonBreakingHyphens(root) {
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (node.data.indexOf("-") === -1) return NodeFilter.FILTER_REJECT;
        var p = node.parentElement;
        return p && p.closest(SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
      },
    });
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (n) {
      n.data = n.data.replace(/-/g, "‑");
    });
  }

  function init() {
    plotObserver.disconnect();
    fixAllPlots(); // catch anything inserted before the observer registered
    var main = document.querySelector("main");
    if (main) nonBreakingHyphens(main);
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
  darkMQ.addEventListener("change", applyColorScheme);
})();
