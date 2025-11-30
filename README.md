# HTTP Hosting

This script provides a local HTTP server built on Python's http.server module. It is designed for sharing files quickly and safely across a local network.

### What it does:

- Creates a small local website on your computer using Python. When you run it, your computer becomes a mini web server that lets you share files with anyone on the same **Wi-Fi or LAN network, not the internet.**
- Allows **Downloading**, **Previewing** of files as well as **Uploading** files back to the server.
- This makes it a quick and safe way to share files with multiple devices without needing email, USB drives, or cloud services.
  
---

## ✅ Compatibility

### **Works on:** **Windows, macOS, and Linux.**
  
## Features:

* Clean, responsive, dark-themed interface.
* **Restricts access** to a defined list of IP addresses.
* **Preview** for images, audio, and video.
* **Download and Upload** files easily.
* Console **QR code** for quick mobile access.

---

## How to Start

### 1. Prerequisites

- Python 3.x.
- (Optional) Install **segno** (QR code dependency):

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

## Screenshots

### Interface
![Interface](img/image1.png)

### Preview
![Preview](img/image2.png)

### Upload
![Upload](img/image3.png)

## Configuration

Modify the variables at the top of `localserver.py`:

| Variable              | Description                                    | Default                                   |
| --------------------- | ---------------------------------------------- | ----------------------------------------- |
| `PORT`                | Port the server listens on                     | `8000`                                    |
| `FOLDER_TO_SERVE`     | Root directory to host                         | `.`                                       |
| `ALLOWED_IPS`         | IPs allowed to connect; supports `.x` wildcard | `["127.0.0.1", "192.168.1.x"]`            |
| `EXCLUDED_EXTENSIONS` | File types hidden or denied                    | `{'.lnk', '.ini', '.url', '.db', '.exe'}` |
| `PREVIEWABLE_EXTS`    | Media types that can be previewed in the modal | Multiple                                  |

 Example: Customizing `ALLOWED_IPS`

```python
ALLOWED_IPS = [
    "127.0.0.1",      # Local machine only
    "192.168.1.x",    # All devices in the 192.168.1.x subnet
    "10.0.0.50",      # Specific device
]
```

---


# ⚠️ SECURITY WARNING: DO NOT USE FOR PRODUCTION OR SENSITIVE DATA
**IF port forwarding is enabled** for this port (port: 8000), it will make your local server **reachable** from the **public internet**. That means anyone outside your network could access it with your **public ip**, so it’s only meant for testing and debugging.

Anyone monitoring the network connection (e.g., MITM attackers, public Wi-Fi sniffers, or your ISP) can read and intercept all information.
- Make sure port forwarding for the port the script is using (port 8000) is **turned OFF**.
- NEVER run this server as the root or Administrator user.

## On the positive side:
Running a simple HTTP server strictly within your local network (LAN) **without port forwarding does not** expose it to the public internet. This means devices outside your home or office network cannot access it, and typical LAN isolation on home routers prevents external attacks. For local testing, this setup is generally safe as long as you trust the devices on your network and avoid handling sensitive data.


---

## ⚖️ License

This project is licensed under the **MIT License** - see the **[LICENSE](LICENSE)** file for details.

## Contributing

Feel free to submit pull requests or raise issues on the GitHub repository!
