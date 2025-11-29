import os
import subprocess
import sys

def run_random_trips(begin, end, period, output, prefix):
    # Ensure SUMO_HOME is set
    SUMO_HOME = os.environ.get("SUMO_HOME")
    if not SUMO_HOME:
        sys.exit("Error: Please declare environment variable 'SUMO_HOME'")
        
    randomTrips = os.path.join(SUMO_HOME, "tools", "randomTrips.py")
    NETWORK = "network/sumo/heilbronn.net.xml"

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
        "--allow-fringe",
        "--vehicle-class", "passenger",
        "--validate",
        "--prefix", prefix  # <--- THIS FIXES THE ID CONFLICT
    ]

    # Run silently
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    print(f"  > Generated: {output} (IDs start with '{prefix}')")


def generate_random_cars():
    # Output paths
    base_dir = "intermediate/car"
    os.makedirs(base_dir, exist_ok=True)
    
    final_output = os.path.join(base_dir, "sumo_cars.rou.xml")

    # Defined windows: (Start, End, Period, Filename, ID_Prefix)
    windows = [
        (0,     21600, 5.0, "night.xml",    "night_"),    # IDs: night_0, night_1...
        (21600, 32400, 0.7, "morning.xml",  "morning_"),  # IDs: morning_0...
        (32400, 57600, 1.5, "day.xml",      "day_"),
        (57600, 68400, 0.7, "evening.xml",  "evening_"),
        (68400, 79200, 2.0, "late.xml",     "late_"),
        (79200, 86400, 4.0, "midnight.xml", "mid_"),
    ]

    print("--- Generating Traffic Segments ---")
    generated_files = []

    # 1. Generate individual segments
    for begin, end, period, filename, prefix in windows:
        filepath = os.path.join(base_dir, filename)
        run_random_trips(begin, end, period, filepath, prefix)
        generated_files.append(filepath)

    print("\n--- Merging Files ---")
    
    # # 2. Merge into one single XML file
    # with open(final_output, "w") as outfile:
    #     outfile.write("<routes>\n")
        
    #     for i, fname in enumerate(generated_files):
    #         with open(fname, "r") as infile:
    #             for line in infile:
    #                 # XML Cleanup Logic
    #                 if "<?xml" in line or "<routes" in line or "</routes>" in line:
    #                     continue
                    
    #                 # Handle duplicate vType definitions
    #                 # Only write the vType from the very first file (night.xml)
    #                 if "<vType" in line and i > 0:
    #                     continue
                        
    #                 outfile.write(line)

    #     outfile.write("</routes>\n")

    # print(f"✅ Success! Combined routes saved to: {final_output}")

    # # 3. Cleanup
    # print("--- Cleaning up temporary files ---")
    # for fname in generated_files:
    #     if os.path.exists(fname):
    #         os.remove(fname)
    # print("Cleaned up.")

if __name__ == "__main__":
    generate_random_cars()