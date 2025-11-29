import os
import sys
import datetime
import xml.etree.ElementTree as ET
import folium
from folium.plugins import TimestampedGeoJson
import sumolib

# --- CONFIGURATION ---
# Robust paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))

NET_FILE = os.path.join(PROJECT_ROOT, "network", "sumo", "heilbronn.net.xml")

# Change this line to point to your car FCD output
TRACE_FILE = os.path.join(PROJECT_ROOT, "results", "trace.xml")

OUTPUT_HTML = os.path.join(PROJECT_ROOT, "results", "interactive_cars.html")

# Visualization Settings
MAX_FRAMES = 86400  # render up to 1 day max
START_DATE = datetime.datetime(2025, 11, 28, 8, 0, 0) # Fake start timestamp


def main():
    print("--- 1. LOADING NETWORK & PROJECTION ---")
    net = sumolib.net.readNet(NET_FILE)

    bbox = net.getBoundary()
    center_x = (bbox[0] + bbox[2]) / 2
    center_y = (bbox[1] + bbox[3]) / 2
    center_lon, center_lat = net.convertXY2LonLat(center_x, center_y)

    print(f"   Map Center: {center_lat:.5f}, {center_lon:.5f}")

    print("--- 2. PARSING CAR TRACE DATA ---")
    features = []
    
    context = ET.iterparse(TRACE_FILE, events=("start", "end"))
    context = iter(context)
    event, root = next(context)

    count = 0
    first_sim_time = None

    for event, elem in context:
        if event == "end" and elem.tag == "timestep":
            t = float(elem.attrib['time'])
            if t > MAX_FRAMES:
                break

            if first_sim_time is None:
                first_sim_time = t
                print(f"   Visualizer detected start at t={t}s")

            if t > (first_sim_time + MAX_FRAMES):
                break

            time_str = (START_DATE + datetime.timedelta(seconds=t)).isoformat()

            # iterate over vehicles
            for veh in elem.findall("vehicle"):
                x = float(veh.attrib["x"])
                y = float(veh.attrib["y"])
                v_type = veh.attrib.get("type", "car")  # fallback
                car_id = veh.attrib["id"]

                lon, lat = net.convertXY2LonLat(x, y)

                # styling for cars
                if "truck" in v_type:
                    color = "#e67e22"
                    radius = 6
                else:
                    color = "#3498db"
                    radius = 1

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat],
                    },
                    "properties": {
                        "time": time_str,
                        "popup": f"Car {car_id}",
                        "icon": "circle",
                        "iconstyle": {
                            "fillColor": color,
                            "fillOpacity": 0.8,
                            "stroke": "false",
                            "radius": radius
                        }
                    }
                }

                features.append(feature)
                count += 1

            root.clear()

    print(f"   Processed {count} car positions.")

    print("--- 3. BUILDING INTERACTIVE MAP ---")
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=17,
        tiles="CartoDB dark_matter"
    )

    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="PT1S",
        add_last_point=False,
        auto_play=False,
        loop=False,
        max_speed=60,
        loop_button=True,
        date_options="HH:mm:ss",
        time_slider_drag_update=True,
        duration="PT0S"
    ).add_to(m)

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    m.save(OUTPUT_HTML)

    print(f"✅ CAR MAP GENERATED: {OUTPUT_HTML}")
    print("   → Open this file in a browser to see the visualization")


if __name__ == "__main__":
    main()
