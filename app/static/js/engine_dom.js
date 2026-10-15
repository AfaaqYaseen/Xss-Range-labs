(function () {
  const cfg = window.LAB_CONFIG || {};
  const root = document.getElementById("lab-root");

  function getSource(src) {
    if (!src) return "";
    switch (src.type) {
      case "hash": return decodeURIComponent(location.hash.slice(1));
      case "search": return new URLSearchParams(location.search).get(src.param || "x") || "";
      case "params": return new URLSearchParams(location.search).get(src.param || "x") || "";
      case "pathname": return decodeURIComponent(location.pathname);
      case "referrer": return document.referrer || "(no referrer - open this page by clicking a link from another page)";
      case "name": return window.name || "";
      case "localStorage": return window.localStorage.getItem(src.key || "pref") || "";
      case "sessionStorage": return window.sessionStorage.getItem(src.key || "draft") || "";
      case "cookie": {
        const m = document.cookie.match(new RegExp("(?:^|; )" + (src.key || "pref") + "=([^;]*)"));
        return m ? decodeURIComponent(m[1]) : "";
      }
      case "postMessage": return window.__lastMessage || "(waiting for a postMessage - see the helper form below)";
      default: return "";
    }
  }

  function applyTransform(name, value) {
    if (name === "url_decode") return decodeURIComponent(value);
    if (name === "url_decode_twice") return decodeURIComponent(decodeURIComponent(value));
    if (name === "lowercase") return value.toLowerCase();
    if (name === "html_entity_decode") {
      const ta = document.createElement("textarea");
      ta.innerHTML = value;
      return ta.value;
    }
    if (name && name.name === "substring") return value.substring(name.start || 0, name.end);
    if (name && name.name === "concatenate") return (name.prefix || "") + value + (name.suffix || "");
    return value;
  }

  function applyReplaceChain(chain, value) {
    (chain || []).forEach((r) => {
      value = value.replace(new RegExp(r.pattern, "g"), r.replacement);
    });
    return value;
  }

  function writeSink(sink, value) {
    const type = (sink && sink.type) || "innerHTML";
    if (type === "innerHTML") {
      root.innerHTML = `<div class="reflect">${value}</div>`;
    } else if (type === "attr_href") {
      root.innerHTML = `<a href="${value}">continue</a>`;
    } else if (type === "document_write") {
      document.write(value); // eslint-disable-line no-restricted-globals
    } else {
      root.innerHTML = `<div class="reflect">${value}</div>`;
    }
  }

  function render() {
    let value = getSource(cfg.source);
    value = applyTransform(cfg.transforms && cfg.transforms[0], value) || value;
    (cfg.transforms || []).forEach((t) => { value = applyTransform(t, value); });
    value = applyReplaceChain(cfg.replace_chain, value);
    if (cfg.conditional && cfg.conditional.pattern) {
      const re = new RegExp(cfg.conditional.pattern);
      if (!re.test(value)) {
        root.innerHTML = `<p class="hint">condition not met yet (pattern: ${cfg.conditional.pattern})</p>`;
        return;
      }
    }
    if (cfg.bootstrap && !value) value = cfg.bootstrap;
    writeSink(cfg.sink, value);
  }

  window.addEventListener("message", (ev) => { window.__lastMessage = ev.data; render(); });
  window.addEventListener("hashchange", render);

  // small helper panel so the labs are usable without curl/devtools
  const helper = document.createElement("div");
  helper.innerHTML = `
    <details class="helper"><summary>helper: set localStorage / sessionStorage / cookie / window.name</summary>
      <form id="helper-form">
        <input name="val" placeholder="value to store">
        <button data-k="localStorage">set localStorage</button>
        <button data-k="sessionStorage">set sessionStorage</button>
        <button data-k="cookie">set cookie</button>
        <button data-k="name">set window.name (reload after)</button>
      </form>
    </details>`;
  document.body.appendChild(helper);
  helper.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const val = helper.querySelector("input[name=val]").value;
      const kind = btn.dataset.k;
      const key = (cfg.source && cfg.source.key) || "pref";
      if (kind === "localStorage") window.localStorage.setItem(key, val);
      if (kind === "sessionStorage") window.sessionStorage.setItem(key, val);
      if (kind === "cookie") document.cookie = `${key}=${encodeURIComponent(val)}; path=/`;
      if (kind === "name") window.name = val;
      render();
    });
  });

  render();
})();
