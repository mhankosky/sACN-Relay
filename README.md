
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

## Installation (Direct on Pi)

```bash
# 1. SSH into your Pi
ssh pi@<pi-ip>

# 2. Clone the repo and install in one command
git clone https://github.com/mhankosky/sACN-Relay.git && cd sACN-Relay && chmod +x install.sh && sudo ./install.sh
```

> The installer:
> - Sets up Python venv
> - Installs dependencies
> - Configures systemd service
> - Enables I2C
> - Starts on boot

---

## Access Web UI

Open in browser:
```
http://<pi-ip>:8080
```

Default password (if enabled): `admin123`

---

## Configuration

All settings saved in:
```
~/sACN-Relay/config.json
```

**Never edit manually** — use the web UI.

---

## File Structure

```
~/sACN-Relay/
├── sacn_relay_controller.py
├── sacn_venv/                 # Python environment
├── config.json                # All settings
└── assets/
    ├── css/                   # SB Admin 2 + dark mode
    ├── js/                    # Bootstrap + SB Admin
    └── html/                  # All web pages
```

---

## Security

- **Password protection** (enable in **Security** tab)
- **Plain text storage** (AirGap safe)
- **Session-based login**
- **Logout button**

---

## Backup & Restore

- **Download**: Full config with hostname
- **Upload**: Validates version + structure
- **Confirm before overwrite**

---

## Version History

| Version | Changes |
|--------|--------|
| `1.1.4` | DNS1/DNS2, partial config save |
| `1.1.0` | Dark mode, security, backup |
| `1.0.1` | Initial release |

---

## Troubleshooting

```bash
# Check status
sudo systemctl status sacn-relay

# View logs
sudo journalctl -u sacn-relay -f

# Restart
sudo systemctl restart sacn-relay
```

---

## License

MIT License — Free for personal and commercial use.

---

**Built with care for reliability in the field.**

---
```

---
