import math
from typing import Any, Dict, Tuple

# ---------- core compute ----------
def calculate_outcome(data) -> dict:
    sample = data["sample"]
    target = data["target"]
    settings = data["settings"]

    # 0) Derived: fringe multiplier from folding
    # fringe_multiplier = 2 if sample["folded"] else 1

    # 1) Rope consumption ratio (knotting-only)
    #    Remove non-scaling parts (attachment + fringe ends) from measured sample rope.
    .
    rope_consumption_ratio = (
        (sample["rope_used"] - sample["attached_length"])
        / sample["k_length"]
    )

    # 2) Sample density (width per rope)
    sample_density = sample["width"] / sample["ropes"]

    # 3) Determine number of ropes and resulting width
    target.get("num_ropes"):
    actual_ropes = int(target["num_ropes"])
    actual_width = actual_ropes * sample_density


    # 3a) target fringe length = sample fringe length
    target["fringe_length"] = sample["fringe_length"]
    
    # 3b) target attached length = sample attached length
    target["attached_length"] = sample["attached_length"]
    
    # 4) Knotting length for target (vertical)
    #    Subtract attachment and ONE fringe length from total vertical length.
    target_k_length = target["total_length"] - target["fringe_length"]

    # 5) Convert knotting length to rope used by knots using the sample ratio
    base_rope_for_knotting = target_k_length * rope_consumption_ratio

    # 6) Per-cord rope: attachment (once) + knots + bottom fringe per end
    total_rope_per_cord = (
        target["attached_length"] + base_rope_for_knotting * target["fringe_length"]
    )

    # 7) Safety margin
    safety_multiplier = 1 + (settings["safety_margin"] / 100.0)
    final_rope_length = total_rope_per_cord * safety_multiplier

    # 8) Totals + conversions
    total_rope_needed = final_rope_length * actual_ropes
    attachment_points = actual_ropes * 2 #ropes are folded

    uom = settings["uom"]
    if uom == "cm":
        uom_converted = "m"
        total_rope_converted = round(total_rope_needed / 100.0, 2)
    else:  # assume inches
        uom_converted = "ft"
        total_rope_converted = round(total_rope_needed / 12.0, 2)

    return {
        "number_of_ropes": int(actual_ropes),
        "length_per_rope": round(final_rope_length, 1),
        "total_rope_length": round(total_rope_needed, 1),
        "total_rope_converted": total_rope_converted,
        "actual_width": round(actual_width, 1),
        "attachment_points": int(attachment_points),
        "uom": uom,
        "uom_converted": uom_converted,
        "calculation_breakdown": {
            "rope_consumption_ratio": round(rope_consumption_ratio, 2),
            "sample_density": round(sample_density, 2),
            "target_k_length": round(target_k_length, 1),
            "input_method": "direct_ropes" if target.get("num_ropes") else "min_width",
        },
    }

# ---------- helpers for Framer binding .---------
INPUT_SCHEMA = [
    # section, key, type, required, hint
    ("sample", "k_length", "number", True, "Knotting length of the sample"),
    ("sample", "rope_used", "number", True, "Total rope used in sample (includes attachment + fringes)"),
    ("sample", "width", "number", True, "Sample width"),
    ("sample", "ropes", "integer", True, "Number of cords used in sample"),
    ("sample", "attached_length", "number", True, "Attachment length included in sample.rope_used"),
    ("sample", "fringe_length", "number", True, "Fringe length per rope end included in sample.rope_used"),
    ("target", "total_length", "number", True, "Final total length"), 
    ("target", "min_width", "number", False, "Min width (ignored if num_ropes provided)"),
    ("target", "num_ropes", "integer", False, "Explicit rope count (overrides min_width)"),
    ("target", "rope_multiplier", "integer", False, "Rope count must be a multiple of this"),
]

OUTPUT_SCHEMA = [
    ("number_of_ropes", "integer", "Calculated total ropes"),
    ("length_per_rope", "number", "Per-rope length (in input unit)"),
    ("total_rope_length", "number", "Total rope length (in input unit)"),
    ("total_rope_converted", "number", "Total rope in converted unit"),
    ("actual_width", "number", "Calculated width (in input unit)"),
    ("attachment_points", "integer", "Attachment points needed"),
    ("uom", "string", "Input unit"),
    ("uom_converted", "string", "Converted unit"),
    ("calculation_breakdown.rope_consumption_ratio", "number", "Rope/knotting ratio from sample (attachment/fringes removed)"),
    ("calculation_breakdown.sample_density", "number", "Width per rope in sample"),
    ("calculation_breakdown.target_k_length", "number", "Knotting length for target (vertical)"),
    ("calculation_breakdown.input_method", "string", "Which targeting method used"),
]

def _denest_params(params: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Allow either nested dicts or flat keys like 'sample.k_length'."""
    if all(isinstance(v, dict) for v in params.values() if v is not None):
        return params
    sample = {}
    target = {}
    settings = {}
    for k, v in params.items():
        if "." in k:
            section, key = k.split(".", 1)
            if section == "sample":
                sample[key] = v
            elif section == "target":
                target[key] = v
            elif section == "settings":
                settings[key] = v
    return {"sample": sample, "target": target, "settings": settings}

def _validate(data: Dict[str, Dict[str, Any]]) -> Tuple[bool, str]:
    # required sections
    for sec in ("sample", "target", "settings"):
        if sec not in data or not isinstance(data[sec], dict):
            return False, f"Missing or invalid section: {sec}"

    # required fields
    required = [(s, k) for (s, k, _t, req, _h) in INPUT_SCHEMA if req]
    for s, k in required:
        if data[s].get(k) in (None, ""):
            return False, f"Missing required field: {s}.{k}"

    # unit & types (light)
    if data["settings"].get("uom") not in ("cm", "in"):
        return False, "settings.uom must be 'cm' or 'in'"

    # numeric sanity (examples)
    try:
        if float(data["sample"]["k_length"]) <= 0:
            return False, "sample.k_length must be > 0"
        if int(data["sample"]["ropes"]) <= 0:
            return False, "sample.ropes must be > 0"
        if int(data["target"]["rope_multiplier"]) <= 0:
            return False, "target.rope_multiplier must be > 0"
    except Exception:
        return False, "Numeric fields must be valid numbers"

    return True, ""

def run(params: dict) -> dict:
    """
    Modes:
      - mode='schema'  -> returns input/output descriptors for Framer wiring
      - mode='compute' -> (default) compute result from provided params
    Accepts nested dicts or flat keys like 'sample.k_length'.
    """
    mode = params.get("mode", "compute")

    if mode == "schema":
        return {
            "ok": True,
            "mode": "schema",
            "inputs": [
                {
                    "id": f"{sec}.{key}",
                    "section": sec,
                    "key": key,
                    "type": typ,
                    "required": req,
                    "hint": hint,
                }
                for (sec, key, typ, req, hint) in INPUT_SCHEMA
            ] + [
                {"id": "settings.safety_margin", "section": "settings", "key": "safety_margin", "type": "number", "required": True, "hint": "Safety margin in %"},
                {"id": "settings.uom", "section": "settings", "key": "uom", "type": "select", "required": True, "hint": "cm or in", "options": ["cm", "in"]},
            ],
            "outputs": [
                {"id": field, "type": typ, "hint": hint}
                for (field, typ, hint) in OUTPUT_SCHEMA
            ],
        }

    # compute mode
    data = _denest_params(params)
    ok, msg = _validate(data)
    if not ok:
        return {"ok": False, "error": msg}

    try:
        result = calculate_outcome(data)
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": f"Computation failed: {e}"}
