import json
import os
import re
import secrets
import sys
from html import escape as _escape
from markupsafe import Markup

from flask import Flask, request, render_template, redirect, url_for, session, g, abort

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lab_loader import load_labs, labs_by_category
from contexts import render_context
from transforms import apply_chain
from filters import apply_filter
import database

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")


def render_walkthrough_text(text: str) -> Markup:
    """Escapes walkthrough/hint text (which routinely contains literal
    payloads like <img src=x onerror=alert(1)>) and then applies a tiny bit
    of markdown-lite formatting on top of the *escaped* text, so example
    payloads are always shown as inert text, never executed on this page."""
    if not text:
        return Markup("")
    safe = _escape(text)
    # `code spans` -> <code>
    safe = re.sub(r"`([^`]+)`", r"<code>\1</code>", safe)
    # **bold** -> <strong>
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", safe)
    # blank-line-separated paragraphs
    paragraphs = [p.strip() for p in safe.split("\n\n") if p.strip()]
    html = "".join(f"<p>{p}</p>" for p in paragraphs)
    return Markup(html)


app.jinja_env.filters["walkthrough"] = render_walkthrough_text

database.init_db()
LABS, LOAD_ERRORS = load_labs()

CATEGORY_LABELS = {
    "reflected": "Reflected XSS",
    "stored": "Stored XSS",
    "dom": "DOM XSS",
    "parsing": "HTML Parsing",
    "mxss": "Mutation XSS",
    "csp": "Content Security Policy",
    "sanitizers": "Sanitizers",
    "prototype_pollution": "Prototype Pollution",
    "frameworks": "Frameworks (React / Vue)",
    "final": "Final: Blind Challenges",
}


def client_config(lab: dict) -> dict:
    """Whatever the client-side engine JS needs, minus anything from
    'private' style notes."""
    return lab.get("client", {}) or {}


@app.route("/")
def dashboard():
    grouped = labs_by_category(LABS)
    solved = session.get("solved", [])
    order = list(CATEGORY_LABELS.keys())
    return render_template(
        "dashboard.html",
        grouped=grouped,
        order=order,
        labels=CATEGORY_LABELS,
        solved=set(solved),
        total=len(LABS),
    )


@app.route("/lab/<lab_id>")
def lab_detail(lab_id):
    lab = LABS.get(lab_id)
    if not lab:
        abort(404)
    solved = lab_id in session.get("solved", [])
    return render_template("lab.html", lab=lab, solved=solved)


@app.route("/lab/<lab_id>/solve", methods=["POST"])
def lab_solve(lab_id):
    if lab_id not in LABS:
        abort(404)
    solved = set(session.get("solved", []))
    solved.add(lab_id)
    session["solved"] = list(solved)
    return redirect(url_for("lab_detail", lab_id=lab_id))


@app.route("/lab/<lab_id>/run", methods=["GET"])
def lab_run(lab_id):
    lab = LABS.get(lab_id)
    if not lab:
        abort(404)
    engine = lab["engine"]

    if engine == "reflected":
        return _run_reflected(lab)
    if engine == "stored":
        return _run_stored(lab)
    if engine == "csp":
        return _run_csp(lab)
    # dom / parse / mxss / pp / purify / react / vue all render a
    # client-only page; the vulnerable logic lives in the browser JS.
    return render_template(
        "client_lab.html",
        lab=lab,
        config_json=json.dumps(client_config(lab)),
    )


@app.route("/lab/<lab_id>/submit", methods=["POST"])
def lab_submit(lab_id):
    lab = LABS.get(lab_id)
    if not lab or lab["engine"] != "stored":
        abort(404)
    cfg = lab["engine_config"]
    for field in cfg["fields"]:
        value = request.form.get(field, "")
        value = apply_chain(cfg.get("transform_in"), value)
        value = apply_filter(cfg.get("filter"), value)
        database.set_stored(lab_id, field, value)
    return redirect(url_for("lab_run", lab_id=lab_id))


@app.route("/lab/<lab_id>/reset", methods=["POST"])
def lab_reset(lab_id):
    lab = LABS.get(lab_id)
    if not lab or lab["engine"] != "stored":
        abort(404)
    database.reset_stored(lab_id)
    return redirect(url_for("lab_run", lab_id=lab_id))


def _run_reflected(lab):
    cfg = lab["engine_config"]
    values = {}
    for param in cfg["params"]:
        raw = request.args.get(param, "")
        v = apply_chain(cfg.get("transform"), raw)
        v = apply_filter(cfg.get("filter"), v)
        values[param] = v
    primary = cfg["params"][0]
    fragment = render_context(cfg["context"], values.get(primary, ""))
    return render_template("run_snippet.html", lab=lab, fragment=fragment, values=values)


def _run_stored(lab):
    cfg = lab["engine_config"]
    stored = database.get_all_stored(lab.get("id"))
    primary = cfg["fields"][0]
    value = stored.get(primary, "")
    value = apply_chain(cfg.get("transform_out"), value)
    fragment = render_context(cfg["context"], value)
    return render_template(
        "run_snippet.html", lab=lab, fragment=fragment, values=stored, stored_lab=True
    )


def _run_csp(lab):
    cfg = lab["engine_config"]
    policy = dict(cfg.get("policy", {}))
    csp_header = "; ".join(f"{k} {v}" for k, v in policy.items())
    if "{NONCE}" in csp_header:
        nonce = secrets.token_urlsafe(12)
        csp_header = csp_header.replace("{NONCE}", nonce)
        g.nonce = nonce
    g.csp = csp_header
    probe = ""
    if "x" in request.args:
        probe = render_context(cfg.get("probe_context", "html_text"), request.args.get("x", ""))
    return render_template(
        "csp_lab.html", lab=lab, page_html=cfg.get("page_html", ""), probe=probe,
        nonce=getattr(g, "nonce", None),
    )


@app.route("/lab/<lab_id>/jsonp")
def jsonp(lab_id):
    callback = request.args.get("callback", "cb")
    return f"{callback}('jsonp endpoint reached');", 200, {"Content-Type": "application/javascript"}


@app.after_request
def add_csp(resp):
    csp = getattr(g, "csp", None)
    if csp:
        resp.headers["Content-Security-Policy"] = csp
    return resp


@app.route("/health")
def health():
    return {"labs": len(LABS), "errors": LOAD_ERRORS}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
