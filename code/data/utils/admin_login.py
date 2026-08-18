import json
import urllib.parse
import threading
import time

from utils.admin_auth import (
    ADMIN_SESSION_SECRET, ADMIN_CSRF_TOKEN, _verify_password
)

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Admin Login</title>
  <style>
    :root {
      --bg: #121212;
      --card: rgba(30, 30, 30, 0.7);
      --text: #e0e0e0;
      --text-dim: #888;
      --accent: #bb86fc;
      --glass-border: rgba(255, 255, 255, 0.1);
      --neon-cyan: #00e5ff;
      --neon-red: #ff00aa;
      --font-main: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      --font-mono: "Courier New", Courier, monospace;
      --radius-lg: 16px;
      --radius-md: 12px;
    }

    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: var(--font-main);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
      font-size: 14px;
      line-height: 1.6;
      position: relative;
      overflow: hidden;
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      background: linear-gradient(
          to bottom,
          rgba(255,255,255,0) 0%,
          rgba(255,255,255,0) 50%,
          rgba(0,0,0,0.95) 50%,
          rgba(0,0,0,0.95) 100%
      );
      background-size: 100% 6px;
      pointer-events: none;
      z-index: 0;
      opacity: 0.95;
    }

    body > * { position: relative; z-index: 1; }

    @keyframes subtlePulse {
        0%, 100% { filter: brightness(0.8); }
        50%       { filter: brightness(1.2); }
    }

    .login-card {
      width: 100%;
      max-width: 400px;
      background: var(--card);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-lg);
      backdrop-filter: blur(20px);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
      padding: 40px 36px;
      text-align: center;
    }

    .login-badge {
      width: 56px;
      height: 56px;
      margin: 0 auto 20px;
      background-color: var(--neon-cyan);
      border-radius: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 26px;
      color: #000;
      box-shadow: 0 0 20px rgba(0, 229, 255, 0.5);
      animation: subtlePulse 4s infinite ease-in-out;
    }

    .login-title {
      font-size: 1.4rem;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 4px;
      color: transparent;
      -webkit-text-stroke: 1.5px var(--neon-cyan);
      text-shadow: 0 0 10px rgba(0, 229, 255, 0.4);
      animation: subtlePulse 4s infinite ease-in-out;
      margin-bottom: 6px;
    }

    .login-sub {
      font-size: 0.75rem;
      letter-spacing: 2px;
      color: var(--text-dim);
      text-transform: uppercase;
      margin-bottom: 30px;
    }

    .login-error {
      display: none;
      background: rgba(255, 0, 170, 0.1);
      border: 1px solid rgba(255, 0, 170, 0.35);
      color: var(--neon-red);
      border-radius: var(--radius-md);
      padding: 10px 14px;
      font-size: 0.85rem;
      font-family: var(--font-mono);
      margin-bottom: 18px;
      text-align: left;
    }

    .login-error.show {
      display: block;
    }

    .field-row {
      margin-bottom: 18px;
      text-align: left;
    }

    .field-label {
      display: block;
      font-size: 0.7rem;
      letter-spacing: 2px;
      text-transform: uppercase;
      color: var(--text-dim);
      margin-bottom: 8px;
      font-family: var(--font-mono);
    }

    input[type=password] {
      width: 100%;
      background: rgba(255, 255, 255, 0.08);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius-md);
      color: var(--text);
      font-family: var(--font-mono);
      font-size: 0.95rem;
      padding: 12px 16px;
      outline: none;
      backdrop-filter: blur(10px);
      transition: border-color 0.2s, box-shadow 0.2s;
    }

    input[type=password]:focus {
      border-color: var(--accent);
      box-shadow: 0 0 10px rgba(187, 134, 252, 0.2);
    }

    input[type=password]::placeholder {
      color: var(--text-dim);
    }

    .btn-login {
      width: 100%;
      background: var(--accent);
      color: #000;
      border: none;
      font-family: var(--font-main);
      font-size: 0.9rem;
      font-weight: 700;
      letter-spacing: 2px;
      text-transform: uppercase;
      padding: 12px 16px;
      border-radius: var(--radius-md);
      cursor: pointer;
      transition: all 0.2s ease;
      margin-top: 6px;
    }

    .btn-login:hover {
      background: #cba4fd;
      box-shadow: 0 4px 15px rgba(187, 134, 252, 0.4);
    }

    .btn-login:active {
      transform: scale(0.97);
    }

    .btn-login:disabled {
      background: #555;
      color: #999;
      cursor: not-allowed;
      box-shadow: none;
      transform: none;
    }

    .login-footer {
      margin-top: 24px;
      font-size: 0.7rem;
      letter-spacing: 1px;
      color: var(--text-dim);
      font-family: var(--font-mono);
    }
  </style>
</head>
<body>
  <div class="login-card">
    <div class="login-badge">🔐</div>
    <div class="login-title">ADMIN</div>
    <div class="login-sub">Restricted Access</div>

    <div class="login-error" id="login-error">Incorrect password. Please try again.</div>

    <form method="POST" action="/admin/login" autocomplete="off">
      <div class="field-row">
        <label class="field-label" for="password">Password</label>
        <input type="password" id="password" name="password" placeholder="Enter admin password" required autofocus>
      </div>
      <button type="submit" class="btn-login">Login</button>
    </form>

    <div class="login-footer">UNAUTHORIZED ACCESS IS PROHIBITED</div>
  </div>
</body>
</html>
"""

LOGIN_HTML_BAD = LOGIN_HTML.replace(
    'class="login-error"', 'class="login-error show"'
)

# Rendered whenever the IP is in lockout: disables the password field and
# the submit button so the browser cannot keep sending attempts.
_LOGIN_LOCKED_HTML = LOGIN_HTML.replace(
    '<input type="password" id="password" name="password" '
    'placeholder="Enter admin password" required autofocus>',
    '<input type="password" id="password" name="password" '
    'placeholder="Enter admin password" required autofocus disabled>'
).replace(
    '<button type="submit" class="btn-login">Login</button>',
    '<button type="submit" class="btn-login" disabled>LOCKED</button>'
)

# ── Internal login protection ──────────────────────────────────────────────
# Server-side, per-IP login throttling. The browser cannot bypass this.
# Five failed attempts locks that IP for 15 minutes.
_LOGIN_MAX_TRIES = 5
_LOGIN_LOCKOUT_SECONDS = 15 * 60
_login_lock = threading.Lock()
_login_failures = {}


def _login_client_ip(handler) -> str:
    # Use the socket peer address. Do not trust X-Forwarded-For here because
    # an untrusted client could spoof it and bypass the per-IP counter.
    return str(handler.client_address[0])


def _login_is_locked(ip: str):
    now = time.monotonic()
    with _login_lock:
        state = _login_failures.get(ip)
        if not state:
            return False, 0

        locked_until = state.get("locked_until", 0)
        if locked_until > now:
            return True, max(1, int(locked_until - now))

        # Only prune the entry once a REAL lockout (locked_until > 0) has
        # expired. A locked_until of 0 simply means the IP is still in the
        # counting phase and must NOT be reset here.
        if locked_until:
            _login_failures.pop(ip, None)
        return False, 0


def _login_record_failure(ip: str):
    now = time.monotonic()
    with _login_lock:
        state = _login_failures.get(ip)

        # Start fresh only when there is no entry yet, or when a REAL
        # lockout (locked_until > 0) has already expired. A locked_until
        # of 0 means attempts are still being counted and must be kept —
        # checking "locked_until <= now" here treats 0 as expired and
        # resets the counter to 1 on every single request, which is what
        # made the count appear stuck at "4 attempts remaining".
        if not state or (state.get("locked_until", 0) and state.get("locked_until", 0) <= now):
            state = {"attempts": 0, "locked_until": 0}

        state["attempts"] += 1

        if state["attempts"] >= _LOGIN_MAX_TRIES:
            state["locked_until"] = now + _LOGIN_LOCKOUT_SECONDS

        _login_failures[ip] = state

        remaining = max(0, _LOGIN_MAX_TRIES - state["attempts"])
        return state["attempts"], remaining


def _login_clear_failures(ip: str):
    with _login_lock:
        _login_failures.pop(ip, None)



def handle_admin_login_get(handler) -> None:
    body = LOGIN_HTML.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def handle_admin_login_post(handler) -> None:
    ip = _login_client_ip(handler)

    # Enforce the limit on the server before checking the password.
    locked, seconds_left = _login_is_locked(ip)
    if locked:
        body = _LOGIN_LOCKED_HTML.replace(
            'id="login-error">Incorrect password. Please try again.',
            f'id="login-error" class="login-error show">'
            f'Too many failed attempts. Try again in {seconds_left} seconds.'
        ).encode("utf-8")
        # The replacement above can duplicate the class attribute if the
        # template changes; keep the response valid in either case.
        body_text = body.decode("utf-8").replace(
            'class="login-error" class="login-error show"',
            'class="login-error show"'
        )
        body = body_text.encode("utf-8")

        handler.send_response(429)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Retry-After", str(seconds_left))
        handler.end_headers()
        handler.wfile.write(body)
        print(f"[Admin] Login blocked for {ip}; {seconds_left}s remaining")
        return

    content_length = int(handler.headers.get("Content-Length", 0))
    raw = handler.rfile.read(min(content_length, 512)).decode("utf-8", errors="replace")

    password = ""
    if handler.headers.get("Content-Type", "").startswith("application/json"):
        try:
            parsed = json.loads(raw)
            password = parsed.get("password", "")
            if not isinstance(password, str):
                password = ""
        except Exception:
            pass
    else:
        params = urllib.parse.parse_qs(raw)
        password = params.get("password", [""])[0]

    if _verify_password(password):
        _login_clear_failures(ip)

        handler.send_response(303)
        handler.send_header(
            "Set-Cookie",
            f"admin_session={ADMIN_SESSION_SECRET}; Path=/admin; HttpOnly; SameSite=Strict",
        )
        handler.send_header(
            "Set-Cookie",
            f"admin_csrf={ADMIN_CSRF_TOKEN}; Path=/admin; SameSite=Strict",
        )
        handler.send_header("Location", "/admin")
        handler.end_headers()
        print(f"[Admin] Login successful from {ip}")
        return

    attempts, remaining = _login_record_failure(ip)

    if remaining == 0:
        body = _LOGIN_LOCKED_HTML.replace(
            'class="login-error"',
            'class="login-error show"',
            1
        ).replace(
            "Incorrect password. Please try again.",
            "Too many failed attempts. Login locked for 15 minutes."
        ).encode("utf-8")

        handler.send_response(429)
        handler.send_header("Content-Type", "text/html; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.send_header("Cache-Control", "no-store")
        handler.send_header("Retry-After", str(_LOGIN_LOCKOUT_SECONDS))
        handler.end_headers()
        handler.wfile.write(body)
        print(f"[Admin] Login locked for {ip} after {attempts} failed attempts")
        return

    body = LOGIN_HTML.replace(
        'class="login-error"',
        'class="login-error show"',
        1
    ).replace(
        "Incorrect password. Please try again.",
        f"Incorrect password. {remaining} attempt(s) remaining."
    ).encode("utf-8")

    handler.send_response(401)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)
    print(f"[Admin] Failed login attempt from {ip}; {remaining} attempt(s) remaining")