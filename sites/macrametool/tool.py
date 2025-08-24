import math

def calculate_outcome(data) -> dict:
    """
    Calculate macrame rope requirements based on sample and target specifications.

    Args:
        data (dict): {"sample": {...}, "target": {...}, "settings": {...}}

    Returns:
        dict: Calculation results
    """
    sample = data["sample"]
    target = data["target"]
    settings = data["settings"]

    # 1) Rope consumption ratio (rope length used per knotting length)
    rope_consumption_ratio = sample["rope_used"] / sample["k_length"]

    # 2) Sample density (width per rope)
    sample_density = sample["width"] / sample["ropes"]

    # 3) Determine number of ropes
    if target.get("num_ropes"):
        actual_ropes = int(target["num_ropes"])
        actual_width = actual_ropes * sample_density
    else:
        ropes_for_minimum = target["min_width"] / sample_density
        required_multiplier_units = math.ceil(ropes_for_minimum / target["rope_multiplier"])
        actual_ropes = int(required_multiplier_units * target["rope_multiplier"])
        actual_width = actual_ropes * sample_density

    # 4) Rope length per cord
    target_k_length = target["total_length"] - target["attached_length"] - target["fringe_length"]
    base_rope_for_knotting = target_k_length * rope_consumption_ratio
    total_rope_per_cord = target["attached_length"] + base_rope_for_knotting + target["fringe_length"]

    # 5) Safety margin
    safety_multiplier = 1 + (settings["safety_margin"] / 100.0)
    final_rope_length = total_rope_per_cord * safety_multiplier

    # 6) Totals + conversions
    total_rope_needed = final_rope_length * actual_ropes
    attachment_points = actual_ropes * (2 if sample["folded"] else 1)

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

# Optional local test (won't run inside n8n exec):
if __name__ == "__main__":
    test_data = {
        "sample": {"k_length": 10, "rope_used": 60, "width": 10, "ropes": 4, "folded": True},
        "target": {"total_length": 30, "attached_length": 2, "fringe_length": 5, "min_width": 22, "num_ropes": None, "rope_multiplier": 4},
        "settings": {"safety_margin": 15, "uom": "cm"},
    }
    
def run(params: dict) -> dict:
    """
    Standard interface for the backend.
    - Receives params from Framer as a dict.
    - Returns a JSON-serializable dict.
    """
    return calculate_outcome(params)
