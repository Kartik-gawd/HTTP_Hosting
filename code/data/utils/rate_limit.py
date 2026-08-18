import time
import threading
from collections import defaultdict

# Rate-limit thresholds live in config.py (RATE_LIMIT_WINDOW, RATE_LIMIT_MAX_REQUESTS).
# Import them here so is_allowed() can reference them without a NameError.
from config import RATE_LIMIT_WINDOW, RATE_LIMIT_MAX_REQUESTS

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock     = threading.Lock()

    def is_allowed(self, ip):
        now = time.time()
        with self.lock:
            self.requests[ip] = [t for t in self.requests[ip] if now - t < RATE_LIMIT_WINDOW]
            if len(self.requests[ip]) >= RATE_LIMIT_MAX_REQUESTS:
                return False
            self.requests[ip].append(now)
            return True

rate_limiter = RateLimiter()
