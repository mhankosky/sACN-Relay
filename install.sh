#!/bin/bash
set -e  # Exit on any error

echo "=== sACN Relay 4 v1.1.4 – Automated Installer ==="

# ------------------- 1. Detect Script Location -------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/sACN-Relay"
VENV_DIR="$APP_DIR/sacn_venv"

echo "[1/7] Script location: $SCRIPT_DIR"
echo "[ ] Installing to: $APP_DIR"

# ------------------- 2. Update System -------------------
echo "[2/7] Updating system..."
sudo apt update && sudo apt upgrade -y

# ------------------- 3. Install Dependencies -------------------
echo "[3/7] Installing system dependencies..."
sudo apt install -y python3-pip python3-venv git i2c-tools

# Enable I2C
echo "[ ] Enabling I2C interface..."
sudo raspi-config nonint do_i2c 1

# ------------------- 4. Create App Directory -------------------
echo "[4/7] Creating application directory: $APP_DIR"
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/assets/css" "$APP_DIR/assets/js" "$APP_DIR/assets/html"

# ------------------- 5. Copy Files -------------------
echo "[5/7] Copying application files from $SCRIPT_DIR..."
cp "$SCRIPT_DIR/sacn_relay_controller.py" "$APP_DIR/"
cp -r "$SCRIPT_DIR/assets/"* "$APP_DIR/assets/" 2>/dev/null || true

# Copy install.sh itself (optional)
cp "$SCRIPT_DIR/install.sh" "$APP_DIR/" 2>/dev/null || true

# ------------------- 6. Setup Python Environment -------------------
echo "[6/7] Setting up Python virtual environment in $VENV_DIR..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install flask flask-session sacn adafruit-circuitpython-ssd1306 pillow gpiozero netifaces

# ------------------- 7. Create Systemd Service -------------------
echo "[7/7] Creating systemd service..."
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

# ------------------- 8. Enable & Start Service -------------------
echo "[ ] Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable sacn-relay.service
sudo systemctl start sacn-relay.service

# ------------------- Final Output -------------------
echo
echo "=== INSTALLATION COMPLETE! ==="
echo "App Location: $APP_DIR"
echo "Web UI: http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo '<IP>'):8080"
echo
echo "=== SERVICE CONTROL ==="
echo "  Status:   sudo systemctl status sacn-relay"
echo "  Logs:     sudo journalctl -u sacn-relay -f"
echo "  Stop:     sudo systemctl stop sacn-relay"
echo "  Start:    sudo systemctl start sacn-relay"
echo
echo "=== HARDWARE CHECK ==="
echo "  OLED:  i2cdetect -y 1  (should show 3C)"
echo "  GPIO:  Test relays via Test page"
echo
echo "Reboot recommended: sudo reboot"