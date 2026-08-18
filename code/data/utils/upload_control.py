import ipaddress
import os
import threading
import time

_cancelled_paths:      dict = {}
_cancelled_paths_lock        = threading.Lock()
CANCEL_BLOCK_TTL             = 60

_upload_cooldowns:     dict = {}
_upload_cooldowns_lock       = threading.Lock()
COOLDOWN_SECONDS             = 300

def is_path_cancelled(path: str) -> bool:
    now = time.time()
    with _cancelled_paths_lock:
        expiry = _cancelled_paths.get(path)
        if expiry is None:
            return False
        if now > expiry:
            _cancelled_paths.pop(path, None)
            return False
        return True

def is_ip_on_cooldown(ip: str) -> tuple[bool, int]:
    now = time.time()
    with _upload_cooldowns_lock:
        expiry = _upload_cooldowns.get(ip)
        if expiry is None or now > expiry:
            _upload_cooldowns.pop(ip, None)
            return False, 0
        return True, int(expiry - now)

def set_ip_cooldown(ip: str) -> None:
    with _upload_cooldowns_lock:
        _upload_cooldowns[ip] = time.time() + COOLDOWN_SECONDS

def cancel_upload_path(target_path: str, modern_handler_class=None, sse_broadcast_fn=None) -> None:
    expiry = time.time() + CANCEL_BLOCK_TTL
    with _cancelled_paths_lock:
        _cancelled_paths[target_path] = expiry

    if modern_handler_class is not None:
        locks_meta      = getattr(modern_handler_class, "_chunk_locks", {})
        locks_meta_lock = getattr(modern_handler_class, "_chunk_locks_meta", threading.Lock())
        with locks_meta_lock:
            locks_meta.pop(target_path, None)

    try:
        if os.path.exists(target_path):
            os.remove(target_path)
    except OSError as e:
        print(f"[Admin] Warning: could not delete partial file {target_path}: {e}")

    if sse_broadcast_fn:
        sse_broadcast_fn("admin_cancel_upload", {"filename": os.path.basename(target_path)})