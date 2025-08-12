#!/bin/bash

# run_dashboard.sh - Script to run Polymarket dashboard with background data collection
# This script starts the market data collection in the background and then runs the dashboard

set -e  # Exit on any error

echo "=== Starting Polymarket Dashboard ==="

# Check if we're in the right directory
if [ ! -f "get_market_data.py" ] || [ ! -f "display_dashboard.py" ]; then
    echo "Error: Please run this script from the Polymarket project directory"
    echo "Make sure get_market_data.py and display_dashboard.py exist"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Detect OS for virtual environment activation
OS=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
    OS="linux"  # Default fallback
fi

# Activate virtual environment
echo "Activating virtual environment..."
case $OS in
    "windows")
        source venv/Scripts/activate
        ;;
    *)
        source venv/bin/activate
        ;;
esac

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Shutting down..."
    if [ ! -z "$DATA_PID" ] && kill -0 $DATA_PID 2>/dev/null; then
        echo "Stopping market data collection (PID: $DATA_PID)..."
        kill $DATA_PID
        wait $DATA_PID 2>/dev/null || true
    fi
    echo "Dashboard stopped."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Create data directories if they don't exist
echo "Ensuring data directories exist..."
mkdir -p data/market_data/democratic-presidential-nominee-2028
mkdir -p data/market_data/republican-presidential-nominee-2028
mkdir -p data/market_data/presidential-election-winner-2028
mkdir -p data/market_data/which-party-wins-2028-us-presidential-election

# Start market data collection in background
echo "Starting market data collection in background..."
python get_market_data.py > data/market_data_log.txt 2>&1 &
DATA_PID=$!

# Give the data collection a moment to start
sleep 2

# Check if the background process is still running
if ! kill -0 $DATA_PID 2>/dev/null; then
    echo "Error: Market data collection failed to start"
    echo "Check data/market_data_log.txt for details"
    exit 1
fi

echo "✓ Market data collection started (PID: $DATA_PID)"
echo "✓ Log file: data/market_data_log.txt"
echo ""
echo "Starting data collection..."
sleep 30
echo "Starting dashboard... (Press Ctrl+C to stop)"
echo "================================================"

# Start the dashboard (this will block until user stops it)
python display_dashboard.py

# If we get here, the dashboard exited normally
cleanup
