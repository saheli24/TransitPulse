import json
import psycopg2, redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
cache = redis.Redis(decode_responses=True)

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
    return cached("hotspots", """
        SELECT station, COUNT(*) AS anomalies, ROUND(AVG(delay_min)::numeric, 1) AS avg_delay
        FROM events WHERE is_anomaly GROUP BY station ORDER BY anomalies DESC LIMIT 10""")

@app.get("/api/recent")
def recent():
    return query("""SELECT ts, route, station, delay_min, ROUND(zscore::numeric, 2) AS zscore
                    FROM events WHERE is_anomaly ORDER BY ts DESC LIMIT 15""")

@app.get("/api/stats")
def stats():
    return cached("stats", """
        SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE is_anomaly) AS anomalies,
               ROUND(AVG(latency_ms)::numeric) AS avg_latency_ms FROM events""")[0]