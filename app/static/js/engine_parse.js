(function () {
  const cfg = window.LAB_CONFIG || {};
  const root = document.getElementById("lab-root");

  function describe(node, depth) {
    const indent = "  ".repeat(depth);
    let line = `${indent}${node.nodeName}`;
    if (node.namespaceURI) line += ` [ns: ${node.namespaceURI.split("/").pop()}]`;
    let out = line + "\n";
    node.childNodes.forEach((c) => {
      if (c.nodeType === Node.ELEMENT_NODE) out += describe(c, depth + 1);
      else if (c.nodeType === Node.TEXT_NODE && c.textContent.trim()) {
        out += `${"  ".repeat(depth + 1)}#text "${c.textContent.trim()}"\n`;
      }
    });
    return out;
  }

  root.innerHTML = `
    <label>markup to parse</label>
    <textarea id="parse-input" rows="4" style="width:100%">${(cfg.demo || "").replace(/</g, "&lt;")}</textarea>
    <button id="parse-run">parse</button>
    <h4>resulting DOM tree</h4>
    <pre id="parse-tree" style="background:#eee;padding:10px;overflow:auto"></pre>
    <div id="parse-sandbox" style="border:1px dashed #999;padding:10px;margin-top:8px"></div>
  `;

  function run() {
    const val = document.getElementById("parse-input").value;
    const sandbox = document.getElementById("parse-sandbox");
    sandbox.innerHTML = val; // intentional: live insertion so students can watch node creation/execution
    const tree = describe(sandbox, 0);
    document.getElementById("parse-tree").textContent = tree;
  }
  document.getElementById("parse-run").addEventListener("click", run);
  run();
})();
