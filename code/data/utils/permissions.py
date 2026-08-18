import threading

user_permissions:      dict = {}
user_permissions_lock        = threading.Lock()

def get_permissions(ip: str, is_host: bool) -> dict:
    """Return the effective permission dict for a client IP."""
    with user_permissions_lock:
        if ip in user_permissions:
            return user_permissions[ip]
    if is_host:
        return {"can_delete": True, "can_rename": True}
    return {"can_delete": False, "can_rename": False}