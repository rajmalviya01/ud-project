from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker # Note: Updated import path
import datetime

DATABASE_URL = "sqlite:///./water_system.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# This line is absolutely correct!
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class WaterLog(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # --- Sensors ---
    tds = Column(Float)
    ph = Column(Float)
    turbidity = Column(Float)
    flow = Column(Float)
    temp = Column(Float)
    
    # NEW: Added from our Wokwi ESP32 simulation
    pressure = Column(Float) 
    dissolved_o2 = Column(Float) 
    
    # --- Alerts & Status ---
    uv_status = Column(String)
    health = Column(String)
    
    # NEW: Added leak detection from ESP32 button
    leak_detected = Column(Boolean) 

    # --- Location ---
    lat = Column(Float)
    lng = Column(Float)
    gps_active = Column(Boolean)

Base.metadata.create_all(bind=engine)
