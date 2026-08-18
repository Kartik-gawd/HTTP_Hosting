import socket

def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def display_qr_code(url: str) -> None:
    try:
        import segno
        qr = segno.make_qr(url)
        print("\n" + "=" * 60)
        print("SCAN THIS QR CODE:")
        print("=" * 60)
        qr.terminal(compact=True)
        print(f"\nScan to connect at: {url}")
        print("=" * 60)
    except Exception as e:
        print(f"QR code generation failed: {e}")