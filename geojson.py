import streamlit as st
import json

# Geojson is een formaat waarin eigenlijk een landkaart zit
@st.cache_data
def load_geojson():
    with open("the-netherlands.geojson", "r", encoding="utf-8") as f:
        return json.load(f)