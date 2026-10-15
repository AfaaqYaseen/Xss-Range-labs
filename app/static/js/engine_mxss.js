(function () {
  const cfg = window.LAB_CONFIG || {};
  const root = document.getElementById("lab-root");

  root.innerHTML = `
    <label>markup</label>
    <textarea id="mx-input" rows="4" style="width:100%">${(cfg.seed || "").replace(/</g, "&lt;")}</textarea>
    <label><input type="checkbox" id="mx-sanitize" ${cfg.sanitizeFirst ? "checked" : ""}> sanitize with DOMPurify before insertion</label>
    <button id="mx-run">run</button>
    <h4>pass 1: after insertion (innerHTML set)</h4>
    <div id="mx-pass1" style="border:1px dashed #999;padding:8px"></div>
    <h4>pass 1 serialized back to a string</h4>
    <pre id="mx-serialized" style="background:#eee;padding:8px;overflow:auto"></pre>
    <h4>pass 2: that string re-inserted (innerHTML set again)</h4>
    <div id="mx-pass2" style="border:1px dashed #999;padding:8px"></div>
  `;

  function run() {
    let val = document.getElementById("mx-input").value;
    if (document.getElementById("mx-sanitize").checked && window.DOMPurify) {
      val = window.DOMPurify.sanitize(val);
    }
    const p1 = document.getElementById("mx-pass1");
    p1.innerHTML = val;
    const serialized = p1.innerHTML;
    document.getElementById("mx-serialized").textContent = serialized;
    const p2 = document.getElementById("mx-pass2");
    p2.innerHTML = serialized;
  }
  document.getElementById("mx-run").addEventListener("click", run);
  run();
})();
