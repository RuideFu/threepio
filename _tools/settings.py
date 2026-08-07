"""
Tiny persistent settings store for Threepio.

Settings live in a JSON file in the working directory, following the same
convention as dec-cal.txt. Currently the only key is "device"
("dataq" | "rtlsdr"), set from the Mode > Device menu.
"""

import json
import os

SETTINGS_FILE = "threepio-settings.json"


def load_settings() -> dict:
    """Return the persisted settings, or {} if the file is missing/corrupt."""
    try:
        with open(SETTINGS_FILE) as f:
            settings = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    return settings if isinstance(settings, dict) else {}


def save_settings(**changes) -> None:
    """Merge changes into the persisted settings."""
    settings = load_settings()
    settings.update(changes)
    temporary = SETTINGS_FILE + ".tmp"
    with open(temporary, "w") as f:
        json.dump(settings, f, indent=2)
    os.replace(temporary, SETTINGS_FILE)
