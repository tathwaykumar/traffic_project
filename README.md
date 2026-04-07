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

## 💡 Viva Talking Points

1. **Why is Smart mode better?**
   - It reduces average wait time by allocating green time proportionally to demand.
   - Prevents short-queue lanes from wasting signal time.

2. **What algorithm does Smart mode use?**
   - A weighted proportional allocation based on real-time queue length.
   - Similar to the "Webster's method" used in real adaptive traffic systems.

3. **How does emergency override work?**
   - A flag (`emergency_dir`) is set when an ambulance enters a queue.
   - The signal controller checks this flag every tick and preempts if needed.

4. **What data structures are used?**
   - `deque` (double-ended queue) for lane queues — O(1) enqueue and dequeue.
   - Dictionary for O(1) lane lookups.

5. **How is the simulation realistic?**
   - Vehicles arrive using a Poisson process approximation.
   - Vehicle mix: 70% cars, 20% trucks, 10% ambulances.
   - Green timing bounds prevent starvation (min 5s) and hogging (max 20s).
