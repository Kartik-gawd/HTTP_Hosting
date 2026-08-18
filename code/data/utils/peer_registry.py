import threading
import time

p2p_peers:      dict[str, dict] = {}
p2p_peers_lock                   = threading.Lock()
P2P_PEER_TIMEOUT                  = 45

def gc_stale_peers() -> None:
    now = time.time()
    with p2p_peers_lock:
        stale = [
            pid for pid, info in p2p_peers.items()
            if now - info["last_seen"] > P2P_PEER_TIMEOUT
        ]
        for pid in stale:
            p2p_peers.pop(pid, None)

def online_peers(exclude_sse_uuid: str | None = None) -> list[dict]:
    gc_stale_peers()
    now = time.time()
    with p2p_peers_lock:
        return [
            {k: v for k, v in info.items() if k != "sse_uuid"}
            for info in p2p_peers.values()
            if now - info["last_seen"] <= P2P_PEER_TIMEOUT
            and info.get("sse_uuid") != exclude_sse_uuid
        ]

def peers_update_payload() -> dict:
    return {"peers": online_peers()}

def register_peer(peer_id: str, name: str, sse_uuid: str, ip: str) -> None:
    with p2p_peers_lock:
        p2p_peers[peer_id] = {
            "peer_id":   peer_id,
            "name":      name,
            "sse_uuid":  sse_uuid,
            "ip":        ip,
            "last_seen": time.time(),
        }

def heartbeat_peer(peer_id: str) -> None:
    with p2p_peers_lock:
        if peer_id in p2p_peers:
            p2p_peers[peer_id]["last_seen"] = time.time()

def remove_peer(peer_id: str) -> bool:
    with p2p_peers_lock:
        return p2p_peers.pop(peer_id, None) is not None

def remove_peers_by_sse_uuid(sse_uuid: str) -> bool:
    removed = False
    with p2p_peers_lock:
        stale = [pid for pid, info in p2p_peers.items() if info.get("sse_uuid") == sse_uuid]
        for pid in stale:
            p2p_peers.pop(pid, None)
            removed = True
    return removed

def get_peer(peer_id: str) -> dict | None:
    with p2p_peers_lock:
        return p2p_peers.get(peer_id)