(function () {
  const cfg = window.LAB_CONFIG || {};
  const root = document.getElementById("lab-root");

  function get(obj, path) {
    return path.split(".").reduce((o, k) => (o == null ? o : o[k]), obj);
  }

  // Deliberately naive: no __proto__/constructor/prototype guard.
  function deepMerge(target, source) {
    for (const key of Object.keys(source)) {
      const sv = source[key];
      if (sv && typeof sv === "object" && !Array.isArray(sv)) {
        if (typeof target[key] !== "object" || target[key] === null) target[key] = {};
        deepMerge(target[key], sv);
      } else {
        target[key] = sv;
      }
    }
    return target;
  }

  function shallowAssign(target, source) {
    // Object.assign-style: safe control example for contrast with deepMerge.
    return Object.assign(target, source);
  }

  function cloneMerge(target, source) {
    const clone = JSON.parse(JSON.stringify(target));
    return deepMerge(clone, source);
  }

  const MERGERS = { deep: deepMerge, shallow: shallowAssign, clone: cloneMerge, assign: shallowAssign };

  function writeSink(gadget, value) {
    const div = document.createElement("div");
    div.className = "gadget-out";
    if (gadget.type === "innerHTML") div.innerHTML = `<div class="reflect">${value ?? "(unset)"}</div>`;
    else if (gadget.type === "attr_href") div.innerHTML = `<a href="${value ?? "#"}">gadget link</a>`;
    else if (gadget.type === "script_src") div.innerHTML = `<code>&lt;script src="${value ?? "(unset)"}"&gt;</code> (would load if this path were reachable)`;
    else div.textContent = String(value);
    return div;
  }

  root.innerHTML = `
    <p>attacker-controlled JSON, merged (<code>${cfg.mode || "deep"}</code> mode) into an internal defaults object:</p>
    <textarea id="pp-input" rows="4" style="width:100%">{"__proto__":{"polluted":"yes"}}</textarea>
    <button id="pp-run">merge &amp; render gadgets</button>
    <h4>gadget outputs (each reads its path off a brand-new <code>{}</code>, not the merged object)</h4>
    <div id="pp-out"></div>
    <pre id="pp-err" style="color:#a00"></pre>
  `;

  function run() {
    const errEl = document.getElementById("pp-err");
    const out = document.getElementById("pp-out");
    out.innerHTML = "";
    errEl.textContent = "";
    let source;
    try {
      source = JSON.parse(document.getElementById("pp-input").value);
    } catch (e) {
      errEl.textContent = "invalid JSON: " + e.message;
      return;
    }
    const target = JSON.parse(JSON.stringify(cfg.defaults || {}));
    const merger = MERGERS[cfg.mode] || deepMerge;
    merger(target, source);

    (cfg.gadgets || []).forEach((g) => {
      const freshObject = {}; // proves the read comes from Object.prototype, not `target`
      const value = get(freshObject, g.path);
      out.appendChild(writeSink(g, value));
    });
  }
  document.getElementById("pp-run").addEventListener("click", run);
  run();
})();
