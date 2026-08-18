import os
import threading
import time

def start_stale_lock_sweeper(handler_class) -> threading.Thread:
    """
    Starts and returns a daemon thread that periodically removes orphaned
    chunk-lock entries and their partial files from disk.
    """
    STALE_SECONDS = 120

    def _sweep():
        while True:
            time.sleep(60)
            if not hasattr(handler_class, "_chunk_locks"):
                continue
            try:
                with handler_class._chunk_locks_meta:
                    stale = [
                        path for path, info in handler_class._chunk_locks.items()
                        if (time.time() - info["last_active"] > STALE_SECONDS
                            and not info["lock"].locked())
                    ]
                for path in stale:
                    with handler_class._chunk_locks_meta:
                        info = handler_class._chunk_locks.get(path)
                        if info is None or info["lock"].locked():
                            continue
                        if time.time() - info["last_active"] > STALE_SECONDS:
                            del handler_class._chunk_locks[path]
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                            print(f"[Sweeper] Deleted stale partial upload: {path}")
                    except OSError as e:
                        print(f"[Sweeper] Could not delete {path}: {e}")
            except Exception as e:
                print(f"[Sweeper] Unexpected error: {e}")

    t = threading.Thread(target=_sweep, daemon=True, name="StaleUploadSweeper")
    t.start()
    return t