(function () {
  const cfg = window.LAB_CONFIG || {};
  const root = document.getElementById("lab-root");
  const params = new URLSearchParams(location.search);
  const e = React.createElement;

  function App() {
    if (cfg.pattern === "dangerous" || cfg.pattern === "dangerous_url") {
      const html = params.get("html") || "<i>try ?html=&lt;img src=x onerror=alert(1)&gt;</i>";
      return e("div", null,
        e("p", null, "rendered with dangerouslySetInnerHTML from ?html="),
        e("div", { dangerouslySetInnerHTML: { __html: html } })
      );
    }
    if (cfg.pattern === "props") {
      const title = params.get("title") || "default title";
      // props still flow through a dangerouslySetInnerHTML sink somewhere downstream
      return e("div", { dangerouslySetInnerHTML: { __html: `<h3>${title}</h3>` } });
    }
    // default / "escaping": React escapes text children automatically.
    const name = params.get("name") || (cfg.defaults && cfg.defaults.name) || "guest";
    return e("div", null,
      e("p", null, "rendered as a normal text child from ?name= (React escapes this):"),
      e("div", { className: "reflect" }, "hello, ", name)
    );
  }

  ReactDOM.render(e(App), root);
})();
