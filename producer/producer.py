import csv, json, os, random, sys, time
from datetime import datetime, timedelta
from confluent_kafka import Producer

TOPIC = "transit-events"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
RATE = float(sys.argv[2]) if len(sys.argv) > 2 else 200  # events/sec; 0 = unlimited

STATIONS = {
    "Line 1": ["Bloor-Yonge", "Union", "St George", "Finch", "Kennedy"],
    "Line 2": ["Kennedy", "Broadview", "Spadina", "Kipling"],
    "Line 4": ["Sheppard-Yonge", "Don Mills"],
}
HOT = {"Bloor-Yonge", "Kennedy"}  # stations with more injected anomalies

def synthetic(n):
    t = datetime(2024, 1, 1, 6, 0)
    for _ in range(n):
        route = random.choice(list(STATIONS))
        station = random.choice(STATIONS[route])
        injected = random.random() < (0.08 if station in HOT else 0.02)
        delay = random.uniform(25, 60) if injected else max(0, random.gauss(3, 1.5))
        t += timedelta(seconds=random.randint(5, 60))
        yield {"ts": t.isoformat(), "route": route, "station": station,
               "delay_min": round(delay, 1), "weather": "unknown", "injected": injected}

def from_csv(path, n):
    # Adjust column names/date format to match the TTC file you download.
    with open(path, newline="", encoding="utf-8-sig") as f:
        count = 0
        for row in csv.DictReader(f):
            if count >= n:
                break
            try:
                ts = datetime.strptime(f"{row['Date'][:10]} {row['Time']}", "%Y-%m-%d %H:%M")
                yield {"ts": ts.isoformat(), "route": row["Line"], "station": row["Station"],
                       "delay_min": float(row["Min Delay"]), "weather": "unknown", "injected": False}
                count += 1
            except (KeyError, ValueError):
                continue

p = Producer({"bootstrap.servers": "localhost:9092", "linger.ms": 20})
source = from_csv("data/ttc.csv", N) if os.path.exists("data/ttc.csv") else synthetic(N)

sent = 0
for ev in source:
    ev["produced_at_ms"] = time.time() * 1000
    p.produce(TOPIC, json.dumps(ev).encode())
    sent += 1
    p.poll(0)
    if RATE > 0:
        time.sleep(1 / RATE)
p.flush()
print(f"Sent {sent} events")