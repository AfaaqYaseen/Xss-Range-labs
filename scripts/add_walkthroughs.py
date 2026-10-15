#!/usr/bin/env python3
"""
Adds a `walkthrough` block (progressive hints + a short solution writeup) to
every lab YAML under labs/<category>/*.yaml.

This is a separate, idempotent pass on top of generate_labs.py: rerunning it
overwrites only the `walkthrough` key on each file and leaves everything
else (id/title/public/engine_config/client/private) untouched. If you add
new labs later, add their id to WALKTHROUGHS below and rerun this script.

Usage:
    python scripts/add_walkthroughs.py
"""
import os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABS = os.path.join(ROOT, "labs")

# id -> {"hints": [str, ...], "solution": str}
# Hints are ordered from vaguest to most specific. `solution` is a short,
# step-by-step walkthrough a trainee can expand after attempting the lab.
WALKTHROUGHS = {

    # ---------------- REFLECTED ----------------
    "R01": {
        "hints": [
            "The `q` parameter comes back somewhere in the page. Look at the response, not just what renders visually.",
            "There's no filter and no output encoding on this one -- whatever you send in `q` lands in the HTML as-is.",
        ],
        "solution": (
            "`q` is reflected straight into an `html_text` context "
            "(`<div class='reflect'>{q}</div>`) with no filter and no "
            "output encoding. Visit:\n\n"
            "`/lab/R01/run?q=<img src=x onerror=alert(1)>`\n\n"
            "The `<img>` tag is inserted as real markup, the browser tries to load `x`, "
            "fails, and fires `onerror`. The fix is to HTML-encode `q` before inserting "
            "it into the page."
        ),
    },
    "R02": {
        "hints": [
            "Check the page source around where `q` lands -- it's inside an HTML attribute, not loose text.",
            "You're already inside a double-quoted `value=\"...\"` attribute. You don't need a full `<script>` tag -- you need to get *out* of the attribute first.",
        ],
        "solution": (
            "`q` lands inside `<input value=\"{q}\">` (`quoted_attribute` context, "
            "no filter). Closing the quote and the tag, then adding an event handler, "
            "escapes the attribute:\n\n"
            "`/lab/R02/run?q=\" onmouseover=alert(1) x=\"`\n\n"
            "or, to fire without interaction:\n\n"
            "`/lab/R02/run?q=\"><img src=x onerror=alert(1)>`\n\n"
            "Either breaks out of the `value=\"...\"` attribute. Fix: HTML-attribute-encode "
            "the value (encode `\"`, `<`, `>`, `&`) before interpolating it."
        ),
    },
    "R03": {
        "hints": [
            "This one reflects into an attribute that isn't quoted at all: `data-note={q}`.",
            "Unquoted attributes end at the first whitespace. You don't need a quote character to break out -- a space is enough.",
        ],
        "solution": (
            "`q` lands in `<div data-note={q} class='reflect-attr'>` with no quotes "
            "around it (`unquoted_attribute` context). A plain space ends the attribute "
            "value, so you can add a new attribute right there:\n\n"
            "`/lab/R03/run?q=x onmouseover=alert(1)`\n\n"
            "(URL-encode the space as `%20` or `+` when sending it as a query string.) "
            "Fix: always quote attribute values, and encode the value inside them."
        ),
    },
    "R04": {
        "hints": [
            "The filter removes the literal words `script` and `onerror` -- but only once, not recursively.",
            "What happens if the word `script` only *appears* after the filter has already run once?",
        ],
        "solution": (
            "The filter does one non-recursive `re.sub` pass per blocked keyword. If you "
            "nest the keyword inside itself, removing the inner copy leaves the outer "
            "copy intact:\n\n"
            "`/lab/R04/run?q=<scrscriptipt>alert(1)</scrscriptipt>`\n\n"
            "Stripping `script` once from `scrscriptipt` leaves `script`, reassembling "
            "`<script>alert(1)</script>`. A case-insensitive attribute variant also works "
            "for `onerror`, e.g. `onerronerrorror`. Fix: filters must be recursive (loop "
            "until no change) or, better, use an allowlist-based encoder instead of a "
            "denylist."
        ),
    },
    "R05": {
        "hints": [
            "Only the literal characters `<` and `>` are stripped -- nothing else.",
            "Do you actually need `<` or `>` to run JavaScript in an attribute context? This lab reflects into plain HTML text, but think about what other contexts need.",
        ],
        "solution": (
            "`q` reflects into `html_text`, and the filter strips every `<` and `>` "
            "character but nothing else. Since the context is plain text, you can't "
            "open a new tag -- but character filters like this are usually paired with "
            "*other* vulnerable contexts elsewhere in a real app, and here the lesson is "
            "that stripping two characters is not equivalent to encoding. Using HTML "
            "entities for the blocked characters yourself doesn't help since they're "
            "stripped verbatim either way; the realistic finding for this lab is that "
            "`<`/`>` character-stripping still leaves every other HTML metacharacter "
            "(`\"`, `'`, `&`, backticks) untouched, which is exploitable the moment this "
            "same value is reused in an attribute or JS-string context elsewhere in the "
            "app. Fix: don't denylist characters -- contextually encode output."
        ),
    },
    "R06": {
        "hints": [
            "The value is URL-decoded on the server *before* the `script` keyword filter runs.",
            "If you URL-encode the word `script` yourself, the filter sees it encoded (and ignores it) -- then the decode step turns it back into the real word afterward.",
        ],
        "solution": (
            "Transform order is `url_decode` then the keyword filter. The filter only "
            "ever sees the *decoded* value once, after your encoded payload has already "
            "been turned back into plaintext... but critically the filter runs **after** "
            "decode, so simply double URL-encoding `script` means after the single "
            "`url_decode` step it's still encoded text (`%2573cript` decodes once to "
            "`%73cript`), which the filter doesn't recognize as the word \"script\" -- "
            "then the browser or a second decode never happens server-side, so instead "
            "the practical bypass is to avoid the word `script` entirely:\n\n"
            "`/lab/R06/run?q=%3Cimg%20src=x%20onerror=alert(1)%3E`\n\n"
            "which decodes to `<img src=x onerror=alert(1)>` -- no `script` keyword "
            "involved at all, so the filter never triggers. Fix: don't rely on keyword "
            "denylists; HTML-encode output regardless of what transforms ran first."
        ),
    },

    # ---------------- STORED ----------------
    "S01": {
        "hints": [
            "Submit the `comment` field, then look at how it's rendered back on reload.",
            "Same idea as R01, just persisted: nothing encodes the value when it's read back out of storage.",
        ],
        "solution": (
            "POST `comment=<img src=x onerror=alert(1)>` via the form, then reload "
            "`/lab/S01/run`. The stored value is re-inserted into `html_text` with no "
            "output encoding, so the payload fires every time the page loads -- that's "
            "what makes it *stored* rather than reflected. Fix: encode on output, "
            "regardless of what was done (or not done) on input."
        ),
    },
    "S02": {
        "hints": [
            "The `nickname` field is stored, then rendered inside a quoted HTML attribute.",
            "Same breakout technique as R02: close the quote, add an event handler.",
        ],
        "solution": (
            "Submit `nickname=\"><img src=x onerror=alert(1)>` and reload. The value is "
            "placed inside a `value=\"...\"` attribute with no encoding, so closing the "
            "quote and tag lets you inject a new element. Fix: attribute-encode on "
            "output."
        ),
    },
    "S03": {
        "hints": [
            "The comment is HTML-encoded on the way *in* (at submit time) -- but check what happens on the way out.",
            "If encoding only happens once, on input, and the output step does nothing, what does the stored (already-encoded) value look like when rendered -- and is it encoded a second time?",
        ],
        "solution": (
            "`transform_in: [html_encode]` runs once at submit time, and `transform_out` "
            "is empty -- the value is encoded once in storage and then rendered "
            "**without re-encoding**, which is actually safe in this specific round-trip "
            "since the stored bytes are already entity-encoded. The real bug this lab "
            "demonstrates is that encoding happens at the wrong layer: it protects *this* "
            "output path by coincidence, but anywhere else in a hypothetical app that "
            "reads the same stored comment and decodes it (e.g. for an API response, an "
            "email digest, or a different template) would get raw HTML back. For this "
            "specific lab, submitting `<img src=x onerror=alert(1)>` gets encoded to "
            "`&lt;img ...&gt;` on the way in and is displayed as inert text -- so the "
            "intended finding is to recognize *why* it's not exploitable here and report "
            "that, rather than force an injection. Mark it solved once you've confirmed "
            "and explained that single-point input encoding without context-aware output "
            "encoding is still a design smell even when this particular path is safe."
        ),
    },
    "S04": {
        "hints": [
            "Only the literal substring `<script` is blocked, applied once, at submit time.",
            "You don't need a `<script>` tag to execute JavaScript in an `html_text` context -- plenty of other tags have event handlers.",
        ],
        "solution": (
            "The filter blocks `<script` (case-insensitive, single pass) but nothing "
            "else. Submit a payload that doesn't contain that substring at all:\n\n"
            "`comment=<img src=x onerror=alert(1)>`\n\n"
            "and reload. No `<script` substring ever appears, so the filter never "
            "triggers, and the stored value renders unencoded. Fix: encode output "
            "regardless of filtering, and don't rely on tag-name denylists."
        ),
    },
    "S05": {
        "hints": [
            "Two fields are stored (`name` and `bio`) but the lab description only mentions `name` -- check what the `run` page actually renders.",
            "`_run_stored` only ever reads and renders `cfg['fields'][0]`, the first field in the list. Does that match what the form actually submits for display?",
        ],
        "solution": (
            "`engine_config.fields` is `[name, bio]`, and `_run_stored` renders "
            "`stored[fields[0]]`, i.e. only `name`, into `html_text` with no encoding. "
            "Submitting `bio=<script>alert(1)</script>` alone does nothing visible since "
            "`bio` isn't the rendered field. Submit `name=<img src=x onerror=alert(1)>` "
            "(the first field) and reload `/lab/S05/run` to see it fire. The lesson: "
            "when multiple fields are stored, confirm exactly which one reaches a sink "
            "before spending time on the others."
        ),
    },

    # ---------------- DOM ----------------
    "D01": {
        "hints": [
            "Open `static/js/engine_dom.js` and trace `getSource` for `type: hash` -- the source is `location.hash`.",
            "The sink is `root.innerHTML = ...` with no sanitization. Set the URL fragment to your payload and the page re-renders on `hashchange`.",
        ],
        "solution": (
            "Source: `location.hash` (URL fragment). Sink: `innerHTML`, no sanitizer. "
            "Navigate to:\n\n"
            "`/lab/D01/run#<img src=x onerror=alert(1)>`\n\n"
            "`getSource` decodes the hash and `writeSink` inserts it directly via "
            "`innerHTML`. Because the fragment never reaches the server, this executes "
            "purely client-side -- note it still shows up in `DevTools > Elements`, not "
            "in `view-source`/raw HTML. Fix: never assign untrusted strings to "
            "`innerHTML`; use `textContent` or a sanitizer."
        ),
    },
    "D02": {
        "hints": [
            "`getSource` for `type: search` reads a named query parameter -- check which one this lab uses (`param: x`).",
            "Same `innerHTML` sink as D01, but the source is `location.search` via `URLSearchParams`, so this one *does* round-trip through the server as a normal GET request.",
        ],
        "solution": (
            "Source: `?x=` query parameter. Sink: `innerHTML`. Visit:\n\n"
            "`/lab/D02/run?x=<img src=x onerror=alert(1)>`\n\n"
            "`getSource` reads `x` via `URLSearchParams`, `writeSink` inserts it "
            "unsanitized. Unlike D01 this value is visible in server logs and "
            "`view-source`, but the vulnerability is still purely client-side (the server "
            "never echoes it -- the client JS does). Fix: sanitize or escape before "
            "assigning to `innerHTML`."
        ),
    },
    "D03": {
        "hints": [
            "`type: name` reads `window.name`, which persists across navigations within the same tab -- there's a helper panel at the bottom of the lab page to set it.",
            "Set `window.name` via the helper form, then reload the page so `render()` re-reads it into `innerHTML`.",
        ],
        "solution": (
            "Source: `window.name`. Sink: `innerHTML`. Open the lab, use the \"helper: "
            "set localStorage / sessionStorage / cookie / window.name\" panel at the "
            "bottom, enter `<img src=x onerror=alert(1)>`, click \"set window.name "
            "(reload after)\", then reload the page. `window.name` survives the reload "
            "(it's tied to the tab, not the page) and gets written straight into "
            "`innerHTML`. In a real attack, `window.name` is typically set by a "
            "cross-origin page before redirecting the victim to the target. Fix: never "
            "trust `window.name`, and sanitize before any DOM sink."
        ),
    },
    "D04": {
        "hints": [
            "`type: localStorage, key: pref` reads `localStorage.getItem('pref')`. Use the helper panel to set it, then reload.",
            "`localStorage` is same-origin and persists indefinitely -- if an attacker can get *any* script to run once on this origin (even from a different, less obviously vulnerable lab/page), they can plant a payload here that fires on every future visit.",
        ],
        "solution": (
            "Source: `localStorage.getItem('pref')`. Sink: `innerHTML`. Use the helper "
            "panel at the bottom of the lab page, type `<img src=x onerror=alert(1)>` "
            "into the value box, click \"set localStorage\", then reload the page -- "
            "`render()` re-reads `pref` on load and inserts it unsanitized. Fix: treat "
            "`localStorage`/`sessionStorage` as untrusted input, same as any network "
            "source."
        ),
    },
    "D05": {
        "hints": [
            "Source is `location.hash` again, but this time there's a `transforms: [url_decode]` step applied client-side before the sink.",
            "Since the hash is already decoded once by the browser when you read `location.hash`, adding your own `url_decode` transform on top means you may need to *double*-encode your payload in the URL.",
        ],
        "solution": (
            "Source: `location.hash`, then `applyTransform('url_decode', value)` "
            "(`decodeURIComponent`) runs on it before the `innerHTML` sink. "
            "`location.hash` already gives you the fragment largely as typed, so sending "
            "a URL-encoded payload gets decoded an *extra* time by the lab's own "
            "transform step. Encode your payload once:\n\n"
            "`/lab/D05/run#%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E`\n\n"
            "`decodeURIComponent` turns it back into the real `<img ...>` tag before "
            "`innerHTML` renders it. (A plain unencoded payload in the hash also works "
            "here, same as D01, since `decodeURIComponent` on an already-plain string is "
            "a no-op -- the point of the lab is to notice that an *extra* decode step "
            "doesn't add any protection.) Fix: decoding is not sanitizing."
        ),
    },
    "D06": {
        "hints": [
            "Source is `document.cookie`, specifically the `pref` cookie. Use the helper panel to set a cookie, then reload.",
            "Cookies set via `document.cookie` from client-side JS (no `HttpOnly`) are readable and writable by any script on the page, including one you've already gotten to run via an earlier lab or the helper panel.",
        ],
        "solution": (
            "Source: `document.cookie`, key `pref`. Sink: `innerHTML`. Use the helper "
            "panel, enter `<img src=x onerror=alert(1)>`, click \"set cookie\", then "
            "reload -- `render()` reads the `pref` cookie via regex and writes it "
            "straight into `innerHTML`. Fix: never trust cookie values for DOM writes; "
            "sanitize or escape before use, and mark sensitive cookies `HttpOnly` "
            "(though that only stops JS *reading* them, not this kind of self-XSS)."
        ),
    },

    # ---------------- PARSING (non-exploit, tokenizer-prediction labs) ----------------
    "B01": {
        "hints": [
            "This isn't an exploit lab -- there's nothing to pop. Type the seed markup into the box and compare the DOM tree the browser actually builds to what you expected.",
            "`<div><p>hello</p></div>` is well-formed; the interesting part is just confirming the tree nests the way the tags suggest.",
        ],
        "solution": (
            "No payload needed -- this lab trains tokenizer intuition. Entering "
            "`<div><p>hello</p></div>` produces exactly the nested tree you'd expect: "
            "`div > p > \"hello\"`. Mark it solved once you've compared the rendered "
            "`innerHTML`/DOM tree against your prediction. The payoff comes in B02-B04, "
            "where the tree *doesn't* match naive expectations."
        ),
    },
    "B02": {
        "hints": [
            "`<spa>` isn't a real tag, and the `<p>` is never closed. The HTML5 tokenizer still has to produce *some* tree -- predict it before you check.",
            "Unknown tags like `<spa>` are treated as ordinary (non-special) elements, so they nest normally; the real question is where the unclosed `</div>` forces things to close.",
        ],
        "solution": (
            "`<div><spa>oops</div>` tokenizes with `<spa>` as a generic unknown element "
            "(browsers don't validate tag names against a dictionary -- any `<name>` is a "
            "valid custom/unknown element). The tree ends up as "
            "`div > spa > \"oops\"`, and the trailing `</div>` closes the `div` because "
            "that's the first open tag matching `/div`'s tag name on the open-elements "
            "stack -- so `spa` gets implicitly closed along with it, not left open. "
            "Confirm with DevTools and mark solved. The lesson: tag-name-based filters "
            "and \"this will never close properly\" assumptions are unreliable -- the "
            "tokenizer is forgiving in specific, memorizable ways that attackers rely on."
        ),
    },
    "B03": {
        "hints": [
            "Does the tokenizer treat `<!-- ... -->` as literal text, or does it actually parse what's inside the comment as markup?",
            "Compare `innerHTML` of the resulting node to the raw text you typed -- is the `<b>` tag still there as text, or did it vanish/execute?",
        ],
        "solution": (
            "`<!-- <b>inside a comment</b> -->` is tokenized as a single HTML comment "
            "node; everything between `<!--` and `-->` is comment data, not parsed as "
            "tags. The `<b>...</b>` text is preserved verbatim as comment content and "
            "never becomes a real DOM element. This matters for XSS because naive "
            "filters sometimes assume \"inside a comment\" is a safe place to drop user "
            "input unescaped -- it's safe *unless* the attacker can inject the literal "
            "sequence `-->` to close the comment early and resume real markup afterward."
        ),
    },
    "B04": {
        "hints": [
            "`<textarea>` is one of a handful of elements with special \"raw text\" parsing rules -- inside it, tags are not parsed as markup at all.",
            "Compare what you see rendered (as literal text inside the textarea) to what `innerHTML` reports as the textarea's content.",
        ],
        "solution": (
            "`<textarea>` (along with `<title>`, `<style>`, `<script>`, `<xmp>`, "
            "`<iframe>`, `<noembed>`, `<noframes>`) is a \"raw text\" / \"escapable raw "
            "text\" element: the tokenizer switches into a special state where it looks "
            "only for the matching end tag (`</textarea>`) and treats everything else, "
            "including `<b>` and `</b>`, as literal character data, not markup. So "
            "`<b>not bold in here</b>` renders as plain visible text inside the textarea "
            "rather than becoming a bold element. This is exactly why D-series/S-series "
            "labs that reflect into a `textarea` context are *not* trivially exploitable "
            "with a bare `<script>` tag -- you'd first need to inject the literal string "
            "`</textarea>` to break out of raw-text mode before any tag you add is "
            "actually parsed."
        ),
    },

    # ---------------- MXSS ----------------
    "M01": {
        "hints": [
            "`<table><tr><td>cell` is inserted once (no sanitizer), serialized back to a string, then re-inserted. Watch what the browser does to stray text when it builds a table.",
            "HTML table parsing moves \"foster-parented\" text (text that appears where only `<tr>`/`<td>` are valid) *outside* the table in the serialized output -- compare pass 1's DOM to pass 2's.",
        ],
        "solution": (
            "On the first insertion, the browser's table-construction algorithm accepts "
            "`<table><tr><td>cell` even though it's missing closing tags -- it auto-closes "
            "`td`/`tr`/`table` at the end. The *input* `<table><tr><td>cell` is inert on "
            "its own. The mutation shows up with text or stray markup placed where the "
            "table parser doesn't expect it (directly inside `<table>`, before any "
            "`<tr>`/`<td>`): that text gets \"foster-parented\" -- moved by the parser to "
            "just *before* the table in the tree, not where it was written. So on the "
            "*second* pass (serialize pass-1's DOM back to a string, then re-parse it), "
            "content that looked trapped safely inside table structure can end up "
            "outside it, in a context where tags that were previously inert (because "
            "they were foster-parented as text/comments) are now parsed as real markup. "
            "Try seeding (via the input box) something like "
            "`<table><td><img src=x onerror=alert(1)></table>` and compare the DOM after "
            "pass 1 vs. after pass 2 -- the `<img>` foster-parents out from under the "
            "table and becomes a live, executing element once re-serialized and "
            "re-inserted."
        ),
    },
    "M02": {
        "hints": [
            "`<svg><desc><b>x</b></desc></svg>` -- `<desc>` is foreign content inside SVG with its own serialization quirks.",
            "Compare `innerHTML` of the live DOM after pass 1 to the same markup re-inserted after being serialized and parsed a second time -- does `<desc>`'s content stay HTML, or does something change namespace?",
        ],
        "solution": (
            "Inside `<svg>`, `<desc>` (and `<title>`, `<foreignObject>`) switch parsing "
            "back to the HTML namespace for their content, so `<b>x</b>` is parsed as a "
            "normal HTML bold element nested in the SVG tree on pass 1 -- this part looks "
            "inert. The mutation appears when that structure is serialized back to a "
            "string (`element.innerHTML` getter) and re-parsed: SVG/XML-ish "
            "serialization and namespace-switching rules don't perfectly round-trip "
            "through `innerHTML`, so content that was namespaced as foreign/SVG content "
            "on the first pass can be re-interpreted as ordinary HTML (or vice versa) on "
            "the second, changing which tags are \"live\" in a way neither a sanitizer "
            "nor a naive diff of the raw markup would catch. This is the same parser "
            "class of bug behind several real DOMPurify mXSS CVEs involving "
            "`<svg><desc>` payloads carrying nested `<style>`/scriptable content; this "
            "lab demonstrates the differential with `sanitizeFirst: false` so you can "
            "see the raw browser behavior before M03 adds a sanitizer into the mix."
        ),
    },
    "M03": {
        "hints": [
            "`sanitizeFirst: true` this time -- DOMPurify runs *before* the mutation round-trip, so your seed markup is sanitized once, and *then* the mutation happens on the sanitized output.",
            "This seed (`<math><mtext><table><mglyph><style>...`) mirrors a real, historical DOMPurify bypass: nesting a raw-text element (`<style>`) inside foreign-content elements that force namespace switches DOMPurify's string-based checks didn't fully account for.",
        ],
        "solution": (
            "This reproduces the structure of a known DOMPurify mXSS bypass class: "
            "`<math><mtext>` switches into MathML foreign content, `<mglyph>` and "
            "`<mtext>` further affect how child content is namespaced, and `<style>` is "
            "a raw-text element whose content the HTML parser treats as opaque CSS text "
            "-- but only in HTML namespace/`<style>` context. When DOMPurify sanitizes "
            "this structure (serializing its internal DOM back to a string to check/clean "
            "it), the namespace-switching + raw-text interaction can cause content that "
            "DOMPurify believed was inert (e.g. treated as `<style>` text data) to be "
            "re-parsed differently once the *sanitized* output is inserted into a real "
            "document a second time -- the classic mXSS pattern of \"sanitize once, "
            "mutate on re-parse.\" Try seeding a payload with a scriptable sink nested "
            "inside the `<style>` (e.g. an attribute with an event handler, or a "
            "`</style>` breakout sequence) and compare pass 1's sanitized DOM to what "
            "happens once that sanitized markup is serialized and re-inserted by the "
            "lab's second pass. If your DOMPurify version is already patched against this "
            "specific gadget, that's also a valid, correct conclusion -- document which "
            "payload you tried and why it no longer mutates, since \"confirmed patched\" "
            "is as real a finding as \"confirmed exploitable.\""
        ),
    },
    "M04": {
        "hints": [
            "`<div id='a class=b'>x</div>` -- look closely at the quoting. Is `class=b` really part of the `id` attribute value, or could the browser's attribute tokenizer read it differently once this gets serialized and re-parsed?",
            "Single-quoted attribute values are valid HTML, but when the DOM is serialized back out (`innerHTML` getter), attribute values are typically re-emitted with double quotes -- think about what happens if the *value itself* contains a double quote or other quote-like character after that re-serialization.",
        ],
        "solution": (
            "On the first pass, `id='a class=b'` parses correctly as a single attribute: "
            "`id=\"a class=b\"` (single quotes delimit the whole value, so `class=b` is "
            "just text inside it, not a second attribute). The mutation appears when the "
            "browser serializes this element back to a string via `innerHTML` -- "
            "serialization normalizes attribute quoting (typically to double quotes) and "
            "escapes only certain characters. If the attacker-controlled value itself "
            "contains a double quote or is otherwise positioned so the round-trip "
            "serialize/re-parse cycle produces different attribute boundaries than the "
            "original markup had, a single logical attribute can split into two on the "
            "second parse -- effectively smuggling a new, attacker-chosen attribute (e.g. "
            "an event handler) into the tag. Experiment with seeds like "
            "`<div id='a onmouseover=alert(1) b=\"'>x</div>` and diff the DOM/outerHTML "
            "after pass 1 against pass 2 to see the attribute boundary shift. The general "
            "lesson: quoting style is not preserved through a serialize/re-parse "
            "round-trip, and that asymmetry is exactly what mXSS exploits."
        ),
    },

    # ---------------- CSP ----------------
    "C01": {
        "hints": [
            "Read the `Content-Security-Policy` response header in DevTools -> Network. What does `script-src 'unsafe-inline'` actually permit?",
            "`'unsafe-inline'` means inline `<script>` tags (and inline event handlers) run exactly as if there were no CSP at all for that purpose.",
        ],
        "solution": (
            "Policy: `script-src 'unsafe-inline'`. This explicitly re-allows the thing "
            "CSP exists to block: inline script execution. The page already ships "
            "`<script>alert('inline script executed')</script>` in its body, which fires "
            "on load -- no injection even needed to demonstrate the gap, though the same "
            "policy would also let a reflected-XSS-style injection execute via an inline "
            "`<script>` tag. Fix: never use `'unsafe-inline'`; use nonces or hashes "
            "instead (see C03)."
        ),
    },
    "C02": {
        "hints": [
            "`default-src 'self'` with no explicit `script-src` -- does `script-src` inherit from `default-src`, and if so, does `'self'` block inline scripts?",
            "`'self'` alone (without `'unsafe-inline'`) already blocks inline `<script>` and inline event handlers under the default CSP spec behavior -- so where's the actual gap? Try reflecting a value with `?x=` and see what context it lands in.",
        ],
        "solution": (
            "`script-src` is unset, so it inherits from `default-src 'self'`, which "
            "*does* block inline scripts and event handlers (no `'unsafe-inline'` was "
            "specified). This policy is actually reasonably strong against classic "
            "inline-script injection. The intended finding for this lab is to attempt "
            "`?x=<script>alert(1)</script>` and `?x=\" onmouseover=alert(1) x=\"` and "
            "confirm the browser blocks both per the CSP (check the console for a CSP "
            "violation report) -- then conclude and document that this specific policy, "
            "as configured, is **not exploitable** for inline-script XSS, even though the "
            "page does reflect `x` unescaped into HTML. (It's still bad practice to "
            "reflect unescaped input -- `default-src 'self'` with no `script-src` is "
            "doing the real protective work here, not the lack of a reflection bug.) "
            "Mark it solved once you've verified and can explain why it holds."
        ),
    },
    "C03": {
        "hints": [
            "Each response gets a fresh nonce in `script-src 'self' 'nonce-...'` -- check the exact header value on *this* response, not a cached one.",
            "Without knowing the current response's nonce in advance, you can't write `<script nonce=\"...\">` yourself. Is there any injection point that could leak or reuse the real nonce, or is this policy actually solid?",
        ],
        "solution": (
            "A correctly generated, per-response, unpredictable nonce (`secrets."
            "token_urlsafe(12)` server-side here) is one of the strongest script-src "
            "configurations: an attacker injecting markup has no way to know the current "
            "nonce value in advance, so they can't craft a `<script nonce=\"...\">` tag "
            "that CSP will allow. This lab's `page_html` doesn't reflect any parameter "
            "and the probe context only reflects `?x=` into plain text with no script "
            "execution path -- verify there's no nonce leak (e.g. the nonce never "
            "appears anywhere an attacker-controlled read could reach it, like a "
            "reflected error message or a predictable pattern) and conclude this policy "
            "is **not exploitable** as configured. Document what you checked."
        ),
    },
    "C04": {
        "hints": [
            "`script-src 'self'` allows any same-origin script URL -- including ones the app itself serves, like a JSONP endpoint.",
            "`/lab/C04/jsonp?callback=...` writes `<callback>('...')` back verbatim as JavaScript. If `callback` isn't validated, what can you make it execute instead of calling a function?",
        ],
        "solution": (
            "`script-src 'self'` allows loading `<script src=\"/lab/C04/jsonp?callback=...\">` "
            "because it's same-origin -- CSP has no way to know the endpoint's output is "
            "attacker-influenced. The JSONP route (`app.py`'s `jsonp` view) does "
            "`f\"{callback}('jsonp endpoint reached');\"` with **no validation** on "
            "`callback`, so instead of a function name you can supply arbitrary "
            "JavaScript:\n\n"
            "`/lab/C04/jsonp?callback=alert(1);//`\n\n"
            "which outputs `alert(1);//('jsonp endpoint reached');` -- valid, "
            "executing JavaScript, served from your own origin, fully inside the "
            "`'self'` allowlist. The page already demonstrates this by loading the "
            "endpoint with `callback=alert`, which calls `alert('jsonp endpoint "
            "reached')`. Fix: `script-src 'self'` is only as strong as every same-origin "
            "endpoint that can return `Content-Type: text/javascript` or be loaded as a "
            "script -- audit JSONP/callback endpoints, open redirects to script-servable "
            "paths, and user uploads served from the same origin."
        ),
    },
    "C05": {
        "hints": [
            "`'unsafe-inline' 'unsafe-eval'` -- the page already ships a \"config widget\" that reads `data-config` off any element and `eval()`s it.",
            "You don't need to inject a `<script>` tag at all. Can you get your own content onto the page as a `data-config` attribute that the existing widget will read and `eval`?",
        ],
        "solution": (
            "The shipped inline script does: "
            "`document.querySelectorAll('[data-config]').forEach(el => eval('(' + el.dataset.config + ')'))`. "
            "`'unsafe-eval'` in the CSP permits this `eval()` call to run at all. This is "
            "a *gadget*: CSP can't tell \"legitimate app eval\" from \"attacker-triggered "
            "eval\" -- it only sees that eval is allowed or not. If any other part of the "
            "app (not shown reflected here, but representative of real apps) lets an "
            "attacker add an element with a `data-config` attribute anywhere on this "
            "page -- a comment field, a profile bio, anything reaching `innerHTML` -- "
            "the existing gadget script will `eval()` it for free, completely bypassing "
            "the need to inject `<script>` yourself. Demonstrate it by using DevTools to "
            "add `<div data-config=\"alert(1)\"></div>` to the DOM and watch the existing "
            "gadget script pick it up on its next pass (or trigger a fresh pass if the "
            "widget re-scans) -- or better, point to how an `innerHTML`-based injection "
            "elsewhere in a real deployment would achieve the same thing without "
            "DevTools. Fix: never ship `'unsafe-eval'`; redesign config-widget patterns "
            "like this to use `JSON.parse` on explicit, validated data, not `eval`."
        ),
    },
    "C06": {
        "hints": [
            "`default-src 'self'; script-src 'self'` -- no `'unsafe-inline'`, no `'unsafe-eval'`, no nonces, no JSONP gadget shipped. Reflect a value with `?x=` and see where it lands.",
            "With no inline-script allowance and no same-origin script-returning endpoint in this lab, is there any remaining way to execute JavaScript, or is the correct answer that this one holds?",
        ],
        "solution": (
            "This is the \"strict, no gaps\" control for the CSP category. `?x=` reflects "
            "into plain `html_text` with no encoding (try `?x=<script>alert(1)</script>` "
            "or an `onerror` attribute payload and watch DevTools console for CSP "
            "violation reports) -- every variant is blocked because `script-src 'self'` "
            "with no `'unsafe-inline'` rejects inline `<script>` tags and inline event "
            "handlers outright, and there's no JSONP-style same-origin endpoint (unlike "
            "C04) or eval gadget (unlike C05) to abuse here. The correct, intended "
            "conclusion is **not exploitable as configured**: document that you tried "
            "an inline-script payload, an inline-event-handler payload, and checked for "
            "any same-origin script-servable endpoint, and that CSP blocked all of them. "
            "Mark it solved on that conclusion -- recognizing a solid policy is as much "
            "the skill being tested here as finding a bypass."
        ),
    },

    # ---------------- SANITIZERS ----------------
    "P01": {
        "hints": [
            "This is real DOMPurify 3.1.6 with its default options (`{}`) -- no custom allowlist restrictions.",
            "Does DOMPurify's default config strip event-handler attributes like `onerror` from an `<img>` tag?",
        ],
        "solution": (
            "DOMPurify's default configuration strips `onerror` (and other event-handler "
            "attributes) from `<img>` by default -- `<img src=x onerror=alert(1)>` "
            "sanitizes down to `<img src=\"x\">`, inert. This lab's seed is deliberately "
            "a payload that a *default* DOMPurify config correctly neutralizes, and the "
            "expected finding is to confirm that and conclude **not exploitable with "
            "default options** -- try it in the box and watch the \"sanitized output\" "
            "panel strip the handler. (Contrast with P02/P03, where custom "
            "`ALLOWED_TAGS` configuration reopens gaps that the defaults close.)"
        ),
    },
    "P02": {
        "hints": [
            "`ALLOWED_TAGS` is restricted to `[b, i, em, strong]` -- `<script>` isn't in that list, so DOMPurify strips it. That part is working as intended.",
            "The seed is `<b>bold</b><script>alert(1)</script>` -- confirm in the sanitized-output panel that the `<script>` tag is gone and only `<b>bold</b>` survives.",
        ],
        "solution": (
            "With `ALLOWED_TAGS: [b, i, em, strong]`, DOMPurify strips the `<script>` "
            "tag entirely (it's not in the allowlist), leaving `<b>bold</b>`, fully "
            "inert. This is the expected, correct behavior of an `ALLOWED_TAGS` "
            "allowlist doing its job -- the intended finding is to try the default seed, "
            "confirm the script tag is stripped, then try to find an allowed-tag-only "
            "bypass (none of `b`/`i`/`em`/`strong` carry any attributes or event "
            "handlers that DOMPurify would pass through in this configuration either), "
            "and conclude **not exploitable with this configuration** -- a tight "
            "allowlist of harmless tags is one of the stronger sanitizer configurations "
            "possible."
        ),
    },
    "P03": {
        "hints": [
            "`ALLOWED_TAGS` here includes `math`, `mtext`, `table`, `mglyph`, `style`, `b` -- an unusual mix of MathML and HTML tags together.",
            "This is the exact structure from M03. Allowing `mglyph`/`mtext`/`table`/`style` together, even through DOMPurify's own allowlist mechanism, mirrors a real historical DOMPurify namespace-confusion bypass.",
        ],
        "solution": (
            "Allowing `math`/`mtext`/`mglyph`/`table`/`style` together in `ALLOWED_TAGS` "
            "reproduces the structure behind a known, real DOMPurify mXSS bypass: "
            "`<math><mtext>` forces a MathML namespace switch, `<mglyph>` and `<table>` "
            "interact with HTML's foreign-content and table-construction rules in ways "
            "that differ depending on namespace, and `<style>`'s raw-text parsing can "
            "end up scoped differently than DOMPurify's string-based serialization "
            "expects -- content DOMPurify believes is safely nested inert text can "
            "become live markup once the sanitized output round-trips through the DOM a "
            "second time (exactly as demonstrated directly, without a sanitizer, in "
            "M03). Paste the seed into the box, inspect the \"sanitized output "
            "(inserted into the DOM)\" panel versus the raw \"sanitized output (string)\" "
            "panel, and try extending the payload with a scriptable gadget nested inside "
            "the `<style>`/`<mglyph>` structure to see whether it survives into the live "
            "DOM. If the installed DOMPurify version (3.1.6) has already patched this "
            "specific gadget, confirming that and explaining why is the correct, valid "
            "conclusion too. Fix: don't combine foreign-content tags (`math`/`svg`-family) "
            "with raw-text tags (`style`/`script`/`textarea`/`title`) in `ALLOWED_TAGS` "
            "unless you specifically need to and have tested the combination."
        ),
    },
    "P04": {
        "hints": [
            "This isn't DOMPurify at all -- `custom: strip_script_regex`. Open `static/js/engine_purify.js` and read what that function actually does.",
            "It's a single regex, run once, non-greedy, non-recursive: `value.replace(/<script[^>]*>.*?<\\/script>/gi, \"\")`. Same class of bug as R04/S04.",
        ],
        "solution": (
            "`customSanitize('strip_script_regex', value)` runs exactly one "
            "`replace(/<script[^>]*>.*?<\\/script>/gi, \"\")` pass -- not DOMPurify, and "
            "not recursive. The seed `<scr<script>ipt>alert(1)</scr</script>ipt>` "
            "demonstrates the nested-match bypass: the regex finds and removes the inner "
            "`<script>ipt>alert(1)</scr</script>` segment (matching from the *first* "
            "`<script...>` it finds to the *first* `</script>` after it, non-greedy), "
            "and what's left over reassembles into `<script>alert(1)</script>`. Paste it "
            "into the box and watch the \"sanitized output (string)\" panel to see the "
            "reassembly, then watch it fire in the \"inserted into the DOM\" panel. Fix: "
            "never hand-roll HTML sanitization with regex; use a real parser-based "
            "sanitizer (DOMPurify) and never attempt to recursively remove tags with "
            "string replacement."
        ),
    },
    "P05": {
        "hints": [
            "`custom: allowlist_simple` -- open `engine_purify.js` and check which tags it actually allows: `b, i, em, strong, a`.",
            "`<a>` is allowed, and the regex only checks the *tag name*, not its attributes. What's in an `<a href=\"...\">`'s `href` that the regex never inspects?",
        ],
        "solution": (
            "`allowlist_simple` keeps any `<a ...>`/`<b>`/`<i>`/`<em>`/`<strong>` tag "
            "(open or close) and strips everything else, but it only matches on the tag "
            "*name* -- it never inspects or filters attribute values. `<a>` is in the "
            "allowlist, so `<a href=\"javascript:alert(1)\">click</a>` passes through "
            "completely untouched. Paste the seed into the box, click \"sanitize\", and "
            "then click the rendered link in the \"inserted into the DOM\" panel to "
            "trigger the `javascript:` URL. Fix: an allowlist must validate attribute "
            "values too (e.g. reject `javascript:`/`data:` URL schemes in `href`/`src`), "
            "not just tag names -- this is exactly the class of gap DOMPurify's real "
            "`ALLOWED_URI_REGEXP` exists to close."
        ),
    },

    # ---------------- PROTOTYPE POLLUTION ----------------
    "PP01": {
        "hints": [
            "The merge is `deep` and copies keys with no `__proto__`/`constructor`/`prototype` guard -- look at `deepMerge` in `engine_pp.js`.",
            "The gadget reads `template` off a *brand-new, empty* object (`{}`), not off the merged result -- so to affect it you have to pollute `Object.prototype.template` itself, not just the merge target.",
        ],
        "solution": (
            "`deepMerge` walks every key of your JSON input, including `__proto__`, and "
            "assigns straight into it with no guard. Submitting:\n\n"
            "`{\"__proto__\":{\"template\":\"<img src=x onerror=alert(1)>\"}}`\n\n"
            "into the textarea and clicking \"merge & render gadgets\" sets "
            "`Object.prototype.template`. The gadget then does "
            "`get({}, 'template')` on a fresh, unrelated object -- since the property "
            "lookup walks the prototype chain and finds `template` on `Object.prototype` "
            "now, it reads back your payload and writes it into `innerHTML`. Fix: guard "
            "`__proto__`/`constructor`/`prototype` explicitly in any recursive merge, or "
            "use `Object.create(null)` / `Map` for merge targets, or `Object.freeze"
            "(Object.prototype)`."
        ),
    },
    "PP02": {
        "hints": [
            "Same `deep` merge gap as PP01, but the gadget this time reads a `redirect` path and writes it into an `<a href>`.",
            "Pollute `Object.prototype.redirect` instead of `template`, and give it a `javascript:` URL.",
        ],
        "solution": (
            "Submit:\n\n"
            "`{\"__proto__\":{\"redirect\":\"javascript:alert(1)\"}}`\n\n"
            "The deep merge writes `redirect` onto `Object.prototype`. The gadget reads "
            "`get({}, 'redirect')` off a fresh object -- the prototype-chain lookup "
            "resolves to your polluted value -- and renders "
            "`<a href=\"javascript:alert(1)\">gadget link</a>`. Click the rendered "
            "\"gadget link\" to trigger it (href-based gadgets need a click, unlike "
            "`innerHTML` gadgets which fire on render if they contain an `onerror`-style "
            "payload). Fix: same as PP01 -- guard dangerous keys in the merge, and never "
            "write an unvalidated value into `href` without checking its scheme."
        ),
    },
    "PP03": {
        "hints": [
            "Mode is `clone` this time: `JSON.parse(JSON.stringify(target))` then `deepMerge`. Does `JSON.stringify`/`parse` change anything about whether `__proto__` pollution still works?",
            "The clone step only clones `target` (the defaults) before merging your `source` into the clone -- your `source` JSON still goes through the same unguarded `deepMerge` afterward.",
        ],
        "solution": (
            "`cloneMerge` does `JSON.parse(JSON.stringify(target))` to clone the "
            "*defaults* object (this step is irrelevant to the attack -- it never "
            "touches your input), then calls the same unguarded `deepMerge(clone, "
            "source)` on your submitted JSON. So the identical payload as PP01 works "
            "here too:\n\n"
            "`{\"__proto__\":{\"template\":\"<img src=x onerror=alert(1)>\"}}`\n\n"
            "The \"clone\" naming might suggest extra safety, but cloning the *target* "
            "does nothing to protect against polluting `Object.prototype` via the "
            "*source* -- the vulnerable step is still the final `deepMerge` call. Fix: "
            "the guard needs to be in `deepMerge` itself, not in how the target is "
            "prepared beforehand."
        ),
    },
    "PP04": {
        "hints": [
            "Two gadgets are wired up this time: `innerHTML` reading `template`, and `attr_href` reading `redirect`. One `__proto__` payload can pollute both keys at once.",
            "Deep merge, so nest both keys under a single `__proto__` object in your JSON.",
        ],
        "solution": (
            "Submit a single payload polluting both gadget paths at once:\n\n"
            "`{\"__proto__\":{\"template\":\"<img src=x onerror=alert(1)>\",\"redirect\":\"javascript:alert(2)\"}}`\n\n"
            "Both `Object.prototype.template` and `Object.prototype.redirect` get set "
            "by the same unguarded `deepMerge` call. The `innerHTML` gadget fires "
            "immediately on render; click the rendered \"gadget link\" to trigger the "
            "`href` gadget too. This demonstrates how a single prototype-pollution "
            "primitive can cascade into multiple independent sinks if more than one "
            "gadget in the app happens to read from `Object.prototype`."
        ),
    },
    "PP05": {
        "hints": [
            "Mode is `assign` -- `Object.assign(target, source)`. Does `Object.assign` ever let you write to `Object.prototype` via a `__proto__` key in the source?",
            "`Object.assign` only copies own enumerable properties, and critically treats `__proto__` as a *regular* own property key on a plain object/array literal from `JSON.parse` -- it does NOT trigger the `__proto__` *setter* the way bare `obj.__proto__ = x` assignment would. Compare that to `deepMerge`'s recursive walk.",
        ],
        "solution": (
            "This is the deliberately **safe control** of the prototype-pollution "
            "category. `Object.assign(target, source)` performs a shallow copy of own "
            "enumerable keys from `source` onto `target` -- if `source` (from "
            "`JSON.parse`) has an own property literally named `\"__proto__\"`, "
            "`Object.assign` sets it as an ordinary own property *on `target`* (because "
            "`[[Set]]` on a plain object triggers the `Object.prototype` `__proto__` "
            "accessor only when the target doesn't already shadow it as an own data "
            "property from the copy -- in practice, `Object.assign` with a JSON-parsed "
            "source containing a `__proto__` key does not pollute `Object.prototype` in "
            "modern JS engines, because `JSON.parse` produces an own property named "
            "`__proto__`, and `Object.assign`'s per-key `[[Set]]`, when the key is "
            "`__proto__`, invokes the inherited setter which only reassigns `target`'s "
            "own prototype, not `Object.prototype` itself). Submitting the same "
            "`{\"__proto__\":{\"template\":\"...\"}}` payload here does **not** pollute "
            "`Object.prototype.template`, and the gadget (reading off a fresh `{}`) "
            "stays at its default. Verify this in the box, confirm the gadget output "
            "never changes no matter what you submit, and mark it solved on the "
            "conclusion **not exploitable -- shallow `Object.assign` does not reach "
            "`Object.prototype` the way the recursive `deepMerge` in PP01-04 does**."
        ),
    },

    # ---------------- FRAMEWORKS (React / Vue) ----------------
    "RE01": {
        "hints": [
            "Try `?name=<script>alert(1)</script>` and `?name=<img src=x onerror=alert(1)>` -- this component renders `name` as a plain JSX text child.",
            "React escapes text children (`e('div', null, 'hello, ', name)`) automatically -- there's no `dangerouslySetInnerHTML` anywhere in this pattern.",
        ],
        "solution": (
            "This is the deliberately **safe control** for the frameworks category. "
            "`name` is rendered as a JSX/`React.createElement` text child, which React "
            "escapes automatically before inserting into the DOM -- `<script>` tags and "
            "HTML metacharacters are rendered as literal visible text, never parsed as "
            "markup. Try `?name=<img src=x onerror=alert(1)>` and confirm the payload "
            "shows up as plain text on the page (e.g. you'll literally see the angle "
            "brackets), not as an executing element. Mark it solved on the conclusion "
            "**not exploitable** -- this is React's default behavior working correctly, "
            "and it's the contrast case for RE02/RE03."
        ),
    },
    "RE02": {
        "hints": [
            "Try `?html=` instead of `?name=` -- this component's `pattern` is `dangerous`.",
            "`dangerouslySetInnerHTML` does exactly what its name says: it bypasses React's escaping entirely and inserts raw HTML.",
        ],
        "solution": (
            "`cfg.pattern === 'dangerous'` reads `?html=` and renders it via "
            "`e('div', { dangerouslySetInnerHTML: { __html: html } })` -- React's "
            "explicit, intentional opt-out of its default text-escaping. Visit:\n\n"
            "`/lab/RE02/run?html=<img src=x onerror=alert(1)>`\n\n"
            "The payload is inserted as real HTML and the handler fires. Fix: avoid "
            "`dangerouslySetInnerHTML` with any user-controlled value; if raw HTML "
            "rendering is genuinely required, sanitize with DOMPurify first (see the "
            "sanitizer labs for how that can still go wrong if misconfigured)."
        ),
    },
    "RE03": {
        "hints": [
            "This pattern is `props` and reads `?title=` -- `?html=`/`?name=` won't do anything here.",
            "The component builds a template string with the title and feeds the whole thing straight into `dangerouslySetInnerHTML` -- same sink as RE02, different-looking source.",
        ],
        "solution": (
            "`cfg.pattern === 'props'` reads `?title=` and does "
            "`e('div', { dangerouslySetInnerHTML: { __html: `<h3>${title}</h3>` } })` "
            "-- interpolating the title into a template string before handing the whole "
            "thing to `dangerouslySetInnerHTML`. Visit:\n\n"
            "`/lab/RE03/run?title=</h3><img src=x onerror=alert(1)><h3>`\n\n"
            "(or simply `?title=<img src=x onerror=alert(1)>`, since the surrounding "
            "`<h3>` tags don't need to be closed cleanly for the `<img>` to still parse "
            "and fire). The lesson versus RE02: the dangerous sink can be one step "
            "removed from the obviously-named `html` parameter -- any prop that "
            "ultimately reaches `dangerouslySetInnerHTML`, however indirectly, is "
            "exploitable the same way."
        ),
    },
    "VU01": {
        "hints": [
            "Try `?name=<script>alert(1)</script>` -- this component uses `{{ name }}` mustache interpolation, not `v-html`.",
            "Vue's `{{ }}` interpolation escapes its output by design, same idea as React's text children in RE01.",
        ],
        "solution": (
            "This is the deliberately **safe control** for the Vue sub-category. "
            "`{{ name }}` mustache interpolation is auto-escaped by Vue -- HTML "
            "metacharacters in `name` render as literal text, never as markup. Confirm "
            "with `?name=<img src=x onerror=alert(1)>` (shows up as visible literal "
            "text) and mark it solved on **not exploitable**. Contrast with VU02/VU03, "
            "which use `v-html` instead."
        ),
    },
    "VU02": {
        "hints": [
            "Try `?html=` instead of `?name=` -- this component's `pattern` is `vhtml`.",
            "`v-html=\"raw\"` is Vue's explicit opt-out of escaping, equivalent to React's `dangerouslySetInnerHTML`.",
        ],
        "solution": (
            "`v-html=\"raw\"` binds the `raw` data property (populated from `?html=`) "
            "directly as innerHTML, bypassing Vue's default escaping entirely. Visit:\n\n"
            "`/lab/VU02/run?html=<img src=x onerror=alert(1)>`\n\n"
            "and it fires immediately on render. Fix: avoid `v-html` with "
            "user-controlled data; sanitize first if raw HTML rendering is required."
        ),
    },
    "VU03": {
        "hints": [
            "The lab title says \"a 'sanitizer' that isn't wired up\" -- look at the actual template/data logic in `engine_vue.js` for the `sanitizer` pattern, not just the lab description.",
            "`isVHtml` is `true` for `pattern === 'sanitizer'` too, and the template logic in this build doesn't apply any distinct sanitization step for that pattern -- it's exactly the same `v-html=\"raw\"` binding as VU02 under a different name.",
        ],
        "solution": (
            "Despite being named/described as having a sanitizer, "
            "`cfg.pattern === 'sanitizer'` routes through the exact same "
            "`v-html=\"raw\"` template as `vhtml` (`isVHtml` is true for both, and no "
            "separate sanitization call is actually made anywhere in `engine_vue.js`). "
            "The same payload as VU02 works unchanged:\n\n"
            "`/lab/VU03/run?html=<img src=x onerror=alert(1)>`\n\n"
            "The lesson is a common real-world pattern: a component or variable *named* "
            "after a safety measure (\"sanitizer\", \"safeHtml\", \"cleanContent\") that "
            "was planned, documented, or partially implemented elsewhere, but never "
            "actually wired into the code path that matters. Naming and comments are not "
            "a substitute for verifying the actual data flow -- always trace where the "
            "raw value is bound, not what the surrounding code implies."
        ),
    },

    # ---------------- FINAL: blind challenges (no public description) ----------------
    # Hints for the blind set are deliberately generic -- naming the exact
    # bug would defeat the "investigate first" point of this category.
    "F01": {
        "hints": [
            "This is a blind lab: there's no description telling you the engine type or source/sink. Start by viewing page source and any linked JS files to identify what kind of lab this is.",
            "The engine is `dom` and the source type is one you've already seen in the D-series -- check `location.hash` and trace it through to its sink.",
        ],
        "solution": (
            "Investigation: view-source / DevTools shows this loads `engine_dom.js` "
            "with a `source: {type: hash}` config -- identical shape to D01. "
            "Confirm by navigating to `/lab/F01/run#<img src=x onerror=alert(1)>` and "
            "watching it execute via the `innerHTML` sink. Conclusion: **vulnerable**, "
            "same root cause as D01 (unsanitized `location.hash` -> `innerHTML`), "
            "presented without a description so you practice identifying the pattern "
            "from the client-side code alone rather than being told the engine type "
            "up front."
        ),
    },
    "F02": {
        "hints": [
            "Blind lab -- check what JS file this page loads and what config it passes in `window.LAB_CONFIG`.",
            "This one loads the prototype-pollution engine with a `deep` merge and an `innerHTML` gadget reading `template` -- same shape as PP01.",
        ],
        "solution": (
            "Investigation: `window.LAB_CONFIG` / the loaded `engine_pp.js` script "
            "reveals `mode: deep` and a `type: innerHTML` gadget reading `template`, "
            "identical in structure to PP01. Confirm by submitting "
            "`{\"__proto__\":{\"template\":\"<img src=x onerror=alert(1)>\"}}` into the "
            "merge box. Conclusion: **vulnerable**, same unguarded deep-merge root "
            "cause as PP01."
        ),
    },
    "F03": {
        "hints": [
            "Blind lab -- but check carefully whether there's actually a dangerous sink anywhere in this one before assuming it's exploitable.",
            "This loads the `parse` engine with a static demo string (`all systems operational`) and no attacker-controlled input path into any sink at all.",
        ],
        "solution": (
            "Investigation: this loads `engine_parse.js` with a fixed `demo` string and "
            "no mechanism for attacker input to reach it (unlike the interactive B-series "
            "parsing labs, there's no input box wired to a sink the attacker controls "
            "here) -- it's a static status display. Conclusion: **not exploitable** / "
            "safe control. Document that you checked for any reachable input-to-sink "
            "path and found none, rather than assuming every blind lab must hide a bug."
        ),
    },
    "F04": {
        "hints": [
            "Blind lab -- identify the engine first. This one's config matches a lab you've already seen in the mXSS category, including the sanitizer setting.",
            "`seed: <svg><desc><b>x</b></desc></svg>`, `sanitizeFirst: true` -- that's the exact M04/M02-style seed, but check which one actually matches by config, not just the markup.",
        ],
        "solution": (
            "Investigation: the loaded config is `engine: mxss`, "
            "`seed: <svg><desc><b>x</b></desc></svg>`, `sanitizeFirst: true` -- same "
            "seed as M02 but *with* DOMPurify sanitizing between the two insertion "
            "passes, making this the sanitized variant of that namespace-switching "
            "`<svg><desc>` differential. Test the same approach as M02/M03: compare the "
            "DOM after the first (sanitized) insertion to the DOM after the "
            "serialize-and-reinsert second pass, and try extending the seed with a "
            "scriptable gadget nested in the `<desc>` to see if DOMPurify's sanitized "
            "output still mutates into something live on re-parse. Conclusion depends "
            "on what you find with the installed DOMPurify version -- document your "
            "payload and the DOM diff either way; \"confirmed exploitable\" and "
            "\"confirmed patched\" are both valid, complete answers for a blind lab."
        ),
    },
    "F05": {
        "hints": [
            "Blind lab -- check the loaded JS and config before trying anything. This one's a DOM-sourced lab reading from the URL in a way you've seen before.",
            "`source: {type: search, param: q}` -- same shape as D02/D05, just a different parameter name.",
        ],
        "solution": (
            "Investigation: `engine_dom.js` with `source: {type: search, param: q}` -- "
            "same pattern as D02, reading `?q=` via `URLSearchParams` into `innerHTML` "
            "with no sanitization. Confirm with:\n\n"
            "`/lab/F05/run?q=<img src=x onerror=alert(1)>`\n\n"
            "Conclusion: **vulnerable**, same root cause as D02. This lab exists to "
            "practice noticing that a renamed query parameter and a missing description "
            "don't actually obscure the underlying bug once you check the client-side "
            "source."
        ),
    },
}


def main():
    patched = 0
    missing = []
    for cat in sorted(os.listdir(LABS)):
        cat_path = os.path.join(LABS, cat)
        if not os.path.isdir(cat_path):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if not fname.endswith(".yaml"):
                continue
            fpath = os.path.join(cat_path, fname)
            with open(fpath) as f:
                cfg = yaml.safe_load(f)
            lab_id = cfg.get("id")
            wt = WALKTHROUGHS.get(lab_id)
            if not wt:
                missing.append(lab_id)
                continue
            cfg["walkthrough"] = wt
            with open(fpath, "w") as f:
                yaml.safe_dump(cfg, f, sort_keys=False, width=100)
            patched += 1

    print(f"patched {patched} lab(s)")
    if missing:
        print(f"no walkthrough defined for: {', '.join(missing)}")


if __name__ == "__main__":
    main()
