import json
import urllib.request

URL = ("https://archive-api.open-meteo.com/v1/archive"
       "?latitude=43.65&longitude=-79.38"
       "&start_date=2024-01-01&end_date=2026-01-31"
       "&hourly=precipitation,snowfall,weather_code&timezone=America/Toronto")

with urllib.request.urlopen(URL, timeout=60) as r:
    h = json.load(r)["hourly"]

def category(snow, precip, code):
    if snow > 0 or code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if precip > 0 or code in (51, 53, 55, 61, 63, 65, 80, 81, 82, 95):
        return "rain"
    return "clear"

out = {t[:13]: category(s or 0, p or 0, c or 0)
       for t, s, p, c in zip(h["time"], h["snowfall"], h["precipitation"], h["weather_code"])}

with open("data/weather.json", "w") as f:
    json.dump(out, f)
print(f"Saved {len(out)} hourly records")