import queue
import json
import threading

# Maps sse_uuid (str) → { "queue": Queue, "ip": str }
_sse_clients: dict[str, dict] = {}
_sse_clients_lock = threading.Lock()

def sse_broadcast(event_type: str, data: dict, exclude_id: str = None) -> None:
    """Broadcast to every connected SSE client.

    exclude_id is a sse_uuid to skip (one specific tab).
    """
    frame = f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode("utf-8")
    dead_ids = []

    with _sse_clients_lock:
        for uid, entry in _sse_clients.items():
            if exclude_id and uid == exclude_id:
                continue
            try:
                entry["queue"].put_nowait(frame)
            except queue.Full:
                dead_ids.append(uid)
    if dead_ids:
        with _sse_clients_lock:
            for uid in dead_ids:
                _sse_clients.pop(uid, None)

def sse_send_to(client_id: str, event_type: str, data: dict) -> bool:
    """Send to the SSE queue identified by sse_uuid (client_id).

    client_id is now a UUID string assigned per browser tab.
    Returns True if the queue accepted the frame.
    """
    frame = f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode("utf-8")
    delivered = False
    dead_ids  = []

    with _sse_clients_lock:
        entry = _sse_clients.get(client_id)
        if entry:
            try:
                entry["queue"].put_nowait(frame)
                delivered = True
            except queue.Full:
                dead_ids.append(client_id)

    if dead_ids:
        with _sse_clients_lock:
            for uid in dead_ids:
                _sse_clients.pop(uid, None)

    return delivered