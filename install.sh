#!/bin/bash
set -e

echo "=== sACN Relay 4/8 v1.2.5 – Final Installer ==="

APP_DIR="$HOME/sACN-Relay"
VENV_DIR="$APP_DIR/sacn_venv"

echo "[1/7] Installing to: $APP_DIR"

# --- System packages ---
sudo apt update
sudo apt install -y python3-pip python3-venv git i2c-tools

# --- Enable I2C ---
#sudo raspi-config nonint do_i2c 1

# --- Create venv ---
echo "[4/7] Creating virtual environment..."
python3 -m venv "$VENV_DIR" || { echo "Failed to create venv"; exit 1; }

# --- Activate & install ---
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install flask flask-session sacn adafruit-circuitpython-ssd1306 pillow gpiozero netifaces psutil adafruit-blinka RPi.GPIO

# --- Fix permissions ---
sudo chown -R pi:pi "$APP_DIR"
sudo chmod -R 755 "$APP_DIR"

# --- Systemd service ---
sudo tee /etc/systemd/system/sacn-relay.service > /dev/null << EOF
[Unit]
Description=sACN Relay 4/8 Controller
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python $APP_DIR/sacn_relay_controller.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable sacn-relay.service

echo
echo "=== INSTALLATION COMPLETE! ==="
echo "Run: sudo systemctl start sacn-relay"
echo "Or: sudo reboot"
echo "Web UI: http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo '<IP>'):8080"