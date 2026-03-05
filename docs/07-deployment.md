# Task Tracker — Deployment Guide

End-to-end setup for the Avalon household task tracker:
9 ESPHome buttons + 1 e-ink display + Pi server + EC2 Signal relay.

---

## Overview

```
[Button press]
     │  HTTP POST /press
     ▼
[Pi Server :8765]  ──── GET /state ────▶  [E-ink Display]
     │
     │  9:30 AM summary only
     ▼
[EC2 :8766 /send-signal]
     │
     ▼
[Signal → Favalon group]
```

**Signal behavior:** One message per day, sent at 9:30 AM Pacific.
Format: `✅ Ryker done | ⚠️ Logan missed: teeth, plates`
No real-time notifications when tasks are completed.

---

## Prerequisites

- Raspberry Pi (any model with WiFi) on the Avalon local network
- EC2 instance at 13.58.219.0 with signal-cli configured for +17074748930
- 9× Seeed XIAO ESP32-C6 boards
- 1× Waveshare 7.5" V2 e-ink display + Waveshare ESP32 driver board
- A machine with ESPHome installed (or use the ESPHome web installer)

---

## Part 1 — EC2 Signal Relay

Do this first so you can test it independently.

### 1.1 SSH into EC2

```bash
ssh -i ~/.ssh/iji_ec2 ubuntu@13.58.219.0
```

### 1.2 Copy signal_relay.py

```bash
scp -i ~/.ssh/iji_ec2 \
  task-tracker/ec2/signal_relay.py \
  ubuntu@13.58.219.0:~/signal_relay.py
```

### 1.3 Install Flask (if not already present)

```bash
pip3 install flask
```

### 1.4 Choose a relay token

Pick any strong random string. You'll use the same value in two places:
- `RELAY_TOKEN` env var on EC2
- `RELAY_TOKEN` env var in the Pi systemd service

```bash
# Generate one:
openssl rand -hex 24
# Example output: a3f7c2b1d4e8f09a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
```

### 1.5 Run standalone (test first)

```bash
RELAY_TOKEN=your_token_here python3 ~/signal_relay.py &
```

### 1.6 Open firewall port 8766

```bash
sudo ufw allow 8766/tcp
sudo ufw status
```

### 1.7 Test it

```bash
curl -X POST http://13.58.219.0:8766/send-signal \
  -H "Content-Type: application/json" \
  -H "X-Relay-Token: your_token_here" \
  -d '{"message": "✅ Test from task tracker"}'
# Expected: {"status": "sent"}
```

Check that the message appeared in the Favalon Signal group.

### 1.8 Make it persistent (systemd)

```bash
cat > /etc/systemd/system/signal-relay.service << 'EOF'
[Unit]
Description=Signal Relay for Task Tracker
After=network.target

[Service]
Type=simple
User=ubuntu
Environment="RELAY_TOKEN=REPLACE_WITH_YOUR_TOKEN"
ExecStart=/usr/bin/python3 /home/ubuntu/signal_relay.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable signal-relay
sudo systemctl start signal-relay
sudo systemctl status signal-relay
```

### 1.9 (Optional) Integrate into existing household-agent

Instead of running standalone, add to your existing Flask app:

```python
from signal_relay import relay_bp
app.register_blueprint(relay_bp)
```

Then skip the separate service above.

---

## Part 2 — Raspberry Pi Server

### 2.1 Give the Pi a static IP

On your router (or via Pi config), assign a fixed IP to the Pi.
Write it down — you'll need it for ESPHome configs.

Example: `192.168.1.50`

### 2.2 Copy server files to Pi

```bash
# From your laptop:
rsync -av task-tracker/server/ pi@192.168.1.50:~/task-tracker/server/
```

### 2.3 Set up Python virtualenv

```bash
ssh pi@192.168.1.50

cd ~/task-tracker/server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

### 2.4 Create state directory

```bash
sudo mkdir -p /var/lib/task-tracker
sudo chown pi:pi /var/lib/task-tracker
```

### 2.5 Configure the systemd service

Edit `task-tracker.service` — replace the two `CHANGE_ME` values:

```ini
Environment="RELAY_TOKEN=your_token_here"   # same token as EC2
```

The `EC2_RELAY_URL` is already set to `http://13.58.219.0:8766/send-signal`.

### 2.6 Install and start the service

```bash
# Copy from Pi home dir to systemd
sudo cp ~/task-tracker/server/task-tracker.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable task-tracker
sudo systemctl start task-tracker
sudo systemctl status task-tracker
```

### 2.7 Verify the server

```bash
# From any device on the local network:
curl http://192.168.1.50:8765/health
# Expected: {"status": "ok", "date": "2026-03-05"}

curl http://192.168.1.50:8765/state
# Expected: JSON with all tasks false, active_window true/false depending on time

# Simulate a button press:
curl -X POST http://192.168.1.50:8765/press \
  -H "Content-Type: application/json" \
  -d '{"owner": "ryker", "task": "laundry"}'
# Expected: {"status": "ok"} or {"status": "outside_window"}
```

### 2.8 Watch logs

```bash
sudo journalctl -u task-tracker -f
```

---

## Part 3 — ESPHome Secrets

### 3.1 Fill in secrets.yaml

```bash
cd task-tracker/esphome
cp secrets.yaml.template secrets.yaml
```

Edit `secrets.yaml`:

```yaml
wifi_ssid: "YourActualSSID"
wifi_password: "YourActualPassword"
api_encryption_key: "$(openssl rand -base64 32)"
ota_password: "choose_something"
pi_ip: "192.168.1.50"       # ← your Pi's static IP
relay_token: "your_token"   # ← not used by buttons directly, just for reference
```

**Never commit secrets.yaml.** It is gitignored by convention (add it if needed).

---

## Part 4 — Flash the Buttons (9× Seeed XIAO ESP32-C6)

Flash each button one at a time. Label each board before flashing.

### 4.1 Install ESPHome (if not already)

```bash
pip install esphome
# or use the ESPHome Dashboard: https://dashboard.esphome.io
```

### 4.2 Flash each button

Connect the XIAO ESP32-C6 via USB-C. Then for each button yaml:

```bash
cd task-tracker/esphome

# First flash (wired):
esphome run button-ryker-laundry.yaml

# Subsequent flashes (OTA, once on WiFi):
esphome run button-ryker-laundry.yaml --device 192.168.1.XXX
```

Repeat for all 9 buttons:
- button-ryker-laundry
- button-ryker-teeth
- button-ryker-plates
- button-ryker-pills
- button-ryker-flute     ← Wednesday only (server handles rejection)
- button-logan-laundry
- button-logan-teeth
- button-logan-plates
- button-logan-trumpet   ← Wednesday only

### 4.3 Test each button

After flashing, press the physical button. Watch the Pi logs:

```bash
sudo journalctl -u task-tracker -f
```

You should see: `Recorded: ryker / laundry`

The button should flash green briefly on success.

**Outside 6–9:30 AM window:** The server returns `outside_window` and the
button flashes double-red. This is expected — press during the window to
confirm `ok`.

**Non-Wednesday for flute/trumpet:** Server returns `not_today`. Button
flashes double-red. Expected.

---

## Part 5 — Flash the Display (Waveshare 7.5" V2)

### 5.1 Update the Pi IP in display-front-door.yaml

Open `esphome/display-front-door.yaml` and update:

```yaml
substitutions:
  pi_ip: "192.168.1.50"   # ← your actual Pi IP
```

### 5.2 Flash the display board

The Waveshare ESP32 driver board connects via USB.

```bash
cd task-tracker/esphome
esphome run display-front-door.yaml
```

### 5.3 Verify display behavior

**During active window (6:00–9:30 AM):**
- Left column: Ryker's tasks with ○ (pending) or ✓ (done)
- Right column: Logan's tasks
- Flute/Trumpet show "-" on non-Wednesdays

**Outside active window:**
- Shows "Good morning! / Tasks open 6:00 – 9:30 AM"

**Both kids done:**
- Shows "All done! / Ryker ✓  |  Logan ✓"

The display refreshes every ~5 seconds when state changes.

> **Note on e-ink refresh rate:** Full refreshes on 7.5" panels take ~3-4
> seconds and flash briefly. This is normal. The display will not flicker
> unnecessarily — it only calls `epaper.update()` after a new HTTP response.
> Consider adding a state-change check in the lambda if flicker is bothersome.

---

## Part 6 — Signal Message Verification

The system sends **one Signal message per day**, at 9:30 AM Pacific.

### Format

```
✅ Ryker done | ✅ Logan done
✅ Ryker done | ⚠️ Logan missed: teeth, plates
⚠️ Ryker missed: pills | ⚠️ Logan missed: teeth, plates
```

### Force a test (manually trigger the 9:30 job)

On the Pi, use a quick Python one-liner:

```bash
curl -X POST http://192.168.1.50:8765/press \
  -H "Content-Type: application/json" \
  -d '{"owner": "ryker", "task": "laundry"}'

# Then temporarily set state.summary_sent = false and call the relay directly:
curl -X POST http://13.58.219.0:8766/send-signal \
  -H "Content-Type: application/json" \
  -H "X-Relay-Token: your_token_here" \
  -d '{"message": "✅ Ryker done | ⚠️ Logan missed: teeth, plates"}'
```

---

## Part 7 — Daily Reset Verification

The 3:00 AM reset wipes all task state. To verify without waiting:

```bash
# Check current state
curl http://192.168.1.50:8765/state | python3 -m json.tool

# Manually wipe state (Pi):
echo '{}' > /var/lib/task-tracker/state.json
sudo systemctl restart task-tracker

# State should reload fresh for today
curl http://192.168.1.50:8765/state | python3 -m json.tool
```

---

## Troubleshooting

| Symptom | Check |
|---|---|
| Button flashes double-red always | Is it outside 6–9:30 AM window? Check Pi time: `date` |
| Button flashes nothing | Check WiFi — button may not be reaching Pi |
| Display shows stale data | Check Pi server is running: `systemctl status task-tracker` |
| Display shows "Good morning!" during active hours | Pi server may be down or unreachable |
| No Signal message at 9:30 | Check Pi logs for relay errors; verify EC2 relay is running |
| Signal relay returns 401 | Token mismatch — verify same RELAY_TOKEN on both Pi and EC2 |
| signal-cli not found | Update SIGNAL_CLI path in signal_relay.py or env var |
| State resets unexpectedly | Corrupt state.json — server auto-recovers on restart |

---

## File Reference

```
task-tracker/
├── esphome/
│   ├── secrets.yaml.template   ← copy → secrets.yaml, fill in values
│   ├── .base-common.yaml       ← WiFi/API/OTA shared config
│   ├── .base-button.yaml       ← button behavior (deep sleep, HTTP, LED)
│   ├── .base-display.yaml      ← display SPI/fonts/polling base
│   ├── button-*.yaml           ← one per physical button (9 total)
│   └── display-front-door.yaml ← e-ink display config + render lambda
├── server/
│   ├── server.py               ← Flask Pi server
│   ├── requirements.txt        ← pip deps
│   └── task-tracker.service    ← systemd unit
├── ec2/
│   └── signal_relay.py         ← Signal relay Flask app/blueprint
└── docs/
    └── 07-deployment.md        ← this file
```
