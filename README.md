# XSS Mastery Range

A local, intentionally-vulnerable training range for learning cross-site
scripting — in the same spirit as DVWA, OWASP Juice Shop, or PortSwigger's
Web Security Academy. It ships 52 labs across 10 categories: reflected,
stored, DOM, HTML parsing, mutation XSS (mXSS), CSP bypasses, sanitizer
gaps, prototype pollution, and React/Vue framework patterns, plus a set of
"final" blind challenges with no description.

> **This app is deliberately vulnerable.** Run it only on your own machine
> or an isolated lab network. Never expose it to the internet. See
> `SECURITY.md`.

## Features

- **52 labs** across 10 categories, each with progressive hints and a
  spoiler-protected solution walkthrough.
- **Real libraries**: DOMPurify 3.1.6 and 2.0.17, React 18.3.1 and Vue 3.4.27
  are vendored byte-for-byte from npm, so the sanitizer and framework labs
  exercise real library behavior rather than a simulation.
- **Config-driven**: one YAML file per lab, so adding a lab needs no code
  changes (see "Adding a lab").
- **Tested**: 13 automated tests (`pytest`) cover lab routing, reflection,
  filter bypasses, stored XSS, CSP headers/nonces, solved-state tracking, and
  that lab internals are never served to the browser.

> **Authorized, educational use only.** Practice these techniques only on
> systems you own or have explicit permission to test.

## Run it

```bash
pip install -r requirements.txt -r requirements-dev.txt
python scripts/generate_labs.py   # writes labs/*.yaml (idempotent-ish; skip if labs/ already populated)
python validate_labs.py           # expect: 52 labs discovered, 0 errors
pytest                            # expect: 13 passed
python app/app.py                 # -> http://localhost:8000
```

Or with Docker:

```bash
docker compose up --build         # -> http://localhost:8000 (bound to localhost only)
```

## Architecture

```
app/
  app.py            Flask routes; dispatches each lab by its "engine"
  lab_loader.py      discovers + validates labs/*/*.yaml
  contexts.py        renders a value RAW into an HTML/JS/attribute/etc. context
  transforms.py       server-side decode/encode chain (url_decode, html_encode, ...)
  filters.py          naive, single-pass, bypassable input filters
  database.py         sqlite storage for stored-XSS labs
  templates/           dashboard, lab detail, and per-engine target pages
  static/js/           client-side lab engines (dom/parse/mxss/pp/purify/react/vue)
  static/vendor/       byte-exact DOMPurify 3.1.6 & 2.0.17, React 18.3.1, Vue 3.4.27
labs/<category>/*.yaml  one file per lab (id, title, difficulty, engine, public info, engine config)
scripts/generate_labs.py   writes the labs/ YAML files
validate_labs.py            checks for missing fields / duplicate ids / bad categories
tests/test_app.py            pytest suite (see above)
```

Each lab YAML has:
- `public`: objective/description shown to the trainee (omitted for `hidden: true` blind labs)
- `engine`: one of `reflected | stored | dom | parse | mxss | csp | purify | pp | react | vue`
- `engine_config` (reflected/stored/csp) or `client` (everything else): the actual
  vulnerable configuration — which context, which filter, which merge mode, etc.
- `private`: a one-line note on *why* it's vulnerable, for your own reference —
  this key is loaded into memory but there is no route that serves it, so it
  never reaches the browser (see `test_solutions_never_served`).
- `walkthrough`: **unlike `private`, this one is shown to the trainee** on the
  lab detail page, behind collapsible `<details>` elements so nothing spoils
  the page by default:
  - `hints`: an ordered list of progressively more specific nudges (each one
    is its own collapsible item, so a trainee can reveal them one at a time)
  - `solution`: a short, step-by-step writeup of the vulnerable code path and
    a working payload, revealed behind a single "Solution walkthrough
    (spoiler)" toggle

  All 52 labs ship with a `walkthrough`
  (`test_every_lab_has_a_walkthrough` enforces this). Solution text is
  HTML-escaped server-side before a tiny bit of markdown-lite formatting
  (`` `code` `` and `**bold**`) is applied on top of the *escaped* text — see
  `render_walkthrough_text` in `app/app.py` — so the example payloads quoted
  in a solution (e.g. `<img src=x onerror=alert(1)>`) always render as inert
  text on the writeup itself rather than executing on the page that's
  supposed to be explaining them
  (`test_walkthrough_payloads_are_escaped_not_executable` covers this).

## Adding a lab

Drop a new YAML file under `labs/<category>/`, matching the shape of an
existing lab in that category, and it's picked up automatically on next
restart — no code changes needed unless you're introducing a genuinely new
engine. Run `python validate_labs.py` after adding labs.

If the lab doesn't already have a `walkthrough`, add its `hints`/`solution`
to the `WALKTHROUGHS` dict in `scripts/add_walkthroughs.py` and rerun it —
it patches only the `walkthrough` key of matching lab files in place and
leaves everything else untouched, so it's safe to rerun after
`generate_labs.py` too.

## Honest limitations / what was cut from the original 229-lab spec

- **Lab count**: 52 representative labs, not 229. The categories and engine
  types are all represented; the *density* within each category (e.g. 25
  reflected-XSS variants down to 6) was cut for the sake of shipping
  something fully working rather than untested bulk.
- **AngularJS was dropped.** AngularJS (1.x) is end-of-life and unmaintained;
  Vue 3 + React 18 cover the "modern reactive framework" teaching goals
  (auto-escaping by default vs. `v-html`/`dangerouslySetInnerHTML` opt-outs).
  Angular-specific `$sce`/trustAsHtml patterns aren't demonstrated.
- **No headless-browser grading.** Like most local ranges of this kind,
  "solved" is a self-reported checkbox, not an automated proof that your
  payload executed — there's no headless Chrome in this environment to
  verify JS execution server-side.

## License

MIT - see `LICENSE`.
