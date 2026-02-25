"""Thread-safe progress tracking for GalTransl project translation."""

from copy import deepcopy
from datetime import datetime
from threading import RLock


VALID_PHASES = {
    "idle",
    "preparing",
    "running",
    "applying_results",
    "completed",
    "failed",
}


def _timestamp_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class GalTranslProgressTracker:
    """In-memory progress state for one active GalTransl session."""

    def __init__(self):
        self._lock = RLock()
        self._state = self._initial_state()

    def _initial_state(self):
        return {
            "active": False,
            "phase": "idle",
            "completedCount": 0,
            "totalCount": 0,
            "currentFile": "",
            "error": "",
            "projectPath": "",
            "startedAt": "",
            "updatedAt": _timestamp_now(),
            "finishedAt": "",
        }

    def snapshot(self):
        with self._lock:
            return deepcopy(self._state)

    def try_start(self, project_path):
        with self._lock:
            if self._state["active"]:
                return False
            self._state = self._initial_state()
            now = _timestamp_now()
            self._state.update(
                {
                    "active": True,
                    "phase": "preparing",
                    "projectPath": str(project_path or ""),
                    "startedAt": now,
                    "updatedAt": now,
                }
            )
            return True

    def reset(self):
        with self._lock:
            self._state = self._initial_state()

    def update(self, payload=None, **kwargs):
        updates = {}
        if isinstance(payload, dict):
            updates.update(payload)
        updates.update(kwargs)
        if not updates:
            return self.snapshot()

        with self._lock:
            phase = updates.get("phase")
            if phase is not None:
                phase = str(phase).strip().lower()
                if phase in VALID_PHASES:
                    updates["phase"] = phase
                else:
                    updates.pop("phase", None)

            for key in ("completedCount", "totalCount"):
                if key not in updates:
                    continue
                try:
                    updates[key] = max(0, int(updates[key]))
                except (TypeError, ValueError):
                    updates.pop(key, None)

            if "currentFile" in updates:
                updates["currentFile"] = str(updates["currentFile"] or "")

            if "error" in updates:
                updates["error"] = str(updates["error"] or "")

            self._state.update(updates)
            if (
                "totalCount" in updates
                and self._state["totalCount"] > 0
                and self._state["completedCount"] > self._state["totalCount"]
            ):
                self._state["completedCount"] = self._state["totalCount"]
            self._state["updatedAt"] = _timestamp_now()
            return deepcopy(self._state)

    def complete(self, force_total=None):
        with self._lock:
            if force_total is not None:
                try:
                    force_total = max(0, int(force_total))
                except (TypeError, ValueError):
                    force_total = None

            total = self._state["totalCount"]
            if force_total is not None:
                total = max(total, force_total)

            completed = self._state["completedCount"]
            if total > 0:
                completed = max(completed, total)

            now = _timestamp_now()
            self._state.update(
                {
                    "active": False,
                    "phase": "completed",
                    "completedCount": completed,
                    "totalCount": total,
                    "error": "",
                    "finishedAt": now,
                    "updatedAt": now,
                }
            )
            return deepcopy(self._state)

    def fail(self, error_msg):
        with self._lock:
            now = _timestamp_now()
            self._state.update(
                {
                    "active": False,
                    "phase": "failed",
                    "error": str(error_msg or "unknown error"),
                    "finishedAt": now,
                    "updatedAt": now,
                }
            )
            return deepcopy(self._state)
