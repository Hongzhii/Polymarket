# Polymarket Data Tools and Dashboard

A Python-based tool for monitoring Polymarket prediction markets, calculating arbitrage opportunities, and displaying real-time market data through an interactive dashboard.

## Features

- **Real-time Market Data**: WebSocket-based monitoring of Polymarket markets
- **Arbitrage Detection**: Identifies intra-party and cross-party arbitrage opportunities
- **Conditional Odds Calculation**: Computes market-implied conditional probabilities
- **Interactive Dashboard**: Live-updating terminal dashboard with Rich formatting
- **Multi-Market Support**: Tracks presidential election, party nomination, and party winner markets

## Quick Start

### 1. Installation

Run the setup script to install all dependencies:

```bash
chmod +x setup.sh
./setup.sh
```

### 2. Run the Dashboard

Start the market data collection and dashboard:

```bash
chmod +x run_dashboard.sh
./run_dashboard.sh
```

This will:
- Start collecting market data in the background
- Launch the interactive dashboard
- Display real-time arbitrage opportunities and conditional odds

### 3. Stop the Application

Press `Ctrl+C` in the dashboard terminal to stop both the dashboard and data collection.

## Manual Usage

### Start Market Data Collection
```bash
python get_market_data.py
```

### Run Dashboard (in another terminal)
```bash
python display_dashboard.py
```

## Market Data

The tool monitors these Polymarket markets:
- Presidential Election Winner 2028
- Republican Presidential Nominee 2028
- Democratic Presidential Nominee 2028
- Which Party Wins 2028 US Presidential Election

Data is stored in `data/market_data/` with separate directories for each market.

## Dashboard Features

### Party Arbitrage Margins
- Synthetic party probabilities calculated from individual candidate prices
- Comparison with actual party market prices
- Identification of risk-free arbitrage opportunities

### Conditional Odds
- Market-implied probability that a candidate wins the presidency given party nomination
- Calculated as: P(Candidate wins presidency) / P(Candidate is nominated)
- Separate tables for GOP and Democratic candidates

## Requirements

- Python 3.10+
- WebSocket connection for real-time data
- Terminal with color support for optimal display

## Project Structure

```
Polymarket/
├── data/market_data/          # Market data storage
├── services/                  # Core services (MarketBook, exceptions)
├── utils/                     # Utilities (WebSocket, data processing)
├── get_market_data.py         # Market data collection script
├── display_dashboard.py       # Interactive dashboard
├── setup.sh                   # Installation script
└── run_dashboard.sh          # Dashboard launcher script
```

## Troubleshooting

### NoValidStatesError
If you see repeated "No valid states" errors, this usually means:
- Market data files are missing or incomplete
- Asset IDs in mappings don't match the market data
- WebSocket connection issues preventing data updates

### Connection Issues
- Ensure you have a stable internet connection
- Check if Polymarket's WebSocket endpoint is accessible
- Restart the data collection script if connection drops
