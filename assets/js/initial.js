(function () {
  "use strict";
  var darkMQ = window.matchMedia("(prefers-color-scheme: dark)");

  // Single source of truth for the color scheme: the reader's choice (the Theme radios in
  // baseof.html), else the system's. single.html reads it for Remark42.
  window.siteTheme = function () {
    return document.documentElement.dataset.theme || (darkMQ.matches ? "dark" : "light");
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
    var dark = siteTheme() == "dark";
    document.querySelectorAll("iframe.plot").forEach(function (f) {
      fixPlot(f, dark);
    });
  }

  // Correct plot srcs as soon as the parser inserts them, so the wrong-theme
  // file is neither fetched nor flashed (some plot files are megabytes).
  var plotObserver = new MutationObserver(function (records) {
    var dark = siteTheme() == "dark";
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

  function init() {
    plotObserver.disconnect();
    fixAllPlots(); // catch anything inserted before the observer registered
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
  darkMQ.addEventListener("change", applyColorScheme);
  window.siteThemeChanged = applyColorScheme;
})();
