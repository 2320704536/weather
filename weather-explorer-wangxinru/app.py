import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone
import plotly.express as px
from streamlit_folium import st_folium
import folium

# --------------------- CONFIG ---------------------
st.set_page_config(page_title="Weather Explorer • wang xinru", page_icon="🌈", layout="wide")

TITLE = "Weather Explorer • wang xinru"
st.markdown(f"<h1 style='margin-bottom:0'>{TITLE}</h1>", unsafe_allow_html=True)
st.caption("Click the map to choose a location • Real-time weather + 7-day forecast • Soft illustration theme")

# --------------------- MAP ---------------------
st.subheader("📍 Select a location on the map")
default_location = [37.5665, 126.9780]  # Seoul by default
m = folium.Map(location=default_location, zoom_start=4, tiles="cartodbpositron")
folium.Marker(default_location, tooltip="Default: Seoul").add_to(m)
map_state = st_folium(m, height=420, width=None)
coords = map_state.get("last_clicked")

if coords:
    lat, lon = round(float(coords["lat"]), 4), round(float(coords["lng"]), 4)
else:
    lat, lon = default_location

# --------------------- API ---------------------
@st.cache_data(ttl=600)
def fetch_weather(lat: float, lon: float):
    # Open-Meteo free API (no key)
    # Docs: https://open-meteo.com/en/docs
    base = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto",
        "current_weather": "true",
        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "wind_speed_10m",
            "precipitation_probability",
            "weathercode"
        ]),
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "weathercode"
        ]),
    }
    r = requests.get(base, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

data = fetch_weather(lat, lon)

# --------------------- helpers ---------------------
WMO = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    56: "Freezing drizzle", 57: "Dense freezing drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    66: "Freezing rain", 67: "Heavy freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Rain showers", 81: "Heavy rain showers", 82: "Violent rain showers",
    85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm (hail)", 99: "Thunderstorm (heavy hail)"
}

def get_current_humidity(data):
    # humidity is in hourly series; match nearest hour to current_weather time
    if "hourly" not in data or "relative_humidity_2m" not in data["hourly"]:
        return None
    times = data["hourly"]["time"]
    hums = data["hourly"]["relative_humidity_2m"]
    target = data["current_weather"]["time"]
    # simple lookup
    try:
        idx = times.index(target)
        return hums[idx]
    except ValueError:
        return None

def describe_condition(code: int) -> str:
    return WMO.get(int(code), "Unknown")

def condition_theme(code: int, is_day: int):
    """Return CSS gradient + illustration svg for background based on weather code."""
    # base gentle gradients
    gradients = {
        "clear_day": "linear-gradient(180deg, #fdfbfb 0%, #ebedee 100%)",
        "clear_night": "linear-gradient(180deg, #1e3c72 0%, #2a5298 100%)",
        "cloudy": "linear-gradient(180deg, #ece9f1 0%, #f5f7fa 100%)",
        "rain": "linear-gradient(180deg, #d7e1ec 0%, #f1f5f9 100% )",
        "snow": "linear-gradient(180deg, #eef2ff 0%, #f8fafc 100%)",
        "storm": "linear-gradient(180deg, #cfd9df 0%, #e2ebf0 100%)",
        "fog": "linear-gradient(180deg, #f0f3f5 0%, #f9fbfc 100%)",
    }
    # soft clouds SVG pattern
    cloud_svg = (
        "url('data:image/svg+xml;utf8,"
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"800\" height=\"600\">"
        "<g opacity=\"0.25\">"
        "<ellipse cx=\"150\" cy=\"120\" rx=\"120\" ry=\"55\" fill=\"white\"/>"
        "<ellipse cx=\"260\" cy=\"130\" rx=\"140\" ry=\"60\" fill=\"white\"/>"
        "<ellipse cx=\"460\" cy=\"110\" rx=\"160\" ry=\"70\" fill=\"white\"/>"
        "<ellipse cx=\"640\" cy=\"140\" rx=\"150\" ry=\"60\" fill=\"white\"/>"
        "</g></svg>')"
    )
    # choose theme
    if code in (61,63,65,80,81,82,66,67,51,53,55,56,57):
        g = gradients["rain"]
    elif code in (71,73,75,77,85,86):
        g = gradients["snow"]
    elif code in (95,96,99):
        g = gradients["storm"]
    elif code in (45,48):
        g = gradients["fog"]
    elif code in (0,1) and is_day == 1:
        g = gradients["clear_day"]
    elif code in (0,1) and is_day == 0:
        g = gradients["clear_night"]
    elif code in (2,3):
        g = gradients["cloudy"]
    else:
        g = gradients["cloudy"]
    return g, cloud_svg

# --------------------- CURRENT CARD ---------------------
if "current_weather" in data:
    cur = data["current_weather"]
    code = int(cur.get("weathercode", 0))
    is_day = int(cur.get("is_day", 1))
    # background
    gradient, overlay_svg = condition_theme(code, is_day)
    st.markdown(f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background: {gradient};
            background-attachment: fixed;
        }}
        [data-testid="stHeader"] {{
            background: transparent;
        }}
        /* soft cloud overlay on top of gradient */
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            inset: 0;
            background-image: {overlay_svg};
            background-repeat: repeat;
            background-size: 100% auto;
            opacity: 0.35;
            pointer-events: none;
        }}
        /* subtle card glassmorphism */
        .glass {{
            background: rgba(255,255,255,0.6);
            border-radius: 18px;
            padding: 18px 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            backdrop-filter: blur(6px);
        }}
        </style>
    """, unsafe_allow_html=True)

    # derive humidity
    humidity = get_current_humidity(data)
    desc = describe_condition(code)
    st.subheader("🌤 Current Weather")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='glass'><h3 style='margin:0'>{cur['temperature']}°C</h3><p style='margin:0'>Temperature</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='glass'><h3 style='margin:0'>{desc}</h3><p style='margin:0'>Condition</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='glass'><h3 style='margin:0'>{cur['windspeed']} m/s</h3><p style='margin:0'>Wind</p></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='glass'><h3 style='margin:0'>{humidity if humidity is not None else '--'}%</h3><p style='margin:0'>Humidity</p></div>", unsafe_allow_html=True)
else:
    st.warning("Failed to load current weather.")

# --------------------- FORECAST (DAILY) ---------------------
st.subheader("📆 Weather Forecast (7-day)")
daily = data.get("daily", {})
if daily:
    ddf = pd.DataFrame({
        "Date": pd.to_datetime(daily["time"]),
        "Max Temp (°C)": daily.get("temperature_2m_max", []),
        "Min Temp (°C)": daily.get("temperature_2m_min", []),
        "Max Wind (m/s)": daily.get("wind_speed_10m_max", []),
        "Rain Prob (%)": daily.get("precipitation_probability_max", []),
        "Code": daily.get("weathercode", []),
    })
    st.dataframe(ddf, hide_index=True, use_container_width=True)

    # Temperature trend
    fig_t = px.line(ddf, x="Date", y=["Max Temp (°C)", "Min Temp (°C)"],
                    markers=True, title="Temperature Trend (Daily)")
    st.plotly_chart(fig_t, use_container_width=True)

    # Wind speed
    fig_w = px.line(ddf, x="Date", y="Max Wind (m/s)",
                    markers=True, title="Max Wind Speed (Daily)")
    st.plotly_chart(fig_w, use_container_width=True)

    # Rain probability
    fig_r = px.line(ddf, x="Date", y="Rain Prob (%)",
                    markers=True, title="Precipitation Probability (Daily)")
    st.plotly_chart(fig_r, use_container_width=True)

# --------------------- HOURLY (48h) ---------------------
st.subheader("⏱ Hourly (next 48 hours)")
hourly = data.get("hourly", {})
if hourly:
    hdf = pd.DataFrame({
        "Time": pd.to_datetime(hourly["time"]),
        "Temp (°C)": hourly.get("temperature_2m", []),
        "Humidity (%)": hourly.get("relative_humidity_2m", []),
        "Wind (m/s)": hourly.get("wind_speed_10m", []),
        "Rain Prob (%)": hourly.get("precipitation_probability", []),
        "Code": hourly.get("weathercode", []),
    })
    now = pd.Timestamp.utcnow().tz_localize("UTC")
    hdf = hdf[hdf["Time"] >= now].head(48).reset_index(drop=True)

    tab1, tab2, tab3 = st.tabs(["Temperature", "Humidity", "Wind"])
    with tab1:
        fig1 = px.line(hdf, x="Time", y="Temp (°C)", markers=True, title="Hourly Temperature (Next 48h)")
        st.plotly_chart(fig1, use_container_width=True)
    with tab2:
        fig2 = px.line(hdf, x="Time", y="Humidity (%)", markers=True, title="Hourly Humidity (Next 48h)")
        st.plotly_chart(fig2, use_container_width=True)
    with tab3:
        fig3 = px.line(hdf, x="Time", y="Wind (m/s)", markers=True, title="Hourly Wind Speed (Next 48h)")
        st.plotly_chart(fig3, use_container_width=True)

# --------------------- FOOTER ---------------------
st.markdown(
    "<p style='opacity:.7'>Data: Open‑Meteo • Theme: soft illustration background • Built with Streamlit</p>",
    unsafe_allow_html=True
)
