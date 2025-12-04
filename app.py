import streamlit as st
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt
import json
import os

# -----------------------
# Page Config and Header
# -----------------------
st.set_page_config(
    page_title="🩸 Sanitary Pad Vending Finder",
    page_icon="🛒",
    layout="wide"
)

st.title("🩸 Sanitary Pad Vending Machine Finder")
st.markdown(
    """
Welcome! This app helps you **locate nearby sanitary pad vending machines** using your current location.  
Use the **map**, **filters**, and **search options** in the sidebar to find machines quickly.  
You can also **add new vending machine locations** which will be saved locally.
""",
    unsafe_allow_html=True
)
st.markdown("---")

# -----------------------
# Constants
# -----------------------
JSON_FILE = "vending_machines.json"


# -----------------------
# Utilities
# -----------------------
def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points"""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371 * c


def load_locations():
    """Load vending machine data from JSON, create sample if missing"""
    if not os.path.exists(JSON_FILE):
        sample_data = [
            {"name": "PadPoint Central", "lat": 12.971598, "lon": 77.594566, "open": True, "accessible": True,
             "stocked": True},
            {"name": "QuickPads Mall", "lat": 12.975000, "lon": 77.592000, "open": True, "accessible": False,
             "stocked": True},
            {"name": "SafeHygiene Hub", "lat": 12.969000, "lon": 77.597000, "open": False, "accessible": True,
             "stocked": False}
        ]
        with open(JSON_FILE, "w") as f:
            json.dump(sample_data, f, indent=4)
        return sample_data
    with open(JSON_FILE, "r") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
        except json.JSONDecodeError:
            return []


def save_location(vm):
    """Append a new vending machine to JSON"""
    data = load_locations()
    data.append(vm)
    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=4)


# -----------------------
# Sidebar Inputs
# -----------------------
st.sidebar.header("Your Location")
user_lat = st.sidebar.number_input("Latitude", value=12.9716, format="%.6f")
user_lon = st.sidebar.number_input("Longitude", value=77.5946, format="%.6f")

st.sidebar.header("Filters / Search")
radius_km = st.sidebar.slider("Radius (km)", 1, 20, 5)
search_term = st.sidebar.text_input("Search by name").lower()
filter_open = st.sidebar.checkbox("Open", value=True)
filter_accessible = st.sidebar.checkbox("Accessible", value=True)
filter_stocked = st.sidebar.checkbox("Stocked", value=True)

st.sidebar.header("Add New Vending Machine")
with st.sidebar.form("add_form"):
    name = st.text_input("Name")
    lat = st.number_input("Latitude", format="%.6f")
    lon = st.number_input("Longitude", format="%.6f")
    open_status = st.checkbox("Open", value=True)
    accessible_status = st.checkbox("Accessible", value=True)
    stocked_status = st.checkbox("Stocked", value=True)
    submitted = st.form_submit_button("Add")
    if submitted:
        if not name:
            st.sidebar.error("Name required")
        else:
            new_vm = {
                "name": name,
                "lat": lat,
                "lon": lon,
                "open": open_status,
                "accessible": accessible_status,
                "stocked": stocked_status
            }
            save_location(new_vm)
            st.sidebar.success(f"{name} added successfully!")
            st.sidebar.info("Refresh the app (F5) to see the updated vending machine list.")

# -----------------------
# Load & Filter Vending Machines
# -----------------------
vending_machines = load_locations()
filtered = []
for vm in vending_machines:
    vm_distance = haversine(user_lat, user_lon, vm["lat"], vm["lon"])
    vm["distance"] = vm_distance
    if vm_distance > radius_km:
        continue
    if search_term and search_term not in vm["name"].lower():
        continue
    if filter_open and not vm.get("open", True):
        continue
    if filter_accessible and not vm.get("accessible", True):
        continue
    if filter_stocked and not vm.get("stocked", True):
        continue
    filtered.append(vm)

filtered.sort(key=lambda x: x["distance"])

# -----------------------
# Map Display
# -----------------------
m = folium.Map(location=[user_lat, user_lon], zoom_start=15)
# User marker
folium.Marker([user_lat, user_lon], tooltip="You are here", icon=folium.Icon(color="blue")).add_to(m)

# Vending machine markers (red)
for vm in filtered:
    folium.Marker(
        location=[vm["lat"], vm["lon"]],
        tooltip=vm["name"],
        icon=folium.Icon(color="red", icon="info-sign"),
        popup=f"Distance: {vm['distance']:.2f} km\nOpen: {vm.get('open')}\nAccessible: {vm.get('accessible')}\nStocked: {vm.get('stocked')}"
    ).add_to(m)

st.subheader(f"Nearby Vending Machines ({len(filtered)})")
st_folium(m, width=700, height=500)

# -----------------------
# Streamlit-native Card UI
# -----------------------
st.subheader("Vending Machines Details")

if filtered:
    for vm in filtered:
        with st.container():
            st.markdown(f"### {vm['name']}")
            st.markdown(f"**Distance:** {vm['distance']:.2f} km")

            # Status badges in three columns
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"**Open:** {'✅' if vm.get('open', True) else '❌'}")
            col2.markdown(f"**Accessible:** {'✅' if vm.get('accessible', True) else '❌'}")
            col3.markdown(f"**Stocked:** {'✅' if vm.get('stocked', True) else '❌'}")

            st.markdown("---")  # Separator between cards
else:
    st.write("No vending machines found in the selected radius with current filters.")
