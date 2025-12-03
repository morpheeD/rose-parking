#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$DIR/venv/bin/activate"

# Check if requests is installed
if ! python -c "import requests" &> /dev/null; then
    echo "Installing missing dependencies..."
    pip install requests
fi

# Run the dashboard app
echo "Starting Dashboard on port 5005..."
python "$DIR/dashboard/app.py"
