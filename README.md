# sACN Relay 4

**A compact, production-ready sACN (E1.31) to DMX relay controller for Raspberry Pi.**

Control **4 relays** via sACN over Ethernet. Perfect for **lighting control**, **theater**, **events**, and **industrial automation**.

---

## Features

| Feature | Description |
|-------|-----------|
| **sACN Input** | Listens to any universe (1–63999) |
| **4 Relays** | Individually controlled via DMX channels |
| **Set-point Threshold** | Relay ON at ≥ X% (1–100%) |
| **Web UI** | Full control from any device |
| **Dark/Light Mode** | Toggle UI theme |
| **Static IP + DNS** | Full network configuration |
| **Hostname Change** | Set custom device name |
| **Password Protection** | Optional login |
| **Backup/Restore** | Export/import `config.json` |
| **OLED Display** | Shows IP, universe, channels |
| **Test Mode** | Pulse relays for 5s |
| **AirGap Ready** | No internet required |
| **Self-Contained** | Runs from `~/sACN-Relay/` |

---

## Hardware Requirements

- Raspberry Pi (Zero W, 3, 4, 5)
- 4-channel relay module (5V, active low)
- 0.96" I2C OLED display (SSD1306, 128x64)
- Ethernet or Wi-Fi

---

## Wiring

| Component | GPIO |
|---------|------|
| Relay 1 | 17 |
| Relay 2 | 18 |
| Relay 3 | 27 |
| Relay 4 | 22 |
| Reset Button | 23 (to GND) |
| OLED | I2C (SCL=3, SDA=2) |

---

## Installation

```bash
# 1. Copy this repo to Pi
scp -r sACN-Relay pi@<pi-ip>:~

# 2. SSH into Pi
ssh pi@<pi-ip>

# 3. Enter folder
cd ~/sACN-Relay

# 4. Run installer
chmod +x install.sh
sudo ./install.sh
