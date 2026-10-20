#!/bin/bash
# =====================================================================
# Agriculture Rover - Raspberry Pi / Linux Environment Setup
# =====================================================================
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "====================================================================="
echo "   Agriculture Rover - Raspberry Pi / Linux Setup"
echo "====================================================================="

echo "[1/4] Checking Python 3..."
python3 --version

echo "[2/4] Installing system dependencies for OpenCV and Serial..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv libgl1-mesa-glx libglib2.0-0
fi

# Add current user to dialout group so Arduino can be accessed without sudo
echo "[3/4] Configuring USB serial permissions..."
sudo usermod -a -G dialout $USER || true

echo "[4/4] Creating virtual environment (.venv) and installing Python packages..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup weights
python models/download_weights.py

echo "====================================================================="
echo "   SETUP COMPLETE!"
echo "   Run the rover using:"
echo "     ./run_rover.sh"
echo "====================================================================="
