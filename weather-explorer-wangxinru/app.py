import streamlit as st
import requests
import pandas as pd
import datetime
import plotly.express as px
from streamlit_folium import st_folium
import folium

# ---- CONFIG ----
st.set_page_config(page_title="Weather Explorer • wang xinru", page_icon="⛅", layout="wide")

# ---- TITLE ----
st.title("Weather Explorer • wang xinru")
st.caption("Interactive weather app: click the map to view real-time and forecast data")

# ---- MAP SELECTION ----
st.subheader("📍 Select a location on the map")
default_location = [37.5665, 126.9780]  # Seoul
m = folium.Map(location=default_location, zoom_start=4)
folium.Marker(default_location, tooltip="Default: Seoul").add_to(m)
map_data = st_folium(m, width=700, height=450)
coords = map_data.get("last_clicked")

if coords:
    lat, lon = coords["lat"], coords["lng"]
else:
    lat, lon = default_location

# ---- WEATHER FETCH ----
@st.cache_data(ttl=600)
def get_weather(lat, lon):
    # Using free no-key API from open-meteo.com
    current_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&current_weather=true"
        f"&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    )
    r = requests.get(current_url, timeout=20)
    r.raise_for_status()
    return r.json()

data = get_weather(lat, lon)

if data and "current_weather" in data:
    current = data["current_weather"]
    st.subheader("🌤 Current Weather")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Temperature (°C)", f"{current['temperature']}°C")
    col2.metric("Weather", current.get("weathercode", 'N/A'))
    col3.metric("Wind Speed (m/s)", current['windspeed'])
    col4.metric("Time", current['time'])
else:
    st.warning("Unable to fetch current weather data.")

# ---- FORECAST ----
if "daily" in data:
    st.subheader("📆 7-Day Forecast")
    daily = data["daily"]
    df = pd.DataFrame({
        "Date": daily["time"],
        "Max Temp (°C)": daily["temperature_2m_max"],
        "Min Temp (°C)": daily["temperature_2m_min"]
    })
    st.dataframe(df)

    # ---- TEMPERATURE CHART ----
    fig = px.line(df, x="Date", y=["Max Temp (°C)", "Min Temp (°C)"],
                  labels={"value": "Temperature (°C)", "variable": "Type"},
                  title="Temperature Forecast Trend")
    st.plotly_chart(fig, use_container_width=True)

# ---- BACKGROUND STYLE ----
bg_image = None
if data.get("current_weather"):
    temp = data["current_weather"]["temperature"]
    if temp > 30:
        bg_image = "https://i.imgur.com/Wj5np6T.jpg"  # hot sunny
    elif temp > 20:
        bg_image = "https://i.imgur.com/ziKtW0D.jpg"  # warm
    elif temp > 10:
        bg_image = "https://i.imgur.com/9vAEpSj.jpg"  # cool
    else:
        bg_image = "https://i.imgur.com/pf62vOX.jpg"  # cold

if bg_image:
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background: url('{bg_image}') no-repeat center center fixed;
            background-size: cover;
        }}
        </style>
        """, unsafe_allow_html=True)
