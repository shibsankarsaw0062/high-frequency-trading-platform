cmake_minimum_required(VERSION 3.10)
project(QuantTradingEngine)

# Set high-performance modern C++ compilation
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3")

# 1. Automatically find the installed PostgreSQL/TimescaleDB development package
find_package(PostgreSQL REQUIRED)

add_executable(trading_engine main.cpp)

# 2. Tell the compiler to link the database library directly into our executable
target_link_libraries(trading_engine PRIVATE PostgreSQL::PostgreSQL)

add_executable(backtester backtest.cpp)
target_link_libraries(backtester pq)