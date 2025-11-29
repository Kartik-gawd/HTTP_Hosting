import http.server
import socketserver
import os
import urllib.parse
import html
import sys
import io
import datetime
import socket
from http import HTTPStatus
import segno

# Config
PORT = 8000

# Folder path to host
#. means current folder where this script is in
FOLDER_TO_SERVE = "." 

ALLOWED_IPS = [
    "127.0.0.1",
    "192.168.1.x", #this allows all local ip
]

EXCLUDED_EXTENSIONS = {'.lnk', '.ini', '.url', '.db', '.exe'}

PREVIEWABLE_EXTS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg',
    '.mp4', '.mkv', '.mov', '.avi', '.webm',
    '.mp3', '.wav', '.ogg','.pdf',
    '.txt', '.py', '.js', '.html', '.css', '.cpp', '.c', '.json', '.md', '.log'
}

# Media extensions for embedded players
MEDIA_EXTS = {
    'video': {'.mp4', '.mkv', '.mov', '.avi', '.webm'},
    'audio': {'.mp3', '.wav', '.ogg'},
    'image': {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
}

class ModernHandler(http.server.SimpleHTTPRequestHandler):
    # IP check
    def do_GET(self):
        client_ip = self.client_address[0]
        allowed = False
        if client_ip in ALLOWED_IPS:
            allowed = True
        else:
            # Check .x match
            for ip in ALLOWED_IPS:
                if ip.endswith('.x'):
                    prefix = ip[:-1] 
                    if client_ip.startswith(prefix):
                        allowed = True
                        break
        
        if not allowed:
            print(f"BLOCKED: {client_ip}")
            self.send_error(403, "Forbidden: IP not allowed.")
            return
        
        super().do_GET()
    
    # Upload
    def do_POST(self):
        client_ip = self.client_address[0]
        allowed = False
        for ip in ALLOWED_IPS:
            if ip.endswith('.x'):
                prefix = ip[:-1]
                if client_ip.startswith(prefix):
                    allowed = True
                    break
            elif client_ip == ip:
                allowed = True
                break
        
        if not allowed:
            self.send_error(403, "Forbidden: IP not allowed.")
            return

        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data'):
            self.send_error(400, "Bad Request: Expected multipart form data")
            return
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            form_data = self.rfile.read(content_length)
        
            boundary = content_type.split('boundary=')[1].encode()
            parts = form_data.split(b'--' + boundary)
            
            target_dir = self.translate_path(self.path)
            
            if not os.path.isdir(target_dir):
                target_dir = os.path.dirname(target_dir)

            uploaded_files = []
            for part in parts:
                if b'name="files[]"' in part and b'filename="' in part:
                    filename_start = part.find(b'filename="') + 10
                    filename_end = part.find(b'"', filename_start)
                    filename = part[filename_start:filename_end].decode()
                    
                    file_content_start = part.find(b'\r\n\r\n') + 4
                    file_content_end = part.find(b'\r\n--', file_content_start)
                    if file_content_end == -1:
                        file_content_end = len(part) - 2
                    
                    file_content = part[file_content_start:file_content_end]
                    
                    safe_filename = os.path.basename(filename)
                    if safe_filename and safe_filename not in EXCLUDED_EXTENSIONS:
                        save_path = os.path.join(target_dir, safe_filename)
                        with open(save_path, 'wb') as f:
                            f.write(file_content)
                        uploaded_files.append(safe_filename)
            
            if uploaded_files:
                self.send_response(303)
                self.send_header('Location', self.path)
                self.end_headers()
                return
            else:
                self.send_error(400, "No valid files found in upload")
            
        except Exception as e:
            print(f"Upload error: {e}")
            self.send_error(500, f"Upload failed: {str(e)}")

    def list_directory(self, path):
        try:
            list_dir = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None
        
        # Get sorting parameter
        sort_by = 'name'
        if 'sort=' in self.path:
            try:
                sort_param = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('sort', ['name'])[0]
                if sort_param in ['name', 'size', 'date', 'type']:
                    sort_by = sort_param
            except:
                pass
        
        # Sort files
        file_data = []
        for name in list_dir:
            fullname = os.path.join(path, name)
            is_dir = os.path.isdir(fullname)
            size = 0
            mtime = 0
            file_type = 'folder' if is_dir else 'file'
            
            if os.path.isfile(fullname):
                try:
                    size = os.path.getsize(fullname)
                    mtime = os.path.getmtime(fullname)
                except OSError:
                    pass
            elif is_dir:
                try:
                    mtime = os.path.getmtime(fullname)
                except OSError:
                    pass
            
            file_data.append({
                'name': name,
                'is_dir': is_dir,
                'size': size,
                'mtime': mtime,
                'type': file_type,
                'ext': os.path.splitext(name)[1].lower()
            })
        
        if sort_by == 'name':
            file_data.sort(key=lambda x: x['name'].lower())
        elif sort_by == 'size':
            file_data.sort(key=lambda x: x['size'], reverse=True)
            file_data.sort(key=lambda x: not x['is_dir'])
        elif sort_by == 'date':
            file_data.sort(key=lambda x: x['mtime'], reverse=True)
        elif sort_by == 'type':
            file_data.sort(key=lambda x: (x['type'], x['ext'], x['name'].lower()))
        
        r = []
    
        parsed_url = urllib.parse.urlparse(self.path)
        clean_path = parsed_url.path 
      
        displaypath = html.escape(urllib.parse.unquote(clean_path))
        
        r.append('<!DOCTYPE html>')
        r.append('<html lang="en">')
        r.append('<head>')
        r.append('<meta charset="utf-8">')
        r.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
        r.append(f'<title>Files: {displaypath}</title>')
        r.append('<style>')
        r.append("""
            :root { 
                --bg: #121212; 
                --card: rgba(30, 30, 30, 0.7); 
                --text: #e0e0e0; 
                --accent: #bb86fc; 
                --hover: rgba(44, 44, 44, 0.6); 
                --glass-border: rgba(255, 255, 255, 0.1);
            }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
                background: var(--bg); 
                color: var(--text); 
                margin: 0; 
                padding: 20px;
                background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
                min-height: 100vh;
            }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; }
            h1 { font-size: 1.5rem; color: var(--accent); margin: 0; }
            .breadcrumb { font-size: 14px; color: #888; margin: 10px 0; }
            .breadcrumb a { color: var(--accent); text-decoration: none; }
            .breadcrumb a:hover { text-decoration: underline; }
            .controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
            input#search { padding: 10px; font-size: 14px; border-radius: 12px; border: none; background: rgba(255, 255, 255, 0.1); color: white; width: 250px; box-sizing: border-box; outline: none; border: 1px solid var(--glass-border); backdrop-filter: blur(10px); }
            input#search:focus { border-color: var(--accent); background: rgba(255, 255, 255, 0.15); }
            .sort-dropdown { position: relative; display: inline-block; }
            .sort-btn { background: rgba(255, 255, 255, 0.1); color: var(--text); border: 1px solid var(--glass-border); padding: 10px 15px; border-radius: 12px; cursor: pointer; backdrop-filter: blur(10px); }
            .sort-content { display: none; position: absolute; background: rgba(30, 30, 30, 0.9); min-width: 160px; box-shadow: 0 8px 32px rgba(0,0,0,0.3); z-index: 1; border-radius: 12px; border: 1px solid var(--glass-border); backdrop-filter: blur(20px); }
            .sort-content a { color: var(--text); padding: 12px 16px; text-decoration: none; display: block; }
            .sort-content a:hover { background: var(--hover); }
            .sort-dropdown:hover .sort-content { display: block; }
            .view-toggle { display: flex; background: rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 4px; border: 1px solid var(--glass-border); backdrop-filter: blur(10px); }
            .view-btn { background: transparent; border: none; padding: 6px 12px; border-radius: 8px; cursor: pointer; color: var(--text); font-size: 16px; }
            .view-btn.active { background: var(--accent); color: black; }
            .upload-btn { background: var(--accent); color: black; border: none; padding: 10px 15px; border-radius: 12px; cursor: pointer; font-weight: 600; text-decoration: none; display: inline-block; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 20px; }
            .list { display: flex; flex-direction: column; gap: 8px; }
            .list .item { flex-direction: row; text-align: left; padding: 12px 16px; border-radius: 12px; }
            .list .file-icon { margin-bottom: 0; margin-right: 15px; }
            .list .info { text-align: left; flex: 1; }
            .list .name { font-size: 14px; }
            .item { display: flex; flex-direction: column; align-items: center; cursor: pointer; color: var(--text); text-decoration: none; padding: 15px; border-radius: 16px; transition: all 0.3s ease; background: var(--card); border: 1px solid var(--glass-border); backdrop-filter: blur(20px); box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2); }
            .item:hover { background: var(--hover); transform: translateY(-2px); box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3); }
            .file-icon { width: 64px; height: 80px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 900; color: white; text-transform: uppercase; margin-bottom: 8px; position: relative; box-shadow: 0 4px 15px rgba(0,0,0,0.3); backdrop-filter: blur(10px); }
            .file-icon::after { content: ''; position: absolute; top: 0; right: 0; border-bottom: 16px solid rgba(0,0,0,0.2); border-left: 16px solid rgba(0,0,0,0.2); border-top: 16px solid transparent; border-right: 16px solid transparent; width: 0; height: 0; }
            .icon-red { background: linear-gradient(135deg, #e53935, #b71c1c); }
            .icon-blue { background: linear-gradient(135deg, #1e88e5, #0d47a1); }
            .icon-green { background: linear-gradient(135deg, #43a047, #1b5e20); }
            .icon-yellow { background: linear-gradient(135deg, #fdd835, #f9a825); color: #212121; }
            .icon-purple { background: linear-gradient(135deg, #8e24aa, #4a148c); }
            .icon-teal { background: linear-gradient(135deg, #00acc1, #006064); }
            .icon-gray { background: linear-gradient(135deg, #757575, #424242); }
            .icon-orange { background: linear-gradient(135deg, #fb8c00, #e65100); }
            .icon-python { background: linear-gradient(135deg, #3776ab 40%, #ffd343 100%); }
            .icon-folder { width: 80px; height: 64px; background: linear-gradient(135deg, #ffa000, #ff6f00); border-radius: 8px; color: rgba(255,255,255,0.8); }
            .icon-folder::after { display: none; }
            .icon-folder::before { content: ''; position: absolute; top: -8px; left: 0; width: 25px; height: 10px; background: #ffa000; border-radius: 6px 6px 0 0; }
            .info { display: flex; flex-direction: column; text-align: center; width: 100%; }
            .name { font-weight: 500; font-size: 12px; word-break: break-word; margin-top: 5px; line-height: 1.3; }
            .meta { font-size: 10px; color: #888; margin-top: 2px; }
            .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; justify-content: center; align-items: center; backdrop-filter: blur(5px); }
            .modal { background: rgba(30, 30, 30, 0.9); padding: 24px; border-radius: 20px; width: 500px; max-width: 90%; text-align: center; border: 1px solid var(--glass-border); box-shadow: 0 20px 40px rgba(0,0,0,0.5); transform: scale(0.95); transition: transform 0.3s ease; backdrop-filter: blur(20px); max-height: 90vh; overflow-y: auto; }
            .modal.active { transform: scale(1); }
            .modal h3 { margin-top: 0; color: white; margin-bottom: 8px; word-break: break-all; }
            .modal p { color: #888; font-size: 0.9rem; margin-bottom: 20px; }
            .media-player { margin: 15px 0; border-radius: 12px; overflow: hidden; }
            .media-player video, .media-player audio { width: 100%; border-radius: 8px; }
            .media-player img { max-width: 100%; max-height: 300px; border-radius: 8px; }
            .btn { display: block; width: 100%; padding: 14px; margin: 8px 0; border: none; border-radius: 12px; font-size: 16px; cursor: pointer; text-decoration: none; box-sizing: border-box; font-weight: 600; transition: all 0.2s ease; backdrop-filter: blur(10px); }
            .btn:active { transform: scale(0.98); }
            .btn-download { background: var(--accent); color: black; }
            .btn-preview { background: rgba(255, 255, 255, 0.1); color: white; border: 1px solid var(--glass-border); }
            .btn-preview:hover { background: rgba(255, 255, 255, 0.2); }
            .btn-cancel { background: transparent; color: #777; font-size: 14px; margin-top: 0px; padding: 10px; }
            .btn-cancel:hover { color: #aaa; }
            .hidden { display: none !important; }
            .upload-form { background: rgba(30, 30, 30, 0.8); padding: 20px; border-radius: 16px; margin: 20px 0; border: 1px solid var(--glass-border); backdrop-filter: blur(20px); }
            .upload-form h3 { margin-top: 0; color: var(--accent); }
            /* Drag and Drop Styles */
            .drop-zone { 
                border: 2px dashed var(--glass-border); 
                border-radius: 12px; 
                padding: 40px; 
                text-align: center; 
                transition: all 0.3s ease;
                background: rgba(255, 255, 255, 0.05);
                cursor: pointer;
            }
            .drop-zone:hover, .drop-zone.dragover {
                border-color: var(--accent);
                background: rgba(255, 255, 255, 0.08);
            }
            .drop-zone.dragover {
                background: rgba(187, 134, 252, 0.1);
            }
            .drop-icon { 
                font-size: 48px; 
                margin-bottom: 16px; 
                color: var(--accent);
            }
            .drop-text { 
                font-size: 16px; 
                margin-bottom: 8px; 
            }
            .drop-hint { 
                font-size: 12px; 
                color: #888; 
            }
            .file-input { 
                display: none; 
            }
            .upload-progress { 
                margin-top: 20px; 
            }
            .progress-bar { 
                width: 100%; 
                height: 6px; 
                background: rgba(255, 255, 255, 0.1); 
                border-radius: 3px; 
                overflow: hidden; 
                margin-bottom: 10px;
            }
            .progress-fill { 
                height: 100%; 
                background: var(--accent); 
                width: 0%; 
                transition: width 0.3s ease;
            }
            .progress-text { 
                font-size: 12px; 
                color: #888; 
                text-align: center;
            }
            .file-list { 
                margin-top: 15px; 
                text-align: left; 
            }
            .file-item { 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                padding: 8px 12px; 
                background: rgba(255, 255, 255, 0.05); 
                border-radius: 8px; 
                margin-bottom: 8px; 
                font-size: 14px;
            }
            .file-name { 
                flex: 1; 
                overflow: hidden; 
                text-overflow: ellipsis; 
                white-space: nowrap; 
            }
            .file-size { 
                color: #888; 
                font-size: 12px; 
                margin-left: 10px;
            }
            .upload-status { 
                margin-left: 10px; 
                font-size: 12px; 
            }
            .status-uploading { color: var(--accent); }
            .status-success { color: #4CAF50; }
            .status-error { color: #f44336; }
        """)
        r.append('</style>')
        r.append('</head>')
        r.append('<body>')
        
        r.append('<div class="header">')
        r.append(f'<h1>File Manager</h1>')
        r.append('</div>')
        
        # --- FIXED BREADCRUMB LOGIC ---
        r.append('<div class="breadcrumb">')
        
        # Split the parsed clean_path (no query strings)
        path_parts = clean_path.strip('/').split('/')
        breadcrumb = []
        current_path_accumulator = ''
        
        breadcrumb.append('<a href="/">Home</a>')
        
        for i, part in enumerate(path_parts):
            if part:
                # Store the encoded part for the href link
                current_path_accumulator += '/' + part
                # Decode the part for display (e.g. "New Folder")
                display_part = urllib.parse.unquote(part)
                
                # Make the link
                # We do NOT use current_path_accumulator directly in href because it might need requoting
                # But since we built it from the raw path parts (which are encoded), it should be fine.
                # To be safe, we can quote the display part again for the path.
                
                breadcrumb.append(f'<a href="{urllib.parse.quote(current_path_accumulator)}/">{html.escape(display_part)}</a>')
        
        r.append(' > '.join(breadcrumb))
        r.append('</div>')
        # ------------------------------
        
        r.append('<div class="controls">')
        r.append('<input type="text" id="search" placeholder="Search files..." onkeyup="filterFiles()">')
        
        r.append('<div style="display: flex; gap: 10px; align-items: center;">')
        r.append('<div class="view-toggle">')
        # Note: HTML defaults removed here, handled by JS
        r.append('<button class="view-btn" onclick="toggleView(\'grid\', event)" title="Grid View">◼◼</button>')
        r.append('<button class="view-btn" onclick="toggleView(\'list\', event)" title="List View">≡</button>')
        r.append('</div>')
        
        r.append('<div class="sort-dropdown">')
        r.append('<button class="sort-btn">Sort By ▾</button>')
        r.append('<div class="sort-content">')
        r.append(f'<a href="?sort=name">Name</a>')
        r.append(f'<a href="?sort=size">Size</a>')
        r.append(f'<a href="?sort=date">Date Modified</a>')
        r.append(f'<a href="?sort=type">Type</a>')
        r.append('</div>')
        r.append('</div>')
        
        r.append('<button class="upload-btn" onclick="showUploadForm()">Upload File</button>')
        r.append('</div>')
        r.append('</div>')
        
        r.append('<div id="upload-form" class="upload-form" style="display: none;">')
        r.append('<h3>Upload Files</h3>')
        r.append('<div class="drop-zone" id="drop-zone">')
        r.append('<div class="drop-icon">📁</div>')
        r.append('<div class="drop-text">Drag and drop files here</div>')
        r.append('<div class="drop-hint">or click to select files</div>')
        r.append('<input type="file" class="file-input" id="file-input" multiple>')
        r.append('</div>')
        r.append('<div class="file-list" id="file-list"></div>')
        r.append('<div class="upload-progress" id="upload-progress" style="display: none;">')
        r.append('<div class="progress-bar">')
        r.append('<div class="progress-fill" id="progress-fill"></div>')
        r.append('</div>')
        r.append('<div class="progress-text" id="progress-text">0%</div>')
        r.append('</div>')
        r.append('<div style="display: flex; gap: 10px; margin-top: 15px;">')
        r.append('<button type="button" class="upload-btn" onclick="startUpload()" id="upload-button">Upload Files</button>')
        r.append('<button type="button" class="btn-cancel" onclick="hideUploadForm()">Cancel</button>')
        r.append('</div>')
        r.append('</div>')
        
        r.append('<div class="grid" id="file-container">')

        for item in file_data:
            name = item['name']
            is_dir = item['is_dir']
            fullname = os.path.join(path, name)
            displayname = linkname = name
            
            ext = item['ext']
            if ext in EXCLUDED_EXTENSIONS:
                continue
            
            if is_dir:
                displayname = name
                linkname = name + "/"
            
            icon_class = "icon-gray"
            icon_text = ext.replace('.', '').upper()
            
            if is_dir:
                icon_class = "icon-folder"
                icon_text = ""
            elif ext == '.pdf':
                icon_class = "icon-red"
                icon_text = "PDF"
            elif ext in ['.doc', '.docx', '.rtf', '.txt']:
                icon_class = "icon-blue"
                if icon_text == "DOCX": icon_text = "DOC"
            elif ext in ['.xls', '.xlsx', '.csv']:
                icon_class = "icon-green"
                if icon_text == "XLSX": icon_text = "XLS"
            elif ext in ['.ppt', '.pptx']:
                icon_class = "icon-yellow"
                if icon_text == "PPTX": icon_text = "PPT"
            elif ext in ['.mp4', '.mkv', '.mov', '.avi', '.webm']:
                icon_class = "icon-purple"
            elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']:
                icon_class = "icon-teal"
                if icon_text == "JPEG": icon_text = "JPG"
            elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                icon_class = "icon-orange"
            elif ext == '.py':
                icon_class = "icon-python" 
                icon_text = "PY"
            elif ext in ['.js', '.html', '.css', '.cpp', '.c', '.json']:
                icon_class = "icon-gray"
                icon_text = "</>"

            if len(icon_text) > 4: icon_text = icon_text[:3]

            size_str = ""
            date_str = ""
            can_preview = False
            media_type = None
            
            if os.path.isfile(fullname):
                if ext in PREVIEWABLE_EXTS:
                    can_preview = True
                
                if ext in MEDIA_EXTS['video']:
                    media_type = 'video'
                elif ext in MEDIA_EXTS['audio']:
                    media_type = 'audio'
                elif ext in MEDIA_EXTS['image']:
                    media_type = 'image'
                
                try:
                    size = item['size']
                    for unit in ['B', 'KB', 'MB', 'GB']:
                        if size < 1024.0:
                            size_str = f"{size:.1f} {unit}"
                            break
                        size /= 1024.0
                except OSError:
                    size_str = "??"
            
            try:
                mtime = item['mtime']
                date_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            except:
                date_str = "Unknown"
            
            type_desc = "Folder" if is_dir else f"{ext.upper().replace('.', '')} File"

            url = urllib.parse.quote(linkname)
            
            if is_dir:
                r.append(f'''
                <a href="{url}" class="item" data-name="{name.lower()}">
                    <div class="file-icon {icon_class}">{icon_text}</div>
                    <div class="info">
                        <span class="name">{displayname}</span>
                        <span class="meta">{type_desc}</span>
                        <span class="meta">{date_str}</span>
                    </div>
                </a>
                ''')
            else:
                preview_flag = 'true' if can_preview else 'false'
                media_type_attr = f"'{media_type}'" if media_type else 'null'
                r.append(f'''
                <div class="item" data-name="{name.lower()}" onclick="showModal('{url}', '{name}', {preview_flag}, {media_type_attr})">
                    <div class="file-icon {icon_class}">{icon_text}</div>
                    <div class="info">
                        <span class="name">{displayname}</span>
                        <span class="meta">{size_str} • {type_desc}</span>
                        <span class="meta">{date_str}</span>
                    </div>
                </div>
                ''')

        r.append('</div>')
        
        r.append("""
        <div id="modal-overlay" class="modal-overlay" onclick="closeModal(event)">
            <div class="modal">
                <h3 id="modal-title">File Name</h3>
                <div id="media-player" class="media-player hidden"></div>
                <p id="modal-description">Select an action</p>
                <a id="btn-preview" href="#" target="_blank" class="btn btn-preview">Preview in New Tab</a>
                <a id="btn-download" href="#" download class="btn btn-download">⬇️ Download</a>
                <button onclick="closeModal(null)" class="btn btn-cancel">Cancel</button>
            </div>
        </div>
        """)
        
        r.append("""
        <script>
            // --- FIXED JS: View Toggle & Default State ---
            function toggleView(viewType, event) {
                const container = document.getElementById('file-container');
                const buttons = document.querySelectorAll('.view-btn');
                
                // Update buttons if event is provided (clicked)
                if (event) {
                    buttons.forEach(btn => btn.classList.remove('active'));
                    event.currentTarget.classList.add('active');
                }
                
                if (viewType === 'list') {
                    container.classList.remove('grid');
                    container.classList.add('list');
                    localStorage.setItem('viewPreference', 'list');
                } else {
                    container.classList.remove('list');
                    container.classList.add('grid');
                    localStorage.setItem('viewPreference', 'grid');
                }
            }
            
            document.addEventListener('DOMContentLoaded', function() {
                const savedView = localStorage.getItem('viewPreference') || 'grid';
                const container = document.getElementById('file-container');
                const btnGrid = document.querySelector('.view-btn[title="Grid View"]');
                const btnList = document.querySelector('.view-btn[title="List View"]');
                
                // Set initial button state
                if (savedView === 'list') {
                    btnList.classList.add('active');
                    container.classList.remove('grid');
                    container.classList.add('list');
                } else {
                    // Default to grid
                    btnGrid.classList.add('active');
                    container.classList.remove('list');
                    container.classList.add('grid');
                }
            });

            function filterFiles() {
                var input = document.getElementById('search');
                var filter = input.value.toLowerCase();
                var container = document.getElementById('file-container');
                var items = container.children;
                
                for (var i = 0; i < items.length; i++) {
                    var name = items[i].getAttribute('data-name');
                    if (name.indexOf(filter) > -1) {
                        items[i].style.display = "";
                    } else {
                        items[i].style.display = "none";
                    }
                }
            }

            function showModal(url, filename, canPreview, mediaType) {
                var overlay = document.getElementById('modal-overlay');
                var title = document.getElementById('modal-title');
                var btnPreview = document.getElementById('btn-preview');
                var btnDownload = document.getElementById('btn-download');
                var mediaPlayer = document.getElementById('media-player');
                var description = document.getElementById('modal-description');
                
                title.innerText = filename;
                btnDownload.href = url;
                btnDownload.setAttribute('download', filename);
                
                if (canPreview) {
                    btnPreview.href = url;
                    btnPreview.classList.remove('hidden');
                } else {
                    btnPreview.classList.add('hidden');
                }
                
                mediaPlayer.innerHTML = '';
                mediaPlayer.classList.add('hidden');
                description.classList.remove('hidden');
                
                if (mediaType) {
                    description.classList.add('hidden');
                    mediaPlayer.classList.remove('hidden');
                    
                    if (mediaType === 'video') {
                        mediaPlayer.innerHTML = `<video controls autoplay><source src="${url}" type="video/mp4">Your browser does not support the video tag.</video>`;
                    } else if (mediaType === 'audio') {
                        mediaPlayer.innerHTML = `<audio controls autoplay><source src="${url}" type="audio/mpeg">Your browser does not support the audio tag.</audio>`;
                    } else if (mediaType === 'image') {
                        mediaPlayer.innerHTML = `<img src="${url}" alt="${filename}">`;
                    }
                }
                
                overlay.style.display = 'flex';
                setTimeout(() => overlay.querySelector('.modal').classList.add('active'), 10);
            }

            function closeModal(e) {
                if (e === null || e.target.id === 'modal-overlay') {
                    var overlay = document.getElementById('modal-overlay');
                    var mediaPlayer = document.getElementById('media-player');
                    
                    var video = mediaPlayer.querySelector('video');
                    var audio = mediaPlayer.querySelector('audio');
                    if (video) {
                        video.pause();
                        video.currentTime = 0;
                    }
                    if (audio) {
                        audio.pause();
                        audio.currentTime = 0;
                    }
                    
                    overlay.querySelector('.modal').classList.remove('active');
                    setTimeout(() => overlay.style.display = 'none', 200);
                }
            }

            // Upload functionality
            let selectedFiles = [];
            
            function showUploadForm() {
                document.getElementById('upload-form').style.display = 'block';
            }
            
            function hideUploadForm() {
                document.getElementById('upload-form').style.display = 'none';
                resetUploadForm();
            }
            
            function resetUploadForm() {
                selectedFiles = [];
                document.getElementById('file-list').innerHTML = '';
                document.getElementById('upload-progress').style.display = 'none';
                document.getElementById('progress-fill').style.width = '0%';
                document.getElementById('progress-text').textContent = '0%';
                document.getElementById('file-input').value = '';
            }
            
            // Drag and drop functionality
            const dropZone = document.getElementById('drop-zone');
            const fileInput = document.getElementById('file-input');
            
            dropZone.addEventListener('click', () => {
                fileInput.click();
            });
            
            fileInput.addEventListener('change', (e) => {
                handleFiles(e.target.files);
            });
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, highlight, false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, unhighlight, false);
            });
            
            function highlight() {
                dropZone.classList.add('dragover');
            }
            
            function unhighlight() {
                dropZone.classList.remove('dragover');
            }
            
            dropZone.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const files = dt.files;
                handleFiles(files);
            });
            
            function handleFiles(files) {
                for (let i = 0; i < files.length; i++) {
                    const file = files[i];
                    // Check if file is not already selected
                    if (!selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
                        selectedFiles.push(file);
                    }
                }
                updateFileList();
            }
            
            function updateFileList() {
                const fileList = document.getElementById('file-list');
                fileList.innerHTML = '';
                
                selectedFiles.forEach((file, index) => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.innerHTML = `
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${formatFileSize(file.size)}</div>
                        <div class="upload-status status-uploading" id="status-${index}"></div>
                        <button onclick="removeFile(${index})" style="background: none; border: none; color: #f44336; cursor: pointer; margin-left: 10px;">×</button>
                    `;
                    fileList.appendChild(fileItem);
                });
            }
            
            function removeFile(index) {
                selectedFiles.splice(index, 1);
                updateFileList();
            }
            
            function formatFileSize(bytes) {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }
            
            function startUpload() {
                if (selectedFiles.length === 0) {
                    alert('Please select files to upload');
                    return;
                }
                
                const formData = new FormData();
                selectedFiles.forEach(file => {
                    formData.append('files[]', file);
                });
                
                const xhr = new XMLHttpRequest();
                const progressBar = document.getElementById('progress-fill');
                const progressText = document.getElementById('progress-text');
                const uploadProgress = document.getElementById('upload-progress');
                
                uploadProgress.style.display = 'block';
                
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        progressBar.style.width = percentComplete + '%';
                        progressText.textContent = Math.round(percentComplete) + '%';
                    }
                });
                
                xhr.addEventListener('load', () => {
                    if (xhr.status === 200 || xhr.status === 303) {
                        progressBar.style.background = '#4CAF50';
                        progressText.textContent = 'Upload Complete!';
                        setTimeout(() => {
                            hideUploadForm();
                            location.reload();
                        }, 1000);
                    } else {
                        progressBar.style.background = '#f44336';
                        progressText.textContent = 'Upload Failed!';
                    }
                });
                
                xhr.addEventListener('error', () => {
                    progressBar.style.background = '#f44336';
                    progressText.textContent = 'Upload Failed!';
                });
                
                xhr.open('POST', window.location.pathname + window.location.search);
                xhr.send(formData);
            }
        </script>
        """)
        
        r.append('</body></html>')
        
        encoded = ''.join(r).encode('utf-8', 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def display_qr_code(url):
    try:
        qr = segno.make_qr(url)
        print("\n" + "="*60)
        print("OPENING QR CODE IMAGE...")
        print("="*60)
        qr.show() 
        print(f"Server is running at: {url}")
        print("="*60)
    except Exception as e:
        print(f"QR code generation failed: {e}")
        print("Make sure 'segno' is installed: pip install segno")

def run_server():
    if not os.path.exists(FOLDER_TO_SERVE):
        print(f"Error: Path not found: {FOLDER_TO_SERVE}")
        return
    try:
        os.chdir(FOLDER_TO_SERVE)
    except Exception as e:
        print(f"Error accessing folder: {e}")
        return
    
    socketserver.TCPServer.allow_reuse_address = True
    
    try:
        with socketserver.TCPServer(("", PORT), ModernHandler) as httpd:
            local_ip = get_local_ip()
            local_url = f"http://{local_ip}:{PORT}"
            
            print(f"\n{'='*60}")
            print(f"--- Modern Secure Server Running ---")
            print(f"Serving: {FOLDER_TO_SERVE}")
            print(f"Port: {PORT}")
            print(f"Local URL: http://127.0.0.1:{PORT}")
            print(f"Network URL: {local_url}")
            print(f"Allowed IPs: {ALLOWED_IPS}")
          
            
            display_qr_code(local_url)
            
            print("Press Ctrl+C to stop the server")
            print(f"{'='*60}\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Server error: {e}")

if __name__ == "__main__":
    try:
        import segno
    except ImportError:
        print("Warning: 'segno' library not installed. QR code feature will be disabled.")
        print("Install it with: pip install segno")
    
    run_server()