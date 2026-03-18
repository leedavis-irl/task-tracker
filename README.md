# Task Tracker

A physical IoT chore tracking system built with ESP32 buttons, a Flask server, and an e-ink display. Buttons are placed at task locations around the house. When a task is completed, pressing the button records it on a central server. A wall-mounted e-ink display shows a live checklist, and a daily summary is sent via Signal.

## How It Works

```
Button press (WiFi) ──HTTP POST──→ Flask server (EC2) ←──HTTP GET── E-ink display (WiFi)
                                        │
                                   9:30 AM daily
                                        │
                                   Signal relay ──→ Signal group
```

1. **Buttons** — Seeed XIAO ESP32-C6 boards with a tact switch, passive buzzer, and LiPo battery. Flashed with ESPHome. On press, sends an HTTP POST to the server with `{"owner": "...", "task": "..."}`.
2. **Server** — Flask app on EC2. Accepts button presses during a configurable morning window (default 6:00–9:30 AM). Tracks task completion per person per day. Resets at 3:00 AM.
3. **Display** — Waveshare 7.5" e-ink (800×480 B/W) on an ESP32 driver board. Polls the server every 60 seconds and renders a two-column checklist.
4. **Signal relay** — Separate Flask endpoint on the same server. At 9:30 AM, the server sends a summary message to a Signal group via signal-cli.

### Buzzer Feedback

Buttons give audio feedback on press:
- **Two short clicks** — task recorded successfully
- **One long click** — task was already completed today
- **Three quick clicks** — outside the active window or error

## Hardware

| Component | Spec | Qty |
|-----------|------|-----|
| Seeed XIAO ESP32-C6 | WiFi microcontroller, USB-C, LiPo charging | 1 per button |
| 6mm tact switch | Momentary, through-hole | 1 per button |
| Passive buzzer | ~12mm, driven via GPIO toggle | 1 per button |
| 400mAh LiPo | 3.7V, soldered to BAT+/BAT- pads | 1 per button |
| Waveshare 7.5" V2 e-ink | 800×480 B/W, SPI interface | 1 |
| ESP32 driver board | Waveshare universal e-Paper driver, Rev 3 | 1 |
| 3.7V LiPo | Powers display via 5V/GND pins | 1 |

Full bill of materials with sourcing links in `docs/05-bill-of-materials.md`.

### 3D-Printed Enclosures

Button enclosures are designed in OpenSCAD (`3d/button-enclosure.scad`):
- Two-piece snap-fit design (base + lid with integrated button cap)
- Internal layout: battery, tact switch on pillar mount, XIAO, buzzer
- USB-C access on bottom edge for charging
- Buzzer sound holes on side wall

## Server

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — returns `{"status": "ok", "date": "YYYY-MM-DD"}` |
| `POST` | `/press` | Record task completion — body: `{"owner": "...", "task": "..."}` |
| `GET` | `/state` | Current state as flat JSON (for display polling) |

### Response Codes for `/press`

| Status | Meaning |
|--------|---------|
| `ok` | Task recorded |
| `already_done` | Task was already completed today |
| `outside_window` | Not within the active time window |
| `not_today` | Task not applicable today (day-specific scheduling) |
| `invalid` | Unknown owner or task |

### Task Definitions

Tasks are defined in `server.py` as Python dicts:

```python
DAILY_TASKS = {
    "child_a": ["laundry", "teeth", "plates", "pills"],
    "child_b": ["laundry", "teeth", "plates"],
}
```

Day-specific tasks (e.g., Wednesday-only) are supported via separate dicts.

### Scheduled Jobs

- **3:00 AM Pacific** — Reset all task state for the new day
- **9:30 AM Pacific** — Send Signal summary (e.g., "Child A done | Child B missed: teeth, plates")

## ESPHome Configuration

Devices use a base template pattern:

```
esphome/
├── .base-common.yaml      WiFi, API, OTA (shared by all devices)
├── .base-button.yaml       Button logic, HTTP POST, buzzer, deep sleep
├── .base-display.yaml      SPI, polling, rendering
├── button-*.yaml           Per-device configs (just substitutions + package includes)
├── display-front-door.yaml Full display config with rendering lambda
└── secrets.yaml.template   Template for WiFi/API credentials
```

Each button config is ~10 lines of substitutions that reference the base templates.

### GPIO Assignments (Buttons)

| Pin | Function |
|-----|----------|
| GPIO1 (D1) | Tact switch input (active LOW, internal pullup) |
| GPIO2 (D2) | Passive buzzer output (GPIO toggle) |
| GPIO15 | Onboard LED status |
| BAT+/BAT- | LiPo battery pads |

### Known Platform Issues

- **LEDC/rtttl** does not work on ESP32-C6 with esp-idf framework — buzzer uses plain GPIO toggle
- **Deep sleep** disabled due to ESP-IDF 5.1.5 crash on ESP32-C6 wake
- **`verify_ssl: false`** required in HTTP requests even for plain HTTP on esp-idf, or requests fail silently

## Deployment

### Server Setup

```bash
# On EC2
pip install -r server/requirements.txt
cp .env.example .env    # Edit with your values

# Run directly
python server/server.py

# Or via systemd (see server/task-tracker.service)
sudo systemctl enable task-tracker
sudo systemctl start task-tracker
```

### Signal Relay

```bash
# Same EC2 instance, separate service
pip install flask
python ec2/signal_relay.py

# Requires signal-cli installed and registered
```

### Flashing Devices

```bash
# First flash (USB)
esphome run esphome/button-child_a-laundry.yaml

# Subsequent updates (OTA)
esphome run esphome/button-child_a-laundry.yaml --device 192.168.x.x
```

Copy `esphome/secrets.yaml.template` to `esphome/secrets.yaml` and fill in WiFi credentials and server IP before flashing.

## Documentation

Detailed guides in `docs/`:

| Doc | Contents |
|-----|----------|
| `01-architecture.md` | System design, data flow, component responsibilities |
| `02-technical-best-practices.md` | ESPHome patterns, server config, e-ink gotchas |
| `03-project-process.md` | Development workflow, testing, deployment procedures |
| `04-task-template.md` | Step-by-step guide for adding new tasks |
| `05-bill-of-materials.md` | Parts list, sourcing, cost breakdown |
| `06-button-design-spec.md` | Enclosure design, mechanical specs |
| `07-deployment.md` | Full EC2 setup and device commissioning |
| `08-button-build-guide.md` | Complete soldering and assembly walkthrough |

## Tech Stack

- **Firmware:** ESPHome (ESP-IDF framework)
- **Microcontrollers:** Seeed XIAO ESP32-C6
- **Display:** Waveshare 7.5" V2 e-ink
- **Server:** Python, Flask, APScheduler
- **Messaging:** signal-cli
- **Enclosures:** OpenSCAD, 3D printed (PLA/PETG)

## License

Private project. Not licensed for redistribution.
