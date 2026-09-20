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
    """IP টা live আছে কিনা ping দিয়ে check"""
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        result = subprocess.run(
            ["ping", param, "3", "-W", str(timeout), ip],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 2
        )
        return result.returncode == 0
    except Exception:
        return None  # None = check করা যায়নি

def check_udp_port(ip, port, timeout=3):
    """
    UDP port check:
    - ICMP Port Unreachable পেলে → CLOSED
    - Timeout হলে → OPEN বা FILTERED (firewall)
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        # ছোট packet পাঠাই
        sock.sendto(b"\x00" * 8, (ip, port))
        try:
            sock.recvfrom(1024)
            # Response পেলে → port open (UDP service আছে)
            sock.close()
            return "open"
        except socket.timeout:
            # Timeout → open বা filtered
            sock.close()
            return "open_or_filtered"
        except ConnectionRefusedError:
            # ICMP Port Unreachable → closed
            sock.close()
            return "closed"
    except Exception as e:
        return "unknown"

def check_tcp_port(ip, port, timeout=3):
    """TCP port open কিনা (bonus check)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return "open" if result == 0 else "closed"
    except Exception:
        return "unknown"
