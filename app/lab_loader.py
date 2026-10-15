import os
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABS_DIR = os.path.join(ROOT, "labs")

VALID_CATEGORIES = (
    "reflected", "stored", "dom", "parsing", "mxss", "csp",
    "sanitizers", "prototype_pollution", "frameworks", "final",
)

REQUIRED_FIELDS = ("id", "title", "category", "difficulty", "engine", "public")


def load_labs():
    """Returns (labs_dict, errors). labs_dict maps id -> lab config."""
    labs = {}
    errors = []
    seen_ids = set()

    if not os.path.isdir(LABS_DIR):
        return labs, [f"labs directory not found at {LABS_DIR}"]

    for cat in sorted(os.listdir(LABS_DIR)):
        cat_path = os.path.join(LABS_DIR, cat)
        if not os.path.isdir(cat_path):
            continue
        for fname in sorted(os.listdir(cat_path)):
            if not fname.endswith(".yaml"):
                continue
            fpath = os.path.join(cat_path, fname)
            with open(fpath) as f:
                cfg = yaml.safe_load(f)

            for field in REQUIRED_FIELDS:
                if field not in cfg:
                    errors.append(f"{fname}: missing field '{field}'")

            if cfg.get("category") not in VALID_CATEGORIES:
                errors.append(f"{fname}: invalid category '{cfg.get('category')}'")

            lab_id = cfg.get("id")
            if lab_id in seen_ids:
                errors.append(f"{fname}: duplicate id '{lab_id}'")
            else:
                seen_ids.add(lab_id)

            labs[lab_id] = cfg

    return labs, errors


def labs_by_category(labs: dict):
    grouped = {}
    for lab in labs.values():
        grouped.setdefault(lab["category"], []).append(lab)
    for cat in grouped:
        grouped[cat].sort(key=lambda l: l["id"])
    return grouped
