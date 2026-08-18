import mimetypes
from utils.get_ip import *

# Configurations:
ALLOWED_NETWORKS = allowed_networks()

PORT = 8000
MAX_UPLOAD_MB = 5000

ADMIN_PASSWORD = "pswd"

FOLDER_TO_SERVE = "."  # current

EXCLUDED_EXTENSIONS = {'.lnk', '.ini', '.url', '.db', '.exe', '.parts', '.py', '.html', '.env', '.pem'}

EXCLUDED_UPLOAD_EXT = {
    '.exe', '.msi', '.dll', '.scr', '.com', '.bat', '.cmd',
    '.vbs', '.ps1', '.js', '.jar', '.sh', '.php', '.py',
    '.lnk', '.url',
    '.docm', '.xlsm', '.pptm', '.ipa', '.iso', '.img', '.vhd',
}

PREVIEWABLE_EXTS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg',
    '.mp4', '.mkv', '.mov', '.avi', '.webm',
    '.mp3', '.wav', '.ogg', '.pdf',
    '.txt', '.md', '.log'
}

MEDIA_EXTS = {
    'video': {'.mp4', '.mkv', '.mov', '.avi', '.webm'},
    'audio': {'.mp3', '.wav', '.ogg'},
    'image': {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
}

# Rate Limiting Config 
RATE_LIMIT_MAX_REQUESTS = 80
RATE_LIMIT_WINDOW = 60  # seconds

# max devies that can download a zip folder at the same time
MAX_CONCURRENT_ZIPS = 2

if not mimetypes.inited:
    mimetypes.init()

mimetypes.add_type('video/mp4', '.mp4')
mimetypes.add_type('video/x-matroska', '.mkv') 
mimetypes.add_type('video/webm', '.webm')
mimetypes.add_type('text/plain', '.srt')
mimetypes.add_type('text/vtt', '.vtt')