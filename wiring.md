
# Wiring Guide – sACN Relay 4/8

This guide shows **exact GPIO connections** for the **Raspberry Pi** to control **4 or 8 relays** and display status on an **OLED**.

---

## Required Components

| Component | Specification |
|--------|---------------|
| **Raspberry Pi** | Zero W, 3, 4, or 5 |
| **Relay Module** | 4-channel or 8-channel, 5V, **active low** (e.g., Songle SRD-05VDC) |
| **OLED Display** | 0.96" I2C, SSD1306, 128x64 |
| **Push Button** | Momentary, for factory reset |
| **Jumper Wires** | Male-to-female or male-to-male |

---

## GPIO Pinout (BCM Mode)

| Function | GPIO | Pin | Notes |
|--------|------|-----|-------|
| **Relay 1** | 17 | 11 | Active LOW |
| **Relay 2** | 18 | 12 | Active LOW |
| **Relay 3** | 27 | 13 | Active LOW |
| **Relay 4** | 22 | 15 | Active LOW |
| **Relay 5** | 23 | 16 | Active LOW |
| **Relay 6** | 24 | 18 | Active LOW |
| **Relay 7** | 25 | 22 | Active LOW |
| **Relay 8** | 26 | 37 | Active LOW |
| **Reset Button** | 5 | 29 | Pull-up, trigger on GND |
| **OLED SDA** | 2 | 3 | I2C Data |
| **OLED SCL** | 3 | 5 | I2C Clock |

> **All relays use 5V logic** — connect VCC to **5V pin (2 or 4)** and GND to **any GND**.

---

## Relay Module Connections

### 4-Channel Mode (Relays 1–4)

| Relay Pin | Pi GPIO |
|---------|--------|
| VCC     | 5V (Pin 2 or 4) |
| GND     | GND (Pin 6, 9, 14, etc.) |
| IN1     | GPIO 17 |
| IN2     | GPIO 18 |
| IN3     | GPIO 27 |
| IN4     | GPIO 22 |

### 8-Channel Mode (Relays 1–8)

| Relay Pin | Pi GPIO |
|---------|--------|
| VCC     | 5V (Pin 2 or 4) |
| GND     | GND (Pin 6, 9, 14, etc.) |
| IN1     | GPIO 17 |
| IN2     | GPIO 18 |
| IN3     | GPIO 27 |
| IN4     | GPIO 22 |
| IN5     | GPIO 23 |
| IN6     | GPIO 24 |
| IN7     | GPIO 25 |
| IN8     | GPIO 26 |

> **Important:** Relay is **active low** — sending `0` turns it **ON**.

---

## OLED Display (I2C)

| OLED Pin | Pi GPIO |
|--------|--------|
| VCC    | 3.3V (Pin 1) |
| GND    | GND (Pin 6) |
| SDA    | GPIO 2 (Pin 3) |
| SCL    | GPIO 3 (Pin 5) |

> **Use 3.3V** — OLED is **not 5V tolerant**.

---

## Reset Button (Factory Reset)

| Button | Pi GPIO |
|-------|--------|
| One leg | GPIO 5 (Pin 29) |
| Other leg | GND |

> **Hold for 5 seconds** → resets to defaults and reboots.

---

## Verify I2C (OLED)

```bash
sudo i2cdetect -y 1
```

You should see:
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
3x:          -- -- -- -- -- -- -- -- -- -- -- -- 3c -- --
```

`3c` = OLED detected

---

## Test Relays

After install, go to **Test** tab in web UI → click **Pulse 5s** → relay should click.

---

## Wiring Diagram (8-Channel)

```
Raspberry Pi GPIO
┌───────────────────────────────────────────────────────────────┐
│  3.3V | 5V | 5V | GND | GND | GND | GND | GND | GND | GND | GND  │
│   1   | 2  | 4  | 6   | 9   | 14  | 20  | 25  | 30  | 34  | 39   │
│  OLED |    |    |     |     |     |     |     |     |     |      │
│  VCC  |    |    |     |     |     |     |     |     |     |      │
│   │   |    |     |     |     |     |     |     |     |      │
│   └──┴────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┴──────┘   │
│       │     │     │     │     │     │     │     │     │        │
│      GND   VCC  IN8  IN7  IN6  IN5  IN4  IN3  IN2  IN1        │
│       │     │     │     │     │     │     │     │     │        │
│    ┌──┴──┐  │  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐     │
│    │     │  │  │ R8  │  │ R7  │  │ R6  │  │ R5  │  │ R4  │  │ R3  │
│    │OLED │  │  │     │  │     │  │     │  │     │  │     │     │
│    └─────┘  │  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘     │
│             │                                            │
│          5V GND                                       5V │
│             │                                            │
└───────────────────────────────────────────────────────────────┘
```

---

**Wiring complete!**  
Your **sACN Relay 4/8** is now ready for power-up.

---
```

---

### Save as `~/sACN-Relay/wiring.md`

```bash
nano ~/sACN-Relay/wiring.md
```

Paste the content → **Ctrl+X → Y → Enter**

---

### Commit to GitHub

```bash
git add wiring.md
git commit -m "Update wiring.md for 8-channel mode"
git push
```

---
