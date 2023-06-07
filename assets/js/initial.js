function updateMode() {
  if (
    localStorage.theme === "dark" ||
    (!("theme" in localStorage) &&
      window.matchMedia("(prefers-color-scheme: dark)").matches)
  ) {
    document.documentElement.classList.add("dark");

    // Adjust code snippets.
    document.getElementById("code-syntax-theme").href = "/css/syntax-dark.css";

    // Adjust plots.
    let plots = document.getElementsByClassName("plot");
    for (var i = plots.length - 1; i >= 0; --i) {
      if (typeof plots[i].src === "undefined") {
        continue;
      }
      let plot_src = plots[i].src.split(".html");
      plots[i].src = plot_src[0] + "-dark" + ".html";
    }

    // Adjust the comments section.
    localStorage.remark42_theme = "dark";
    if (window.REMARK42) {
      window.REMARK42.changeTheme("dark");
    }
  } else {
    document.documentElement.classList.remove("dark");

    // Adjust code snippets.
    document.getElementById("code-syntax-theme").href = "/css/syntax-light.css";

    // Adjust plots.
    let plots = document.getElementsByClassName("plot");
    for (var i = plots.length - 1; i >= 0; --i) {
      if (typeof plots[i].src === "undefined") {
        continue;
      }
      plots[i].src = plots[i].src.replace(/-dark/g, "");
    }

    // Adjust the comments section.
    localStorage.remark42_theme = "light";
    if (window.REMARK42) {
      window.REMARK42.changeTheme("light");
    }
  }
}

function toggleMode() {
  if ("theme" in localStorage) {
    if (localStorage.theme === "dark") {
      localStorage.theme = "light";
    } else {
      localStorage.theme = "dark";
    }
  } else {
    if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
      localStorage.theme = "light";
    } else {
      localStorage.theme = "dark";
    }
  }
  updateMode();
}

function handleToc() {
  toc = document.getElementById("TableOfContents");
  if (toc) {
    if (window.innerWidth < 1400) {
      toc.style.display = "none";

      if (!toc.childNodes.length) {
        document.getElementById("toc-btn").style.display = "none";
      }
    } else {
      toc.style.display = "block";
    }
  }
}

// window.addEventListener("load", (event) => {
// });

function document_ready(f) {
  // in case the document is already rendered
  if (document.readyState != "loading") f();
  else if (document.addEventListener)
    document.addEventListener("DOMContentLoaded", f);
}

(function () {
  window.addEventListener("hResize", (event) => {
    handleToc();
  });

  document_ready(function () {
    handleToc();
    updateMode();
  });

  // Horizontal window resize events.
  var prev_width = window.innerWidth;

  window.onresize = function () {
    var curr_width = window.innerWidth;

    if (
      (curr_width < 1400 && prev_width >= 1400) ||
      (curr_width >= 1400 && prev_width < 1400)
    ) {
      window.dispatchEvent(new Event("hResize"));
    }

    prev_width = curr_width;
  };
})();
