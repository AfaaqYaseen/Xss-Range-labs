(function () {
  const cfg = window.LAB_CONFIG || {};
  const params = new URLSearchParams(location.search);

  const isVHtml = cfg.pattern === "vhtml" || cfg.pattern === "sanitizer" || cfg.pattern === "router";
  const template = isVHtml
    ? `<div>
         <p>rendered with v-html from ?html=</p>
         <div v-html="raw"></div>
       </div>`
    : `<div>
         <p>rendered with mustache interpolation from ?name= (Vue escapes this):</p>
         <div class="reflect">hello, {{ name }}</div>
       </div>`;

  const app = Vue.createApp({
    template,
    data() {
      return {
        name: params.get("name") || (cfg.defaults && cfg.defaults.name) || "guest",
        raw: params.get("html") || "<i>try ?html=&lt;img src=x onerror=alert(1)&gt;</i>",
      };
    },
  });
  app.mount("#lab-root");
})();
