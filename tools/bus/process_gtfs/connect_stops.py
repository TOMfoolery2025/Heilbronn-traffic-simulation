import os
import sys
import subprocess
import xml.etree.ElementTree as ET

# --- FILES ---
NET_FILE = "network/sumo/heilbronn.net.xml"
INPUT_STOPS = "intermediate/bus/sumo_stops_filtered.add.xml"    
INPUT_ROUTES = "intermediate/bus/sumo_routes_filtered.rou.xml" 
OUTPUT_TRIPS = "intermediate/bus/trips_connected.rou.xml"         
FINAL_ROUTES = "intermediate/bus/sumo_routes_connected.rou.xml"    

def get_edge_from_lane(lane_id):
    if not lane_id: return None
    return lane_id.rpartition('_')[0]

def main():
    print("--- 1. Mapping Stops to Edges ---")
    if not os.path.exists(INPUT_STOPS):
        sys.exit(f"Error: {INPUT_STOPS} not found.")

    stops_tree = ET.parse(INPUT_STOPS)
    stop_to_edge = {}
    for stop in stops_tree.getroot().findall('busStop'):
        s_id = stop.get('id')
        lane = stop.get('lane')
        edge = get_edge_from_lane(lane)
        if edge:
            stop_to_edge[s_id] = edge

    print("--- 2. Building & SORTING Trips ---")
    routes_tree = ET.parse(INPUT_ROUTES)
    routes_root = routes_tree.getroot()
    
    # Store tuples of (depart_time, element) so we can sort them
    trip_list = []
    vtypes = []

    # Copy vTypes
    for vtype in routes_root.findall('vType'):
        vtypes.append(vtype)
        
    skipped_count = 0
    
    for vehicle in routes_root.findall('vehicle'):
        veh_id = vehicle.get('id')
        stops = vehicle.findall('stop')
        depart = float(vehicle.get('depart', 0)) # Get time as float
        
        if len(stops) < 2:
            skipped_count += 1
            continue
            
        first_stop_id = stops[0].get('busStop')
        last_stop_id = stops[-1].get('busStop')
        
        start_edge = stop_to_edge.get(first_stop_id)
        end_edge = stop_to_edge.get(last_stop_id)
        
        if not start_edge or not end_edge:
            skipped_count += 1
            continue

        # Create Trip
        trip = ET.Element("trip")
        trip.set("id", veh_id)
        trip.set("type", vehicle.get("type", "bus_standard"))
        trip.set("depart", f"{depart:.2f}") # Ensure string format
        trip.set("from", start_edge)
        trip.set("to", end_edge)
            
        for s in stops:
            trip.append(s)
            
        # Add to list for sorting
        trip_list.append((depart, trip))

    # --- THE FIX: SORT BY TIME ---
    print(f"Sorting {len(trip_list)} trips by departure time...")
    trip_list.sort(key=lambda x: x[0]) # Sort by the first element (depart time)

    # Write sorted file
    trips_root = ET.Element("routes")
    for vt in vtypes:
        trips_root.append(vt)
    for _, trip_elem in trip_list:
        trips_root.append(trip_elem)
        
    ET.ElementTree(trips_root).write(OUTPUT_TRIPS)
    print(f"Saved sorted trips to {OUTPUT_TRIPS}")

    # --- 3. Run Duarouter (Robust Mode) ---
    print("--- 3. Running Duarouter ---")
    
    cmd = [
        "duarouter",
        "--net-file", NET_FILE,
        "--route-files", OUTPUT_TRIPS,
        "--additional-files", INPUT_STOPS,
        "--output-file", FINAL_ROUTES,
        "--ignore-errors",     # Drop vehicles with no path (don't crash)
        "--repair",            # Attempt to fix connectivity gaps
        "--remove-loops",      # Remove weird looping behavior
        # "--ignore-vclasses",   # CRITICAL: Allow buses to drive on car-only roads (idk lets see)
        "--no-step-log"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Check output
    warnings = [line for line in result.stderr.split('\n') if "Warning" in line]
    errors = [line for line in result.stderr.split('\n') if "Error" in line]
    successes = [line for line in result.stderr.split('\n') if "Success" in line]

    print(f"\nStats from Duarouter:")
    print(f"  - Warnings (usually disconnected stops): {len(warnings)}")
    print(f"  - Dropped Vehicles (Impossible routes): {len(errors)}")
    
    if os.path.exists(FINAL_ROUTES):
        print(f"\n✅ SUCCESS! Routes generated: {FINAL_ROUTES}")
        print("Use this file in your simulation.")
    else:
        print("\n❌ FAILED. No output file generated.")
        print(result.stderr)

if __name__ == "__main__":
    main()