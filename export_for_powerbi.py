import sqlite3
import pandas as pd
import os

def generate_excel():
    db_file = 'water_system.db'
    
    # Check if database exists
    if not os.path.exists(db_file):
        print("❌ Error: 'water_system.db' nahi mila! Pehle simulator aur main.py chalayein.")
        return

    try:
        # 1. Connect to Database
        conn = sqlite3.connect(db_file)
        
        # 2. SQL data ko Pandas DataFrame mein layein
        df = pd.read_sql_query("SELECT * FROM logs", conn)
        
        # 3. Excel file mein save karein
        excel_name = "water_analytics_data.xlsx"
        df.to_excel(excel_name, index=False)
        
        print(f"✅ Success! Power BI ke liye file taiyar hai: {excel_name}")
        conn.close()
    except Exception as e:
        print(f"⚠️ Kuch gadbad hui: {e}")

if __name__ == "__main__":
    generate_excel()