#!/bin/bash

# setup.sh - Installation script for Polymarket Data Tools
# This script sets up everything needed to run the Polymarket dashboard

set -e  # Exit on any error

echo "=== Polymarket Data Tools Setup ==="
echo "Setting up your environment..."

# Detect OS
OS=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="windows"
else
    echo "Unknown OS: $OSTYPE"
    echo "This script supports Linux, macOS, and Windows"
    exit 1
fi

echo "Detected OS: $OS"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Python 3.10+ if not available
echo "Checking Python installation..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        echo "✓ Python $PYTHON_VERSION found"
        PYTHON_CMD="python3"
    else
        echo "✗ Python 3.10+ required, found $PYTHON_VERSION"
        INSTALL_PYTHON=true
    fi
elif command_exists python; then
    PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        echo "✓ Python $PYTHON_VERSION found"
        PYTHON_CMD="python"
    else
        echo "✗ Python 3.10+ required, found $PYTHON_VERSION"
        INSTALL_PYTHON=true
    fi
else
    echo "✗ Python not found"
    INSTALL_PYTHON=true
fi

# Install Python if needed
if [ "$INSTALL_PYTHON" = true ]; then
    echo "Installing Python 3.10+..."
    
    case $OS in
        "macos")
            if command_exists brew; then
                brew install python@3.11
                PYTHON_CMD="python3.11"
            else
                echo "Please install Homebrew first: https://brew.sh"
                echo "Then run: brew install python@3.11"
                exit 1
            fi
            ;;
        "linux")
            if command_exists apt-get; then
                sudo apt-get update
                sudo apt-get install -y python3.11 python3.11-pip python3.11-venv
                PYTHON_CMD="python3.11"
            elif command_exists yum; then
                sudo yum install -y python311 python311-pip
                PYTHON_CMD="python3.11"
            elif command_exists dnf; then
                sudo dnf install -y python3.11 python3.11-pip
                PYTHON_CMD="python3.11"
            else
                echo "Please install Python 3.10+ manually"
                exit 1
            fi
            ;;
        "windows")
            echo "Please install Python 3.10+ from https://python.org/downloads/"
            echo "Make sure to check 'Add Python to PATH' during installation"
            exit 1
            ;;
    esac
fi

# Check pip
echo "Checking pip installation..."
if command_exists pip3; then
    PIP_CMD="pip3"
elif command_exists pip; then
    PIP_CMD="pip"
else
    echo "Installing pip..."
    $PYTHON_CMD -m ensurepip --upgrade
    PIP_CMD="$PYTHON_CMD -m pip"
fi

echo "✓ pip found"

# Create virtual environment
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
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

# Upgrade pip in virtual environment
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install required packages
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    # Update requirements.txt to include rich for the dashboard
    if ! grep -q "rich" requirements.txt; then
        echo "rich" >> requirements.txt
    fi
    if ! grep -q "requests" requirements.txt; then
        echo "requests" >> requirements.txt
    fi
    
    pip install -r requirements.txt
else
    # Install essential packages directly
    pip install websockets rich requests asyncio
fi

# Create data directory structure
echo "Creating data directories..."
mkdir -p data/market_data/democratic-presidential-nominee-2028
mkdir -p data/market_data/republican-presidential-nominee-2028
mkdir -p data/market_data/presidential-election-winner-2028
mkdir -p data/market_data/which-party-wins-2028-us-presidential-election

echo "✓ Data directories created"

# Make scripts executable
echo "Making scripts executable..."
chmod +x run_dashboard.sh 2>/dev/null || true

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To run the dashboard:"
echo "  ./run_dashboard.sh"
echo ""
echo "To manually run components:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Start data collection: python get_market_data.py"
echo "  3. Start dashboard: python display_dashboard.py"
echo ""
echo "Press Ctrl+C to stop the dashboard"
