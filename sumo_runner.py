import os, sys

# --- TraCI Path Setup ---
# 1. Define the exact path to the SUMO tools directory
SUMO_TOOLS_PATH = "/Library/Frameworks/EclipseSUMO.framework/Versions/1.25.0/EclipseSUMO/share/sumo/tools"

# 2. Add the tools directory to the Python path
if SUMO_TOOLS_PATH not in sys.path:
    sys.path.append(SUMO_TOOLS_PATH)

# 3. Import traci and sumolib (sumolib is often required/used by traci)
try:
    import traci
    # Optional: import sumolib
except ImportError:
    sys.exit("Error: Could not import 'traci'. Check if SUMO_TOOLS_PATH is correct.")

# --- Define Constants ---
SUMO_CONFIG_FILE = "simulation.sumocfg" # The file you generated earlier


# --- 1. Define the Command to Start SUMO ---
# Use the 'sumo' executable (no GUI) for speed, or 'sumo-gui' to see the simulation
sumo_binary = "/Library/Frameworks/EclipseSUMO.framework/Versions/1.25.0/EclipseSUMO/bin/sumo" # MacOS only


# This command lists the arguments needed to launch the SUMO server
sumo_cmd = [sumo_binary, "-c", SUMO_CONFIG_FILE]


# --- 2. Start the Simulation and Connect ---
# traci.start() launches the external program (SUMO) and immediately connects to it.
print("Starting SUMO server and connecting via TraCI...")
traci.start(sumo_cmd) 


# --- 3. The Main Simulation Loop ---
step = 1
while(True):
    steps = input("Specify number of steps: ")
    if steps.isdigit():
        steps = int(steps)
        break
    else:
        print("Invalid Input. Provide correct number of steps.")

while step <= steps: 
    # Tell SUMO to advance by one step (usually 1 second)
    traci.simulationStep() 
    
    # --- TraCI Logic (Example) ---
    # Get the number of vehicles currently in the network
    vehicle_count = traci.simulation.getMinExpectedNumber()
    print(f"Step {step}: Current vehicles in network: {vehicle_count}")
    
    # Example control: Get speed of a known vehicle (replace 'veh0' with a real ID)
    # try:
    #     speed = traci.vehicle.getSpeed("veh0")
    #     print(f"  Vehicle veh0 speed: {speed:.2f} m/s")
    # except traci.TraCIException:
    #     pass # Vehicle might not exist yet
    # ---------------------------
    
    step += 1


# --- 4. Clean Up and Close ---
print("Closing TraCI connection and shutting down SUMO.")
traci.close()
sys.stdout.flush()

