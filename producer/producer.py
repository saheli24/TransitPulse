import csv, json, os, random, sys, time
from datetime import datetime, timedelta
from confluent_kafka import Producer

TOPIC = "transit-events"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
RATE = float(sys.argv[2]) if len(sys.argv) > 2 else 200  # events/sec; 0 = unlimited

STATIONS = {
    "Line 1": ["Finch", "York Mills", "Sheppard-Yonge", "Lawrence", "Eglinton",
               "Bloor-Yonge", "Wellesley", "Dundas", "Union", "St George", "Spadina"],
    "Line 2": ["Kipling", "Islington", "High Park", "Keele", "Spadina",
               "Broadview", "Pape", "Victoria Park", "Kennedy"],
    "Line 4": ["Sheppard-Yonge", "Bayview", "Don Mills"],
}
HOT = {"Bloor-Yonge", "Kennedy", "Union"}  # stations with more injected anomalies

WEATHER = {}
if os.path.exists("data/weather.json"):
    with open("data/weather.json") as f:
        WEATHER = json.load(f)
WX_MULT = {"snow": 2.0, "rain": 1.4}
EVENTS = {}
if os.path.exists("data/events.json"):
    with open("data/events.json") as f:
        EVENTS = json.load(f)
EVENT_MULT = 1.6

def synthetic(n):
    t = datetime(2024, 1, 1, 0, 0)
    for _ in range(n):
        route = random.choice(list(STATIONS))
        station = random.choice(STATIONS[route])
        t += timedelta(seconds=random.randint(5, 60))
        wx = WEATHER.get(t.strftime("%Y-%m-%dT%H"), "unknown")
        ev_name = EVENTS.get(t.strftime("%Y-%m-%d"))
        rush = 2.0 if t.hour in (7, 8, 9, 16, 17, 18) else 1.0
        base = 0.08 if station in HOT else 0.02
        mult = rush * WX_MULT.get(wx, 1.0) * (EVENT_MULT if ev_name else 1.0)
        injected = random.random() < min(base * mult, 0.9)
        delay = random.uniform(25, 60) if injected else max(0, random.gauss(3, 1.5))
        yield {"ts": t.isoformat(), "route": route, "station": station,
               "delay_min": round(delay, 1), "weather": wx, "event": ev_name,
               "injected": injected}
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
t0 = time.perf_counter()
for ev in source:
    ev["produced_at_ms"] = time.time() * 1000
    p.produce(TOPIC, json.dumps(ev).encode())
    sent += 1
    p.poll(0)
    if RATE > 0:
        delay = t0 + sent / RATE - time.perf_counter()
        if delay > 0:
            time.sleep(delay)
p.flush()
print(f"Sent {sent} events")