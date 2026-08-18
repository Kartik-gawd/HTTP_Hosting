"""
Endpoints
---------
GET  /peer.html          → serve the peer chat/transfer UI
POST /p2p/register       → assign a stable peer_id; return JSON
GET  /p2p/peers          → list currently-online peers (JSON array)
POST /p2p/signal         → relay a WebRTC signal to a target client_id

Security
--------
All endpoints require check_access() (subnet lock) — enforced by server.py
BEFORE calling peer.handle_request().  The /p2p/register and /p2p/signal
endpoints additionally enforce a 64 KB body cap.
"""

from __future__ import annotations

import html as _html
import json
import os
import secrets
import threading
import time
from typing import TYPE_CHECKING

#utils
from utils.http_helpers import *

def _json_response(handler, data: dict) -> None:
    send_json(handler, 200, data)
from utils.peer_registry import *

if TYPE_CHECKING:
    pass  # ModernHandler — referenced by type only

# Module-level references (populated by init) 
_g: dict = {}

def _peer_html_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "peer.html")


def init(server_globals: dict) -> None:
    
    global _g
    _g = server_globals
    print("[P2P] Signaling module loaded.")



def _sse_send_to(sse_uuid: str, event_type: str, data: dict) -> bool:
    fn = _g.get("sse_send_to")
    if fn:
        return fn(sse_uuid, event_type, data)
    return False


def _sse_broadcast(event_type: str, data: dict) -> None:
    fn = _g.get("sse_broadcast")
    if fn:
        fn(event_type, data)

# Request handlers (called by handle_request dispatcher) 

def _serve_peer_html(handler) -> None:
    # Serve peer.html
    path = _peer_html_path()
    try:
        with open(path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        handler.send_error(404, "peer.html not found")
        return

    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    # peer.html is loaded in cross-origin iframes; allow embedding from same host
    handler.send_header("X-Frame-Options", "SAMEORIGIN")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(data)

def purge_by_sse_uuid(sse_uuid: str) -> None:
    removed = remove_peers_by_sse_uuid(sse_uuid)
    if removed:
        _sse_broadcast("p2p_peers_update", {"peers": online_peers()})

def _handle_register(handler) -> None:
    """
    POST /p2p/register
    Body: { "name": "Alice", "peer_id": "<optional-existing-id>", "sse_uuid": "<uuid>" }
    Assigns a unique peer_id per browser tab (keyed to sse_uuid)
    """
    raw = read_body(handler)
    if raw is None:
        return

    try:
        body = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        handler.send_error(400, "Invalid JSON")
        return

    ip       = handler.client_address[0]
    sse_uuid = body.get("sse_uuid", "")


    existing_pid = body.get("peer_id", "")
    if existing_pid:
        # Blindly trust the client-supplied peer_id (covers reload races where
        # the old SSE connection was just purged before re-registration).
        peer_id = existing_pid
    else:
        # Each tab gets its own peer_id — no IP-level deduplication.
        peer_id = secrets.token_urlsafe(8)

    raw_name  = body.get("name", f"Device-{peer_id[:4]}")
    safe_name = _html.escape(str(raw_name).strip()[:40]) or f"Device-{peer_id[:4]}"

    register_peer(peer_id, safe_name, sse_uuid, ip)

    _json_response(handler, {"peer_id": peer_id, "name": safe_name})


def _handle_heartbeat(handler) -> None:
    """
    POST /p2p/heartbeat
    Body: { "peer_id": "" }
    Updates last_seen so the peer isn't GC'd while the SSE tab is open
    but the user hasn't sent a signal recently.
    """
    raw = read_body(handler, max_bytes=256)
    if raw is None:
        return
    try:
        body = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        handler.send_error(400, "Invalid JSON")
        return

    pid = body.get("peer_id", "")
    heartbeat_peer(pid)
    _json_response(handler, {"status": "ok"})


def _handle_disconnect(handler) -> None:
    """
    POST /p2p/disconnect
    Body: { "peer_id": "..." }
    Immediately removes the peer from the registry and broadcasts the updated
    presence list to all connected clients.
    """
    raw = read_body(handler, max_bytes=256)
    if raw is None:
        return
    try:
        body = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        handler.send_error(400, "Invalid JSON")
        return

    pid = body.get("peer_id", "")
    removed = remove_peer(pid)

    if removed:
        _sse_broadcast("p2p_peers_update", peers_update_payload())

    _json_response(handler, {"status": "ok"})


def _handle_peers(handler) -> None:
    """
    GET /p2p/peers
    Returns a JSON array of currently-online peers, excluding the requester's tab.
    """
    import urllib.parse as _up
    sse_uuid = _up.parse_qs(_up.urlparse(handler.path).query).get("sse_uuid", [""])[0]
    peers    = online_peers(exclude_sse_uuid=sse_uuid or None)
    _json_response(handler, peers)


def _handle_signal(handler) -> None:
    """
    POST /p2p/signal
    Body: {
        "to":    "<target_peer_id>",
        "from":  "<sender_peer_id>",
        "type":  "offer" | "answer" | "ice" | "decline" | "chat",
        "payload": <SDP object | ICE candidate | string>
    }

    Looks up the target peer's SSE client_id and drops the signal into
    their queue via sse_send_to().  The target's existing /events thread
    immediately writes it to the wire as a  'p2p_signal'  SSE event.
    """
    raw = read_body(handler)
    if raw is None:
        return

    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        handler.send_error(400, "Invalid JSON")
        return

    target_pid  = body.get("to", "")
    sender_pid  = body.get("from", "")
    sig_type    = body.get("type", "")
    sig_payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}

    if not target_pid:
        handler.send_error(400, "Missing 'to' field")
        return

    with p2p_peers_lock:
        target_info = p2p_peers.get(target_pid)
        sender_info = p2p_peers.get(sender_pid, {})

    if target_info is None:
        handler.send_error(404, f"Peer '{target_pid}' not registered")
        return

    target_sse_uuid = target_info["sse_uuid"]

    # Stamp the sender's display name so the receiver can show it without
    # a second lookup.
    payload = dict(body)
    payload["from_name"] = sender_info.get("name", sender_pid)

    ok = _sse_send_to(target_sse_uuid, "p2p_signal", payload)
    if ok:
        _json_response(handler, {"status": "delivered"})
    else:
        # Target's SSE queue is gone — peer disconnected.
        remove_peer(target_pid)
        _sse_broadcast("p2p_peers_update", peers_update_payload())
        handler.send_error(404, f"Peer '{target_pid}' SSE queue not found (disconnected?)")


# ── Main dispatcher (called from server.py do_GET / do_POST) 

def handle_request(handler) -> bool:
    """
    Inspect the handler's path and method; dispatch to the correct sub-handler.
    Returns True if the request was handled (so server.py can return early).
    Returns False if this module doesn't own the path.

    server.py should call this AFTER its own auth/rate-limit checks.
    """
    import urllib.parse
    parsed = urllib.parse.urlparse(handler.path)
    path   = parsed.path
    method = handler.command

    # ── Serve peer.html 
    if path == "/peer.html" and method == "GET":
        _serve_peer_html(handler)
        return True

    # ── P2P API routes 
    if not path.startswith("/p2p/"):
        return False

    if path == "/p2p/peers" and method == "GET":
        _handle_peers(handler)
        return True

    if path == "/p2p/disconnect" and method == "POST":
        _handle_disconnect(handler)
        return True

    if path == "/p2p/register" and method == "POST":
        _handle_register(handler)
        return True

    if path == "/p2p/heartbeat" and method == "POST":
        _handle_heartbeat(handler)
        return True

    if path == "/p2p/signal" and method == "POST":
        _handle_signal(handler)
        return True

    # Unknown /p2p/ sub-path
    handler.send_error(404, "Unknown P2P endpoint")
    return True
