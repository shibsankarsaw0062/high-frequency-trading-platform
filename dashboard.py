import streamlit as st
import pandas as pd
import psycopg2
import plotly.graph_objects as go
import time

# ==========================================
#   PAGE CONFIGURATION
# ==========================================
st.set_page_config(page_title="Quant Trading Platform", layout="wide")
st.title("⚡ Live High-Frequency Trading Dashboard")
st.markdown("Visualizing C++ Execution Engine, Z-Score Anomalies, and Live Trade Routes.")

# Placeholder to allow live-refreshing the chart without reloading the whole webpage
chart_placeholder = st.empty()

# ==========================================
#   DATABASE CONNECTION
# ==========================================
def get_db_connection():
    return psycopg2.connect(
        host="127.0.0.1",
        port="5432",
        dbname="postgres",
        user="postgres",
        password="your_password"
    )

# ==========================================
#   LIVE RENDER LOOP
# ==========================================
while True:
    try:
        conn = get_db_connection()
        
        # 1. Fetch data from TimescaleDB
        df_ticks = pd.read_sql_query("SELECT time, price, volume FROM tick_data ORDER BY time DESC LIMIT 200;", conn)
        df_orders = pd.read_sql_query("SELECT time, execution_price, status FROM trade_orders ORDER BY time DESC LIMIT 50;", conn)
        conn.close()

        # Prevent math errors if the database is completely empty
        if not df_ticks.empty:
            
            # === THE TIMELINE FIX: Force unified UTC datetime parsing ===
            df_ticks['time'] = pd.to_datetime(df_ticks['time'], utc=True)
            df_ticks = df_ticks.sort_values('time') # Sort chronologically safely
            
            if not df_orders.empty:
                df_orders['time'] = pd.to_datetime(df_orders['time'], utc=True)

            # 3. Data Science Math: Replicate the C++ VWAP & Z-Score environment in Pandas
            df_ticks['cumulative_volume'] = df_ticks['volume'].cumsum()
            df_ticks['cumulative_value'] = (df_ticks['price'] * df_ticks['volume']).cumsum()
            df_ticks['vwap'] = df_ticks['cumulative_value'] / df_ticks['cumulative_volume']
            
            # Calculate a rolling 30-tick standard deviation to mimic the C++ Welford warmup
            df_ticks['std_dev'] = df_ticks['price'].rolling(window=30).std()
            df_ticks['lower_band'] = df_ticks['vwap'] - (2.0 * df_ticks['std_dev'])

            # ==========================================
            #   PLOTLY FINANCIAL CHARTING
            # ==========================================
            fig = go.Figure()

            # Plot A: Live Market Price
            fig.add_trace(go.Scatter(x=df_ticks['time'], y=df_ticks['price'], 
                                     mode='lines', name='Live Price', line=dict(color='#2962FF', width=2)))

            # Plot B: The VWAP (Institutional Average)
            fig.add_trace(go.Scatter(x=df_ticks['time'], y=df_ticks['vwap'], 
                                     mode='lines', name='VWAP', line=dict(color='#FF6D00', width=2, dash='dash')))

            # Plot C: The -2.0 Z-Score Anomaly Trigger Line
            fig.add_trace(go.Scatter(x=df_ticks['time'], y=df_ticks['lower_band'], 
                                     mode='lines', name='-2.0 Z-Score Target', line=dict(color='#FF1744', width=1, dash='dot')))

            # Plot D: Overlay C++ Execution Signals!
            if not df_orders.empty:
                fig.add_trace(go.Scatter(
                    x=df_orders['time'], 
                    y=df_orders['execution_price'],
                    mode='markers',
                    name='C++ Trade Executed',
                    marker=dict(color='#00E676', size=14, symbol='triangle-up', line=dict(color='black', width=1))
                ))

            # Chart Styling
            fig.update_layout(
                height=600,
                template="plotly_dark",
                xaxis_title="Time",
                yaxis_title="Price (USD)",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                margin=dict(l=0, r=0, t=30, b=0)
            )

            # Render the chart to the Streamlit placeholder
            chart_placeholder.plotly_chart(fig, use_container_width=True)

        # Pause before hitting the database again
        time.sleep(1)

    except Exception as e:
        st.error(f"Waiting for database connection or data... Error: {e}")
        time.sleep(2)