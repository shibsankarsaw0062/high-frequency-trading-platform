import psycopg2
from psycopg2 import extras
import csv
import random
import math
from datetime import datetime, timedelta

print("==================================================")
print("  Quant Historical Backtest Loader v1.0")
print("==================================================")

CSV_FILENAME = "historical_ticks.csv"
TOTAL_TICKS = 10000

# 1. GENERATE THE HISTORICAL DATASET (Simulating a Flash Crash)
print(f"[*] Generating {TOTAL_TICKS} historical ticks...")
with open(CSV_FILENAME, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["time", "price", "volume"])
    
    start_time = datetime.utcnow() - timedelta(days=1)
    base_price = 65000.0
    
    for i in range(TOTAL_TICKS):
        # Mathematical flash crash: Starts flat, crashes heavily in the middle, recovers
        crash_factor = math.sin(i / 1000.0) * 1500  
        noise = random.uniform(-10, 10)
        
        if 4000 < i < 6000:
            price = base_price - abs(crash_factor) * 2.5 + noise
        else:
            price = base_price + crash_factor + noise
            
        volume = random.uniform(0.1, 5.0)
        timestamp = start_time + timedelta(milliseconds=i * 500)
        writer.writerow([timestamp.isoformat(), round(price, 2), round(volume, 4)])

print("[+] Synthetic Flash Crash CSV created.")

# 2. HIGH-SPEED BULK INGESTION INTO TIMESCALEDB
print("[*] Connecting to TimescaleDB Core...")
try:
    conn = psycopg2.connect(
        host="127.0.0.1", port="5432", dbname="postgres", user="postgres", password="your_password"
    )
    cursor = conn.cursor()

    # Wipe the live data clean for the backtest
    cursor.execute("TRUNCATE tick_data, ml_predictions, trade_orders;")
    conn.commit()

    print(f"[*] Bulk loading {CSV_FILENAME} into database...")
    with open(CSV_FILENAME, 'r') as f:
        reader = csv.reader(f)
        next(reader) # Skip header
        
        insert_query = "INSERT INTO tick_data (time, price, volume) VALUES %s"
        extras.execute_values(cursor, insert_query, list(reader))

    conn.commit()
    print("[+] Backtest data injected successfully! Database is ready.")

except Exception as e:
    print(f"Database Error: {e}")
finally:
    if conn:
        cursor.close()
        conn.close()
