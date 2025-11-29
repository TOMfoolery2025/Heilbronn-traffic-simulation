import os
import sys
import traci
import sumolib
import threading
import time
import datetime

# --- CONSTANTS ---
WEIPERT_TLS_ID = "2900153591"    

class SimulationManager:
    def __init__(self, base_path):
        self.base_path = base_path
        self.config_file = os.path.join(base_path, "simulation.sumocfg")
        self.net_file = os.path.join(base_path, "network", "sumo", "heilbronn.net.xml")
        
        # Load Network
        print("Loading Network...")
        self.net = sumolib.net.readNet(self.net_file)
        
        self.status = "Idle"
        self.stop_event = threading.Event()
        self.sim_delay = 0.05
        
        # Data Containers
        self.current_data = {
            "vehicles": [], 
            "stats": {
                "count": 0, "speed": 0, 
                "current_co2": 0, "total_co2": 0, 
                "stopped": 0, "time": "00:00:00"
            }
        }
        self.accumulated_co2 = 0.0
        
        # Simulation Start Time (Seconds from midnight)
        # Matching your sumocfg begin value (04:00 AM)
        self.start_offset = 14400 

    def start_simulation(self):
        if self.status == "Running": return
        self.stop_event.clear()
        self.accumulated_co2 = 0.0 
        thread = threading.Thread(target=self._run_loop)
        thread.start()

    def stop_simulation(self):
        self.stop_event.set()

    def set_speed(self, delay_seconds):
        try:
            self.sim_delay = max(0.001, float(delay_seconds)) # Allow faster speeds
        except ValueError:
            pass

    def _run_loop(self):
        self.status = "Running"
        
        try:
            # Start TraCI (Headless)
            cmd = ["sumo", "-c", self.config_file, "--no-step-log", "true", "--step-length", "0.5"]
            traci.start(cmd)

            step = 0
            while not self.stop_event.is_set():
                traci.simulationStep()
                step += 1
                
                # Update Data for Frontend
                # We calculate current time based on step + offset
                current_sim_time = self.start_offset + (step * 0.5) # 0.5 is step-length
                self._update_live_data(current_sim_time)
                
                time.sleep(self.sim_delay) 

            traci.close()
            self.status = "Stopped"

        except Exception as e:
            self.status = f"Error: {str(e)}"
            try: traci.close()
            except: pass

    def _update_live_data(self, sim_seconds):
        veh_ids = traci.vehicle.getIDList()
        total_veh = len(veh_ids)
        
        # Format Time String (HH:MM:SS)
        # Using datetime for easy formatting
        time_str = (datetime.datetime(2024, 1, 1) + datetime.timedelta(seconds=sim_seconds)).strftime("%H:%M:%S")

        # Defaults if empty
        if total_veh == 0:
            self.current_data['vehicles'] = []
            self.current_data['stats'] = {
                "count": 0, "speed": 0, 
                "current_co2": 0, "total_co2": round(self.accumulated_co2, 2), 
                "stopped": 0, "time": time_str
            }
            return

        # 1. Metrics Calculation
        step_co2_mg = sum([traci.vehicle.getCO2Emission(v) for v in veh_ids])
        step_co2_kg = step_co2_mg / 1000000.0
        self.accumulated_co2 += step_co2_kg

        speeds = [traci.vehicle.getSpeed(v) for v in veh_ids]
        avg_speed_ms = sum(speeds) / total_veh
        avg_speed_kmh = avg_speed_ms * 3.6
        stopped_count = len([s for s in speeds if s < 0.1])

        # 2. Coordinate Mapping
        live_vehicles = []
        for vid in veh_ids:
            x, y = traci.vehicle.getPosition(vid)
            lon, lat = self.net.convertXY2LonLat(x, y)
            vtype = traci.vehicle.getTypeID(vid)
            
            color = "#4D7CFE" # Default Car
            radius = 2
            if "bus" in vtype:
                color = "#FF4B4B"
                radius = 5
            elif "student" in vtype: color = "#00FF99"
            elif "ped" in vtype: color = "#FFD166"

            live_vehicles.append({
                "id": vid, "lat": lat, "lon": lon, "color": color, "radius": radius
            })

        self.current_data = {
            "vehicles": live_vehicles,
            "stats": {
                "count": total_veh,
                "speed": round(avg_speed_kmh, 1),
                "current_co2": round(step_co2_kg, 4),
                "total_co2": round(self.accumulated_co2, 2),
                "stopped": stopped_count,
                "time": time_str # <--- Sent to frontend
            }
        }

# Global Manager
manager = SimulationManager(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))