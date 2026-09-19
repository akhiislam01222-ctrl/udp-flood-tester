# utils/validators.py
import socket

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