import datetime
import random
import time
import psycopg2

# Database connection configurations
DB_PARAMS = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "postgres",
    "user": "postgres",
    "password": "your_password"
}

def generate_mock_tick():
    """Simulates a live streaming price update from an exchange tick stream."""
    current_time = datetime.datetime.now(datetime.timezone.utc)
    symbol = "BTCUSD"
    base_price = 65000.00
    
    # Generate random deviations for bid/ask spread
    noise = random.uniform(-10.0, 10.0)
    price = round(base_price + noise, 2)
    volume = round(random.uniform(0.01, 2.5), 4)
    
    bid_price = round(price - 0.5, 2)
    ask_price = round(price + 0.5, 2)
    bid_size = round(random.uniform(1.0, 10.0), 2)
    ask_size = round(random.uniform(1.0, 10.0), 2)
    
    return (current_time, symbol, price, volume, bid_price, ask_price, bid_size, ask_size)

def stream_data_to_timescale():
    print("Connecting to TimescaleDB...")
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()
    print("Connection successful! Streaming live mock tick data (Press Ctrl+C to stop)...")
    
    insert_query = """
    INSERT INTO tick_data (time, symbol, price, volume, bid_price, ask_price, bid_size, ask_size)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    
    try:
        while True:
            tick_data = generate_mock_tick()
            cursor.execute(insert_query, tick_data)
            conn.commit()  # Flush the row to the database
            print(f"[{tick_data[0].strftime('%H:%M:%S')}] Inserted {tick_data[1]} trade at ${tick_data[2]} | Vol: {tick_data[3]}")
            
            # Wait 1 second before sending the next trading tick
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\nStreaming paused safely by user.")
    finally:
        cursor.close()
        conn.close()
        print("Database connection closed cleanly.")

if __name__ == "__main__":
    stream_data_to_timescale()