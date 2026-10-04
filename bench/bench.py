import subprocess, sys, time
import psycopg2

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20000
RATE = sys.argv[2] if len(sys.argv) > 2 else "0"   # events/sec, 0 = unlimited
TIMEOUT = 900

conn = psycopg2.connect(host="localhost", dbname="transitpulse", user="transit", password="transit")
conn.autocommit = True
cur = conn.cursor()
cur.execute("TRUNCATE events")

start = time.time()
subprocess.run([sys.executable, "producer/producer.py", str(N), RATE], check=True)
while True:
    cur.execute("SELECT COUNT(*) FROM events")
    if cur.fetchone()[0] >= N:
        break
    if time.time() - start > TIMEOUT:
        sys.exit("Timed out. Is the consumer running?")
    time.sleep(2)
elapsed = time.time() - start

cur.execute("""SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY latency_ms),
                      percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) FROM events""")
p50, p95 = cur.fetchone()
cur.execute("""SELECT COUNT(*) FILTER (WHERE is_anomaly AND injected),
                      COUNT(*) FILTER (WHERE is_anomaly AND NOT injected),
                      COUNT(*) FILTER (WHERE NOT is_anomaly AND injected) FROM events""")
tp, fp, fn = cur.fetchone()

print(f"Events: {N} in {elapsed:.1f}s -> {N/elapsed:.0f} events/sec (end to end)")
print(f"Latency p50: {p50:.0f} ms, p95: {p95:.0f} ms")
print(f"TP={tp} FP={fp} FN={fn}")
print(f"Precision: {tp/max(tp+fp,1):.2f}  Recall: {tp/max(tp+fn,1):.2f}")