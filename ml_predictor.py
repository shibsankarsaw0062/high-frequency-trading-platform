import psycopg2
import time
import numpy as np
from sklearn.linear_model import SGDRegressor

print("==================================================")
print("  Live ML Prediction Microservice v1.1 (STABILIZED)")
print("  Model: Stochastic Gradient Descent (Online)")
print("==================================================")

def get_db_connection():
    return psycopg2.connect(
        host="127.0.0.1", port="5432", dbname="postgres", user="postgres", password="your_password"
    )

# THE FIX: Switch to an adaptive learning rate to prevent mathematical explosions
model = SGDRegressor(learning_rate='adaptive', eta0=0.001)
is_model_initialized = False
last_processed_time = None

print("ML Engine Listening for Ticks... (Ctrl+C to halt)\n")

while True:
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch the latest 3 ticks to get a trailing history of changes
        cursor.execute("SELECT time, price FROM tick_data ORDER BY time DESC LIMIT 3;")
        rows = cursor.fetchall()

        if len(rows) == 3:
            current_time = rows[0][0]
            p0 = float(rows[0][1]) # Current Price
            p1 = float(rows[1][1]) # Previous Price
            p2 = float(rows[2][1]) # Price 2 ticks ago

            if current_time != last_processed_time:
                last_processed_time = current_time
                
                # Feature Engineering: Small, bounded delta values
                v_current = p0 - p1   # Current price velocity
                v_previous = p1 - p2  # Previous price velocity
                
                # X = Features (previous movement), y = Target (the NEXT movement)
                X = np.array([[v_previous]])
                y = np.array([v_current])
                
                # 1. LIVE TRAINING (Stays perfectly stable because inputs are small)
                model.partial_fit(X, y)

                # 2. INFERENCE: Predict the NEXT velocity shift
                predicted_velocity = float(model.predict(np.array([[v_current]]))[0])

                # Reconstruction: Final Price = Current Price + Predicted Velocity
                predicted_next_price = p0 + predicted_velocity

                # 3. ROUTING TO DB
                cursor.execute(
                    "INSERT INTO ml_predictions (time, predicted_price) VALUES (%s, %s);",
                    (current_time, predicted_next_price)
                )
                conn.commit()

                print(f"[ML TICK] Current: ${p0:.2f} | Predicted Next: ${predicted_next_price:.2f} (Delta: {predicted_velocity:+.4f})")

        cursor.close()
        conn.close()
        time.sleep(0.5)

    except Exception as e:
        print(f"ML Pipeline Error: {e}")
        time.sleep(1)