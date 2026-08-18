import threading
import time

active_users      = {}
active_users_lock = threading.Lock()
user_aliases      = {}
user_aliases_lock = threading.Lock()