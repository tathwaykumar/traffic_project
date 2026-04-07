# Smart Traffic Signal Optimization System
### College Engineering Project — Python Simulation with GUI

---

## 📁 Project Structure

```
traffic_project/
├── main.py           ← GUI application (Tkinter) — RUN THIS
├── simulation.py     ← Core simulation engine
├── traffic_light.py  ← TrafficLight class
├── vehicle.py        ← Vehicle class
├── utils.py          ← Helper functions & statistics
└── README.md         ← This file
```

---

## ▶️ How to Run

### Requirements
- Python 3.8 or higher (Tkinter is built-in — no installation needed)
- Optional: `matplotlib` for comparison charts

```bash
# Install optional matplotlib
pip install matplotlib

# Run the simulation
python main.py
```

---

## 🖥️ GUI Guide

| Button | Action |
|---|---|
| ▶ NORMAL MODE | Switch to fixed-timing signal control |
| ⚡ SMART MODE | Switch to AI-based dynamic signal timing |
| ⏸ PAUSE / RESUME | Freeze and unfreeze the simulation |
| 🚨 SPAWN AMBULANCE | Inject an emergency vehicle — triggers immediate green |
| 📊 COMPARE MODES | Run both modes for 60s each and show comparison chart |
| ↺ RESET | Restart the current mode |

---

## 🧠 How It Works

### Normal Mode
- Each lane (N, S, E, W) gets a fixed **10-second green** in rotation.
- Vehicles move through at ~2 vehicles/second while their light is green.

### Smart Mode
- Before each green phase, the system counts vehicles in the target lane.
- Green duration is calculated as:
  ```
  share = lane_vehicles / total_vehicles_at_intersection
  green_duration = 5s + share × (20s - 5s)
  ```
- The busiest lane gets up to **20 seconds** of green time.
- A lane with no vehicles gets the minimum **5 seconds**.

### Emergency Override
- When an ambulance arrives, it immediately preempts the current rotation.
- The ambulance's lane turns green until the ambulance clears.
- Normal rotation resumes afterwards.

---

## 📊 Comparison Feature
Clicking **📊 COMPARE MODES** runs both simulations for 60 seconds each
(headless, in the background) and displays:
- Vehicles cleared
- Average waiting time
- Throughput (vehicles/minute)
- Bar charts (requires matplotlib)

---
