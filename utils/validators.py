# utils/validators.py
import socket
import subprocess
import platform

def valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except:
        return False

def valid_port(port):
    try:
        p = int(port)
        return 1 <= p <= 65535
    except:
        return False

def valid_duration(d):
    try:
        n = int(d)
        return 1 <= n <= 21000
    except:
        return False

def check_ip_alive(ip, timeout=3):
    """IP reachable কিনা TCP connect দিয়ে check"""
    try:
        # Common ports দিয়ে try করি
        for port in [80, 443, 22, 53]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip, port))
                sock.close()
                if result in [0, 111, 61]:  # connected or refused = IP alive
                    return True
            except:
                continue

        # UDP ICMP fallback
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(b'\x00' * 8, (ip, 7))
        try:
            sock.recvfrom(1024)
            sock.close()
            return True
        except socket.timeout:
            sock.close()
            return True  # no ICMP unreachable = host likely up
        except ConnectionRefusedError:
            sock.close()
            return True  # ICMP = host is responding

    except Exception:
        return None

def check_udp_port(ip, port, timeout=3):
    """UDP port open/filtered/closed"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        sock.sendto(b'\x00' * 8, (ip, port))
        try:
            sock.recvfrom(1024)
            sock.close()
            return "open"
        except socket.timeout:
            sock.close()
            return "open_or_filtered"
        except ConnectionRefusedError:
            sock.close()
            return "closed"
    except Exception:
        return "unknown"

def check_tcp_port(ip, port, timeout=3):
    """TCP port open কিনা"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return "open" if result == 0 else "closed"
    except Exception:
        return "unknown"
