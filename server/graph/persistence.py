"""Flat-file session checkpointing -- lets a room that was idle-disconnected
(see agent/worker.py's away-timeout handling) be resumed later with the
student's actual progress intact, without standing up a database. Matches
the project's "$0, local, no accounts" scope: one small JSON file per room
under `_CHECKPOINT_DIR`, nothing else.

Not a general persistence layer -- state is only ever written right before an
intentional idle-disconnect and read back once, at the start of a session
for a room that has a matching file. A session that ends normally (COMPLETE,
or an explicit disconnect while still active) does not write a checkpoint.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from graph.schemas import ApproachGrade, ComprehensionGrade
from graph.state import TutorState

logger = logging.getLogger("graph.persistence")

_CHECKPOINT_DIR = Path(__file__).resolve().parents[1] / ".sessions"

# A checkpoint this old is treated as abandoned rather than resumable -- with
# no TTL, a session that's never revisited (the common case) would leave a
# JSON file behind forever. 24h comfortably covers "came back later the same
# day" without silently accumulating stale files indefinitely.
_CHECKPOINT_MAX_AGE_S = 24 * 60 * 60

# TutorState keys whose values are Pydantic models rather than plain
# JSON-safe types -- need explicit model_dump()/model_validate() on the way
# out/in instead of plain json.dumps/loads.
_MODEL_FIELDS: dict[str, type] = {
    "comprehension_result": ComprehensionGrade,
    "brute_force_grade": ApproachGrade,
    "optimal_grade": ApproachGrade,
}


def _checkpoint_path(session_key: str) -> Path:
    # Sanitized for filesystem safety -- see callers (worker.py) for how
    # session_key is composed. Deliberately NOT just the LiveKit room name:
    # this app's room-naming convention makes the room name equal to the bare
    # problem slug (see worker.py's room-naming doc), which is shared by
    # every session on that problem. Keying on that alone means any two
    # sessions on the same problem -- a different visitor, or the same
    # student starting over -- would silently inherit each other's saved
    # progress. Callers must compose a key that also includes something
    # unique to the actual room *instance* (its LiveKit SID), not just its
    # name.
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in session_key)
    return _CHECKPOINT_DIR / f"{safe_name}.json"


def save_checkpoint(session_key: str, state: TutorState) -> None:
    """Best-effort save -- a failure here should never take down the
    disconnect flow that's calling it, just means resumption won't work."""
    try:
        _CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        serializable: dict[str, Any] = {"_saved_at": time.time()}
        for key, value in state.items():
            if key in _MODEL_FIELDS and value is not None:
                serializable[key] = value.model_dump(mode="json")
            else:
                serializable[key] = value
        _checkpoint_path(session_key).write_text(json.dumps(serializable), encoding="utf-8")
    except Exception:
        logger.exception("failed to save session checkpoint for key %r", session_key)


def load_checkpoint(session_key: str) -> TutorState | None:
    """Returns the saved state for this session key, or None if there isn't
    one, it's too old (see `_CHECKPOINT_MAX_AGE_S`), or it fails to load --
    callers should fall back to a fresh `initial_state` rather than
    propagate, since a missing/stale/corrupt checkpoint is recoverable by
    just starting over. A too-old checkpoint is deleted here rather than
    just ignored, so it doesn't linger on disk forever."""
    path = _checkpoint_path(session_key)
    if not path.exists():
        return None

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        saved_at = raw.pop("_saved_at", 0)
        if time.time() - saved_at > _CHECKPOINT_MAX_AGE_S:
            path.unlink(missing_ok=True)
            return None
        for key, model_cls in _MODEL_FIELDS.items():
            if raw.get(key) is not None:
                raw[key] = model_cls.model_validate(raw[key])
        return TutorState(**raw)
    except Exception:
        logger.exception("failed to load session checkpoint for key %r; starting fresh instead", session_key)
        return None


def delete_checkpoint(session_key: str) -> None:
    try:
        _checkpoint_path(session_key).unlink(missing_ok=True)
    except Exception:
        logger.exception("failed to delete session checkpoint for key %r", session_key)
