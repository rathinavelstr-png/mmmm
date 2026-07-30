import requests
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Coimbatore Weather Dashboard", page_icon="🌤️", layout="wide")

# ---------------------------------------------------------------------------
# Location: Coimbatore, Tamil Nadu, India
# ---------------------------------------------------------------------------
LATITUDE = 11.0168
LONGITUDE = 76.9558
LOCATION_NAME = "Coimbatore, Tamil Nadu"

# Open-Meteo is free and requires no API key
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


@st.cache_data(ttl=600)
def fetch_weather():
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,"
                   "precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
                 "precipitation_probability_max,wind_speed_10m_max",
        "timezone": "Asia/Kolkata",
        "forecast_days": 8,
    }
    response = requests.get(WEATHER_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title(f"🌤️ Weather Dashboard — {LOCATION_NAME}")
st.caption(f"Last updated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

try:
    data = fetch_weather()
except Exception as e:
    st.error(f"Could not fetch weather data: {e}")
    st.stop()

current = data["current"]
daily = data["daily"]

# --- Current conditions ---
st.header("Current Conditions")
condition = WEATHER_CODES.get(current["weather_code"], "Unknown")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Temperature", f"{current['temperature_2m']:.1f} °C")
col2.metric("Feels Like", f"{current['apparent_temperature']:.1f} °C")
col3.metric("Humidity", f"{current['relative_humidity_2m']:.0f}%")
col4.metric("Wind Speed", f"{current['wind_speed_10m']:.1f} km/h")
col5.metric("Condition", condition)

if current["precipitation"] > 0:
    st.info(f"🌧️ Currently raining: {current['precipitation']} mm")

# --- 8-day forecast table ---
st.header("8-Day Forecast")

forecast_df = pd.DataFrame({
    "Date": pd.to_datetime(daily["time"]),
    "Condition": [WEATHER_CODES.get(c, "Unknown") for c in daily["weather_code"]],
    "High (°C)": daily["temperature_2m_max"],
    "Low (°C)": daily["temperature_2m_min"],
    "Rain Chance (%)": daily["precipitation_probability_max"],
    "Max Wind (km/h)": daily["wind_speed_10m_max"],
})
forecast_df["Day"] = forecast_df["Date"].dt.strftime("%a, %d %b")

st.dataframe(
    forecast_df[["Day", "Condition", "High (°C)", "Low (°C)", "Rain Chance (%)", "Max Wind (km/h)"]],
    use_container_width=True,
    hide_index=True,
)

# --- Charts ---
col1, col2 = st.columns(2)

with col1:
    fig_temp = px.line(
        forecast_df,
        x="Day",
        y=["High (°C)", "Low (°C)"],
        title="Temperature Trend",
        markers=True,
    )
    fig_temp.update_layout(yaxis_title="Temperature (°C)", legend_title="")
    st.plotly_chart(fig_temp, use_container_width=True)

with col2:
    fig_rain = px.bar(
        forecast_df,
        x="Day",
        y="Rain Chance (%)",
        title="Rain Probability",
        color="Rain Chance (%)",
        color_continuous_scale="Blues",
    )
    st.plotly_chart(fig_rain, use_container_width=True)

st.caption("Data source: Open-Meteo (open-meteo.com) — free, no API key required.")
