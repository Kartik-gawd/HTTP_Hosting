import mimetypes
import ipaddress

# Configurations:

ALLOWED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/0"), 
]

PORT = 8000
MAX_UPLOAD_MB = 5000

FOLDER_TO_SERVE = "." 

EXCLUDED_EXTENSIONS = {'.lnk', '.ini', '.url', '.db', '.exe', '.parts'}
EXCLUDED_UPLOAD_EXT = {
    '.exe', '.msi', '.dll', '.scr', '.com', '.bat', '.cmd',
    '.vbs', '.ps1', '.js', '.jar', '.sh', '.php', '.py',
    '.lnk', '.url',
    '.docm', '.xlsm', '.pptm', '.ipa', '.iso', '.img', '.vhd',
}

PREVIEWABLE_EXTS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg',
    '.mp4', '.mkv', '.mov', '.avi', '.webm',
    '.mp3', '.wav', '.ogg','.pdf',
    '.txt', '.py', '.js', '.html', '.css', '.cpp', '.c', '.json', '.md', '.log'
}

MEDIA_EXTS = {
    'video': {'.mp4', '.mkv', '.mov', '.avi', '.webm'},
    'audio': {'.mp3', '.wav', '.ogg'},
    'image': {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
}

# Rate Limiting Config 
RATE_LIMIT_MAX_REQUESTS = 80
RATE_LIMIT_WINDOW = 60  # seconds

if not mimetypes.inited:
    mimetypes.init()
mimetypes.add_type('video/mp4', '.mp4')
mimetypes.add_type('video/mp4', '.mkv') 
mimetypes.add_type('video/webm', '.webm')
mimetypes.add_type('text/plain', '.srt')
mimetypes.add_type('text/vtt', '.vtt')