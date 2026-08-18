import json

def send_json(handler, code: int, data: dict) -> None:
    body = json.dumps(data, indent=2).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)

def send_ok(handler, data: dict) -> None:
    send_json(handler, 200, {"ok": True, **data})

def send_error_json(handler, code: int, message: str) -> None:
    send_json(handler, code, {"ok": False, "error": message})

def send_admin_ok(handler, data: dict) -> None:
    send_json(handler, 200, {"ok": True, **data})

def send_admin_error(handler, code: int, message: str) -> None:
    send_json(handler, code, {"ok": False, "error": message})

def read_body(handler, max_bytes: int = 65_536) -> bytes | None:
    """Read request body up to max_bytes; sends 413 and returns None if exceeded."""
    try:
        length = int(handler.headers.get("Content-Length", 0))
    except (ValueError, TypeError):
        length = 0
    if length > max_bytes:
        handler.send_error(413, "Payload too large")
        return None
    return handler.rfile.read(length)