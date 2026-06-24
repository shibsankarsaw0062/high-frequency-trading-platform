# AI-Driven High-Frequency Quantitative Trading Architecture

## Overview
This repository contains a full-stack, decentralized quantitative trading execution platform. Designed for ultra-low latency environments, the architecture separates data ingestion, machine learning inference, and visual analytics into independent Python microservices, while centralizing the core statistical anomaly detection and risk management inside a microsecond-latency C++ execution engine.

The system utilizes an online-learning Machine Learning model to validate structural statistical anomalies in real-time, functioning as a complete "Consensus Engine."

---

## System Architecture

The platform operates on a decentralized microservices topology, communicating through a localized TimescaleDB core:

* **Data Ingestion Pipeline (Python):** An asynchronous data generation layer simulating a live cryptocurrency exchange websocket. It pushes high-frequency price and volume data (`tick_data`) into the storage core.
* **Time-Series Storage Core (TimescaleDB / PostgreSQL via Docker):** Acts as the high-speed data bridge. Utilizes hypertable partitioning to allow instant `ORDER BY time DESC` querying without degradation over millions of rows.
* **ML Inference Microservice (Python / Scikit-Learn):** A continuous machine learning script that pulls recent price history, calculates price velocity (momentum), and updates a Stochastic Gradient Descent (SGD) model using `partial_fit()`. It pushes live price predictions to the `ml_predictions` table.
* **Execution Consensus Engine (C++17):** The ultra-low latency brain of the operation. It polls the database, calculates streaming statistics in O(1) time, checks the ML prediction, calculates dynamic risk ceilings, and executes the trade.
* **Visual Analytics Dashboard (Streamlit / Plotly):** A timezone-aware frontend that reconstructs the C++ mathematical environment using Pandas and visualizes the asset price, Institutional VWAP, Bollinger Bands, and executed trade coordinates in real-time.

---

## Core Mathematical Models

### 1. O(1) Streaming Statistics (Welford's Algorithm)
To achieve microsecond latency, the C++ engine does not store historical arrays of data. Standard deviation and variance are calculated dynamically as data streams in, avoiding floating-point catastrophic cancellation:

* Running Mean Update:  
  `Mean_n = Mean_{n-1} + (x_n - Mean_{n-1}) / n`
* M2 Accumulator Update:  
  `M2_n = M2_{n-1} + (x_n - Mean_{n-1}) * (x_n - Mean_n)`
* Rolling Sample Standard Deviation:  
  `StdDev = sqrt(M2 / (n - 1))`

### 2. Statistical Anomaly Detection (Z-Score)
The system calculates the real-time Volume Weighted Average Price (VWAP) and triggers a primary signal when the asset price enters the extreme tail of the probability distribution (e.g., crashing below the VWAP):

`Z_Score = (Current_Price - VWAP) / StdDev`

*Primary Trigger Condition:* `Z_Score <= -2.0`

### 3. ML Target Transformation & Consensus
To prevent gradient explosion when dealing with high-value assets (e.g., a $65,000 Bitcoin price), the SGD neural weights are trained on the **Price Delta (Velocity)** rather than raw asset values. 

The C++ engine requires absolute consensus before executing a trade. It will block the statistical `Z_Score <= -2.0` trigger if the AI model predicts continued downward momentum:
* `if (Z_Score <= -2.0 && ML_Predicted_Price > Current_Price) -> Execute Trade`

---

## Performance & Latency Profiling

The C++ execution core uses the `std::chrono::high_resolution_clock` to benchmark its own logic cycle on every tick.

* **Algorithmic Time Complexity:** O(1)
* **Memory Space Complexity:** O(1) (Explicit pointer management prevents RAM leaks)
* **Average Tick-to-Trade Latency:** 3 to 5 microseconds (µs).

### Pre-Trade Risk Gateway
Hardcoded limits ensure capital protection before the database is altered. If a proposed order exceeds the maximum notional exposure (e.g., $150,000), the engine dynamically calculates a fractional order size:
* `Executed Quantity = Max Notional / Current Price`

---

## Setup and Deployment

**1. Initialize the TimescaleDB Docker Container:**
```bash
docker run -d --name timescale-trading -p 5432:5432 -e POSTGRES_PASSWORD=your_password timescale/timescaledb:latest-pg14
