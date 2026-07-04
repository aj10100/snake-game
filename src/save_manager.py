"""persistent high scores and run history (JSON)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.scoring import RunStats, Session

MAX_HISTORY = 10
SAVE_PATH = Path(__file__).resolve().parent.parent / "data" / "save.json"


def default_save() -> dict[str, Any]:
    return {
        "high_score": 0,
        "history": [],
    }


def _validate_save(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("Save root must be an object")
    if "high_score" not in data or "history" not in data:
        raise ValueError("Save missing required keys")
    if not isinstance(data["high_score"], int):
        raise ValueError("high_score must be an integer")
    if not isinstance(data["history"], list):
        raise ValueError("history must be an array")
    return data


def load_save() -> dict[str, Any]:
    try:
        if not SAVE_PATH.exists():
            data = default_save()
            write_save(data)
            return data

        raw = SAVE_PATH.read_text(encoding="utf-8")
        data = _validate_save(json.loads(raw))
        return data
    except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
        print(f"[SAVE] Could not load save file ({exc}); creating fresh default.")
        data = default_save()
        write_save(data)
        return data


def write_save(data: dict[str, Any]) -> None:
    SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SAVE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def record_run(
    data: dict[str, Any],
    session: Session,
    run_stats: RunStats,
    now_ms: int,
) -> bool:

    entry = {
        "score": run_stats.score,
        "session_id": session.session_id,
        "survival_seconds": round(run_stats.survival_seconds(now_ms), 1),
        "death_cause": run_stats.death_cause,
    }

    history: list[dict[str, Any]] = data.get("history", [])
    history.insert(0, entry)
    data["history"] = history[:MAX_HISTORY]

    new_record = run_stats.score > data.get("high_score", 0)
    if new_record:
        data["high_score"] = run_stats.score

    write_save(data)
    return new_record


def get_high_score(data: dict[str, Any]) -> int:
    return int(data.get("high_score", 0))


def reset_all_save(data: dict[str, Any]) -> None:
    fresh = default_save()
    data.clear()
    data.update(fresh)
    write_save(data)
    print("[SAVE] All session data reset.")
