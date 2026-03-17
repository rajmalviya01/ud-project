import requests
import time
import random
import math
from datetime import datetime

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8000/ingest"
DEVICE_ID = "PIPE_001"

def generate_sine_wave(amplitude, frequency, offset):
    """Creates smooth natural fluctuations (like temperature or flow)."""
    return offset + amplitude * math.sin(time.time() * frequency)

def simulate_sensors():
    print(f"🚀 AquaGuard Pro Simulator Active: Sending data to {API_URL}")
    print("Press Ctrl+C to stop simulation.\n")
    
    step = 0
    while True:
        step += 1
        
        # 1. TDS: Normally stable (150-200), occasionally spikes
        tds = round(generate_sine_wave(10, 0.05, 180) + random.uniform(-2, 2), 2)
        if step % 20 == 0: tds += 300  # Occasional contamination spike

        # 2. pH: Slighly basic (7.2), tests danger logic every 15th reading
        ph = round(generate_sine_wave(0.2, 0.02, 7.2), 2)
        if step % 15 == 0: ph = 5.8  # Simulate Acidity Alert

        # 3. Flow: Fluctuates based on "demand"
        flow = round(generate_sine_wave(5, 0.1, 10), 1)
        
        # 4. UV Status & Leak Logic
        # Simulate a leak: High flow but UV is OFF
        uv_status = "ON"
        if step % 25 == 0:
            uv_status = "OFF"
            flow = 12.5 # Forced high flow to trigger "Leak Alert" on dashboard

        # 5. Turbidity & Temp
        turbidity = round(random.uniform(0.8, 1.5), 2)
        temp = round(generate_sine_wave(2, 0.01, 24), 1)

        # 6. GPS: Slight movement (Simulating sensor sway or drift)
        lat = 22.7196 + (math.sin(step * 0.1) * 0.0005)
        lng = 75.8577 + (math.cos(step * 0.1) * 0.0005)

        # PREPARE PAYLOAD
        payload = {
            "device_id": DEVICE_ID,
            "tds": tds,
            "ph": ph,
            "turbidity": turbidity,
            "flow": flow,
            "temp": temp,
            "uv_status": uv_status,
            "lat": lat,
            "lng": lng,
            "gps_active": True
        }

        try:
            response = requests.post(API_URL, json=payload, timeout=2)
            health = response.json().get("health_assigned", "UNKNOWN")
            
            # Professional Console Logging
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Sent Data | pH: {ph} | Flow: {flow} | Health: {health}")
            
        except requests.exceptions.ConnectionError:
            print("❌ Error: Backend is not running! Start main.py first.")
        except Exception as e:
            print(f"⚠️ Unexpected Error: {e}")

        time.sleep(3) # Send data every 3 seconds

if __name__ == "__main__":
    simulate_sensors()