#!/usr/bin/env python3
"""
Generates a representative subset of labs (~50) across all 10 categories,
using the schema consumed by app/app.py + app/lab_loader.py.

This intentionally trims the original 229-lab spec down to a size that can
be fully written, run, and tested in one pass. The engine/schema supports
dropping in more labs later using the same pattern -- add a YAML file under
labs/<category>/ and it's picked up automatically (see lab_loader.py).
"""
import os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABS = os.path.join(ROOT, "labs")


def w(cat, id, cfg):
    path = os.path.join(LABS, cat, f"{id}.yaml")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)


def pub(objective, description="", instructions=None):
    return {
        "objective": objective,
        "description": description,
        "instructions": instructions or "Find an input that causes JavaScript to execute in the target, "
                                         "then come back and mark the lab solved.",
    }


# ---------------- REFLECTED (6) ----------------
REFLECTED = [
    ("R01", "Basic HTML reflection", "beginner", ["q"], "html_text", [], {"type": "none"}),
    ("R02", "Quoted attribute context", "beginner", ["q"], "quoted_attribute", [], {"type": "none"}),
    ("R03", "Unquoted attribute context", "intermediate", ["q"], "unquoted_attribute", [], {"type": "none"}),
    ("R04", "Keyword filter (single pass)", "intermediate", ["q"], "html_text", [],
     {"type": "keyword", "blocked": ["script", "onerror"]}),
    ("R05", "Character filter", "intermediate", ["q"], "html_text", [], {"type": "character", "blocked": ["<", ">"]}),
    ("R06", "URL-decode before filter", "advanced", ["q"], "html_text", ["url_decode"],
     {"type": "keyword", "blocked": ["script"]}),
]
for id, title, diff, params, ctx, transform, filt in REFLECTED:
    w("reflected", id, {
        "id": id, "title": title, "category": "reflected", "difficulty": diff, "engine": "reflected",
        "public": pub(
            "Make the target execute JavaScript via a GET parameter.",
            f"The page reflects the `{params[0]}` parameter back into the page.",
        ),
        "engine_config": {"params": params, "context": ctx, "transform": transform, "filter": filt},
        "private": {"why": "user input reaches an HTML/JS context without output encoding, "
                            "and any filter present is a single non-recursive pass"},
    })

# ---------------- STORED (5) ----------------
STORED = [
    ("S01", "Basic stored XSS", "beginner", ["comment"], "html_text", [], [], {"type": "none"}),
    ("S02", "Stored attribute context", "intermediate", ["nickname"], "quoted_attribute", [], [], {"type": "none"}),
    ("S03", "Encoded on the way in, not out", "advanced", ["comment"], "html_text", ["html_encode"], [], {"type": "none"}),
    ("S04", "Naive keyword filter at submit time", "advanced", ["comment"], "html_text", [], [],
     {"type": "keyword", "blocked": ["<script"]}),
    ("S05", "Multiple stored fields", "intermediate", ["name", "bio"], "html_text", [], [], {"type": "none"}),
]
for id, title, diff, fields, ctx, tin, tout, filt in STORED:
    w("stored", id, {
        "id": id, "title": title, "category": "stored", "difficulty": diff, "engine": "stored",
        "public": pub(
            "Store a value that executes JavaScript when the record is viewed.",
            f"Submit the `{fields[0]}` field below, then reload to see it rendered back.",
        ),
        "engine_config": {"fields": fields, "context": ctx, "transform_in": tin, "transform_out": tout, "filter": filt},
        "private": {"why": "stored value is rendered without output encoding at view time"},
    })

# ---------------- DOM (6) ----------------
DOM = [
    ("D01", "location.hash -> innerHTML", "beginner", {"source": {"type": "hash"}}),
    ("D02", "location.search -> innerHTML", "beginner", {"source": {"type": "search", "param": "x"}}),
    ("D03", "window.name -> innerHTML", "intermediate", {"source": {"type": "name"}}),
    ("D04", "localStorage -> innerHTML", "intermediate", {"source": {"type": "localStorage", "key": "pref"}}),
    ("D05", "URL-decoded hash", "advanced", {"source": {"type": "hash"}, "transforms": ["url_decode"]}),
    ("D06", "document.cookie -> innerHTML", "advanced", {"source": {"type": "cookie", "key": "pref"}}),
]
for id, title, diff, client in DOM:
    w("dom", id, {
        "id": id, "title": title, "category": "dom", "difficulty": diff, "engine": "dom",
        "public": pub(
            "Trace a client-side source to a client-side sink and achieve execution.",
            "Everything here happens in the browser -- view the page source / static/js/engine_dom.js.",
        ),
        "client": client,
        "private": {"why": "client-side source reaches innerHTML without sanitization"},
    })

# ---------------- PARSING (4) ----------------
PARSING = [
    ("B01", "Basic tokenization", "beginner", "<div><p>hello</p></div>"),
    ("B02", "Broken/unclosed tags", "beginner", "<div><spa>oops</div>"),
    ("B03", "Comment parsing", "intermediate", "<!-- <b>inside a comment</b> -->"),
    ("B04", "textarea parsing", "intermediate", "<textarea><b>not bold in here</b></textarea>"),
]
for id, title, diff, demo in PARSING:
    w("parsing", id, {
        "id": id, "title": title, "category": "parsing", "difficulty": diff, "engine": "parse",
        "public": pub(
            "Predict how the browser tokenizes this markup, then verify against the rendered DOM tree.",
            "Enter markup and inspect the resulting DOM structure below it.",
        ),
        "client": {"demo": demo},
        "private": {"why": "HTML tokenizer state machine rules (special elements, comments, quirks) reshape the tree"},
    })

# ---------------- MXSS (4) ----------------
MXSS = [
    ("M01", "Basic mutation via table/td", "intermediate", "<table><tr><td>cell", False),
    ("M02", "SVG desc mutation", "advanced", "<svg><desc><b>x</b></desc></svg>", False),
    ("M03", "Mutation surviving DOMPurify", "expert",
     "<math><mtext><table><mglyph><style><b>m</b></style></mglyph></table></mtext></math>", True),
    ("M04", "Malformed attribute quoting", "intermediate", "<div id='a class=b'>x</div>", False),
]
for id, title, diff, seed, sanitize_first in MXSS:
    w("mxss", id, {
        "id": id, "title": title, "category": "mxss", "difficulty": diff, "engine": "mxss",
        "public": pub(
            "Find markup that looks inert after one insertion pass but changes meaning after a second.",
            "Markup is (optionally sanitized, then) inserted, serialized back to a string, and re-inserted.",
        ),
        "client": {"seed": seed, "sanitizeFirst": sanitize_first},
        "private": {"why": "parser/serializer differentials mutate the tree across passes"},
    })

# ---------------- CSP (6) ----------------
CSP = [
    ("C01", "unsafe-inline", "beginner", {"script-src": "'unsafe-inline'"}, "inline"),
    ("C02", "default-src self, no script-src", "beginner", {"default-src": "'self'"}, "none"),
    ("C03", "nonce-based CSP", "intermediate", {"script-src": "'self' 'nonce-{NONCE}'"}, "nonce"),
    ("C04", "JSONP endpoint under script-src 'self'", "advanced", {"script-src": "'self'"}, "jsonp"),
    ("C05", "unsafe-eval + inline script gadget", "advanced", {"script-src": "'unsafe-inline' 'unsafe-eval'"}, "gadget"),
    ("C06", "strict CSP, reflected param only", "advanced", {"default-src": "'self'", "script-src": "'self'"}, "attr"),
]


def csp_page(kind, lab_id):
    if kind == "inline":
        return "<script>alert('inline script executed')</script><p>this page ships an inline script tag</p>"
    if kind == "nonce":
        return "<p>this lab issues a per-response nonce -- check the response header, not the page source</p>"
    if kind == "jsonp":
        return f'<script src="/lab/{lab_id}/jsonp?callback=alert"></script><p>page loads a same-origin JSONP endpoint</p>'
    if kind == "gadget":
        return ("<div data-config='1'></div>"
                "<script>document.querySelectorAll('[data-config]').forEach(el=>{try{eval('('+el.dataset.config+')')}catch(e){}})</script>"
                "<p>a 'config widget' reads data-config and eval()s it</p>")
    return "<p>reflect a value with ?x= above and see where it lands</p>"


for id, title, diff, policy, kind in CSP:
    w("csp", id, {
        "id": id, "title": title, "category": "csp", "difficulty": diff, "engine": "csp",
        "public": pub(
            "Assess the Content-Security-Policy header. Execute JavaScript despite it, or explain why you can't.",
            "Check DevTools -> Network -> response headers for the exact policy.",
        ),
        "engine_config": {"policy": policy, "page_html": csp_page(kind, id), "probe_context": "html_text"},
        "private": {"why": f"policy gap category: {kind}"},
    })

# ---------------- SANITIZERS (5) ----------------
SANITIZERS = [
    ("P01", "Basic DOMPurify (default config)", "beginner", {}, "3.1.6", None,
     "<img src=x onerror=alert(1)>"),
    ("P02", "Restrictive ALLOWED_TAGS", "intermediate", {"ALLOWED_TAGS": ["b", "i", "em", "strong"]}, "3.1.6", None,
     "<b>bold</b><script>alert(1)</script>"),
    ("P03", "ALLOWED_TAGS includes svg/math", "advanced",
     {"ALLOWED_TAGS": ["math", "mtext", "table", "mglyph", "style", "b"]}, "3.1.6", None,
     "<math><mtext><table><mglyph><style><b>m</b></style></mglyph></table></mtext></math>"),
    ("P04", "Naive regex 'sanitizer' (single pass, non-recursive)", "intermediate", {}, None, "strip_script_regex",
     "<scr<script>ipt>alert(1)</scr</script>ipt>"),
    ("P05", "Naive tag-allowlist regex sanitizer", "advanced", {}, None, "allowlist_simple",
     "<a href=\"javascript:alert(1)\">click</a>"),
]
for id, title, diff, opts, version, custom, seed in SANITIZERS:
    w("sanitizers", id, {
        "id": id, "title": title, "category": "sanitizers", "difficulty": diff, "engine": "purify",
        "public": pub(
            "Find input the configured sanitizer mishandles.",
            "Untrusted HTML is sanitized, then the sanitized result is also inserted into the live DOM below.",
        ),
        "client": {"options": opts, "version": version, "custom": custom, "seed": seed},
        "private": {"why": "config gap (allowed dangerous tags/attrs) or a naive single-pass custom filter"},
    })

# ---------------- PROTOTYPE POLLUTION (5) ----------------
PP = [
    ("PP01", "Deep-merge pollution -> innerHTML gadget", "advanced", "deep",
     [{"type": "innerHTML", "path": "template"}], {"template": "<b>default</b>"}),
    ("PP02", "Deep-merge pollution -> href gadget", "advanced", "deep",
     [{"type": "attr_href", "path": "redirect"}], {"redirect": "https://example.com"}),
    ("PP03", "Clone-then-merge pollution", "expert", "clone",
     [{"type": "innerHTML", "path": "template"}], {"template": "<b>default</b>"}),
    ("PP04", "Multi-gadget chain", "expert", "deep",
     [{"type": "innerHTML", "path": "template"}, {"type": "attr_href", "path": "redirect"}],
     {"template": "<b>default</b>", "redirect": "https://example.com"}),
    ("PP05", "Object.assign merge (safe control example)", "intermediate", "assign",
     [{"type": "innerHTML", "path": "template"}], {"template": "<b>default</b>"}),
]
for id, title, diff, mode, gadgets, defaults in PP:
    w("prototype_pollution", id, {
        "id": id, "title": title, "category": "prototype_pollution", "difficulty": diff, "engine": "pp",
        "public": pub(
            "Pollute Object.prototype via the merge below, then get a gadget to read the polluted value into a sink.",
            f"The merge implementation here uses '{mode}' semantics.",
        ),
        "client": {"mode": mode, "gadgets": gadgets, "defaults": defaults},
        "private": {"why": f"{mode} merge copies attacker keys without guarding __proto__/constructor/prototype"},
    })

# ---------------- FRAMEWORKS: react + vue (6) ----------------
REACT = [
    ("RE01", "Default text-child escaping (safe control)", "beginner", "escaping"),
    ("RE02", "dangerouslySetInnerHTML from a URL param", "intermediate", "dangerous"),
    ("RE03", "dangerouslySetInnerHTML fed by a 'title' prop", "advanced", "props"),
]
for id, title, diff, pattern in REACT:
    w("frameworks", id, {
        "id": id, "title": title, "category": "frameworks", "difficulty": diff, "engine": "react",
        "public": pub(
            "Assess this React 18 app for XSS via URL parameters (?name=, ?html=, ?title=).",
            "React auto-escapes text children; look for anywhere that opts out of that.",
        ),
        "client": {"pattern": pattern, "defaults": {"name": "guest"}},
        "private": {"why": "dangerouslySetInnerHTML bypasses React's default escaping" if pattern != "escaping"
                    else "text children ARE escaped by React -- this one should not be exploitable"},
    })

VUE = [
    ("VU01", "Default mustache escaping (safe control)", "beginner", "interpolation"),
    ("VU02", "v-html from a URL param", "intermediate", "vhtml"),
    ("VU03", "v-html behind a 'sanitizer' that isn't wired up", "advanced", "sanitizer"),
]
for id, title, diff, pattern in VUE:
    w("frameworks", id, {
        "id": id, "title": title, "category": "frameworks", "difficulty": diff, "engine": "vue",
        "public": pub(
            "Assess this Vue 3 app for XSS via URL parameters (?name=, ?html=).",
            "Vue escapes {{ }} interpolation; look for any v-html binding.",
        ),
        "client": {"pattern": pattern, "defaults": {"name": "guest"}},
        "private": {"why": "v-html inserts raw HTML" if pattern != "interpolation"
                    else "mustache interpolation IS escaped -- this one should not be exploitable"},
    })

# ---------------- FINAL: blind challenges (5) ----------------
FINAL = [
    ("F01", "Portal", "advanced", "dom", {"source": {"type": "hash"}}, True),
    ("F02", "Dashboard widget", "advanced", "pp", {"mode": "deep",
     "gadgets": [{"type": "innerHTML", "path": "template"}], "defaults": {"template": "<b>ok</b>"}}, True),
    ("F03", "Static status page (safe control)", "intermediate", "parse",
     {"demo": "<div>all systems operational</div>"}, False),
    ("F04", "Kiosk widget", "advanced", "mxss", {"seed": "<svg><desc><b>x</b></desc></svg>", "sanitizeFirst": True}, True),
    ("F05", "Search box", "beginner", "dom", {"source": {"type": "search", "param": "q"}}, True),
]
for id, title, diff, engine, client, vuln in FINAL:
    w("final", id, {
        "id": id, "title": title, "category": "final", "difficulty": diff, "engine": engine,
        "hidden": True,
        "public": pub(
            "Determine whether this application is exploitable for XSS. Conclude vulnerable, or not "
            "exploitable and why, then mark it solved either way.",
        ),
        "client": client,
        "private": {"why": ("blind chain -- investigate" if vuln else
                             "deliberately safe control: nothing here reaches a dangerous sink")},
    })

total = len(REFLECTED) + len(STORED) + len(DOM) + len(PARSING) + len(MXSS) + len(CSP) + \
    len(SANITIZERS) + len(PP) + len(REACT) + len(VUE) + len(FINAL)
print(f"generated {total} labs")
