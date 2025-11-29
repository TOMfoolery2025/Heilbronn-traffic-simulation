# final-HN-traffic-simulator

# 🚀 Heilbronn Multi-Modal Mobility & Congestion Solver


**Hackathon Challenge:** Heilbronn Traffic Simulations (Prof. Ziyue Li, Transportation Analytics)


---


## 🎯 The Core Problem: The Weipertstraße Bottleneck


Construction has reduced lane capacity on Weipertstraße, causing cascading delays for:
- **Student mobility** (University Bus Line delays → minutes of education lost)
- **Public transit efficiency** (bus bunching, schedule reliability degradation)
- **Vulnerable road users** (pedestrian safety risks at congested crosswalks)
- **Environmental impact** (emissions from idling vehicles in the bottleneck)


Our mission: **Quantify impact mathematically and prove efficiency gains from intervention strategies.**


---


## 🔬 Technical Methodology: Agent-Based Microscopic Simulation


### Simulation Engine
- **Eclipse SUMO (Simulation of Urban Mobility)** in headless mode for performance and automation
- Microscopic fidelity: individual vehicle dynamics, signal interactions, queueing behavior
- Data source: OpenStreetMap (OSM) data of Heilbronn, cleaned and patched with netconvert


### Python Integration Pipeline
- **traci** (SUMO Traffic Control Interface) for simulation control
- **sumolib** for network geometry and FCD extraction
- Data processing: pandas, numpy
- Visualization: matplotlib, seaborn (evidence-based graphics)


---


## 📊 Three Scientific Scenarios


We model three distinct realities to isolate construction impact and validate interventions:


| Scenario | Status | Description |
|----------|--------|-------------|
| **Baseline (Status Quo)** | Road network pre-construction | Ideal flow conditions (benchmark) |
| **The Disruption** | Current reality with construction | Lane closure on Weipertstraße + speed reduction |
| **The Intervention** | Construction + optimization strategy | Adaptive signal control, bus priority lanes, or creative solutions |


---


## 📈 Advanced Transportation Analytics Metrics


Moving beyond "car counting" to meaningful insights:


### 1. **Student Latency Metric**
- `waitingTime` differential between Bus agents vs. Private Car agents
- Quantifies "Minutes of Education Lost" due to construction delays
- Cross-referenced with class schedule impact


### 2. **Vulnerable Road User (VRU) Exposure**
- Pedestrian queue times at crosswalks
- Safety metrics: conflict points, crossing delay variance
- Determines if construction makes walking inefficient or unsafe


### 3. **Space-Time Diagrams (Marey Graphs)**
- Visualize congestion shockwaves propagating backward from the construction site
- Stop-and-go wave frequency and amplitude analysis
- Lane-level trajectory plots


### 4. **Emissions Proxy**
- CO₂/NOₓ accumulation from idling vehicles
- Calculated via fuel consumption model based on speed profiles
- Cumulative emissions by scenario


### 5. **Mobility Equity Analysis**
- Travel time reliability (standard deviation of arrival times by mode)
- Accessibility score for transit-dependent populations
- Modal shift impacts (do students avoid the route?)


### 6. **Operational Efficiency Metrics**
- **Queue Length Dynamics:** Max queue depth, mean queue persistence
- **Throughput Analysis:** Vehicles per time period through bottleneck
- **Schedule Adherence:** Bus line punctuality degradation
- **Intersection Saturation:** v/c ratios before/after intervention


---


## 🛠️ Project Structure


```
Heilbronn-traffic-simulation/
├── network/
│   ├── osm/
│   │   └── map.osm              # Raw OpenStreetMap data
│   └── sumo/
│       ├── heilbronn.net.xml    # SUMO network file (auto-generated)
│       ├── heilbronn.rou.xml    # Route/demand file (auto-generated)
│       └── config.sumocfg       # SUMO configuration file
├── scenarios/                   # Scenario definitions (baseline, disruption, intervention)
├── tools/
│   ├── analytics/
│   │   └── analyze_data.py      # Parse SUMO output, compute metrics
│   ├── testing/
│   │   └── check_map.py         # Verify network geometry
│   └── visualization/
│       └── make_animation.py    # Generate GIFs from trace data
├── results/                     # Simulation outputs (XML, CSV, images)
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```


---


## 🚀 Getting Started


### 1. Install Dependencies
```bash
pip install -r requirements.txt
```


### 2. Ensure SUMO is Installed
```bash
# macOS with Homebrew
brew install sumo


# Or download from: https://sumo.dlr.de/docs/Downloads.php
export SUMO_HOME=/path/to/sumo
```


### 3. Generate Network from OSM
```bash
netconvert --osm-files network/osm/map.osm -o network/sumo/heilbronn.net.xml
```


### 4. Run a Scenario
```bash
sumo -c network/sumo/config.sumocfg
# or with traci control: python scenarios/baseline_scenario.py
```


### 5. Analyze Results
```bash
python tools/analytics/analyze_data.py
python tools/visualization/make_animation.py
```


---


## 📋 Reproducible Data Pipeline


Our code is architected for **scalability and reproducibility:**


- ✅ No hard-coded maps — accepts any OSM input
- ✅ Parameterized scenarios (demand levels, signal timing, bus routing)
- ✅ Automated analysis reports with standard metrics
- ✅ Version-controlled outputs for comparison
- ✅ Can scale from Weipertstraße to entire Heilbronn region


---


## 📊 Visualization Strategy


### Automated Evidence-Based Graphics
1. **Congestion Shockwave GIFs** — FCD trace → matplotlib animation
2. **Comparative Dashboards** — Seaborn heatmaps overlaying three scenarios
3. **Trajectory Plots** — Individual vehicle paths colored by mode/delay
4. **Time-Series Analysis** — Queue length, throughput, emissions over time
5. **Modal Comparison Charts** — Bus vs. car latency, reliability, emissions


---


## 🎓 Academic Rigor


This project demonstrates:
- **Quantitative methods:** Queuing theory, network flow analysis
- **Data-driven decision making:** Evidence-based policy recommendations
- **Scalability:** Reproducible pipeline applicable to broader city planning
- **Interdisciplinary thinking:** Transportation + Computer Science + Urban Planning


---


## 📝 Authors & Credits


- Project: Heilbronn Traffic Simulation Hackathon
- Advisor: Prof. Ziyue Li (Transportation Analytics)
- Tools: SUMO, Python, OpenStreetMap


---


**Last Updated:** November 28, 2025




import_gtfs_data_buses.py
filter_stops.py
connect_stops.py

https://drive.google.com/drive/folders/1D_ZX7kHyKceVdqYu1Q8uZC3iuWe1XSJP?usp=share_link
