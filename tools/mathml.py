"""Post-build step: python3 tools/mathml.py PUBLIC_DIR, after `hugo` and before `pagefind`.

Converts every formula single.html left as TeX (in <span data-pagefind-ignore>) to MathML with
Temml (npm, pinned in package.json; run `npm ci` in the theme first), set by the browser in
Garamond-Math. Temml writes MathML Core (Unicode math letters, \\tag and aligned widths) and
groups an inline formula into pieces that end at TeX's break points; fix_mml recuts them, sets
each piece of an inline formula as its own <math>, joined by a space carrying its math glue, so
the browser can break and justify between them, and wraps a display's pieces so a phone breaks it
instead of scrolling it; an equation tag links to its anchor. The page rewrites around the
formulas: a character glued before a formula stays with it, URLs get break points, numeric table
columns are marked. Run once on a fresh build. Stdlib only.
"""
import html
import json
import pathlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

THEME = pathlib.Path(__file__).resolve().parent.parent

# ---- TeX's inline-formula break points, on MathML in Temml's encoding: delimiters carry
# form="prefix"/"postfix" and fence (stretchy "false" when plain), commas separator="true", big
# operators movablelimits, ordinary symbols are mi.
SCRIPTED = {"msub", "msup", "msubsup", "munder", "mover", "munderover", "mmultiscripts"}


def breaks_after(e):
    """TeX breaks an inline formula after a relation or binary operator (TeXbook p. 173), scripts
    and all (⪰_lex); Temml also after a comma. Not after a fence, a unary sign or a big operator."""
    if e.tag in SCRIPTED and len(e):
        e = e[0]
    return (e.tag == "mo" and e.get("form") not in ("prefix", "postfix")
            and "fence" not in e.attrib and "movablelimits" not in e.attrib)


def pieces(top):
    """A formula's outer level cut after each break point. A plain delimiter pair is opened when
    it holds a relation or binary operator: \\{n ∈ S\\} is not a group in TeX (\\left\\{ …
    \\right\\} is: stretchy, kept); a tuple (f₁, …, fₘ) is not opened, as TeX does not break
    after a comma. Glue after the operator stays with it. Chromium drops the spacing of a piece
    holding one operator, so it joins the piece before."""
    def pair(e):
        return (e.tag == "mrow" and len(e) > 2 and e[0].tag == e[-1].tag == "mo"
                and e[0].get("stretchy") == e[-1].get("stretchy") == "false"
                and e[0].get("form") == "prefix" and e[-1].get("form") == "postfix")

    def outer(es):
        out = []
        for e in es:
            inner = outer(e) if pair(e) else []
            out += inner if any(breaks_after(x) and x.get("separator") != "true"
                                for x in inner[:-1]) else [e]
        return out

    top = outer(top)
    out, cur = [], []
    for e, nxt in zip(top, top[1:] + [None]):
        cur.append(e)
        last = next((x for x in reversed(cur) if x.tag != "mspace"), e)
        if nxt is not None and nxt.tag != "mspace" and breaks_after(last):
            if len(cur) == 1 and cur[0].tag == "mo" and out:
                out[-1] += cur
            else:
                out.append(cur)
            cur = []
    return out + [cur] if cur else out


# Chromium's (MathML Core's) lspace and rspace, in em, for the infix operators that end a piece;
# anything else (relations, arrows, the dictionary's default) is thick. Measured, not derived.
# ponytail: a new medium or thin operator (±, ⊗) falls back to thick, 1 px off; add it here.
PUNCT, THIN, MEDIUM = set(",:"), set("⋅×∘"), set("+−∖∪∩/")


def space(op, side):
    """An operator's lspace or rspace in em. An empty one (Temml's \\allowbreak) has none, as in
    TeX; Chromium spaced it as a relation."""
    if op.get(side):
        return float(op.get(side).removesuffix("em"))
    t = op.text
    return (0.0 if not t or t in PUNCT and side == "lspace" else 3 / 18 if t in PUNCT | THIN
            else 4 / 18 if t in MEDIUM else 5 / 18)


def inline_pieces(ps):
    """An inline formula's pieces as <math> elements joined by TeX's math glue, each glue a space
    with its width in --w: the operator ending a piece moves to a <math> of its own, its lspace
    becomes a space the line cannot break at (class mk) and its rspace, with any glue after it
    (\\pmod's 8mu), one it can (mg). Justification stretches both, as TeX stretches thick and
    medium math glue, so a line ending at a break is flush and so is a line holding only
    "x ←" before an unbreakable piece; the glue at a break hangs, as TeX discards it. The piece
    before such an operator is class ml: main.css leaves room beside it for the operator, which
    must share its line."""
    def math(es, attrs=""):
        inner = "".join(ET.tostring(e, encoding="unicode") for e in es)
        return f"<math{attrs}>{inner}</math>"

    def sp(cls, w):
        return f'<span class={cls} style="--w:{w:.4f}em"> </span>'

    out = []
    for p in ps[:-1]:
        r = 0.0
        while p[-1].tag == "mspace":
            r += float(p.pop().get("width").removesuffix("em"))
        op = p[-1][0] if p[-1].tag in SCRIPTED else p[-1]
        assert op.tag == "mo", ET.tostring(op)
        lsp, r = space(op, "lspace"), r + space(op, "rspace")
        op.set("lspace", "0")
        op.set("rspace", "0")
        if len(p) > 1 and lsp:  # a formula's first operator has nothing to space from, as in TeX
            out += [math(p[:-1], " class=ml"), sp("mk", lsp)]
            p = p[-1:]
        out += [math(p), sp("mg", r)]
    return "".join(out) + math(ps[-1])


def group(tex):
    """Whether a formula is one TeX group {…}, which TeX never breaks."""
    tex = re.sub(r"\\[{}]", "..", tex.strip())  # \{ \} are delimiters, not braces
    depth = 0
    for i, c in enumerate(tex):
        depth += (c == "{") - (c == "}")
        if not depth:
            return tex[0] == "{" and i == len(tex) - 1
    return False


def fix_mml(mml, grouped=False):
    """Garamond-Math draws its prime (U+2032) already raised, so a superscripted prime is set after
    its base instead (r′₀, as most math fonts' fallback). MathML Core keeps operator spacing in
    scripts; TeX drops it in script style, so operators in scripts and in inline fractions get
    zero lspace/rspace. An ellipsis is an operator with relation-like spacing in MathML Core and
    an ordinary symbol in TeX (g₁, …, gₘ), so it becomes an mi. An inline formula is set as one
    <math> per break piece, joined by its math glue (inline_pieces) as spaces the line can stretch
    and break at: Temml's own flex-wrap breaks a formula only when it is wider than the whole
    column, and a bare <wbr> left a line of formula nothing to justify with. A
    display's pieces become flex items, each line centred, so a phone breaks it instead of
    scrolling it."""
    root = ET.fromstring(mml)
    inline = root.get("display") != "block"
    for e in root.iter("mo"):
        if e.text in ("…", "⋯", "⋮", "⋱"):
            e.tag = "mi"
            e.attrib.clear()

    def walk(e, script):
        for i, c in enumerate(list(e)):
            if (c.tag in ("msup", "msubsup") and c[-1].tag == "mo"
                    and "tml-prime" in c[-1].get("class", "")):
                del c[-1].attrib["class"]
                based = ET.Element("mrow")
                based.extend([c[0], c[-1]])
                if c.tag == "msubsup":
                    sub, based = based, ET.Element("msub")
                    based.extend([sub, c[1]])
                e[i] = c = based
            s = script or (e.tag in SCRIPTED and i > 0) or (e.tag == "mfrac" and inline)
            if c.tag == "mo" and s:
                c.attrib.setdefault("lspace", "0em")
                c.attrib.setdefault("rspace", "0em")
            walk(c, s)

    walk(root, False)
    if inline:  # Temml's pieces (mrows). One mrow is its one piece (y² ≻_rclex xz: Temml does not
        # cut after a scripted relation), unless the formula is one {group} or a delimiter pair,
        # which pieces() opens when TeX would.
        one = (len(root) == 1 and root[0].tag == "mrow" and len(root[0])
               and root[0][0].get("fence") != "true" and not grouped)
        ps = pieces([e for p in root for e in p] if len(root) > 1 or one else list(root))
    elif len(root) == 1 and root[0].tag == "mrow" and len(root[0]) and (
            root[0][0].get("fence") != "true"):
        ps = pieces(list(root[0]))  # Temml does not cut a display: its one mrow
    else:  # \tag, aligned, a lone \left…\right: one box
        ps = []
    if len(ps) > 1:
        text = "".join(root.itertext())
        if inline:
            assert not root.attrib, mml
            out = inline_pieces(ps)
        else:  # flex items (main.css math.tml-wrap): one mrow per piece, inside one per equation
            # when glue parts several (f₁ = …,\quad f₂ = …), so a line breaks between them first
            groups = [[]]
            for p in ps:
                groups[-1].append(p)
                if p[-1].tag == "mspace":
                    groups.append([])
            groups = [g for g in groups if g]
            for c in list(root):
                root.remove(c)
            for g in groups:
                eq = ET.SubElement(root, "mrow", {"class": "tml-eq"}) if len(groups) > 1 else root
                for p in g:
                    ET.SubElement(eq, "mrow").extend(p)
            del root.attrib["style"]
            root.set("class", "tml-display tml-wrap")
            out = ET.tostring(root, encoding="unicode")
        lost = re.sub("<span class=m[gk][^>]*> </span>|<[^>]+>", "", out)
        assert lost == html.escape(text, quote=False), mml  # nothing lost
        return out
    return ET.tostring(root, encoding="unicode")


assert group("{a = b}") and not group("{a}{b}") and not group(r"\{x\} = y") and not group("a")

TEX = re.compile(r"<span data-pagefind-ignore>(\\\(|\\\[|\$\$)(.*?)(?:\\\)|\\\]|\$\$)</span>",
                 re.DOTALL)
TEMML_RUN = ("const t = require('temml'); process.stdout.write(JSON.stringify(JSON.parse("
             "require('fs').readFileSync(0, 'utf8')).map(([s, d]) => t.renderToString(s, "
             "{displayMode: d, wrap: 'tex', throwOnError: true}))))")


def key(m):
    """The TeX as typed: the Markdown typographer turned ' into ’ inside math."""
    return html.unescape(m[2]).replace("’", "'"), m[1] != "\\("


def mathml(pages):
    """Replace every formula's TeX with MathML: one Temml run over the whole site."""
    tex = sorted({key(m) for s in pages.values() for m in TEX.finditer(s)})
    run = subprocess.run(["node", "-e", TEMML_RUN], cwd=THEME, check=True,
                         input=json.dumps(tex), stdout=subprocess.PIPE, text=True)
    mml = {k: fix_mml(m, group(k[0])) for k, m in zip(tex, json.loads(run.stdout))}
    assert not any("tml-prime" in m for m in mml.values())
    for page, s in pages.items():
        s = TEX.sub(lambda m: f"<span data-pagefind-ignore>{mml[key(m)]}</span>", s)
        pages[page] = TAG.sub(lambda m, page=s: tag(m, page), s)
    return len(tex)


TAG = re.compile(r'<mtext class="tml-tag">\(([^<()]+)\)</mtext>')


def tag(m, page):
    """An equation tag (d9) links to its anchor, eqn-d9, when the page has one."""
    if not re.search(rf'id="?eqn-{re.escape(m[1])}[\s">]', page):
        return m[0]
    return f'<mtext class="tml-tag"><a href="#eqn-{m[1]}">({m[1]})</a></mtext>'


# ---- Page rewrites, on the minified pages (unquoted attributes).
# The nowrap span (math-punct, from single.html) holds a formula and the punctuation after it. A
# character glued before it, "(" or the k of kΩ, joins it too: Chromium breaks between text and
# a <math>.
GLUE = re.compile(r"(&#?\w+;|[^\s<>])(<span class=math-punct>)?"
                  r"(<span data-pagefind-ignore>\\\([^<]*\\\)</span><b hidden>[^<]*</b>)")


def glue(m):
    return f"<span class=math-punct>{m[1]}{m[3]}" + ("" if m[2] else "</span>")


URL = re.compile(r'<a href=("?)(https?:)//([^ >"]+)\1>\2//\3</a>')  # a link set as its own URL


def url(m):
    """Break points in a URL (Chicago 14.18): after the //, before / . ? #. Unbroken, it leaves a
    loose line before it."""
    q, scheme, rest = m.groups()
    return (f"<a class=url href={q}{scheme}//{rest}{q}>{scheme}//<wbr>"
            + re.sub(r"(?=[/.?#])", "<wbr>", rest) + "</a>")


# Tables: numeric columns get class=num (right-aligned), long cells class=prose (may wrap).
NUM = re.compile(r"^[−-]?[\d.,]*\d%?(?:\s?[a-zA-Zµμ]{1,3})?$|^N/A$|^—$")
CELL = re.compile(r"<(t[hd])((?: [^>]*)?)>(.*?)</\1>", re.DOTALL)


def text(cell):
    cell = re.sub(r"<span data-pagefind-ignore>.*?</span>", "", cell, flags=re.DOTALL)
    return html.unescape(re.sub(r"<[^>]+>", "", cell)).strip()


def table(m):
    tb = m.group(0)
    body = tb[tb.index("<tbody>"):]
    rows = [CELL.findall(r) for r in re.findall(r"<tr>(.*?)</tr>", body, re.DOTALL)]
    ncol = max(len(r) for r in rows)
    num = {j for j in range(ncol)
           if all(j < len(r) and NUM.match(text(r[j][2])) for r in rows)
           and any(re.search(r"\d", text(r[j][2])) for r in rows)}

    def row(rm):
        col = 0

        def cell(cm):
            nonlocal col
            tag, attrs, inner = cm.groups()
            span = int((re.search(r"colspan=(\d+)", attrs) or [0, 1])[1])
            cls = ("num" if span == 1 and col in num else
                   "prose" if tag == "td" and len(text(inner)) > 30 else "")
            col += span
            assert "class=" not in attrs, attrs
            return f"<{tag}{attrs}{' class=' + cls if cls else ''}>{inner}</{tag}>"

        return "<tr>" + CELL.sub(cell, rm.group(1)) + "</tr>"

    return re.sub(r"<tr>(.*?)</tr>", row, tb, flags=re.DOTALL)


def main(public):
    pages = {}
    for page in pathlib.Path(public).rglob("*.html"):
        s = page.read_text()
        if not re.search(r'<main id="?main-content', s):  # a theme page, not a data file
            continue
        # single.html trims the hidden copy, so the minifier cannot merge the real space after a
        # formula into it.
        assert not re.search(r"\s</b>[A-Za-z(\[]", s), page
        assert not re.search(r"<b hidden>[^<]*\\", s), page  # no TeX left in a copy
        s = URL.sub(url, s)
        s = GLUE.sub(glue, s)
        s = re.sub(r"<table(?: style=[^>]*)?>.*?</table>", table, s, flags=re.DOTALL)
        pages[page] = s
    n = mathml(pages)
    for page, s in pages.items():
        page.write_text(s)
    print(f"mathml: {n} formulas in {len(pages)} pages")


if __name__ == "__main__":
    main(sys.argv[1])
