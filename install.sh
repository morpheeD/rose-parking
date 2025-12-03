#!/bin/bash

# Parking Management System - Installation Script
# For Raspberry Pi

set -e

echo "========================================="
echo "Parking Management System - Installation"
echo "========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "📦 Updating system packages..."
sudo apt-get update

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libopencv-dev \
    python3-opencv \
    libatlas-base-dev \
    libjpeg-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Download YOLO model (will be cached)
echo "🤖 Downloading YOLOv8 model..."
python3 << EOF
from ultralytics import YOLO
print("Downloading YOLOv8n model...")
model = YOLO('yolov8n.pt')
print("Model downloaded successfully!")
EOF

# Create systemd service
echo "⚙️  Creating systemd service..."
SERVICE_FILE="/etc/systemd/system/parking.service"
CURRENT_DIR=$(pwd)

sudo tee $SERVICE_FILE > /dev/null << EOF
[Unit]
Description=Parking Management System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment="PATH=$CURRENT_DIR/venv/bin"
ExecStart=$CURRENT_DIR/venv/bin/python3 $CURRENT_DIR/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable service
echo "✅ Enabling service to start on boot..."
sudo systemctl enable parking

echo ""
echo "========================================="
echo "✅ Installation completed successfully!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Configure your camera in config.json"
echo "2. Adjust entry/exit line positions if needed"
echo "3. Start the service:"
echo "   sudo systemctl start parking"
echo ""
echo "4. Access the web interface at:"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Useful commands:"
echo "  - Start:   sudo systemctl start parking"
echo "  - Stop:    sudo systemctl stop parking"
echo "  - Restart: sudo systemctl restart parking"
echo "  - Logs:    sudo journalctl -u parking -f"
echo ""
echo "========================================="
