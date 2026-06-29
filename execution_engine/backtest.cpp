#include <iostream>
#include <string>
#include <chrono>
#include <cmath>
#include <postgresql/libpq-fe.h>

using namespace std;
using namespace std::chrono; 

const double Z_SCORE_THRESHOLD  = -1.0;
const int WARMUP_TICKS          = 30;
const double STANDARD_ORDER_QTY = 2.5;

int main() {
    cout << "==================================================" << endl;
    cout << "  C++ Historical Backtest Engine v1.0 " << endl;
    cout << "==================================================" << endl;

    const char* conninfo = "host=127.0.0.1 port=5432 dbname=postgres user=postgres password=your_password";
    PGconn* conn = PQconnectdb(conninfo);

    if (PQstatus(conn) != CONNECTION_OK) {
        cerr << "CRITICAL: Connection failed: " << PQerrorMessage(conn) << endl;
        PQfinish(conn);
        return 1;
    }

    cout << "STATUS: Connected. Fetching historical dataset..." << endl;

    // Fetch the entire dataset chronologically
    PGresult* res = PQexec(conn, "SELECT time, price, volume FROM tick_data ORDER BY time ASC;");
    
    if (PQresultStatus(res) != PGRES_TUPLES_OK) {
        cerr << "Query failed: " << PQerrorMessage(conn) << endl;
        PQclear(res);
        PQfinish(conn);
        return 1;
    }

    int total_rows = PQntuples(res);
    cout << "DATA LOADED: " << total_rows << " ticks retrieved. Commencing simulation...\n" << endl;

    double total_cumulative_value = 0.0, total_cumulative_volume = 0.0;
    int tick_count = 0;
    int trades_executed = 0;
    double running_mean = 0.0, M2 = 0.0;

    auto start_time = high_resolution_clock::now();

    // The Backtest Loop: Process data at maximum CPU speed
    for (int i = 0; i < total_rows; i++) {
        string current_timestamp = PQgetvalue(res, i, 0);
        double price = stod(PQgetvalue(res, i, 1));
        double volume = stod(PQgetvalue(res, i, 2));

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

        // Trade Execution Logic
        if (tick_count > WARMUP_TICKS && z_score <= Z_SCORE_THRESHOLD) {
            trades_executed++;
            
            string insert_sql = "INSERT INTO trade_orders (time, asset, execution_price, requested_qty, executed_qty, status) VALUES ('" 
                                + current_timestamp + "', 'BTCUSD', " + to_string(price) + ", " 
                                + to_string(STANDARD_ORDER_QTY) + ", " + to_string(STANDARD_ORDER_QTY) + ", 'BACKTEST_FILL');";
            
            PGresult* insert_res = PQexec(conn, insert_sql.c_str());
            PQclear(insert_res);
        }
    }

    auto end_time = high_resolution_clock::now();
    auto duration = duration_cast<milliseconds>(end_time - start_time);

    cout << "==================================================" << endl;
    cout << "BACKTEST COMPLETE" << endl;
    cout << "Total Ticks Processed : " << tick_count << endl;
    cout << "Total Trades Executed : " << trades_executed << endl;
    cout << "Simulation Runtime    : " << duration.count() << " ms" << endl;
    cout << "==================================================" << endl;

    PQclear(res); 
    PQfinish(conn);
    return 0;
}
