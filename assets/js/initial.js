function isDark() {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function applyColorScheme() {
  var dark = isDark();

  // Adjust code snippets.
  document.getElementById("code-syntax-theme").href = dark
    ? "/css/syntax-dark.css"
    : "/css/syntax-light.css";

  // Adjust plots.
  var plots = document.getElementsByClassName("plot");
  for (var i = plots.length - 1; i >= 0; --i) {
    if (typeof plots[i].src === "undefined") continue;
    // Normalize to light version first, then add -dark if needed.
    var src = plots[i].src.replace(/-dark\.html/, ".html");
    plots[i].src = dark ? src.replace(/\.html/, "-dark.html") : src;
  }

  // Adjust the comments section.
  var theme = dark ? "dark" : "light";
  localStorage.remark42_theme = theme;
  if (window.REMARK42) {
    window.REMARK42.changeTheme(theme);
  }

}

function replaceText(node) {
  // Use a Unicode NON-BREAKING HYPHEN (U+2011) instead of a regular hyphen to
  // prevent line breaks at hyphens.
  if (node.nodeType == 3) {
    node.data = node.data.replace(/-/g, "\u2011");
  }

  if (
    node.nodeType == 1 &&
    node.nodeName != "SCRIPT" &&
    node.nodeName != "STYLE" &&
    node.nodeName != "PRE"
  ) {
    for (var i = 0; i < node.childNodes.length; i++) {
      replaceText(node.childNodes[i]);
    }
  }
}

(function () {
  function init() {
    applyColorScheme();
    replaceText(document.body);
  }

  if (document.readyState != "loading") {
    init();
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }

  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", applyColorScheme);
})();
