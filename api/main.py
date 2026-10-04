import json
import psycopg2, redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
cache = redis.Redis(decode_responses=True)

# Approximate station coordinates (demo values)
COORDS = {
    "Finch": (43.7806, -79.4147), "York Mills": (43.7442, -79.4066),
    "Sheppard-Yonge": (43.7615, -79.4111), "Lawrence": (43.7254, -79.4023),
    "Eglinton": (43.7058, -79.3985), "Bloor-Yonge": (43.6709, -79.3857),
    "Wellesley": (43.6655, -79.3837), "Dundas": (43.6561, -79.3802),
    "Union": (43.6453, -79.3806), "St George": (43.6683, -79.3997),
    "Spadina": (43.6672, -79.4037), "Kipling": (43.6371, -79.5361),
    "Islington": (43.6453, -79.5246), "High Park": (43.6538, -79.4667),
    "Keele": (43.6560, -79.4602), "Broadview": (43.6770, -79.3591),
    "Pape": (43.6798, -79.3447), "Victoria Park": (43.6948, -79.2886),
    "Kennedy": (43.7326, -79.2636), "Bayview": (43.7669, -79.3868),
    "Don Mills": (43.7754, -79.3460),
}

def query(sql):
    conn = psycopg2.connect(host="localhost", dbname="transitpulse",
                            user="transit", password="transit")
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()

def cached(key, sql, ttl=5):
    hit = cache.get(key)
    if hit:
        return json.loads(hit)
    data = query(sql)
    cache.set(key, json.dumps(data, default=str), ex=ttl)
    return data

@app.get("/api/hotspots")
def hotspots():
    rows = cached("hotspots", """
        SELECT station, COUNT(*) AS events,
               COUNT(*) FILTER (WHERE is_anomaly) AS anomalies,
               ROUND(100.0 * COUNT(*) FILTER (WHERE is_anomaly) / COUNT(*), 1) AS rate,
               ROUND((AVG(delay_min))::numeric, 1) AS avg_delay
        FROM events GROUP BY station ORDER BY anomalies DESC""")
    out = []
    for r in rows:
        if r["station"] in COORDS:
            r["lat"], r["lon"] = COORDS[r["station"]]
            out.append(r)
    return out

@app.get("/api/patterns")
def patterns():
    return cached("patterns", """
        SELECT EXTRACT(HOUR FROM ts)::int AS hour,
               COUNT(*) FILTER (WHERE is_anomaly) AS anomalies,
               ROUND(AVG(delay_min)::numeric, 1) AS avg_delay
        FROM events GROUP BY hour ORDER BY hour""", ttl=10)

@app.get("/api/weather")
def weather():
    return cached("weather", """
        SELECT weather, COUNT(*) AS events,
               COUNT(*) FILTER (WHERE is_anomaly) AS anomalies,
               ROUND(100.0 * COUNT(*) FILTER (WHERE is_anomaly) / COUNT(*), 1) AS anomaly_pct
        FROM events GROUP BY weather ORDER BY anomaly_pct DESC""", ttl=10)

@app.get("/api/recent")
def recent():
    return query("""SELECT ts, route, station, delay_min, ROUND(zscore::numeric, 2) AS zscore
                    FROM events WHERE is_anomaly ORDER BY ts DESC LIMIT 15""")

@app.get("/api/stats")
def stats():
    return cached("stats", """
        SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE is_anomaly) AS anomalies,
               ROUND(AVG(latency_ms)::numeric) AS avg_latency_ms FROM events""")[0]

@app.get("/api/events")
def events():
    return cached("events", """
        SELECT COALESCE(event, 'Regular day') AS event, COUNT(*) AS events,
               COUNT(*) FILTER (WHERE is_anomaly) AS anomalies,
               ROUND(100.0 * COUNT(*) FILTER (WHERE is_anomaly) / COUNT(*), 1) AS anomaly_pct
        FROM events GROUP BY 1 ORDER BY anomaly_pct DESC""", ttl=10)