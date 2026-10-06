"""Check a built site: uv run --with playwright python tools/check_typography.py URL.

Serve the Hugo output (including its Pagefind index) before running this check.
"""

import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen
from xml.etree import ElementTree

from playwright.sync_api import sync_playwright

# Non-final lines of justified running text that end short of the column. A run of lines ends at
# a block-level descendant (a display) or <br>; inline math and other atoms count whole.
SHORT_LINES = r"""() => {
  const short = [];
  for (const b of document.querySelectorAll('.article-content :is(p, li, dd, .csl-entry)')) {
    const cs = getComputedStyle(b);
    if (cs.textAlign !== 'justify') continue;
    const right = b.getBoundingClientRect().right - parseFloat(cs.paddingRight);
    const runs = [[]];
    (function walk(el) {
      for (const n of el.childNodes) {
        if (n.nodeType === 3 && n.data.trim()) {
          const r = document.createRange();
          r.selectNodeContents(n);
          runs.at(-1).push(...[...r.getClientRects()].filter(x => x.width));
        } else if (n.nodeType === 1) {
          const d = getComputedStyle(n).display;
          if (d === 'none' || getComputedStyle(n).float !== 'none') continue;
          if (n.tagName === 'BR' || !/^(inline|contents|math$)/.test(d)) runs.push([]);
          else if (/^(inline|contents)$/.test(d)) walk(n);
          else runs.at(-1).push(n.getBoundingClientRect());
        }
      }
    })(b);
    for (const rects of runs) {
      const lines = [];  // [middle, right edge]
      for (const x of rects.sort((p, q) => p.top - q.top)) {
        const mid = (x.top + x.bottom) / 2;
        const l = lines.find(l => Math.abs(l[0] - mid) < parseFloat(cs.lineHeight) / 2);
        if (l) l[1] = Math.max(l[1], x.right); else lines.push([mid, x.right]);
      }
      lines.sort((p, q) => p[0] - q[0]).slice(0, -1).forEach(l => {
        if (right - l[1] > 1.5) short.push(b.textContent.trim().slice(0, 40));
      });
    }
  }
  return short;
}"""


def check(base):
    base = base.rstrip("/") + "/"
    origin = urlsplit(base).netloc
    sitemap = ElementTree.fromstring(urlopen(urljoin(base, "sitemap.xml")).read())
    paths = [urlsplit(node.text).path for node in sitemap.iter()
             if node.tag.endswith("}loc")]
    screenshots = Path("typography-check")
    screenshots.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path="/usr/bin/chromium")
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        # The comments embed is unrelated and must not contact a live service.
        page.route("**/remark42.marek.onl/**", lambda route: route.fulfill(
            body="", content_type="application/javascript"))
        errors = []
        external_math = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("response", lambda response: errors.append(
            f"{response.status} {response.url}")
            if response.status >= 400 and urlsplit(response.url).netloc == origin
            and urlsplit(response.url).path.startswith(("/vendor/", "/fonts/", "/css/", "/js/"))
            else None)
        page.on("request", lambda request: external_math.append(request.url)
                if "mathjax" in request.url.lower()
                and urlsplit(request.url).netloc != origin else None)

        def visit(path):
            response = page.goto(urljoin(base, path.lstrip("/")), wait_until="domcontentloaded")
            assert response.ok, path
            page.evaluate("document.fonts.ready")
            # tools/mathml.py left no TeX and no Temml error; equation tags link to anchors.
            assert not page.locator("merror, .tml-error").count(), path
            assert page.evaluate(r"""() => !/\\\(|\\\[|\$\$/.test(
              document.querySelector('.article-content')?.innerText ?? '')"""), path
            assert page.evaluate("""() => [...document.querySelectorAll('.tml-tag a')]
              .every(a => document.getElementById(a.hash.slice(1)))"""), path
            if page.locator(".article-content math").count():
                family = page.evaluate(
                    "getComputedStyle(document.querySelector('math')).fontFamily")
                assert family.lower().startswith('"garamond-math sans", garamond-math'), path
                assert page.evaluate("document.fonts.check('20px Garamond-Math')"), path
            assert page.evaluate("getComputedStyle(document.body).fontFamily").startswith('"EB Garamond"'), path
            assert page.evaluate("document.fonts.check('20px \"EB Garamond\"')"), path
            assert not errors, (path, errors)

        # Every published page: detect unconverted TeX and rendering errors.
        for path in paths:
            visit(path)
            # At desktop width no inline formula is wide enough to scroll in its own box.
            assert not page.evaluate("""() => [...document.querySelectorAll(
              'math:not(.tml-display)')].some(m => m.scrollWidth > m.clientWidth)"""), path
            print("render", path, flush=True)
        assert not external_math, external_math
        assert page.evaluate("""async () => {
          const faces = await Promise.all(['normal 400', 'italic 400', 'normal 600', 'italic 600']
            .map(style => document.fonts.load(style + ' 20px "EB Garamond"')));
          return faces.every(loaded => loaded.length === 1 && loaded[0].status === 'loaded');
        }""")

        for width in (1440, 768, 390, 320):
            page.set_viewport_size({"width": width, "height": 1000})
            for path in ("aes/", "field/", "groebner-basis/"):
                visit(path)
                assert page.evaluate(
                    "document.documentElement.scrollWidth <= innerWidth + 1"), (width, path)
                # Every line reaches the right edge. At 320 px a line can hold one formula piece
                # with no glue in it ("AddRoundKey(state,"), which TeX too leaves short.
                if width >= 390:
                    assert not (short := page.evaluate(SHORT_LINES)), (width, path, short)
                assert page.evaluate("""() => [...document.querySelectorAll('math')].every(c => {
                  const r = c.getBoundingClientRect();
                  if (r.left >= -1 && r.right <= innerWidth + 1) return true;
                  // Algorithms and matrices can scroll in a containing block.
                  for (let el = c; el && el !== document.body; el = el.parentElement) {
                    const rect = el.getBoundingClientRect();
                    if (/auto|scroll/.test(getComputedStyle(el).overflowX) &&
                        el.scrollWidth > el.clientWidth && rect.left >= -1 &&
                        rect.right <= innerWidth + 1) return true;
                  }
                  return false;
                })"""), (width, path)
            visit("aes/")
            assert page.locator(".article-content b[hidden]").count()
            assert page.locator(".math-punct").first.evaluate(
                "element => getComputedStyle(element).whiteSpace") == "nowrap"
            equation = page.locator('.tml-tag a[href="#eqn-d9"]')
            equation.click()
            assert page.evaluate("location.hash") == "#eqn-d9"
            # On a narrow phone, a matrix may be irreducibly wider than the
            # column. Its complete equation tag must still be scrollable into
            # view, not clipped by either the renderer or its paragraph.
            assert page.evaluate("""() => [...document.querySelectorAll('.tml-tag')].every(tag => {
              const scrollers = [];
              for (let el = tag.parentElement; el && el !== document.body; el = el.parentElement) {
                if (/auto|scroll/.test(getComputedStyle(el).overflowX)) {
                  el.scrollLeft = el.scrollWidth;
                  scrollers.push(el);
                }
              }
              const r = tag.getBoundingClientRect();
              const visible = r.left >= 0 && r.right <= innerWidth && scrollers.every(el => {
                const parent = el.getBoundingClientRect();
                return r.left >= parent.left - 1 && r.right <= parent.right + 1;
              });
              for (const el of scrollers) el.scrollLeft = 0;
              return visible;
            })"""), width
            # Text metrics affect line breaks; wide matrices may scroll on
            # phones, but must fit without scrolling on tablets and desktops.
            if width >= 768:
                assert equation.evaluate("element => element.getBoundingClientRect().right <= innerWidth"), width
            page.screenshot(path=str(screenshots / f"equation-{width}.png"))
            page.evaluate("window.scrollTo(0, 0)")
            if width < 1280:
                page.locator("#toc-btn").click()
                assert page.locator("#TableOfContents").is_visible()
                assert page.locator("#toc-btn").get_attribute("aria-expanded") == "true"
                page.locator("#toc-btn").click()
                assert not page.locator("#TableOfContents").is_visible()
            page.screenshot(path=str(screenshots / f"article-{width}.png"))
            print("responsive", width, flush=True)

        page.emulate_media(color_scheme="dark")
        visit("groebner-basis/")
        page.screenshot(path=str(screenshots / "article-dark.png"))
        page.locator(".pagefind-ui__search-input").fill("ideal")
        page.locator(".pagefind-ui__result-link").first.wait_for()
        assert page.locator(".pagefind-ui__result-link").count()
        assert not errors, errors
        browser.close()
    print("Typography, MathML, equation anchors, justified lines, responsive layout, ToC and"
          " search passed.")


if __name__ == "__main__":
    check(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8875/")
