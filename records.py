"""Personal bests for BOUNCE BACK, stored in best.json next to the game.

Keys: "solo" / "versus" best single-player score, and "best_bank", the
longest single-bullet bank chain ever landed. A missing or unreadable
file just means "no records yet".
"""

import json
import os

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "best.json")


def _load():
    try:
        with open(_PATH) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def _write(data):
    try:
        with open(_PATH, "w") as f:
            json.dump(data, f)
    except OSError:
        pass


def best_score(mode):
    return int(_load().get(mode, 0))


def save_score(mode, score):
    """Store the mode's best score if beaten. True when a new record."""
    data = _load()
    if score > int(data.get(mode, 0)):
        data[mode] = score
        _write(data)
        return True
    return False


def best_bank():
    return int(_load().get("best_bank", 0))


def save_bank(bounces):
    """Store the lifetime longest-bank record if beaten. True when new."""
    data = _load()
    if bounces > int(data.get("best_bank", 0)):
        data["best_bank"] = bounces
        _write(data)
        return True
    return False
