# Local_Hosting
This script provides a local HTTP server built on Python's http.server module. It is designed for sharing files quickly and safely across a local network.

---

## Features

* Clean, responsive, dark-themed interface.
* Restricts access to a defined list of IP addresses.
* Drag-and-drop or file selection uploads to the current directory.
* Modal viewer for images, audio, and video.
* Console QR code for quick mobile access.

---

## How to Start

### 1. Prerequisites

- Install Python 3.x.
- Install the optional QR code dependency:

```bash
pip install segno
```

> If skipped, the script runs normally but without QR code display.

---

### 2. Run the Server

Copy the script into the folder you want to share, then run it using:

```bash
python localserver.py
```
or by running it through any IDE.

---

### 3. Access the Server

The console/terminal will show:

```
============================================================
--- Modern Secure Server Running ---
Serving: .
Port: 8000
Local URL: http://127.0.0.1:8000
Network URL: http://192.168.1.10:8000
Allowed IPs: ['127.0.0.1', '192.168.1.x']

# ... QR Code Image will appear here (if segno is installed) ...

Press Ctrl+C to stop the server
============================================================
```

Open one of the URLs in your browser to access the file manager.

---

## Configuration

Modify the variables at the top of `localserver.py`:

| Variable              | Description                                    | Default                                   |
| --------------------- | ---------------------------------------------- | ----------------------------------------- |
| `PORT`                | Port the server listens on                     | `8000`                                    |
| `FOLDER_TO_SERVE`     | Root directory to host                         | `.`                                       |
| `ALLOWED_IPS`         | IPs allowed to connect; supports `.x` wildcard | `["127.0.0.1", "192.168.1.x"]`            |
| `EXCLUDED_EXTENSIONS` | File types hidden or denied                    | `{'.lnk', '.ini', '.url', '.db', '.exe'}` |
| `PREVIEWABLE_EXTS`    | Media types that can be previewed in the modal | Multiple                                  |

### Example: Customizing `ALLOWED_IPS`

```python
ALLOWED_IPS = [
    "127.0.0.1",      # Local machine only
    "192.168.1.x",    # All devices in the 192.168.1.x subnet
    "10.0.0.50",      # Specific device
]
```

---

## Usage

### File Upload

1. Click **Upload File**.
2. A drag-and-drop zone appears.
3. Drag files or click to select.
4. Click **Upload Files** to send them to the current directory.

---

### File Interaction

When clicking a non-directory file:

* **Preview in New Tab**
* **Download**
* **Embedded Player** for supported media (MP4, MP3, JPG, etc.)

---

