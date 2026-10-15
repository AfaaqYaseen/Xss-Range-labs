import html
import urllib.parse


def apply_transform(name: str, value: str) -> str:
    if name == "html_encode":
        return html.escape(value)
    if name == "url_decode":
        return urllib.parse.unquote(value)
    if name == "url_decode_twice":
        return urllib.parse.unquote(urllib.parse.unquote(value))
    if name == "html_entity_decode":
        return html.unescape(value)
    if name == "lowercase":
        return value.lower()
    return value


def apply_chain(chain, value: str) -> str:
    for name in chain or []:
        value = apply_transform(name, value)
    return value
