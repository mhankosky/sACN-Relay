# sACN Relay 4/8

**A compact, production-ready sACN (E1.31) to DMX relay controller for Raspberry Pi.**

Control **4 or 8 relays** via sACN over Ethernet. Perfect for **lighting control**, **theater**, **events**, and **industrial automation**.

---

## Features

| Feature | Description |
|-------|-----------|
| **sACN Input** | Listens to any universe (1–63999) |
| **4 or 8 Relays** | Selectable in **Device Settings** |
| **Set-point Threshold** | Relay ON at ≥ X% (1–100%) |
| **Web UI** | Full control from any device |
| **Dark/Light Mode** | Toggle UI theme |
| **Static IP + DNS** | Full network configuration |
| **Hostname Change** | Set custom device name |
| **Password Protection** | Optional login |
| **Backup/Restore** | Export/import `config.json` |
| **OLED Display** | Shows IP, universe, active channels |
| **Test Mode** | Pulse relays for 5s |
| **AirGap Ready** | No internet required |
| **Self-Contained** | Runs from `~/sACN-Relay/` |

---

## Hardware Requirements

- Raspberry Pi (Zero W, 3, 4, 5)  
  [Tested with Pi 4/B](https://www.amazon.com/Raspberry-Model-2019-Quad-Bluetooth/dp/B07TC2BK1X)
- 4-channel or 8-channel relay module (5V, **active low**)  
  [Example: 4-channel](https://www.amazon.com/dp/B00KTEN3TM)
  [Example: 8-channel](https://www.amazon.com/DEVMO-Electrical-Equipments-Optocoupler-Compatible/dp/B08TMN8KN6)
- 0.96" I2C OLED display (SSD1306, 128x64)  
  [Example](https://www.amazon.com/UCTRONICS-SSD1306-Self-Luminous-Display-Raspberry/dp/B072Q2X2LL)
- POE Hat (Optional)  
  [Example](https://www.amazon.com/dp/B0928ZD7QQ)
- Ethernet or Wi-Fi

> **Ethernet is recommended over Wi-Fi for reliability**

---

## Wiring

See detailed wiring guide: [`wiring.md`](wiring.md)

---

## Installation (Direct on Pi)

```bash
# 1. Clone anywhere
git clone https://github.com/mhankosky/sACN-Relay.git ~/my-temp-folder

# 2. Go to folder
cd ~/my-temp-folder

# 3. Run installer — installs to ~/sACN-Relay/
chmod +x install.sh
sudo ./install.sh

The installer:

Sets up Python venv
Installs dependencies (psutil, sacn, etc.)
Configures systemd service
Enables I2C
Starts on boot



Access Web UI
Open in browser:
texthttp://<pi-ip>:8080
Default password (if enabled): admin123

Configuration
All settings saved in:
text~/sACN-Relay/config.json
Never edit manually — use the web UI.

File Structure
text~/sACN-Relay/
├── sacn_relay_controller.py
├── sacn_venv/                 # Python environment
├── config.json                # All settings
├── install.sh                 # Installer
├── wiring.md                  # Wiring guide
└── assets/
    ├── css/                   # SB Admin 2 + dark mode
    ├── js/                    # Bootstrap + SB Admin
    └── html/                  # All web pages

Security

Password protection (enable in Security tab)
Plain text storage (AirGap safe)
Session-based login
Logout button


Backup & Restore

Download: Full config with hostname and mode
Upload: Validates version + structure
Confirm before overwrite


Version History

























VersionChanges1.2.08-channel mode, CPU/Memory monitor, Reboot Pi button1.1.4DNS1/DNS2, partial config save1.1.0Dark mode, security, backup1.0.1Initial release

Troubleshooting
bash# Check status
sudo systemctl status sacn-relay

# View logs
sudo journalctl -u sacn-relay -f

# Restart
sudo systemctl restart sacn-relay

License
MIT License — Free for personal and commercial use.

Built with care for reliability in the field.