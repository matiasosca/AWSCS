"""Fetch current weather for world capitals and render a single graphic.

Uses Open-Meteo's free current-weather API (no API key required) and
matplotlib to plot every capital on a world map. Points are colored by
temperature; the warmest and coldest cities are annotated.

Run:
    python world_capitals_weather.py [--out weather.png]

Dependencies: requests, matplotlib
    pip install requests matplotlib
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import matplotlib.pyplot as plt
import requests
from matplotlib.patches import Rectangle


# (capital, country, latitude, longitude)
CAPITALS: list[tuple[str, str, float, float]] = [
    ("Abu Dhabi", "United Arab Emirates", 24.4539, 54.3773),
    ("Abuja", "Nigeria", 9.0765, 7.3986),
    ("Addis Ababa", "Ethiopia", 9.0300, 38.7400),
    ("Algiers", "Algeria", 36.7538, 3.0588),
    ("Amman", "Jordan", 31.9454, 35.9284),
    ("Amsterdam", "Netherlands", 52.3676, 4.9041),
    ("Ankara", "Turkey", 39.9334, 32.8597),
    ("Antananarivo", "Madagascar", -18.8792, 47.5079),
    ("Astana", "Kazakhstan", 51.1605, 71.4704),
    ("Asuncion", "Paraguay", -25.2637, -57.5759),
    ("Athens", "Greece", 37.9838, 23.7275),
    ("Baghdad", "Iraq", 33.3152, 44.3661),
    ("Baku", "Azerbaijan", 40.4093, 49.8671),
    ("Bangkok", "Thailand", 13.7563, 100.5018),
    ("Beijing", "China", 39.9042, 116.4074),
    ("Beirut", "Lebanon", 33.8938, 35.5018),
    ("Belgrade", "Serbia", 44.7866, 20.4489),
    ("Berlin", "Germany", 52.5200, 13.4050),
    ("Bern", "Switzerland", 46.9480, 7.4474),
    ("Bogota", "Colombia", 4.7110, -74.0721),
    ("Brasilia", "Brazil", -15.8267, -47.9218),
    ("Bratislava", "Slovakia", 48.1486, 17.1077),
    ("Brussels", "Belgium", 50.8503, 4.3517),
    ("Bucharest", "Romania", 44.4268, 26.1025),
    ("Budapest", "Hungary", 47.4979, 19.0402),
    ("Buenos Aires", "Argentina", -34.6037, -58.3816),
    ("Cairo", "Egypt", 30.0444, 31.2357),
    ("Canberra", "Australia", -35.2809, 149.1300),
    ("Caracas", "Venezuela", 10.4806, -66.9036),
    ("Copenhagen", "Denmark", 55.6761, 12.5683),
    ("Dakar", "Senegal", 14.7167, -17.4677),
    ("Damascus", "Syria", 33.5138, 36.2765),
    ("Dhaka", "Bangladesh", 23.8103, 90.4125),
    ("Doha", "Qatar", 25.2854, 51.5310),
    ("Dublin", "Ireland", 53.3498, -6.2603),
    ("Hanoi", "Vietnam", 21.0285, 105.8542),
    ("Harare", "Zimbabwe", -17.8252, 31.0335),
    ("Havana", "Cuba", 23.1136, -82.3666),
    ("Helsinki", "Finland", 60.1699, 24.9384),
    ("Islamabad", "Pakistan", 33.6844, 73.0479),
    ("Jakarta", "Indonesia", -6.2088, 106.8456),
    ("Kabul", "Afghanistan", 34.5553, 69.2075),
    ("Kampala", "Uganda", 0.3476, 32.5825),
    ("Kathmandu", "Nepal", 27.7172, 85.3240),
    ("Khartoum", "Sudan", 15.5007, 32.5599),
    ("Kiev", "Ukraine", 50.4501, 30.5234),
    ("Kingston", "Jamaica", 17.9712, -76.7920),
    ("Kuala Lumpur", "Malaysia", 3.1390, 101.6869),
    ("Kuwait City", "Kuwait", 29.3759, 47.9774),
    ("La Paz", "Bolivia", -16.4897, -68.1193),
    ("Lima", "Peru", -12.0464, -77.0428),
    ("Lisbon", "Portugal", 38.7223, -9.1393),
    ("Ljubljana", "Slovenia", 46.0569, 14.5058),
    ("London", "United Kingdom", 51.5074, -0.1278),
    ("Luanda", "Angola", -8.8390, 13.2894),
    ("Madrid", "Spain", 40.4168, -3.7038),
    ("Manila", "Philippines", 14.5995, 120.9842),
    ("Mexico City", "Mexico", 19.4326, -99.1332),
    ("Minsk", "Belarus", 53.9006, 27.5590),
    ("Montevideo", "Uruguay", -34.9011, -56.1645),
    ("Moscow", "Russia", 55.7558, 37.6173),
    ("Nairobi", "Kenya", -1.2921, 36.8219),
    ("New Delhi", "India", 28.6139, 77.2090),
    ("Nicosia", "Cyprus", 35.1856, 33.3823),
    ("Nuuk", "Greenland", 64.1836, -51.7214),
    ("Oslo", "Norway", 59.9139, 10.7522),
    ("Ottawa", "Canada", 45.4215, -75.6972),
    ("Paris", "France", 48.8566, 2.3522),
    ("Phnom Penh", "Cambodia", 11.5564, 104.9282),
    ("Prague", "Czech Republic", 50.0755, 14.4378),
    ("Pretoria", "South Africa", -25.7479, 28.2293),
    ("Pyongyang", "North Korea", 39.0392, 125.7625),
    ("Quito", "Ecuador", -0.1807, -78.4678),
    ("Rabat", "Morocco", 34.0209, -6.8416),
    ("Reykjavik", "Iceland", 64.1466, -21.9426),
    ("Riga", "Latvia", 56.9496, 24.1052),
    ("Riyadh", "Saudi Arabia", 24.7136, 46.6753),
    ("Rome", "Italy", 41.9028, 12.4964),
    ("San Jose", "Costa Rica", 9.9281, -84.0907),
    ("Santiago", "Chile", -33.4489, -70.6693),
    ("Seoul", "South Korea", 37.5665, 126.9780),
    ("Singapore", "Singapore", 1.3521, 103.8198),
    ("Skopje", "North Macedonia", 41.9981, 21.4254),
    ("Sofia", "Bulgaria", 42.6977, 23.3219),
    ("Stockholm", "Sweden", 59.3293, 18.0686),
    ("Taipei", "Taiwan", 25.0330, 121.5654),
    ("Tallinn", "Estonia", 59.4370, 24.7536),
    ("Tashkent", "Uzbekistan", 41.2995, 69.2401),
    ("Tbilisi", "Georgia", 41.7151, 44.8271),
    ("Tehran", "Iran", 35.6892, 51.3890),
    ("Tokyo", "Japan", 35.6762, 139.6503),
    ("Tunis", "Tunisia", 36.8065, 10.1815),
    ("Ulaanbaatar", "Mongolia", 47.8864, 106.9057),
    ("Vienna", "Austria", 48.2082, 16.3738),
    ("Vilnius", "Lithuania", 54.6872, 25.2797),
    ("Warsaw", "Poland", 52.2297, 21.0122),
    ("Washington", "United States", 38.9072, -77.0369),
    ("Wellington", "New Zealand", -41.2865, 174.7762),
    ("Yerevan", "Armenia", 40.1792, 44.4991),
    ("Zagreb", "Croatia", 45.8150, 15.9819),
]


@dataclass
class Reading:
    city: str
    country: str
    lat: float
    lon: float
    temp_c: float


def fetch_one(city: str, country: str, lat: float, lon: float) -> Reading | None:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current_weather=true"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        temp = r.json()["current_weather"]["temperature"]
    except (requests.RequestException, KeyError, ValueError) as exc:
        print(f"  ! {city}: {exc}", file=sys.stderr)
        return None
    return Reading(city, country, lat, lon, float(temp))


def fetch_all() -> list[Reading]:
    readings: list[Reading] = []
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(fetch_one, *c) for c in CAPITALS]
        for fut in as_completed(futures):
            r = fut.result()
            if r is not None:
                readings.append(r)
    return readings


def plot(readings: list[Reading], out_path: str) -> None:
    readings.sort(key=lambda r: r.temp_c)
    coldest = readings[:5]
    warmest = readings[-5:][::-1]

    fig = plt.figure(figsize=(16, 9), facecolor="#0b1020")
    gs = fig.add_gridspec(1, 4, width_ratios=[3, 1, 0.05, 0.05], wspace=0.15)
    ax = fig.add_subplot(gs[0, 0])
    side = fig.add_subplot(gs[0, 1])
    cax = fig.add_subplot(gs[0, 2])

    for a in (ax, side):
        a.set_facecolor("#0b1020")
        for spine in a.spines.values():
            spine.set_color("#3a4264")

    lons = [r.lon for r in readings]
    lats = [r.lat for r in readings]
    temps = [r.temp_c for r in readings]

    ax.add_patch(Rectangle((-180, -90), 360, 180, facecolor="#11183a", zorder=0))
    for lon in range(-180, 181, 30):
        ax.axvline(lon, color="#1d2750", lw=0.5, zorder=1)
    for lat in range(-90, 91, 30):
        ax.axhline(lat, color="#1d2750", lw=0.5, zorder=1)

    sc = ax.scatter(
        lons, lats, c=temps, cmap="RdYlBu_r", s=80,
        edgecolors="white", linewidths=0.6, vmin=-30, vmax=40, zorder=3,
    )

    for r in coldest + warmest:
        ax.annotate(
            r.city,
            xy=(r.lon, r.lat),
            xytext=(6, 6),
            textcoords="offset points",
            color="white",
            fontsize=8,
            fontweight="bold",
        )

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude", color="#aab1d6")
    ax.set_ylabel("Latitude", color="#aab1d6")
    ax.tick_params(colors="#aab1d6")
    ax.set_title(
        f"Current temperature at {len(readings)} world capitals",
        color="white", fontsize=14, pad=12,
    )

    cb = fig.colorbar(sc, cax=cax)
    cb.set_label("°C", color="white")
    cb.ax.yaxis.set_tick_params(color="#aab1d6")
    plt.setp(cb.ax.get_yticklabels(), color="#aab1d6")

    side.axis("off")
    side.set_xlim(0, 1)
    side.set_ylim(0, 1)

    def write_block(title: str, items: list[Reading], y_top: float, color: str) -> None:
        side.text(0.0, y_top, title, color=color, fontsize=13, fontweight="bold")
        for i, r in enumerate(items):
            y = y_top - 0.05 - i * 0.05
            side.text(0.0, y, f"{r.city}, {r.country}", color="white", fontsize=10)
            side.text(1.0, y, f"{r.temp_c:5.1f} °C",
                      color=color, fontsize=10, ha="right", family="monospace")

    write_block("Warmest", warmest, 0.98, "#ff6b6b")
    write_block("Coldest", coldest, 0.45, "#6bb6ff")

    fig.savefig(out_path, dpi=140, facecolor=fig.get_facecolor(), bbox_inches="tight")
    print(f"Saved: {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default="capitals_weather.png",
                        help="output image path (default: capitals_weather.png)")
    args = parser.parse_args()

    print(f"Fetching weather for {len(CAPITALS)} capitals...")
    readings = fetch_all()
    if not readings:
        print("No data fetched.", file=sys.stderr)
        return 1
    print(f"Got {len(readings)}/{len(CAPITALS)} readings.")
    plot(readings, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
