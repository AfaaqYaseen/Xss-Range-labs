import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data"), exist_ok=True)

import pytest
from app import app, LABS, LOAD_ERRORS


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_labs_loaded_without_errors():
    assert LOAD_ERRORS == []
    assert len(LABS) > 0


def test_dashboard(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"XSS Mastery Range" in r.data


def test_all_lab_detail_and_run_routes(client):
    for lid in LABS:
        r1 = client.get(f"/lab/{lid}")
        assert r1.status_code == 200, f"{lid} detail page failed"
        r2 = client.get(f"/lab/{lid}/run")
        assert r2.status_code == 200, f"{lid} run page failed"


def test_reflected_reflects_unescaped():
    client_ = app.test_client()
    r = client_.get("/lab/R01/run?q=%3Cimg+src%3Dx+onerror%3Dalert(1)%3E")
    assert b"<img src=x onerror=alert(1)>" in r.data


def test_reflected_filter_is_bypassable_single_pass():
    # classic bypass: "<scr" + "script" + "ipt>" -- removing the literal
    # substring "script" once collapses this back into "<script>".
    import urllib.parse
    client_ = app.test_client()
    payload = "<scrscriptipt>alert(1)</scrscriptipt>"
    r = client_.get("/lab/R04/run?q=" + urllib.parse.quote(payload))
    assert b"<script>alert(1)</script>" in r.data


def test_stored_roundtrip():
    client_ = app.test_client()
    client_.post("/lab/S01/submit", data={"comment": "<b>stored</b>"})
    r = client_.get("/lab/S01/run")
    assert b"<b>stored</b>" in r.data
    client_.post("/lab/S01/reset")
    r2 = client_.get("/lab/S01/run")
    assert b"<b>stored</b>" not in r2.data


def test_csp_header_present(client):
    r = client.get("/lab/C01/run")
    assert "Content-Security-Policy" in r.headers


def test_csp_nonce_is_substituted(client):
    r = client.get("/lab/C03/run")
    csp = r.headers["Content-Security-Policy"]
    assert "{NONCE}" not in csp
    assert "nonce-" in csp


def test_solve_marks_session(client):
    r = client.post("/lab/R01/solve", follow_redirects=True)
    assert r.status_code == 200
    with client.session_transaction() as sess:
        assert "R01" in sess.get("solved", [])


def test_solutions_never_served(client):
    # 'private' notes live inside the YAML in memory but there is no route
    # that serves lab internals/config as raw data.
    r = client.get("/lab/R01")
    assert b"config gap" not in r.data
    assert b"single non-recursive pass" not in r.data


def test_walkthrough_hints_and_solution_render(client):
    r = client.get("/lab/R01")
    assert r.status_code == 200
    assert b"Hints (2)" in r.data
    assert b"Solution walkthrough (spoiler)" in r.data
    assert b"HTML-encode" in r.data


def test_every_lab_has_a_walkthrough():
    for lid, lab in LABS.items():
        assert "walkthrough" in lab, f"{lid} is missing a walkthrough"
        assert lab["walkthrough"].get("hints"), f"{lid} has no hints"
        assert lab["walkthrough"].get("solution"), f"{lid} has no solution"


def test_walkthrough_payloads_are_escaped_not_executable(client):
    # Solutions quote real payloads like <img src=x onerror=alert(1)>; make
    # sure they reach the browser HTML-encoded (as literal text) rather than
    # as live markup that would itself fire on the lab's own detail page.
    r = client.get("/lab/R01")
    assert b"<img src=x onerror=alert(1)>" not in r.data
    assert b"&lt;img src=x onerror=alert(1)&gt;" in r.data
