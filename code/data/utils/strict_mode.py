import threading

STRICT_MODE       = False
_strict_mode_lock = threading.Lock()

_strict_pending:      dict = {}
_strict_pending_lock        = threading.Lock()

STRICT_RAM_LIMIT = 50 * 1024 * 1024   # 50 MB

def get_strict_mode() -> bool:
    with _strict_mode_lock:
        return STRICT_MODE

def set_strict_mode(value: bool) -> bool:
    """Set strict mode; returns the new value."""
    global STRICT_MODE
    with _strict_mode_lock:
        STRICT_MODE = value
        return STRICT_MODE

def add_to_strict_queue(uid: str, entry: dict) -> None:
    with _strict_pending_lock:
        _strict_pending[uid] = entry

def remove_from_strict_queue(uid: str) -> None:
    with _strict_pending_lock:
        _strict_pending.pop(uid, None)

def get_strict_queue_snapshot() -> list[dict]:
    with _strict_pending_lock:
        return [
            {
                "id":             uid,
                "filename":       entry["filename"],
                "size":           entry["size"],
                "content_type":   entry["content_type"],
                "uploader_ip":    entry["uploader_ip"],
                "uploader_label": entry["uploader_label"],
                "queued_at":      entry["queued_at"],
                "has_buffer":     entry["buffer"] is not None,
            }
            for uid, entry in _strict_pending.items()
        ]

def get_strict_entry(uid: str) -> dict | None:
    with _strict_pending_lock:
        return _strict_pending.get(uid)