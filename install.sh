#!/bin/bash
set -e  # Exit on any error

echo "=== sACN Relay 4 – Automated Installer ==="

# ------------------- 1. Update System -------------------
echo "[1/7] Updating system..."
sudo apt update && sudo apt upgrade -y

# ------------------- 2. Install Dependencies -------------------
echo "[2/7] Installing system dependencies..."
sudo apt install -y python3-pip python3-venv git i2c-tools

# Enable I2C
echo "[ ] Enabling I2C interface..."
sudo raspi-config nonint do_i2c 1

# ------------------- 3. Create Python Virtual Environment -------------------
echo "[3/7] Setting up Python virtual environment..."
VENV_DIR="$HOME/sacn_venv"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Install Python packages
pip install --upgrade pip
pip install flask sacn adafruit-circuitpython-ssd1306 pillow gpiozero netifaces

# ------------------- 4. Copy Files to Final Location -------------------
echo "[4/7] Copying application files..."
APP_DIR="$HOME"
mkdir -p "$APP_DIR/assets" "$APP_DIR/templates"

cp "$HOME/install/sacn_relay_controller.py" "$APP_DIR/"
cp -r "$HOME/install/assets/"* "$APP_DIR/assets/"
cp -r "$HOME/install/templates/"* "$APP_DIR/templates/"

# ------------------- 5. Create Systemd Service -------------------
echo "[5/7] Creating systemd service..."
sudo tee /etc/systemd/system/sacn-relay.service > /dev/null << EOF
[Unit]
Description=sACN Relay 4 Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python $APP_DIR/sacn_relay_controller.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# ------------------- 6. Enable & Start Service -------------------
echo "[6/7] Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable sacn-relay.service
sudo systemctl start sacn-relay.service

# ------------------- 7. Final Instructions -------------------
echo "[7/7] Installation complete!"
echo
echo "=== ACCESS YOUR RELAY ==="
echo "Web UI: http://$(hostname -I | awk '{print $1}'):8080"
echo
echo "=== SERVICE CONTROL ==="
echo "  Stop:     sudo systemctl stop sacn-relay"
echo "  Start:    sudo systemctl start sacn-relay"
echo "  Status:   sudo systemctl status sacn-relay"
echo "  Logs:     sudo journalctl -u sacn-relay -f"
echo
echo "=== HARDWARE CHECK ==="
echo "  OLED:  i2cdetect -y 1  (should show 3C)"
echo "  GPIO:  Test relays with Status page toggle"
echo
echo "Reboot recommended: sudo reboot"