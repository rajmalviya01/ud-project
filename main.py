from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import database, httpx

app = FastAPI(title="AquaGuard Pro Backend")

# --- CORS SETTINGS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- TELEGRAM CONFIG ---
BOT_TOKEN = "YOUR_BOT_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def get_db():
    db = database.SessionLocal()
    try: 
        yield db
    finally: 
        db.close()

async def send_telegram_alert(message: str):
    """Sends a push notification to your phone via Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json={"chat_id": CHAT_ID, "text": message})
        except:
            print("Telegram failed to send. Check Token/Network.")

# --- ENDPOINT 1: DATA INGESTION (From Wokwi/ESP32) ---
@app.post("/ingest")
async def ingest_data(data: dict, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    
    # 1. Safely Unpack the Nested JSON
    device_id = data.get('device_id', 'UNKNOWN')
    sensors = data.get('sensors', {})
    alerts = data.get('alerts', {})
    location = data.get('location', {})

    ph_val = sensors.get('ph', 0.0)
    tds_val = sensors.get('tds_ppm', 0)
    turb_val = sensors.get('turbidity_ntu', 0.0)
    do_val = sensors.get('dissolved_o2_mgl', 0.0)
    temp_val = sensors.get('temp_c', 0.0)
    flow_val = sensors.get('flow_rate_lpm', 0.0)
    pressure_val = sensors.get('pressure_psi', 0.0)
    
    uv_active = "ON" if alerts.get('uv_active') else "OFF"
    leak_detected = alerts.get('leak_detected', False)
    
    lat_val = location.get('lat', 0.0)
    lng_val = location.get('lng', 0.0)

    # 2. Determine Health Status
    health_status = "SAFE"
    
    if ph_val < 6.5 or ph_val > 8.5 or tds_val > 500:
        health_status = "DANGER"
        bg_tasks.add_task(send_telegram_alert, f"🧪 QUALITY ALERT!\nDevice: {device_id}\npH: {ph_val}\nTDS: {tds_val}")

    if leak_detected:
        health_status = "DANGER"
        bg_tasks.add_task(send_telegram_alert, f"💧 LEAK ALERT!\nMassive pressure drop detected at {device_id}!")

    # 3. Save to Database
    new_log = database.WaterLog(
        device_id=device_id,
        tds=tds_val,
        ph=ph_val,
        turbidity=turb_val,
        dissolved_o2=do_val,
        temp=temp_val,
        flow=flow_val,
        pressure=pressure_val,
        uv_status=uv_active,
        leak_detected=leak_detected,
        lat=lat_val,
        lng=lng_val,
        health=health_status
    )
    db.add(new_log)
    db.commit()
    
    return {"status": "success", "health_assigned": health_status}

# --- ENDPOINT 2: DASHBOARD TELEMETRY ---
@app.get("/frontend/dashboard/{device_id}")
async def get_dashboard(device_id: str, db: Session = Depends(get_db)):
    latest = db.query(database.WaterLog).filter_by(device_id=device_id).order_by(database.WaterLog.timestamp.desc()).first()
    
    if not latest:
        return {"error": "NO_DATA"}

    return {
        "sensors": {
            "tds": latest.tds, "ph": latest.ph, "flow": latest.flow, 
            "turbidity": latest.turbidity, "temp": latest.temp,
            "pressure": latest.pressure, "dissolved_o2": latest.dissolved_o2
        },
        "health": latest.health,
        "uv": latest.uv_status,
        "leak_detected": latest.leak_detected,
        "gps": {"lat": latest.lat, "lng": latest.lng}
    }

# --- ENDPOINT 3: HISTORICAL DATA (For Charts) ---
@app.get("/frontend/history/{device_id}")
async def get_history(device_id: str, db: Session = Depends(get_db)):
    logs = db.query(database.WaterLog).filter_by(device_id=device_id).order_by(database.WaterLog.timestamp.desc()).limit(50).all()
    return logs[::-1]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
