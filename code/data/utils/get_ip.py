import ipaddress
import socket

# gets the local IP of server and creates a /24 allowed network range.

def allowed_networks():
    networks = [ipaddress.ip_network("127.0.0.0/8")]  # Always allow localhost
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        local_net = ipaddress.ip_network(f"{local_ip}/24", strict=False)
        networks.append(local_net)
        
    except Exception:
        networks.extend([
            ipaddress.ip_network("192.168.0.0/16"),
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12")
        ])
    return networks

# Creates a UDP socket. then Pretends to connect to Google DNS (8.8.8.8).
# No real data is sent, but this forces the OS to choose the network interface/IP it would use for internet access.
