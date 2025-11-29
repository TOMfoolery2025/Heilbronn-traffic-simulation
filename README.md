# Heilbronn Traffic Simulation

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![SUMO](https://img.shields.io/badge/Simulator-Eclipse%20SUMO-orange)

A microscopic traffic simulation of the **Heilbronn urban area**, developed to analyze traffic flow, detect bottlenecks, and visualize environmental impacts. This project utilizes **Eclipse SUMO** for the core simulation engine and custom Python modules for interactive dashboards and web-based visualizations.

## 📌 Table of Contents
- [About the Project](#-about-the-project)
- [Key Features](#-key-features)
- [Repository Structure](#-repository-structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
  - [Running the Simulation](#1-running-the-simulation)
  - [Launching the Dashboard](#2-launching-the-dashboard)
- [Authors](#-authors)

---

## 📖 About the Project

This project models the road network of Heilbronn, Germany, to simulate realistic traffic patterns. By leveraging floating car data (FCD) and trip information, the system provides insights into:
- **Traffic Density:** Identifying high-congestion zones.
- **Emissions:** Analyzing CO2 and NOx outputs based on vehicle trajectories.
- **Trip Efficiency:** Measuring average travel times and waiting periods.

The repository includes not just the simulation configuration, but also a suite of **analytics tools** (`app/` and `tools/`) to transform raw XML data into human-readable visual insights.

---

## 🚀 Key Features

* **Realistic Network Topology:** Full import of the Heilbronn road network via OpenStreetMap and SUMO.
* **Automated Runner:** A `sumo_runner.py` script to orchestrate simulation steps and manage data export.
* **Interactive Dashboard:** A dedicated app (located in `app/`) to visualize statistics like delays and emissions.
* **Web-based Visualization:** Tools to generate standalone HTML maps for spatial analysis of traffic flow.
* **Custom Route Management:** Flexible handling of traffic demand via XML route configurations.

---

## 📂 Repository Structure

```plaintext
Heilbronn-traffic-simulation/
├── app/                  # Analytics Dashboard source code
├── intermediate/         # Temporary processing files
├── network/              # SUMO network files (.net.xml) and polygons
├── results/              # Simulation output (FCD, Tripinfo, Emission logs)
├── tools/                # Utility scripts (e.g., HTML map generator)
├── simulation.sumocfg    # Main SUMO configuration file
├── sumo_runner.py        # Main execution script for the simulation
├── requirements.txt      # Python dependencies
└── routes.rou.xml        # Baseline traffic demand



import_gtfs_data_buses.py
filter_stops.py
connect_stops.py

https://drive.google.com/drive/folders/1D_ZX7kHyKceVdqYu1Q8uZC3iuWe1XSJP?usp=share_link
