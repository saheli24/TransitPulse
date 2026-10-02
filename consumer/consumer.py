import json, time
from collections import deque
import psycopg2
from psycopg2.extras import execute_values
from confluent_kafka import Consumer

TOPIC = "transit-events"
THRESHOLD = 3.0      # z-score cutoff; try 2.0 / 2.5 / 3.0 for the benchmark
WINDOW = 500         # per-route rolling baseline size
MIN_SAMPLES = 30     # no scoring until the baseline has this many points

consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "transitpulse-consumer",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
})
consumer.subscribe([TOPIC])

conn = psycopg2.connect(host="localhost", dbname="transitpulse", user="transit", password="transit")
cur = conn.cursor()

# Per-route rolling window with running sums, so each event is scored in O(1)
windows = {}  # route -> {"vals": deque, "sum": float, "sumsq": float}

def score(route, x):
    w = windows.setdefault(route, {"vals": deque(), "sum": 0.0, "sumsq": 0.0})
    n = len(w["vals"])
    z = 0.0
    if n >= MIN_SAMPLES:
        mean = w["sum"] / n
        var = max(w["sumsq"] / n - mean * mean, 0.0)
        std = var ** 0.5
        if std > 0:
            z = (x - mean) / std
    is_anom = z > THRESHOLD
    if not is_anom:  # keep anomalies out of the baseline so they don't skew it
        w["vals"].append(x); w["sum"] += x; w["sumsq"] += x * x
        if len(w["vals"]) > WINDOW:
            old = w["vals"].popleft(); w["sum"] -= old; w["sumsq"] -= old * old
    return z, is_anom

print("Consumer running. Ctrl+C to stop.")
total = 0
try:
    while True:
        msgs = consumer.consume(num_messages=500, timeout=1.0)
        rows = []
        for m in msgs:
            if m.error():
                continue
            e = json.loads(m.value())
            z, is_anom = score(e["route"], e["delay_min"])
            rows.append([e["ts"], e["route"], e["station"], e["delay_min"], e["weather"],
                         z, is_anom, e["injected"], time.time() * 1000 - e["produced_at_ms"]])
        if rows:
            execute_values(cur,
                """INSERT INTO events (ts, route, station, delay_min, weather,
                                       zscore, is_anomaly, injected, latency_ms) VALUES %s""", rows)
            conn.commit()
            consumer.commit()
            total += len(rows)
            print(f"Processed {total} events")
except KeyboardInterrupt:
    pass
finally:
    consumer.close(); conn.close()