import datetime
import ipaddress
import json
import os
import threading

from utils.strict_mode import get_strict_mode, set_strict_mode

admin_config_lock = threading.Lock()

ALLOWED_NETWORKS: list = []
BANNED_IPS: set        = set()
admin_notes: dict     = {}

# Snapshot of the allowlist taken when the kill switch is activated, so the
# subnets can be restored later. Persisted in admin_config.json.
previous_networks: list = []

# Remember where the config file lives so write_admin_config() can be called
# without an argument from the admin handlers.
_CONFIG_PATH: str = ""

def _config_path(base_file: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(base_file)), "admin_config.json")

def load_admin_config(base_file: str, admin_password: str) -> bytes:
    """
    Populates ALLOWED_NETWORKS, BANNED_IPS, admin_notes.
    Returns the SHA-256 hash of admin_password for the caller to store.
    """
    global ALLOWED_NETWORKS, BANNED_IPS, admin_notes, previous_networks, _CONFIG_PATH
    import hashlib
    password_hash = hashlib.sha256(admin_password.encode()).digest()

    _CONFIG_PATH = _config_path(base_file)
    cfg_path = _CONFIG_PATH
    if not os.path.exists(cfg_path):
        # Mutate in place (not reassign) so modules that did
        # `from utils.admin_config import *` keep pointing at the same objects.
        ALLOWED_NETWORKS.clear()
        ALLOWED_NETWORKS.extend([
            ipaddress.ip_network("192.168.0.0/16"),
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
        ])
        BANNED_IPS.clear()
        admin_notes.clear()
        write_admin_config(base_file)
        return password_hash

    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        ALLOWED_NETWORKS.clear()
        for net_str in cfg.get("allowed_networks", []):
            try:
                ALLOWED_NETWORKS.append(ipaddress.ip_network(net_str, strict=False))
            except ValueError:
                print(f"[Admin] Warning: invalid network in config: {net_str!r}")
        BANNED_IPS.clear()
        BANNED_IPS.update(cfg.get("banned_ips", []))
        admin_notes.clear()
        admin_notes.update(cfg.get("notes", {}))
        previous_networks.clear()
        for net_str in cfg.get("previous_networks", []):
            try:
                previous_networks.append(ipaddress.ip_network(net_str, strict=False))
            except ValueError:
                print(f"[Admin] Warning: invalid previous network in config: {net_str!r}")
        # Restore the persisted strict-mode state.
        set_strict_mode(bool(cfg.get("strict_mode", False)))
        print(f"[Admin] Config loaded: {len(ALLOWED_NETWORKS)} networks, "
              f"{len(BANNED_IPS)} banned IPs, "
              f"strict_mode={get_strict_mode()}.")
    except Exception as e:
        print(f"[Admin] Config load error: {e} — using defaults.")

    return password_hash

def write_admin_config(base_file: str = "") -> None:
    with admin_config_lock:
        cfg = {
            "version": 1,
            "last_modified": datetime.datetime.utcnow().isoformat() + "Z",
            "allowed_networks": [str(n) for n in ALLOWED_NETWORKS],
            "banned_ips": sorted(BANNED_IPS),
            "notes": admin_notes,
            "strict_mode": get_strict_mode(),
            "previous_networks": [str(n) for n in previous_networks],
        }
        # If no base_file was supplied, fall back to the path recorded by
        # load_admin_config(). This lets admin handlers call
        # write_admin_config() with no arguments.
        cfg_path = _config_path(base_file) if base_file else _CONFIG_PATH
        if not cfg_path:
            raise RuntimeError("write_admin_config() called before load_admin_config()")
        tmp_path = cfg_path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
            os.replace(tmp_path, cfg_path)
        except Exception as e:
            print(f"[Admin] Config write error: {e}")
            raise