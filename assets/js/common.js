function updateMode() {
  // On page load or when changing themes, best to add inline in `head` to avoid FOUC
  if (
    localStorage.theme === "dark" ||
    (!("theme" in localStorage) &&
      window.matchMedia("(prefers-color-scheme: dark)").matches)
  ) {
    document.documentElement.classList.add("dark");
    document.getElementById("code-syntax-theme").href = "/css/syntax-dark.css";

    localStorage.remark42_theme = "dark";
    if (window.REMARK42) {
      window.REMARK42.changeTheme("dark");
    }
  } else {
    document.documentElement.classList.remove("dark");
    document.getElementById("code-syntax-theme").href = "/css/syntax-light.css";

    localStorage.remark42_theme = "light";
    if (window.REMARK42) {
      window.REMARK42.changeTheme("light");
    }
  }
}

function toggleMode() {
  if ("theme" in localStorage) {
    if (localStorage.theme === "dark") {
      // Whenever the user explicitly chooses light mode
      localStorage.theme = "light";
    } else {
      // Whenever the user explicitly chooses dark mode
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

function toggleMenu() {
  let navbar = document.getElementById("navbar-default");
  if (navbar.classList.contains("hidden")) {
    navbar.classList.remove("hidden");
  } else {
    navbar.classList.add("hidden");
  }
}

function toggleToc() {
  let toc = document.getElementById("TableOfContents");
  if (window.getComputedStyle(toc, null).display == "none") {
    toc.style.display = "block";
  } else {
    toc.style.display = "none";
  }
}

function handleToc() {
  if (window.innerWidth < 1400) {
    toc = document.getElementById("TableOfContents");
    toc.style.display = "none";

    if (!toc.childNodes.length) {
      document.getElementById("toc-btn").style.display = "none";
    }
  } else {
    toc.style.display = "block";
  }
}

window.onload = function () {
  updateMode();
  handleToc();
};

window.onresize = function () {
  if (window.innerWidth >= 1400) {
    toc.style.display = "block";
  }
};
