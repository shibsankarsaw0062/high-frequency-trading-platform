#include <iostream>
#include <string>
#include <thread>
#include <chrono>
#include <cmath>
#include <postgresql/libpq-fe.h>

using namespace std;
using namespace std::chrono; 

const double Z_SCORE_THRESHOLD  = -2.0;
const int WARMUP_TICKS          = 30;
const double RISK_MAX_NOTIONAL  = 150000.0;
const double STANDARD_ORDER_QTY = 2.5;

int main() {
    cout << "==================================================" << endl;
    cout << "  Quant Trading Execution Engine v6.0 (CONSENSUS) " << endl;
    cout << "==================================================" << endl;

    const char* conninfo = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=your_password";
    PGconn* conn = PQconnectdb(conninfo);

    if (PQstatus(conn) != CONNECTION_OK) {
        cerr << "CRITICAL: Connection failed: " << PQerrorMessage(conn) << endl;
        PQfinish(conn);
        return 1;
    }
    cout << "SUCCESS: Tied to TimescaleDB Core System.\n" << endl;

    double total_cumulative_value = 0.0, total_cumulative_volume = 0.0;
    string last_processed_timestamp = "";
    
    int tick_count = 0;
    double running_mean = 0.0, M2 = 0.0;
    double total_latency = 0.0;

    cout << "Engine Listening... Evaluating Multi-Layer AI Consensus... (Ctrl+C to halt)\n";
    cout << "-----------------------------------------------------------------\n";

    while (true) {
        // Fetch latest raw tick
        PGresult* res = PQexec(conn, "SELECT time, price, volume FROM tick_data ORDER BY time DESC LIMIT 1;");

        if (PQresultStatus(res) == PGRES_TUPLES_OK && PQntuples(res) > 0) {
            string current_timestamp = PQgetvalue(res, 0, 0);
            
            if (current_timestamp != last_processed_timestamp) {
                auto start_time = high_resolution_clock::now();
                last_processed_timestamp = current_timestamp;

                double price = stod(PQgetvalue(res, 0, 1));
                double volume = stod(PQgetvalue(res, 0, 2));

                // 1. Core Welford & VWAP Calculations
                total_cumulative_value += (price * volume);
                total_cumulative_volume += volume;
                double current_vwap = total_cumulative_value / total_cumulative_volume;

                tick_count++; 
                double delta = price - running_mean;
                running_mean += delta / tick_count;
                double delta2 = price - running_mean;
                M2 += delta * delta2;

                double variance = (tick_count > 1) ? M2 / (tick_count - 1) : 0.0;
                double std_dev = sqrt(variance);
                double z_score = (std_dev > 0) ? (price - current_vwap) / std_dev : 0.0;

                // 2. FETCH LATEST AI INFERENCE FROM THE ML SERVICE
                double predicted_price = price; // Default to neutral if query fails
                PGresult* ml_res = PQexec(conn, "SELECT predicted_price FROM ml_predictions ORDER BY time DESC LIMIT 1;");
                if (PQresultStatus(ml_res) == PGRES_TUPLES_OK && PQntuples(ml_res) > 0) {
                    predicted_price = stod(PQgetvalue(ml_res, 0, 0));
                }
                PQclear(ml_res); // Free ML query memory immediately

                bool ml_agreement = (predicted_price > price);

                // Print updated system tracking line
                cout << "[TICK " << tick_count << "] Z-Score: " << z_score 
                     << " | ML Forecast: $" << predicted_price 
                     << " | ML Signal: " << (ml_agreement ? "BUY_CONFIRMED" : "HOLD") << endl;

                // 3. THE CONSENSUS GATEWAY
                if (tick_count > WARMUP_TICKS && z_score <= Z_SCORE_THRESHOLD) {
                    
                    if (ml_agreement) {
                        cout << "\n>>> [CONSENSUS MATCH] Statistical anomaly confirmed by ML model! Executing Route..." << endl;
                        
                        double proposed_notional = price * STANDARD_ORDER_QTY;
                        double executed_qty = STANDARD_ORDER_QTY;
                        string trade_status = "EXECUTED_FULL";

                        if (proposed_notional > RISK_MAX_NOTIONAL) {
                            executed_qty = RISK_MAX_NOTIONAL / price; 
                            trade_status = "EXECUTED_RESIZED";
                        }

                        string insert_sql = "INSERT INTO trade_orders (time, asset, execution_price, requested_qty, executed_qty, status) VALUES (NOW(), 'BTCUSD', " 
                                            + to_string(price) + ", " + to_string(STANDARD_ORDER_QTY) + ", " 
                                            + to_string(executed_qty) + ", '" + trade_status + "');";

                        PGresult* insert_res = PQexec(conn, insert_sql.c_str());
                        PQclear(insert_res); 
                    } else {
                        cout << ">>> [SIGNAL BLOCKED] Z-Score triggered, but ML model predicted further downward momentum. Trade filtered out safely." << endl;
                    }
                }

                auto end_time = high_resolution_clock::now();
                auto duration = duration_cast<microseconds>(end_time - start_time);
                total_latency += duration.count();
                // Average calculation safe from division by zero
                double avg_latency = total_latency / tick_count; 
                
                cout << "      └─ Microsecond Performance Profile -> Latency: " << duration.count() << "us | Avg: " << avg_latency << "us" << endl;
            }
        }
        PQclear(res); 
        this_thread::sleep_for(milliseconds(500));
    }

    PQfinish(conn);
    return 0;
}