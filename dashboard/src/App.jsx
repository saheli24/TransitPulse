import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const API = "http://localhost:8000/api";

export default function App() {
  const [hot, setHot] = useState([]);
  const [recent, setRecent] = useState([]);
  const [stats, setStats] = useState({});

  useEffect(() => {
    const load = async () => {
      try {
        setHot(await (await fetch(`${API}/hotspots`)).json());
        setRecent(await (await fetch(`${API}/recent`)).json());
        setStats(await (await fetch(`${API}/stats`)).json());
      } catch (e) {
        console.error(e);
      }
    };
    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, []);

  return (
    <div style={{ maxWidth: 900, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <h1>TransitPulse</h1>
      <p>
        Events: {stats.total} | Anomalies: {stats.anomalies} | Avg latency: {stats.avg_latency_ms} ms
      </p>

      <h2>Delay hotspots (anomaly count by station)</h2>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={hot}>
          <XAxis dataKey="station" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="anomalies" fill="#d9480f" />
        </BarChart>
      </ResponsiveContainer>

      <h2>Recent anomalies</h2>
      <table width="100%" cellPadding={6}>
        <thead>
          <tr><th>Time</th><th>Route</th><th>Station</th><th>Delay</th><th>Z</th></tr>
        </thead>
        <tbody>
          {recent.map((r, i) => (
            <tr key={i}>
              <td>{r.ts}</td><td>{r.route}</td><td>{r.station}</td>
              <td>{r.delay_min}</td><td>{r.zscore}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}