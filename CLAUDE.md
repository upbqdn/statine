# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Statine is a Hugo theme for [marek.onl](https://marek.onl), forked from [hugo-astatine-theme](https://github.com/hugcis/hugo-astatine-theme). It's a minimal, dark-mode-capable blog theme with Tailwind CSS, MathJax, Pagefind search, and Remark42 comments.

## Commands

Build Tailwind CSS (compiles `assets/css/main.css` → `assets/css/style.css`):
```
npm run build-tw
```

This theme is used inside a Hugo site. Hugo commands are run from the parent site directory (`/home/m/marek.onl/`), not from the theme directory.

Hugo requires Extended edition, minimum v0.57.0.

## Architecture

### Template Hierarchy

`layouts/_default/baseof.html` is the base layout. All pages extend it via Hugo's block system.

- **baseof.html** — HTML skeleton, dark mode class, Pagefind search UI, ToC toggle
  - **partials/head.html** — Meta, favicons, Open Graph, CSS/JS loading, MathJax, Font Awesome
  - **partials/nav.html** — Site title + dark mode toggle
  - **partials/footer.html** — About link + social icons (Bluesky, GitHub, GitLab)
  - **partials/extra_js.html** — Conditional JS loading
- **_default/single.html** — Blog posts (Schema.org microdata, reading time, references, Remark42 comments)
- **_default/list.html** — Tag/category listings, uses `partials/list-item.html`
- **index.html** — Homepage tag cloud with logarithmic weight sizing

### CSS Pipeline

Source: `assets/css/main.css` (Tailwind directives + custom `@layer base` styles, imports `katex.css`)
→ Tailwind CLI compiles to `assets/css/style.css`
→ Hugo minifies at build time

Tailwind config: class-based dark mode, 40rem max-width container, KaTeX as default sans font.

### JavaScript

Two Hugo-processed scripts (inlined via `safeJS`):
- `assets/js/initial.js` — Theme toggle, ToC visibility, non-breaking hyphen replacement, syntax highlight theme switching, plot image light/dark switching, Remark42 theme sync
- `assets/js/toc.js` — ToC scroll tracking with current section highlighting (uses jQuery)

Static JS: jQuery 3.3.1 slim, MathJax 3 config + CDN

### Static Assets

- `static/css/` — Syntax highlighting themes (light + dark)
- `static/fonts/` — KaTeX woff2 fonts
- `static/img/` — Icons (dark/light mode variants, RSS)
- `static/js/` — jQuery, MathJax config

### Internationalization

`i18n/` has translations for en, de, fr.
