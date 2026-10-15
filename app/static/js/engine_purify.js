(function () {
  const cfg = window.LAB_CONFIG || {};
  const root = document.getElementById("lab-root");
  const version = cfg.version || "3.1.6";
  const src = version === "2.0.17" ? "/static/vendor/purify-2.0.17.min.js" : "/static/vendor/purify-3.1.6.min.js";

  root.innerHTML = `
    <p>DOMPurify <code>${version}</code>${cfg.options ? " with config: <code>" + JSON.stringify(cfg.options) + "</code>" : ""}</p>
    <textarea id="pu-input" rows="4" style="width:100%">${(cfg.seed || "").replace(/</g, "&lt;")}</textarea>
    <button id="pu-run" disabled>loading DOMPurify…</button>
    <h4>sanitized output (string)</h4>
    <pre id="pu-clean-str" style="background:#eee;padding:8px;overflow:auto"></pre>
    <h4>sanitized output (inserted into the DOM)</h4>
    <div id="pu-clean-dom" style="border:1px dashed #999;padding:8px"></div>
  `;

  function customSanitize(kind, value) {
    if (kind === "strip_script_regex") {
      // classic broken "sanitizer": one non-recursive regex pass.
      return value.replace(/<script[^>]*>.*?<\/script>/gi, "");
    }
    if (kind === "allowlist_simple") {
      const allowed = ["b", "i", "em", "strong", "a"];
      return value.replace(/<\/?([a-zA-Z0-9]+)([^>]*)>/g, (m, tag) =>
        allowed.includes(tag.toLowerCase()) ? m : ""
      );
    }
    return value;
  }

  function run() {
    const raw = document.getElementById("pu-input").value;
    let clean;
    if (cfg.custom) {
      clean = customSanitize(cfg.custom, raw);
    } else if (window.DOMPurify) {
      clean = window.DOMPurify.sanitize(raw, cfg.options || {});
    } else {
      clean = "(DOMPurify failed to load)";
    }
    document.getElementById("pu-clean-str").textContent = clean;
    document.getElementById("pu-clean-dom").innerHTML = clean;
  }

  function enable() {
    const btn = document.getElementById("pu-run");
    btn.disabled = false;
    btn.textContent = "sanitize";
    btn.addEventListener("click", run);
    run();
  }

  if (cfg.custom) {
    enable();
  } else {
    const s = document.createElement("script");
    s.src = src;
    s.onload = enable;
    document.head.appendChild(s);
  }
})();
