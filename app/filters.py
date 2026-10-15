import re


def apply_filter(cfg: dict, value: str) -> str:
    """Applies a single-pass, non-recursive filter -- the classic mistake
    that makes 'scr<script>ipt' style bypasses possible, since removing
    'script' once does not re-scan the result."""
    if not cfg or cfg.get("type") in (None, "none"):
        return value

    ftype = cfg["type"]

    if ftype == "keyword":
        out = value
        for kw in cfg.get("blocked", []):
            out = re.sub(re.escape(kw), "", out, flags=re.IGNORECASE)
        return out

    if ftype == "character":
        out = value
        for ch in cfg.get("blocked", []):
            out = out.replace(ch, "")
        return out

    if ftype == "regex":
        pattern = cfg.get("pattern", "")
        return re.sub(pattern, "", value)

    if ftype == "denylist":
        out = value
        for pattern in cfg.get("patterns", []):
            out = re.sub(pattern, "", out)
        return out

    if ftype == "waf_like":
        out = value
        for kw in cfg.get("blocked_keywords", []):
            out = re.sub(re.escape(kw), "", out, flags=re.IGNORECASE)
        for ch in cfg.get("blocked_chars", []):
            out = out.replace(ch, "")
        pattern = cfg.get("pattern")
        if pattern:
            out = re.sub(pattern, "", out)
        return out

    return value
