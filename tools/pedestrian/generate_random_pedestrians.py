import os
import subprocess
import sys

def run_random_trips(begin, end, period, output, prefix):
    # Ensure SUMO_HOME is set
    SUMO_HOME = os.environ.get("SUMO_HOME")
    if not SUMO_HOME:
        sys.exit("Error: Please declare environment variable 'SUMO_HOME'")
        
    randomTrips = os.path.join(SUMO_HOME, "tools", "randomTrips.py")
    NETWORK = "network/sumo/heilbronn.net.xml" # Points to your NEW small map

    cmd = [
        sys.executable, randomTrips,
        "-n", NETWORK,
        "-o", output,
        "--seed", "42",
        "--begin", str(begin),
        "--end", str(end),
        "--period", str(period),
        "--binomial", "3",
        "--min-distance", "200",
        "--persontrips",      # Generates walking persons
        "--validate",         # Crucial: Checks validity against CURRENT map
        "--prefix", prefix 
    ]

    # Run silently
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    print(f"  > Generated segment: {output}")


def generate_random_pedestrians():
    # Output paths
    base_dir = "intermediate/pedestrian"
    os.makedirs(base_dir, exist_ok=True)
    
    final_output = os.path.join(base_dir, "sumo_pedestrians.rou.xml")

    # Defined windows: (Start, End, Period, Filename, ID_Prefix)
    windows = [
        (0,     21600, 5.0, "night.xml",    "p_night_"),    
        (21600, 32400, 0.7, "morning.xml",  "p_morn_"),  
        (32400, 57600, 1.5, "day.xml",      "p_day_"),
        (57600, 68400, 0.7, "evening.xml",  "p_eve_"),
        (68400, 79200, 2.0, "late.xml",     "p_late_"),
        (79200, 86400, 4.0, "midnight.xml", "p_mid_"),
    ]

    print("--- Generating Pedestrian Segments ---")
    generated_files = []

    # 2. Generate individual segments
    for begin, end, period, filename, prefix in windows:
        filepath = os.path.join(base_dir, filename)
        run_random_trips(begin, end, period, filepath, prefix)
        generated_files.append(filepath)

    print("\n--- Merging Files ---")
    
    # 3. MERGE LOGIC (UNCOMMENTED)
    with open(final_output, "w") as outfile:
        outfile.write("<routes>\n")
        
        for i, fname in enumerate(generated_files):
            if not os.path.exists(fname): continue

            with open(fname, "r") as infile:
                for line in infile:
                    # XML Cleanup Logic
                    if "<?xml" in line or "<routes" in line or "</routes>" in line:
                        continue
                    
                    # Handle duplicate vType definitions
                    # randomTrips defines a default 'person' type in every file.
                    # We only want to write it for the FIRST file (i==0).
                    if "<vType" in line and i > 0:
                        continue
                        
                    outfile.write(line)

        outfile.write("</routes>\n")

    print(f"✅ Success! Combined routes saved to: {final_output}")

    # 4. Cleanup
    for fname in generated_files:
        if os.path.exists(fname):
            os.remove(fname)

if __name__ == "__main__":
    generate_random_pedestrians()