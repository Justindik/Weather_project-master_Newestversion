import streamlit as st
import folium
import json
import asyncio
import python_weather
from datetime import datetime
import pytz
from streamlit_folium import st_folium


# pagina dingen
st.set_page_config(
    page_title="Weer App Nederland",
    layout="wide"
)

st.title("🇳🇱 Weer App Europa")
st.info("Selecteer of zoek een provincie")


# Geojson
@st.cache_data
def load_geojson():
    with open("the-netherlands.geojson", "r", encoding="utf-8") as f:
        return json.load(f)


geojson_data = load_geojson()

# lijst maken van de provincies
province_list = [f["properties"]["name"] for f in geojson_data["features"]]


# weer ophalen en async functies
async def get_weather(city):
    async with python_weather.Client(unit=python_weather.METRIC) as client:
        weather = await client.get(city)
        return weather


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return loop.run_until_complete(coro)
    except RuntimeError:
        pass
    return asyncio.run(coro)


# zijkant menu (sidebar)
st.sidebar.title("🗺️ Provincies")

# Streamlit zorgt er voor dat je kan typen en suggesties krijgt
selected_province = st.sidebar.selectbox(
    "🔍 Zoek provincie",
    options=province_list,
    index=None,
    placeholder="Typ een provincie..."
)


# huidige dag + tijd van Nederland
amsterdam_tz = pytz.timezone("Europe/Amsterdam")
now = datetime.now(amsterdam_tz)

dagen_nl = {
    0: "Maandag",
    1: "Dinsdag",
    2: "Woensdag",
    3: "Donderdag",
    4: "Vrijdag",
    5: "Zaterdag",
    6: "Zondag"
}

dag_tijd = f"{dagen_nl[now.weekday()]} {now.strftime('%H:%M')}"

st.sidebar.markdown(f"### 🕒 {dag_tijd}")
st.sidebar.markdown("--------")


# kaart kleur en stijl
def style(feature):
    name = feature["properties"]["name"]
    # Kleur de provincie oranje als deze overeenkomt met de uiteindelijke selectie
    match = selected_province and selected_province.lower() == name.lower()
    return {
        "fillColor": "orange" if match else "turquoise",
        "color": "black",
        "weight": 2 if match else 1,
        "fillOpacity": 0.6 if match else 0.3,
    }


# map maken met de coordinaten
min_lat, max_lat = 50.5, 54.0
min_lon, max_lon = 3.0, 7.5

m = folium.Map(
    location=[52.2130, 5.2794],
    zoom_start=8,
    min_zoom=7,
    max_zoom=11,
    max_bounds=True,
    min_lat=min_lat,
    max_lat=max_lat,
    min_lon=min_lon,
    max_lon=max_lon
)


# We bouwen de GeoJson op basis van de huidige selectie
folium.GeoJson(
    geojson_data,
    style_function=style,
    highlight_function=lambda f: {
        "fillColor": "yellow",
        "color": "red",
        "weight": 3,
        "fillOpacity": 0.7,
    },
    tooltip=folium.GeoJsonTooltip(fields=["name"])
).add_to(m)

output = st_folium(m, height=500, use_container_width=True)


# Als er niet gezocht is via de balk, maar wel op de kaart geklikt is, update de selectie
if not selected_province and output.get("last_active_drawing"):
    selected_province = output["last_active_drawing"]["properties"]["name"]



# WEATHER INFO DISPLAY (Nederlands)

# dagen afkortingen voor voorspelling
dagen_kort_nl = {0: "Maandag", 1: "Dinsdag", 2: "Woensdag", 3: "Donderdag", 4: "Vrijdag", 5: "Zaterdag", 6: "Zondag"}

if selected_province:
    try:
        weather = run_async(get_weather(selected_province))
        forecasts = list(weather.daily_forecasts)

        # 1. info laten zien op de sidebar
        st.sidebar.markdown(f"## 📍 {selected_province}")
        st.sidebar.info(f"**Status:** {weather.description}")

        if forecasts:
            st.sidebar.write("🌅 Zonsopkomst: 05:42")
            st.sidebar.write("🌇 Zonsondergang: 21:35")

        # 2. grote metrics op het scherm
        st.subheader(f"📊 Live Weerrapport {selected_province}")

        col1, col2, col3 = st.columns(3)
        col1.metric("🌡️ Temperatuur", f"{weather.temperature}°C")
        col2.metric("💧 Luchtvochtigheid", f"{weather.humidity}%")
        col3.metric("💨 Windsnelheid", f"{weather.wind_speed} km/h")

        # 3. 3 dagen voorspelling hieronder
        st.markdown("### 📅 3-Daagse Voorspelling")
        cols = st.columns(3)

        for i in range(min(3, len(forecasts))):
            dag = forecasts[i]

            if i == 0:
                dag_naam = "VANDAAG"
            elif i == 1:
                dag_naam = "MORGEN"
            else:
                dag_naam = dagen_kort_nl[dag.date.weekday()]

            with cols[i]:
                st.info(dag_naam)
                st.write(f"Max: **{dag.highest_temperature}°C**")
                st.write(f"Min: **{dag.lowest_temperature}°C**")

    except Exception as e:
        st.sidebar.error("Fout bij het laden van het weer.")
        st.error(f"Foutdetails: {e}")

else:
    st.sidebar.warning("⚠️ Zoek een provincie of klik op de kaart om het weer te bekijken.")