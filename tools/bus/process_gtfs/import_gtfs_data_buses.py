import os
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import datetime
import sys

# --- CONFIGURATION ---
FILES = {
    'stops': 'network/bus/stops.txt',
    'routes': 'network/bus/routes.txt',
    'trips': 'network/bus/trips.txt',
    'stop_times': 'network/bus/stop_times.txt',
    'calendar': 'network/bus/calendar.txt',
    'calendar_dates': 'network/bus/calendar_dates.txt',
}

def get_user_date():
    """Prompts the user via console to input a date."""
    print("-" * 40)
    print("GTFS TO SUMO: PHYSICAL BUS GENERATOR")
    print("-" * 40)
    while True:
        user_input = input("Please enter the date to simulate (YYYYMMDD): ").strip()
        if len(user_input) == 8 and user_input.isdigit():
            try:
                datetime.datetime.strptime(user_input, "%Y%m%d")
                return user_input
            except ValueError:
                print("Error: Invalid calendar date.")
        else:
            print("Error: Use format YYYYMMDD.")

def get_active_services(target_date_str):
    """Returns a set of service_ids active on the target date."""
    active_services = set()
    try:
        target_date = datetime.datetime.strptime(target_date_str, "%Y%m%d")
        day_of_week = target_date.strftime("%A").lower()
    except ValueError:
        return set()

    # 1. Calendar
    try:
        cal = pd.read_csv(FILES['calendar'], dtype=str)
        for _, row in cal.iterrows():
            start = datetime.datetime.strptime(row['start_date'], "%Y%m%d")
            end = datetime.datetime.strptime(row['end_date'], "%Y%m%d")
            if start <= target_date <= end:
                if row.get(day_of_week) == '1':
                    active_services.add(row['service_id'])
    except: pass

    # 2. Calendar Dates
    try:
        cal_dates = pd.read_csv(FILES['calendar_dates'], dtype=str)
        relevant = cal_dates[cal_dates['date'] == target_date_str]
        for _, row in relevant.iterrows():
            if row['exception_type'] == '1': active_services.add(row['service_id'])
            elif row['exception_type'] == '2': active_services.discard(row['service_id'])
    except: pass

    return active_services

def seconds_from_midnight(time_str):
    try:
        if pd.isna(time_str): return 0
        parts = list(map(int, time_str.split(':')))
        # Handle cases like 25:00:00 (1 AM next day)
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    except:
        return 0

def prettify_xml(elem):
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

def create_stops_xml(stops_df):
    root = ET.Element("additional")
    print(f"Processing {len(stops_df)} stops...")
    for _, row in stops_df.iterrows():
        stop = ET.SubElement(root, "busStop")
        stop.set("id", str(row['stop_id']))
        stop.set("name", str(row['stop_name']))
        stop.set("lat", str(row['stop_lat']))
        stop.set("lon", str(row['stop_lon']))
    return prettify_xml(root)

# --- THE MAGIC FUNCTION ---
def create_routes_xml_blocks(trips_df, stop_times_df, active_services, target_date):
    root = ET.Element("routes")
    
    # 1. Define ONE bus type
    vtype = ET.SubElement(root, "vType")
    vtype.set("id", "bus_standard")
    vtype.set("vClass", "ignoring") 
    vtype.set("accel", "2.0")
    vtype.set("decel", "4.0")
    vtype.set("length", "12")
    
    # 2. Filter Data
    print(f"Total trips available: {len(trips_df)}")
    trips_df = trips_df[trips_df['service_id'].isin(active_services)]
    print(f"Trips active on {target_date}: {len(trips_df)}")

    valid_trip_ids = set(trips_df['trip_id'])
    stop_times_df = stop_times_df[stop_times_df['trip_id'].isin(valid_trip_ids)]
    
    # Group stop times for fast access
    stop_times_grouped = stop_times_df.groupby('trip_id')

    # 3. GROUP BY BLOCK_ID
    # This is what forces the "wait for arrival" logic.
    # If block_id is missing, we use trip_id (fallback to 1 trip = 1 bus)
    if 'block_id' not in trips_df.columns:
        print("Warning: block_id column missing. Fallback to single trips.")
        trips_df['block_id'] = trips_df['trip_id']
    else:
        # If specific rows have empty blocks, fill them
        trips_df['block_id'] = trips_df['block_id'].fillna(trips_df['trip_id'])

    blocks_grouped = trips_df.groupby('block_id')
    print("-" * 30)
    print(f"CONVERTING {len(trips_df)} TRIPS INTO {len(blocks_grouped)} PHYSICAL BUSES")
    print("-" * 30)

    vehicle_count = 0

    for block_id, block_trips in blocks_grouped:
        # A. Collect Start Times for all trips in this block
        trip_sequence = []
        
        for _, trip in block_trips.iterrows():
            t_id = trip['trip_id']
            if t_id in stop_times_grouped.groups:
                # Get the VERY FIRST stop of this trip
                first_stop = stop_times_grouped.get_group(t_id).sort_values('stop_sequence').iloc[0]
                start_sec = seconds_from_midnight(first_stop['arrival_time'])
                trip_sequence.append({
                    'start_time': start_sec,
                    'trip_id': t_id,
                    'route_id': trip['route_id']
                })
        
        # B. Sort trips chronologically (Trip 1 -> Trip 2 -> Trip 3)
        trip_sequence.sort(key=lambda x: x['start_time'])

        if not trip_sequence:
            continue

        # C. Create ONE Vehicle Element
        # The vehicle spawns ONCE at the beginning of the first trip.
        first_trip = trip_sequence[0]
        
        vehicle = ET.SubElement(root, "vehicle")
        vehicle.set("id", str(block_id)) # ID is the Block (Physical Bus)
        vehicle.set("type", "bus_standard")
        vehicle.set("depart", str(first_trip['start_time']))
        vehicle.set("color", "1,0,0") 

        # D. Add stops for ALL trips in the chain
        for trip_data in trip_sequence:
            t_id = trip_data['trip_id']
            route_name = trip_data['route_id']
            
            stops = stop_times_grouped.get_group(t_id).sort_values('stop_sequence')
            
            for _, stop_row in stops.iterrows():
                arrival = seconds_from_midnight(stop_row['arrival_time'])
                departure = seconds_from_midnight(stop_row['departure_time'])
                
                # Calculate duration (dwell time)
                duration = max(0, departure - arrival)
                
                stop_elem = ET.SubElement(vehicle, "stop")
                stop_elem.set("busStop", str(stop_row['stop_id']))
                stop_elem.set("duration", str(duration))
                
                # OPTIONAL: "until"
                # If you uncomment this, the bus will wait at the stop until the schedule says so.
                # If you leave it commented, the bus leaves as soon as 'duration' is over.
                # stop_elem.set("until", str(departure))

        vehicle_count += 1

    return prettify_xml(root)

def main():
    print("Loading GTFS files...")
    stops = pd.read_csv(FILES['stops'], dtype=str)
    trips = pd.read_csv(FILES['trips'], dtype=str)
    stop_times = pd.read_csv(FILES['stop_times'], dtype=str)
    stop_times['stop_sequence'] = stop_times['stop_sequence'].astype(int)

    target_date = get_user_date()
    active_services = get_active_services(target_date)
    
    if not active_services:
        print("CRITICAL: No active services. Check date.")
        return

    # Generate
    OUTPUT_DIR = "intermediate/bus" 
    os.makedirs(OUTPUT_DIR, exist_ok=True) 

    # 1. Stops
    with open(os.path.join(OUTPUT_DIR, "sumo_stops.add.xml"), "w", encoding="utf-8") as f:
        f.write(create_stops_xml(stops))
    
    # 2. Routes (The Block Version)
    with open(os.path.join(OUTPUT_DIR, "sumo_routes.rou.xml"), "w", encoding="utf-8") as f:
        f.write(create_routes_xml_blocks(trips, stop_times, active_services, target_date))
        
    print("\nSUCCESS. Please run the rest of your pipeline (Connect -> Run).")

if __name__ == "__main__":
    main()