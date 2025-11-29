import os
import sys
import xml.etree.ElementTree as ET

# --- Configuration ---
NET_FILE = "network/sumo/heilbronn.net.xml"             # Your OSM Network file
INPUT_STOPS = "intermediate/bus/sumo_stops.add.xml"   # The raw stops from step 1
INPUT_ROUTES = "intermediate/bus/sumo_routes.rou.xml" # The raw routes from step 1
OUTPUT_STOPS = "intermediate/bus/sumo_stops_filtered.add.xml"
OUTPUT_ROUTES = "intermediate/bus/sumo_routes_filtered.rou.xml"
# OUTPUT_STOPS_DISCARDED = "intermediate/bus/sumo_stops_discarded.add.xml" # For debugging

# --- Bounding Box (Heilbronn Area) ---
MIN_LAT = 49.1375900
MIN_LON = 9.2056000
MAX_LAT = 49.1639200
MAX_LON = 9.2360700

# --- Search Parameters ---
LANE_SEARCH_RADIUS = 50.0  # meters to look for a suitable lane
BUS_STOP_LENGTH = 12.0     # meters


# --- Import Sumolib ---
if 'SUMO_HOME' in os.environ:
    sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
    sys.exit("Error: Please set 'SUMO_HOME' environment variable or install sumolib")
import sumolib

def main():
    print(f"Loading network: {NET_FILE}...")
    try:
        net = sumolib.net.readNet(NET_FILE)
    except Exception as e:
        print(f"CRITICAL ERROR: Could not load map. {e}")
        return

    # ---------------------------------------------------------
    # PART 1: Process Stops (Filter by Area -> Map to Lane)
    # ---------------------------------------------------------
    print("Processing Bus Stops...")
    stops_tree = ET.parse(INPUT_STOPS)
    stops_root = stops_tree.getroot()
    
    valid_stop_ids = set()
    stops_to_remove = []
    
    # For debugging: create a separate file for discarded stops
    discarded_stops_root = ET.Element('additional')
    
    # Counters for statistics
    count_total = 0
    count_outside_box = 0
    count_no_road = 0

    for stop in stops_root.findall('busStop'):
        count_total += 1
        try:
            lat = float(stop.get('lat'))
            lon = float(stop.get('lon'))
            stop_id = stop.get('id')

            # 1. BOUNDING BOX FILTER: If the stop is outside the box, mark for removal
            if not (MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON):
                stops_to_remove.append(stop)
                count_outside_box += 1
                stop.set('color', '1,0,0') # Red for out of bounds
                stop.set('comment', 'Removed: Outside bounding box')
                discarded_stops_root.append(stop)
                continue

            # 2. CONVERT & MAP TO LANE
            x, y = net.convertLonLat2XY(lon, lat)
            
            # Look for a bus-friendly lane within 50 meters
            lanes = net.getNeighboringLanes(x, y, LANE_SEARCH_RADIUS, includeJunctions=False)
            best_lane = None
            best_dist = float('inf')

            for lane, dist in lanes:
                # Must allow bus and be the closest one found
                if lane.allows("bus") and dist < best_dist:
                    best_lane = lane
                    best_dist = dist

            if best_lane:
                # Calculate position on the lane
                lane_shape = best_lane.getShape()
                pos_on_lane, _ = sumolib.geomhelper.polygonOffsetAndDistanceToPoint((x,y), lane_shape)
                
                lane_len = best_lane.getLength()
                half_stop_len = BUS_STOP_LENGTH / 2
                
                # Center the stop (12m long) around the matched point
                start_pos = max(0, pos_on_lane - half_stop_len)
                end_pos = min(lane_len, start_pos + BUS_STOP_LENGTH)
                
                if end_pos - start_pos < 10:
                    start_pos = max(0, lane_len - 12)
                    end_pos = lane_len

                stop.set('lane', best_lane.getID())
                stop.set('startPos', f"{start_pos:.2f}")
                stop.set('endPos', f"{end_pos:.2f}")
                
                valid_stop_ids.add(stop_id)
            else:
                # Inside the box, but no road found (e.g., inside a building or private area)
                stops_to_remove.append(stop)
                count_no_road += 1
                stop.set('color', '1,1,0') # Yellow for no road
                stop.set('comment', 'Removed: No suitable road found nearby')
                discarded_stops_root.append(stop)

        except (ValueError, TypeError):
            stops_to_remove.append(stop)

    # Remove the invalid stops from the XML structure
    print(f"  > Total stops processed: {count_total}")
    for stop in stops_to_remove:
        stops_root.remove(stop)
        
    # --- Print statistics ---
    print(f"  > Stops removed (outside bounding box): {count_outside_box}")
    print(f"  > Stops removed (no nearby road): {count_no_road}")
    print(f"  > Final valid stops in area: {len(valid_stop_ids)}")

    # Write the debugging file for discarded stops
    # ET.ElementTree(discarded_stops_root).write(OUTPUT_STOPS_DISCARDED, encoding="utf-8", xml_declaration=True)
    # print(f"  > Discarded stops saved to {OUTPUT_STOPS_DISCARDED} for debugging.")
    stops_tree.write(OUTPUT_STOPS, encoding="utf-8", xml_declaration=True)

    # ---------------------------------------------------------
    # PART 2: Clean Routes (Remove deleted stops)
    # ---------------------------------------------------------
    print("Cleaning Routes...")
    routes_tree = ET.parse(INPUT_ROUTES)
    routes_root = routes_tree.getroot()
    
    vehicles_to_remove = []
    
    for vehicle in routes_root.findall('vehicle'):
        stops = vehicle.findall('stop')
        valid_stops_in_trip = 0
        
        for stop in stops:
            bus_stop_id = stop.get('busStop')
            # Check if this stop ID survived the filtering above
            if bus_stop_id in valid_stop_ids:
                valid_stops_in_trip += 1
            else:
                # Remove this specific stop from the vehicle's plan
                vehicle.remove(stop)
        
        # If the bus has fewer than 2 stops left, it can't really "drive" a route
        # (You can change this to '0' if you want buses that just appear and stand still)
        if valid_stops_in_trip < 2:
            vehicles_to_remove.append(vehicle)

    for veh in vehicles_to_remove:
        routes_root.remove(veh)

    print(f"  > Removed {len(vehicles_to_remove)} trips/vehicles that had < 2 stops in the area.")
    
    routes_tree.write(OUTPUT_ROUTES, encoding="utf-8", xml_declaration=True)
    print("Done! Files saved.")

if __name__ == "__main__":
    main()