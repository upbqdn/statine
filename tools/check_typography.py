"""Check a built site: uv run --with playwright python tools/check_typography.py URL.

Serve the Hugo output (including its Pagefind index) before running this check.
"""

import sys
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import urlopen
from xml.etree import ElementTree

from playwright.sync_api import sync_playwright


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
            if page.locator("#MathJax-script").count():
                page.wait_for_function("window.MathJax && MathJax.startup && MathJax.startup.promise")
                page.evaluate("MathJax.startup.promise")
                assert page.evaluate("MathJax.version") == "4.1.3", path
                assert page.evaluate("MathJax.config.output.font") == "mathjax-pagella", path
                assert page.locator("mjx-container").count(), path
                assert not page.locator("mjx-merror").count(), path
                assert page.evaluate("""() => [...document.querySelectorAll('mjx-mtd[id]')]
                  .every(td => !document.getElementById('eqn-' + td.id.slice(8)) ||
                    td.querySelector('a')?.getAttribute('href') === '#eqn-' + td.id.slice(8))"""), path
            page.evaluate("document.fonts.ready")
            assert page.evaluate("getComputedStyle(document.body).fontFamily").startswith('"TeX Gyre Pagella"'), path
            assert page.evaluate("document.fonts.check('20px \"TeX Gyre Pagella\"')"), path
            assert not errors, (path, errors)

        # Every published page: detect missing TeX extensions and rendering errors.
        for path in paths:
            visit(path)
            print("render", path, flush=True)
        assert not external_math, external_math
        assert page.evaluate("""async () => {
          const faces = await Promise.all(['normal 400', 'italic 400', 'normal 700', 'italic 700']
            .map(style => document.fonts.load(style + ' 20px "TeX Gyre Pagella"')));
          return faces.every(loaded => loaded.length === 1 && loaded[0].status === 'loaded');
        }""")

        for width in (1440, 768, 390, 320):
            page.set_viewport_size({"width": width, "height": 1000})
            for path in ("aes/", "field/", "groebner-basis/"):
                visit(path)
                assert page.evaluate("document.body.scrollWidth <= innerWidth + 1"), (width, path)
                assert page.evaluate("""() => [...document.querySelectorAll('mjx-container')].every(c => {
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
            equation = page.locator('mjx-mtd a[href="#eqn-d9"]')
            equation.click()
            assert page.evaluate("location.hash") == "#eqn-d9"
            # On a narrow phone, a matrix may be irreducibly wider than the
            # column. Its complete equation tag must still be scrollable into
            # view, not clipped by either the renderer or its paragraph.
            assert page.evaluate("""() => [...document.querySelectorAll('mjx-mtd[id]')].every(tag => {
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
            if width >= 390:
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
    print("Typography, MathJax, equation anchors, responsive layout, ToC and search passed.")


if __name__ == "__main__":
    check(sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8875/")
