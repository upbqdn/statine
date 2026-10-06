window.MathJax = {
  loader: {
    paths: { fonts: "[mathjax]/../@mathjax" }
  },
  tex: {
    tags: "ams"
  },
  output: {
    font: "mathjax-pagella",
    displayOverflow: "linebreak",
    // Keep inline math and its punctuation together, as in the source text.
    // Leave room for equation tags and the renderer's display padding.
    linebreaks: { inline: false, width: "95%" }
  },
  chtml: {
    matchFontHeight: false
  },
  startup: {
    pageReady: function () {
      return document.fonts.ready.then(function () {
        return MathJax.startup.defaultPageReady();
      }).then(function () {
        document.querySelectorAll('mjx-mtd[id]').forEach(function (td) {
          var id = td.id;
          if (!id.startsWith('mjx-eqn:')) return;
          var tag = 'eqn-' + id.slice('mjx-eqn:'.length);
          var anchor = document.getElementById(tag);
          if (!anchor) return;
          var link = document.createElement('a');
          link.href = '#' + tag;
          link.style.color = 'inherit';
          link.style.textDecoration = 'none';
          while (td.firstChild) link.appendChild(td.firstChild);
          td.appendChild(link);
        });
        clampWideInlineMath();
        window.addEventListener("resize", clampWideInlineMath, { passive: true });
      });
    }
  }
};

// Inline math cannot line-break, so a formula wider than the text column gets
// clipped by the page (html is overflow-x: hidden). Make just the too-wide
// containers scrollable; every other container is left untouched to avoid
// clipping glyph overhang.
function clampWideInlineMath() {
  document.querySelectorAll('mjx-container:not([display="true"])').forEach(function (c) {
    var block = c.parentElement;
    while (block && getComputedStyle(block).display.indexOf("inline") !== -1) {
      block = block.parentElement;
    }
    if (!block) return;
    var r = c.getBoundingClientRect();
    if (r.width > block.clientWidth + 1 ||
        r.right > document.documentElement.clientWidth + 1) {
      c.style.display = "inline-block";
      c.style.maxWidth = "100%";
      c.style.overflowX = "auto";
      c.style.overflowY = "hidden";
    }
  });
}
