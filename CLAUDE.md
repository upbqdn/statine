# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Statine is a Hugo theme for [marek.onl](https://marek.onl), forked from [hugo-astatine-theme](https://github.com/hugcis/hugo-astatine-theme). It's a minimal, dark-mode-capable blog theme with Tailwind CSS v4, MathJax, Pagefind search, and Remark42 comments.

## Commands

Build Tailwind CSS (compiles `assets/css/main.css` → `assets/css/style.css`):
```
npm run build-tw
```

This theme is used inside a Hugo site. Hugo commands are run from the parent site directory (`/home/m/marek.onl/`), not from the theme directory.

**Always run `npm run build-tw` after editing `main.css`.** The compiled `style.css` is checked into git.

## Architecture

### Template Hierarchy

`layouts/_default/baseof.html` is the base layout. All pages extend it via Hugo's block system.

- **baseof.html** — HTML skeleton, Pagefind search UI, ToC toggle button
  - **partials/head.html** — Meta, favicons, Open Graph, CSS/JS loading, MathJax, Font Awesome 6.7.2, Iosevka web font
  - **partials/nav.html** — Site title
  - **partials/footer.html** — About link + social icons (Bluesky via inline SVG, GitHub/GitLab via Font Awesome)
  - **partials/extra_js.html** — Loads `toc.js`
- **_default/single.html** — Blog posts (Schema.org microdata, reading time, references, Remark42 comments)
- **_default/list.html** — Tag/category listings, uses `partials/list-item.html`
- **index.html** — Homepage tag cloud with logarithmic weight sizing

### CSS Pipeline

Source: `assets/css/main.css` (Tailwind v4 directives + custom `@layer base` styles)
→ `@tailwindcss/cli` compiles to `assets/css/style.css`
→ Hugo minifies at build time via `resources.Minify`

All theme customization is in `main.css` using Tailwind's `@theme` directive for design tokens (colors, fonts, grid templates). Dark mode uses `prefers-color-scheme` media queries (no class toggle).

### ToC Positioning

The Table of Contents is fixed-position on desktop (≥1280px), placed to the right of content. Its `margin-left` in `main.css` must be `calc(<half-container-width> + 30px)` — update this when changing the container `max-width`.

### JavaScript

Two Hugo-processed scripts (inlined via `safeJS` in `<head>` and at page end):
- `assets/js/initial.js` — Color scheme detection, syntax highlight theme switching, plot light/dark switching, Remark42 theme sync, non-breaking hyphen replacement
- `assets/js/toc.js` — ToC scroll tracking with current section highlighting, responsive show/hide (uses jQuery)

### Fonts

- **EB Garamond** — Body text, self-hosted woff2 at `/fonts/EBGaramond.woff2`, set as `--font-sans` in `@theme`
- **Iosevka Web** — Code blocks, loaded from `iosevka-webfonts.github.io`

### Dark Mode

System-only via `prefers-color-scheme` — no manual toggle. `initial.js` listens for changes and updates: syntax highlight CSS, plot iframe sources (`-dark.html` variants), and Remark42 theme. An inline `<style>` in `head.html` sets background/text immediately to prevent FOUC.

### Internationalization

`i18n/` has translations for en, de, fr.
