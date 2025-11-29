import os
import sys
import datetime
import xml.etree.ElementTree as ET
import folium
from folium.plugins import TimestampedGeoJson
import sumolib

# --- CONFIGURATION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
NET_FILE = os.path.join(PROJECT_ROOT, "network", "sumo", "heilbronn.net.xml")
TRACE_FILE = os.path.join(PROJECT_ROOT, "results","trace.xml")
OUTPUT_HTML = os.path.join(PROJECT_ROOT, "results", "interactive_map.html")

# Optimization Settings
MAX_FRAMES = 86400  
START_DATE = datetime.datetime(2025, 11, 28, 8, 0, 0)
SKIP_FRAMES = 5  # Only render every 5th second (Huge performance boost)
STATIONARY_THRESHOLD = 180  # Despawn if stationary for this many seconds


def main():
    print("--- 1. LOADING NETWORK ---")
    net = sumolib.net.readNet(NET_FILE)
    bbox = net.getBoundary()
    center_lon, center_lat = net.convertXY2LonLat((bbox[0]+bbox[2])/2, (bbox[1]+bbox[3])/2)
    
    print("--- 2. PARSING TRACE (FAST MODE) ---")
    features = []
    
    context = ET.iterparse(TRACE_FILE, events=("start", "end"))
    context = iter(context)
    event, root = next(context)

    vehicle_tracking = {}  # {vehicle_id: {'last_pos': (x,y), 'last_move_time': t, 'last_seen': t}}
    despawn_times = {}  # {vehicle_id: despawn_time}


    count = 0
    frames_processed = 0
    first_sim_time = None

    for event, elem in context:
        if event == "end" and elem.tag == "timestep":
            t = float(elem.attrib['time'])
            
            # Skip frames logic
            if int(t) % SKIP_FRAMES != 0:
                root.clear()
                continue

            if first_sim_time is None:
                first_sim_time = t
                print(f"   Start detected at: {t}s")
            
            if t > (first_sim_time + MAX_FRAMES):
                break

            time_str = (START_DATE + datetime.timedelta(seconds=t)).isoformat()

            for veh in elem.findall('vehicle'):
                x, y = float(veh.attrib['x']), float(veh.attrib['y'])
                v_type = veh.attrib['type']
                bus_id = veh.attrib['id']

                # Initialize tracking for new vehicles
                if bus_id not in vehicle_tracking:
                    vehicle_tracking[bus_id] = {
                        'last_pos': (x, y),
                        'last_move_time': t,
                        'last_seen': t
                    }
                else:
                    # Check if vehicle has moved (tolerance of 0.5 meters)
                    last_x, last_y = vehicle_tracking[bus_id]['last_pos']
                    distance = ((x - last_x)**2 + (y - last_y)**2)**0.5
                    
                    if distance > 0.5:  # Vehicle moved
                        vehicle_tracking[bus_id]['last_pos'] = (x, y)
                        vehicle_tracking[bus_id]['last_move_time'] = t
                    
                    vehicle_tracking[bus_id]['last_seen'] = t
                    
                    # Check if stationary too long
                    stationary_duration = t - vehicle_tracking[bus_id]['last_move_time']
                    if stationary_duration > STATIONARY_THRESHOLD and bus_id not in despawn_times:
                        despawn_times[bus_id] = t
                        print(f"    Bus {bus_id} stationary for {stationary_duration:.0f}s - marking for despawn")
                        continue  # Don't add more features for this bus
                
                # Skip if already marked for despawn
                if bus_id in despawn_times:
                    continue

                
                lon, lat = net.convertXY2LonLat(x, y)
                
                # Style
                color = "#3498db"
                radius = 2
                if 'bus' in v_type:
                    color = '#e74c3c'
                    radius = 5
            
                features.append({
                    'type': 'Feature',
                    'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                    'properties': {
                        'time': time_str,
                        'popup': bus_id,
                        'icon': 'circle',
                        'iconstyle': {
                            'fillColor': color, 
                            'fillOpacity': 0.8, 
                            'stroke': 'false', 
                            'radius': radius
                        }
                    }
                })
                count += 1
            
            frames_processed += 1
            root.clear() # Clear memory

    for p in elem.findall('person'):
        x, y = float(p.attrib['x']), float(p.attrib['y'])
        p_id = p.attrib['id']
        
        lon, lat = net.convertXY2LonLat(x, y)

        # Person Style
        color = "#f1c40f" # Default Pedestrian (Yellow)
        radius = 1      # Smaller than cars

        features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
            'properties': {
                'time': time_str,
                'popup': p_id,
                'icon': 'circle',
                'iconstyle': {
                    'fillColor': color, 
                    'fillOpacity': 0.9, 
                    'stroke': 'false', 
                    'radius': radius
                }
            }
        })
        count += 1
    
    frames_processed += 1
    root.clear() # Clear memory
            
    print(f"   Processed {count} positions across {frames_processed} frames.")

    print("--- 3. BUILDING MAP ---")
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles='CartoDB dark_matter')

    # Calculate duration string to match SKIP_FRAMES
    # PT5S means the point stays on screen for 5 seconds

    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': features},
        period='PT5S',
        duration='PT0S', 
        add_last_point=False,
        auto_play=False,
        loop=False,
        max_speed=20,
        loop_button=True,
        date_options='HH:mm:ss'
    ).add_to(m)

    m.save(OUTPUT_HTML)
    print(f"✅ MAP GENERATED: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()