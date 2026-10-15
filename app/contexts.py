"""
Renders a value, RAW/unescaped on purpose, into one of several HTML/JS
"contexts". This is the deliberately-vulnerable half of the range: labs
choose a context, an optional filter, and whether output encoding is
applied; this module never adds encoding of its own.
"""

CONTEXTS = (
    "html_text", "quoted_attribute", "unquoted_attribute", "event_handler",
    "javascript_string", "javascript_template", "url", "comment",
    "textarea", "title", "svg", "mathml",
)


def render_context(context: str, value: str) -> str:
    value = value or ""
    if context == "html_text":
        return f"<div class='reflect'>{value}</div>"
    if context == "quoted_attribute":
        return f"<input type='text' value=\"{value}\" class='reflect-attr'>"
    if context == "unquoted_attribute":
        return f"<div data-note={value} class='reflect-attr'>note</div>"
    if context == "event_handler":
        return f"<button onclick=\"handle('{value}')\">go</button>"
    if context == "javascript_string":
        return f"<script>var name = '{value}';</script>"
    if context == "javascript_template":
        return f"<script>var msg = `hello {value}`;</script>"
    if context == "url":
        return f"<a href=\"{value}\">continue</a>"
    if context == "comment":
        return f"<!-- feedback: {value} -->"
    if context == "textarea":
        return f"<textarea>{value}</textarea>"
    if context == "title":
        return f"<svg><title>{value}</title></svg>"
    if context == "svg":
        return f"<svg>{value}</svg>"
    if context == "mathml":
        return f"<math>{value}</math>"
    return f"<div class='reflect'>{value}</div>"
