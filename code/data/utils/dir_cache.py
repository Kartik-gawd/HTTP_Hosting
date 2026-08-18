import os
import threading
import time

_DIR_CACHE: dict = {}
_DIR_CACHE_LOCK  = threading.Lock()
_DIR_CACHE_TTL   = 30

def _cached_listdir(path: str) -> list:
    """Return os.listdir(path), served from an in-process TTL cache."""
    now = time.time()
    with _DIR_CACHE_LOCK:
        entry = _DIR_CACHE.get(path)
        if entry and (now - entry[0]) < _DIR_CACHE_TTL:
            return entry[1]
        result = os.listdir(path)
        _DIR_CACHE[path] = (now, result)
        return result

def _invalidate_dir_cache(path: str = None, broadcast_fn=None, folder_to_serve: str = ".") -> None:
    with _DIR_CACHE_LOCK:
        if path is None:
            _DIR_CACHE.clear()
            affected_url = None
        else:
            _DIR_CACHE.pop(path, None)
            try:
                rel = os.path.relpath(path, folder_to_serve).replace("\\", "/")
                affected_url = "/" if rel == "." else "/" + rel
            except ValueError:
                affected_url = None
    if broadcast_fn:
        broadcast_fn("refresh_files", {
            "path": affected_url,
            "reason": "fs_change",
        })