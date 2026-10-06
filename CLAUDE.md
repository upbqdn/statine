# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Statine is a Hugo theme for [marek.onl](https://marek.onl), forked from [hugo-astatine-theme](https://github.com/hugcis/hugo-astatine-theme). It's a minimal blog theme with light and dark modes, Tailwind CSS v4, native MathML (converted from TeX at build time with Temml), Pagefind search, and Remark42 comments. Its design is direction D of the Arboretum design (EB Garamond, Garamond-Math): ink on paper, one accent for links, statement kinds coded by rule weight, running text justified and hyphenated at every width. No third-party origins are in the critical render path: fonts are self-hosted and no script renders mathematics; only the Remark42 embed loads cross-origin.

## Commands

Install the pinned build tools (Tailwind, Temml) and build Tailwind CSS (compiles `assets/css/main.css` → `assets/css/style.css`):
```
npm ci
npm run build-tw
```

After `hugo`, convert the formulas to MathML, then index (from the site directory):
```
python3 themes/statine/tools/mathml.py public
npx pagefind@1.5.2 --site public
```
The step `tools/mathml.py` (stdlib Python; runs Temml through `node`) is part of the build, not optional: without it pages show raw TeX. Deploys run it between `hugo` and `pagefind`.

Serve the output and run the browser
regression (including responsive mathematics and equation anchors):
```
uv run --with playwright python tools/check_typography.py http://127.0.0.1:8875/
```
It uses Chromium at `/usr/bin/chromium` and writes ignored screenshots to
`typography-check/`.

This theme is used inside a Hugo site. Hugo commands are run from the parent site directory (`/home/m/marek.onl/`), not from the theme directory.

**Always run `npm run build-tw` after editing `main.css` or changing classes in `layouts/`.** The compiled `style.css` is generated and untracked (gitignored); Hugo needs it on disk, so run `build-tw` once after cloning and after every relevant edit. Deploys regenerate it. Tailwind scans only `layouts/` (via `@source` in `main.css`).

## Architecture

### Template Hierarchy

`layouts/_default/baseof.html` is the base layout. All pages extend it via Hugo's block system.

- **baseof.html** — HTML skeleton, skip link, one header bar: wordmark and nav (`partials/nav.html`), Pagefind search UI (guarded init; the index only exists after a `pagefind` run), light/dark toggle, Contents button (aria-expanded) on posts with a ToC
  - **partials/head.html** — Stored theme choice and anti-FOUC style, meta (canonical, description, theme-color per scheme), favicons, Open Graph, font preload, JS, Pagefind assets, then the stylesheet (after Pagefind's, which it restyles), RSS links
  - **partials/pagefind-dir.html** — Pagefind bundle directory; `HUGO_PAGEFIND_VERSION` versions the URL so a cached client never meets a mismatched index
  - **partials/nav.html** — Wordmark (author name), Notes, Arboretum, About
  - **partials/footer.html** — E-mail, GitHub and Bluesky, in words
  - **partials/tag-chip.html**, **partials/post-date.html** — shared chip markup; a date as "2 January 2026", unbroken
  - **partials/extra_js.html** — Loads `toc.js`
- **_default/single.html** — Blog posts: title and date line (with the revision date), Schema.org microdata, statement heads ("Theorem n4 (Name).", italic "Proof."), formulas wrapped in `data-pagefind-ignore` spans for `tools/mathml.py` with a hidden plain-text copy for search (trimmed, so the minifier cannot swallow the space after a formula), Remark42 comments (host/site_id read `site.Params.remark42` with marek.onl defaults)
- **_default/list.html** — Generic listings, uses `partials/list-item.html`
- **taxonomy/tag.html**, **taxonomy/tag.terms.html** — term pages and the /tags/ cloud
- **index.html** — Homepage: tags, then the notes, newest first

### CSS Pipeline

Source: `assets/css/main.css` (Tailwind v4 directives, Temml's stylesheet imported from `node_modules`, `@layer base` defaults, then the design's rules unlayered so they win over the templates' utility classes and over Pagefind's and Temml's stylesheets)
→ `@tailwindcss/cli` compiles to `assets/css/style.css`
→ Hugo minifies and fingerprints at build time via `resources.Minify` and `resources.Fingerprint`

All theme customization is in `main.css`. Colour tokens (`--paper`, `--ink`, `--muted`, `--hairline`, `--accent`) are set on `:root` per scheme; Tailwind's `@theme` palette maps onto them, so utility classes follow. The anti-FOUC inline style in `head.html` duplicates `--paper`/`--ink` as literals — keep them in sync.

### ToC

Layout derives from custom properties on `:root`: `--page-max-width` (content column, also used by `.container`), `--toc-width`, `--toc-gap`. The desktop ToC offset is `calc(var(--page-max-width) / 2 + var(--toc-gap))` — change the container width in one place and the ToC follows. The desktop breakpoint (1280px) exists in exactly three places, marked with cross-referencing comments: the `min-width: 1280px` block and the header's `max-width: 1279px` rule in `main.css`, and one `matchMedia` in `toc.js`.

CSS owns ToC appearance through three class hooks: `.toc-open` (mobile manual open), `li > ul.expanded` (scroll-spy branch), `a.current` (highlight). JS toggles state only. Templates mark the contracts explicitly: `data-toc-anchor` (the title the fixed ToC aligns to), `data-toc-scope` (the element whose headings are scroll-spied).

### JavaScript

No jQuery, and none for mathematics. Two Hugo-processed scripts:
- `assets/js/initial.js` (in `<head>`) — `siteTheme()` global (the toggle's choice, else the system's), `siteThemeChanged()` for the toggle, Remark42 theme sync, plot iframe light/dark swap (a parse-time MutationObserver corrects `iframe.plot` srcs before the wrong-theme file is fetched)
- `assets/js/toc.js` (end of body) — ToC scroll-spy, mobile toggle, desktop positioning

### Mathematics

The post-build step `tools/mathml.py` rewrites the built pages: every formula's TeX becomes MathML (Temml, pinned in `package.json`; one `node` run per build), set by the browser in Garamond-Math. An inline formula is cut into one `<math>` per TeX break point (after relations and binary operators), joined by spaces carrying the operator's math glue (`mk` before it, unbreakable; `mg` after it, the break), so justified lines break and stretch inside formulas as TeX does; a piece wider than the column scrolls on its own; a display breaks the same way, each line centred, and scrolls only when one piece is wider than the column. Around the formulas it glues a character set before a formula to it, adds break points to URLs, marks numeric table columns (`num`) and long cells (`prose`), and links each equation tag `(d9)` to its anchor `eqn-d9`. It asserts that the hidden search copies hold no TeX and swallow no space.

### Fonts

All self-hosted in `static/fonts/`, SIL OFL 1.1, licence texts beside them:
- **EB Garamond** — text; `eb-garamond-{regular,italic,semibold,semibolditalic}.woff2` (regular preloaded), Latin and Greek with every layout feature (lining figures, real small caps)
- **Garamond-Math** — mathematics, `garamond-math.woff2`: the whole font (its MATH table), with `SubscriptBaselineDropMin` set to 0 (a letter's subscript sits where TeX puts it) and the 13 italic Greek capitals that share a glyph with a Latin capital dropped from the cmap, so copy and search see the Latin. Stylistic set ss03 draws `\mathcal`; the same file at `size-adjust: 93.9%` serves `\mathsf` (its sans alphabet) and text arrows
- **Iosevka Web** — code; `iosevka.woff2`, Iosevka Regular subset to Latin-1, punctuation and arrows; set at the text's x-height
- **Libertinus Math** — `libertinus-heart.woff2`, the one ♡ the text faces lack

The earlier faces (EB Garamond variable, Iosevka Extended, TeX Gyre Pagella) remain for cached stylesheets.

### Dark Mode

The system's scheme by default; the header toggle stores the reader's choice in `localStorage.theme` and sets `data-theme` on `<html>`, which an inline script in `head.html` restores before first paint. CSS keys every token on `[data-theme]` or, without it, `prefers-color-scheme`; Tailwind's `dark:` variants still follow the system alone, harmless while every palette colour maps to a token. The script `initial.js` re-themes plot iframes and Remark42 on either change. Code has no syntax colour (no Chroma stylesheet). The `theme-color` metas carry `media` attributes.

### CI

The CI file `.gitlab-ci.yml` runs GitLab SAST plus `build-tw` (after `npm ci`), which fails if `main.css` no longer compiles.
