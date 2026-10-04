import { useEffect, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip as MapTip } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import { MapPin, Clock, CloudRain, Ticket, Siren } from "lucide-react";

const API = "http://localhost:8000/api";
const color = (rate, max) => `hsl(${120 * (1 - Math.min(rate / (max || 1), 1))}, 85%, 45%)`;

const NAV = [
  { key: "hotspots", Icon: MapPin, label: "Hotspots" },
  { key: "patterns", Icon: Clock, label: "Patterns" },
  { key: "weather", Icon: CloudRain, label: "Weather" },
  { key: "events", Icon: Ticket, label: "Events" },
  { key: "recent", Icon: Siren, label: "Recent" },
];

export default function App() {
  const [open, setOpen] = useState(null);
  const [hot, setHot] = useState([]);
  const [patterns, setPatterns] = useState([]);
  const [wx, setWx] = useState([]);
  const [evs, setEvs] = useState([]);
  const [recent, setRecent] = useState([]);
  const [stats, setStats] = useState({});

  useEffect(() => {
    const get = async (path) => (await fetch(`${API}/${path}`)).json();
    const load = async () => {
      try {
        setHot(await get("hotspots"));
        setPatterns(await get("patterns"));
        setWx(await get("weather"));
        setEvs(await get("events"));
        setRecent(await get("recent"));
        setStats(await get("stats"));
      } catch (e) {
        console.error(e);
      }
    };
    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, []);

  const maxRate = Math.max(...hot.map((h) => Number(h.rate)), 1);
  const maxCount = Math.max(...hot.map((h) => Number(h.anomalies)), 1);
  const toggle = (k) => setOpen(open === k ? null : k);
  const title = NAV.find((n) => n.key === open)?.label;

  return (
    <div className="app">
      <div className="sidebar">
        <div className="logo">TRANSIT<br />PULSE</div>
        {NAV.map((n) => (
          <button key={n.key} className={`nav-btn ${open === n.key ? "active" : ""}`}
                  onClick={() => toggle(n.key)}>
            <n.Icon size={22} strokeWidth={2} />{n.label}
          </button>
        ))}
      </div>

      <div className="map">
        <MapContainer center={[43.70, -79.40]} zoom={11} style={{ height: "100%", width: "100%" }}>
          <TileLayer
  attribution="&copy; OpenStreetMap contributors"
  url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
/>
          {hot.map((h) => (
            <CircleMarker key={h.station} center={[h.lat, h.lon]}
              radius={8 + 22 * (Number(h.anomalies) / maxCount)}
              pathOptions={{
                color: color(Number(h.rate), maxRate),
                fillColor: color(Number(h.rate), maxRate),
                fillOpacity: 0.6,
              }}>
              <MapTip>{h.station}: {h.anomalies} anomalies ({h.rate}% of {h.events} events)</MapTip>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>

      <div className="statbar">
        <div><b>{Number(stats.total || 0).toLocaleString()}</b>Events</div>
        <div><b>{Number(stats.anomalies || 0).toLocaleString()}</b>Anomalies</div>
        <div><b>{stats.avg_latency_ms ?? "-"} ms</b>Avg latency</div>
      </div>

      <div className="legend">
        Circle size = anomaly count
        <div className="bar" />
        <div className="ends"><span>low rate</span><span>high rate</span></div>
      </div>

      {open && (
        <div className="panel">
          <button className="close" onClick={() => setOpen(null)}>×</button>
          <h2>{title}</h2>

          {open === "hotspots" && (
            <>
              <p className="sub">Stations ranked by anomaly count.</p>
              <table>
                <thead><tr><th>Station</th><th>Anomalies</th><th>Rate</th><th>Avg delay</th></tr></thead>
                <tbody>
                  {hot.slice(0, 10).map((h) => (
                    <tr key={h.station}>
                      <td>{h.station}</td><td>{h.anomalies}</td>
                      <td>{h.rate}%</td><td>{h.avg_delay} min</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}

          {open === "patterns" && (
            <>
              <p className="sub">Anomalies by hour of day. Rush hours stand out.</p>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={patterns}>
                  <XAxis dataKey="hour" /><YAxis /><Tooltip />
                  <Line type="monotone" dataKey="anomalies" stroke="#d9480f" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </>
          )}

          {open === "weather" && (
            <>
              <p className="sub">Share of events flagged as anomalies, by weather.</p>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={wx}>
                  <XAxis dataKey="weather" /><YAxis unit="%" /><Tooltip />
                  <Bar dataKey="anomaly_pct" fill="#2563eb" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          {open === "events" && (
            <>
              <p className="sub">Anomaly rate on event days vs a regular day.</p>
              <ResponsiveContainer width="100%" height={Math.max(240, evs.length * 40)}>
                <BarChart data={evs} layout="vertical" margin={{ left: 40 }}>
                  <XAxis type="number" unit="%" />
                  <YAxis type="category" dataKey="event" width={130} />
                  <Tooltip />
                  <Bar dataKey="anomaly_pct" fill="#7c3aed" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          {open === "recent" && (
            <>
              <p className="sub">Latest detected anomalies.</p>
              <table>
                <thead><tr><th>Station</th><th>Route</th><th>Delay</th><th>Z</th></tr></thead>
                <tbody>
                  {recent.map((r, i) => (
                    <tr key={i}>
                      <td>{r.station}</td><td>{r.route}</td>
                      <td>{r.delay_min} min</td><td>{r.zscore}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}
    </div>
  );
}