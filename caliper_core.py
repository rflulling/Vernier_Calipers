import json
import math
import os
from pathlib import Path


INCH_TO_MM = 25.4
PLACES = ("1", "0.1", "0.01", "0.001", "0.0001")
TOOLS = ("Inner", "Outer")
DEFAULT_TOOL_SETTINGS = {
    "offset_in": 0.0,
    "offset_mm": 0.0,
    "scale_position": "not_reached",
    "jaw_fit": "gap",
}


def default_settings():
    return {tool: DEFAULT_TOOL_SETTINGS.copy() for tool in TOOLS}


def settings_path():
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "VernierCalipers" / "settings.json"


def load_settings(path):
    settings = default_settings()
    try:
        with Path(path).open(encoding="utf-8") as settings_file:
            saved = json.load(settings_file)
    except (OSError, ValueError, TypeError):
        return settings

    for tool in TOOLS:
        values = saved.get(tool, {}) if isinstance(saved, dict) else {}
        if not isinstance(values, dict):
            continue
        for key in ("offset_in", "offset_mm"):
            try:
                number = float(values.get(key, settings[tool][key]))
                if math.isfinite(number):
                    settings[tool][key] = number
            except (TypeError, ValueError):
                pass
        if values.get("scale_position") in ("past_zero", "not_reached"):
            settings[tool]["scale_position"] = values["scale_position"]
        if values.get("jaw_fit") in ("overlap", "gap"):
            settings[tool]["jaw_fit"] = values["jaw_fit"]
    return settings


def save_settings(path, settings):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)


def calculate_reading(values):
    return sum(float(value) * (10 ** -place) for place, value in enumerate(values))


def corrected_reading(value, offset, scale_position, jaw_fit="gap", tool="Outer"):
    direction = -1 if scale_position == "past_zero" else 1
    if tool == "Inner" and jaw_fit == "gap":
        direction *= -1
    return value + direction * offset


def converted_readings(value, unit):
    if unit == "in":
        return value, value * INCH_TO_MM
    return value / INCH_TO_MM, value
