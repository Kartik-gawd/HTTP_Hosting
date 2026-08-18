import ipaddress

def is_loopback(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_loopback
    except ValueError:
        return False

def parse_ip(ip: str):
    #Return an IPv4Address/IPv6Address or raise ValueError
    return ipaddress.ip_address(ip)