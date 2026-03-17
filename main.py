from fastapi import FastAPI, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import database, httpx
from datetime import datetime, timedelta

app = FastAPI(title="AquaGuard Pro Backend")

# --- CORS SETTINGS ---
# Allows your index.html to talk to this backend
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
    try: yield db
    finally: db.close()

async def send_telegram_alert(message: str):
    """Sends a push notification to your phone via Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json={"chat_id": CHAT_ID, "text": message})
        except:
            print("Telegram failed to send. Check Token/Network.")

# --- ENDPOINT 1: DATA INGESTION (From Simulator/ESP32) ---
@app.post("/ingest")
async def ingest_data(data: dict, bg_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Determine Health Status
    health_status = "SAFE"
    
    # Logic: Danger if pH is acidic/alkaline or TDS is too high
    if data['ph'] < 6.5 or data['ph'] > 8.5 or data['tds'] > 500:
        health_status = "DANGER"
        bg_tasks.add_task(send_telegram_alert, f"🧪 QUALITY ALERT!\nDevice: {data['device_id']}\npH: {data['ph']}\nTDS: {data['tds']}")

    # Logic: Leak Detection (Flow detected but UV is OFF)
    if data['flow'] > 1.0 and data['uv_status'] == "OFF":
        health_status = "DANGER"
        bg_tasks.add_task(send_telegram_alert, f"💧 LEAK ALERT!\nUnexpected flow of {data['flow']} L/min detected.")

    # 2. Save to Database
    new_log = database.WaterLog(
        device_id=data['device_id'],
        tds=data['tds'],
        ph=data['ph'],
        turbidity=data['turbidity'],
        flow=data['flow'],
        temp=data['temp'],
        uv_status=data['uv_status'],
        lat=data['lat'],
        lng=data['lng'],
        gps_active=data['gps_active'],
        health=health_status
    )
    db.add(new_log)
    db.commit()
    
    return {"status": "success", "health_assigned": health_status}

# --- ENDPOINT 2: DASHBOARD TELEMETRY (For index.html Cards) ---
@app.get("/frontend/dashboard/{device_id}")
async def get_dashboard(device_id: str, db: Session = Depends(get_db)):
    latest = db.query(database.WaterLog).filter_by(device_id=device_id).order_by(database.WaterLog.timestamp.desc()).first()
    
    if not latest:
        return {"sensors": {"tds":0, "ph":0, "flow":0, "turbidity":0, "temp":0}, "health": "NO_DATA"}

    return {
        "sensors": {
            "tds": latest.tds, "ph": latest.ph, "flow": latest.flow, 
            "turbidity": latest.turbidity, "temp": latest.temp
        },
        "health": latest.health,
        "uv": latest.uv_status,
        "gps": {"lat": latest.lat, "lng": latest.lng}
    }

# --- ENDPOINT 3: HISTORICAL DATA (For index.html Charts) ---
@app.get("/frontend/history/{device_id}")
async def get_history(device_id: str, db: Session = Depends(get_db)):
    # Get last 50 readings for the graphs
    logs = db.query(database.WaterLog).filter_by(device_id=device_id).order_by(database.WaterLog.timestamp.desc()).limit(50).all()
    # Reverse so the oldest is first for the chart x-axis
    return logs[::-1]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)