# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Statine is a Hugo theme for [marek.onl](https://marek.onl), forked from [hugo-astatine-theme](https://github.com/hugcis/hugo-astatine-theme). It's a minimal, dark-mode-capable blog theme with Tailwind CSS v4, MathJax, Pagefind search, and Remark42 comments. No third-party origins are in the critical render path: fonts are self-hosted and icons are inline SVG; only MathJax (pinned, SRI, async, math pages only) and the Remark42 embed load cross-origin.

## Commands

Build Tailwind CSS (compiles `assets/css/main.css` → `assets/css/style.css`):
```
npm run build-tw
```

This theme is used inside a Hugo site. Hugo commands are run from the parent site directory (`/home/m/marek.onl/`), not from the theme directory.

**Always run `npm run build-tw` after editing `main.css` or changing classes in `layouts/`.** The compiled `style.css` is generated and untracked (gitignored); Hugo needs it on disk, so run `build-tw` once after cloning and after every relevant edit. Deploys regenerate it. Tailwind scans only `layouts/` (via `@source` in `main.css`).

## Architecture

### Template Hierarchy

`layouts/_default/baseof.html` is the base layout. All pages extend it via Hugo's block system.

- **baseof.html** — HTML skeleton, skip link, Pagefind search UI (guarded init; the index only exists after a `pagefind` run), ToC toggle button (inline SVG, aria-expanded)
  - **partials/head.html** — Meta (canonical, description, theme-color per scheme), favicons, Open Graph, font preload, CSS/JS loading, MathJax, RSS links
  - **partials/pagefind-dir.html** — Pagefind bundle directory; `HUGO_PAGEFIND_VERSION` versions the URL so a cached client never meets a mismatched index
  - **partials/mathjax.html** — Pinned MathJax 3.2.2 with SRI, async, loaded only on pages whose raw content has math delimiters (`math` front-matter param overrides)
  - **partials/nav.html** — Site title
  - **partials/footer.html** — About link + GitHub/Bluesky icons (inline Font Awesome SVG paths, CC BY 4.0 attribution in each)
  - **partials/tag-chip.html**, **partials/post-date.html** — shared chip and date markup
  - **partials/extra_js.html** — Loads `toc.js`
- **_default/single.html** — Blog posts (Schema.org microdata, math wrapping for Pagefind, Remark42 comments; host/site_id read `site.Params.remark42` with marek.onl defaults)
- **_default/list.html** — Generic listings, uses `partials/list-item.html`
- **taxonomy/tag.html**, **taxonomy/tag.terms.html** — term pages and the /tags/ cloud
- **index.html** — Homepage tag cloud

### CSS Pipeline

Source: `assets/css/main.css` (Tailwind v4 directives + custom `@layer base` styles)
→ `@tailwindcss/cli` compiles to `assets/css/style.css`
→ Hugo minifies at build time via `resources.Minify`

All theme customization is in `main.css` using Tailwind's `@theme` directive for design tokens (colors, fonts). Dark mode uses `prefers-color-scheme` media queries (no class toggle). The anti-FOUC inline style in `head.html` duplicates `--color-dark`/`--color-fg` as literals — keep them in sync with `@theme`.

### ToC

Layout derives from custom properties on `:root`: `--page-max-width` (content column, also used by `.container`), `--toc-width`, `--toc-gap`. The desktop ToC offset is `calc(var(--page-max-width) / 2 + var(--toc-gap))` — change the container width in one place and the ToC follows. The desktop breakpoint (1280px) exists in exactly two places, marked with cross-referencing comments: one `@media` block in `main.css` and one `matchMedia` in `toc.js`.

CSS owns ToC appearance through three class hooks: `.toc-open` (mobile manual open), `li > ul.expanded` (scroll-spy branch), `a.current` (highlight). JS toggles state only. Templates mark the contracts explicitly: `data-toc-anchor` (the title the fixed ToC aligns to), `data-toc-scope` (the element whose headings are scroll-spied).

### JavaScript

No jQuery. Two Hugo-processed scripts (inlined via `safeJS`):
- `assets/js/initial.js` (in `<head>`) — `siteTheme()` global, Remark42 theme sync, plot iframe light/dark swap (a parse-time MutationObserver corrects `iframe.plot` srcs before the wrong-theme file is fetched), non-breaking-hyphen pass (TreeWalker over `<main>`; never touches `code`/`kbd`/`samp`/`pre`, raw-TeX spans, or MathJax output — MathJax silently drops U+2011)
- `assets/js/toc.js` (end of body) — ToC scroll-spy, mobile toggle, desktop positioning

### Fonts

All self-hosted in `static/fonts/`, SIL OFL 1.1:
- **EB Garamond** — body text; `EBGaramond.woff2` (regular, preloaded in head) + `EBGaramond-Italic.woff2` (true italics)
- **Iosevka Web** — code; `IosevkaExtended.woff2`, the extended (125%-wide) face subsetted to Latin + punctuation + arrows + box drawing (~26 KB). Regenerate with `pyftsubset` (woff2 → ttf → subset → woff2) if wider glyph coverage is ever needed.

### Dark Mode

System-only via `prefers-color-scheme` — no manual toggle. Syntax-highlight CSS uses two `<link media="...">` tags (no JS swap). `initial.js` reacts to scheme changes for plot iframes and Remark42. An inline `<style>` in `head.html` sets background/text immediately to prevent FOUC. `theme-color` metas carry `media` attributes.

### CI

`.gitlab-ci.yml` runs GitLab SAST plus `build-tw`, which fails if `main.css` no longer compiles.
