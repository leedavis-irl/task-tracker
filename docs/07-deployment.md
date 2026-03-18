# Task Tracker — Deployment Guide

End-to-end setup for the Avalon household task tracker:
7 ESPHome buttons + 1 e-ink display + EC2 server + EC2 Signal relay.

---

## Overview

```
[Button press]
     │  HTTP POST /press
     ▼
[EC2 Server :8765]  ──── GET /state ────▶  [E-ink Display]
     │
     │  9:30 AM summary only
     ▼
[EC2 :8766 /send-signal]
     │
     ▼
[Signal → Favalon group]
```

**Signal behavior:** One message per day, sent at 9:30 AM Pacific.
Format: `Ryker done | Logan missed: teeth, plates`
No real-time notifications when tasks are completed.

---

## Prerequisites

- AWS EC2 instance (currently at 34.208.73.189) with ports 8765 and 8766 open
- SSH key: `~/.ssh/the-pem-key.pem`
- signal-cli configured on EC2 for +17074748930
- 7× Seeed XIAO ESP32-C6 boards
- 1× Waveshare 7.5" V2 e-ink display + Waveshare ESP32 driver board
- A machine with ESPHome installed (`pip install esphome`)

---

## Part 1 — EC2 Signal Relay

Do this first so you can test it independently.

### 1.1 SSH into EC2

```bash
ssh -i ~/.ssh/the-pem-key.pem ubuntu@34.208.73.189
```

### 1.2 Copy signal_relay.py

```bash
scp -i ~/.ssh/the-pem-key.pem \
  task-tracker/ec2/signal_relay.py \
  ubuntu@34.208.73.189:~/signal_relay.py
```

### 1.3 Install Flask (if not already present)

```bash
pip3 install flask
```

### 1.4 Choose a relay token

Pick any strong random string. You'll use the same value in two places:
- `RELAY_TOKEN` env var on EC2 (signal relay)
- `RELAY_TOKEN` env var in the task-tracker systemd service

```bash
# Generate one:
openssl rand -hex 24
```

### 1.5 Run standalone (test first)

```bash
RELAY_TOKEN=your_token_here python3 ~/signal_relay.py &
```

### 1.6 Open firewall port 8766

In AWS Console → EC2 → Security Groups, add inbound rule:
- Type: Custom TCP
- Port: 8766
- Source: 0.0.0.0/0 (or restrict to your home IP)

### 1.7 Test it

```bash
curl -X POST http://34.208.73.189:8766/send-signal \
  -H "Content-Type: application/json" \
  -H "X-Relay-Token: your_token_here" \
  -d '{"message": "Test from task tracker"}'
# Expected: {"status": "sent"}
```

Check that the message appeared in the Favalon Signal group.

### 1.8 Make it persistent (systemd)

```bash
sudo cat > /etc/systemd/system/signal-relay.service << 'EOF'
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

---

## Part 2 — EC2 Task Tracker Server

### 2.1 Copy server files to EC2

```bash
scp -i ~/.ssh/the-pem-key.pem \
  task-tracker/server/server.py \
  task-tracker/server/requirements.txt \
  ubuntu@34.208.73.189:~/task-tracker/
```

### 2.2 Set up Python virtualenv

```bash
ssh -i ~/.ssh/the-pem-key.pem ubuntu@34.208.73.189

cd ~/task-tracker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

### 2.3 Configure the systemd service

```bash
sudo cat > /etc/systemd/system/task-tracker.service << 'EOF'
[Unit]
Description=Avalon Task Tracker Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/task-tracker
Environment="STATE_FILE=/home/ubuntu/task-tracker/state.json"
Environment="EC2_RELAY_URL=http://127.0.0.1:8766/send-signal"
Environment="RELAY_TOKEN=REPLACE_WITH_YOUR_TOKEN"
ExecStart=/home/ubuntu/task-tracker/venv/bin/python server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=task-tracker

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable task-tracker
sudo systemctl start task-tracker
sudo systemctl status task-tracker
```

Note: `EC2_RELAY_URL` uses `127.0.0.1` since both services run on the same EC2 instance.

### 2.4 Verify the server

```bash
# From any device:
curl http://34.208.73.189:8765/health
# Expected: {"status": "ok", "date": "2026-03-11"}

curl http://34.208.73.189:8765/state
# Expected: JSON with all tasks false, active_window true/false depending on time

# Simulate a button press:
curl -X POST http://34.208.73.189:8765/press \
  -H "Content-Type: application/json" \
  -d '{"owner": "ryker", "task": "laundry"}'
# Expected: {"status": "ok"} or {"status": "outside_window"}
```

### 2.5 Watch logs

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
wifi_ssid: "Avalon"
wifi_password: "YourWiFiPassword"
api_encryption_key: "$(openssl rand -base64 32)"
ota_password: "choose_something"
pi_ip: "34.208.73.189"
relay_token: "your_token"
```

**Never commit secrets.yaml.** It is in `.gitignore`.

---

## Part 4 — Flash the Buttons (9× Seeed XIAO ESP32-C6)

Flash each button one at a time. Label each board before flashing.

### 4.1 Install ESPHome (if not already)

```bash
pip install esphome
```

### 4.2 Flash each button

Connect the XIAO ESP32-C6 via USB-C. Then for each button yaml:

```bash
cd task-tracker/esphome

# First flash (wired):
esphome run button-ryker-laundry.yaml --device /dev/cu.usbmodem*

# Subsequent flashes (OTA, once on WiFi):
esphome upload button-ryker-laundry.yaml --device button-ryker-laundry.local
```

Repeat for all 7 buttons:
- button-ryker-laundry
- button-ryker-teeth
- button-ryker-plates
- button-ryker-pills
- button-logan-laundry
- button-logan-teeth
- button-logan-plates

### 4.3 Test each button

After flashing, press the physical button. Watch the EC2 logs:

```bash
ssh -i ~/.ssh/the-pem-key.pem ubuntu@34.208.73.189 \
  "sudo journalctl -u task-tracker -f"
```

You should see: `Recorded: ryker / laundry`

The button should play two clicks on success.

**Outside 6–9:30 AM window:** The server returns `outside_window` and the
button plays three quick clicks. This is expected.

---

## Part 5 — Flash the Display (Waveshare 7.5" V2)

### 5.1 Verify pi_ip in secrets.yaml

The display config references `!secret pi_ip` which should be `34.208.73.189`.

### 5.2 Flash the display board

The Waveshare ESP32 driver board connects via USB.

```bash
cd task-tracker/esphome
esphome run display-front-door.yaml
```

For OTA updates:
```bash
esphome upload display-front-door.yaml --device display-front-door.local
```

### 5.3 Verify display behavior

**During active window (6:00–9:30 AM):**
- Left column: Ryker's tasks with ( ) (pending) or [X] (done)
- Right column: Logan's tasks

**Outside active window:**
- Shows "Good morning! / Tasks open 6:00 – 9:30 AM"

**Both kids done:**
- Shows "All done! / Ryker [X]  |  Logan [X]"

The display polls the server every 60 seconds.

---

## Part 6 — Signal Message Verification

The system sends **one Signal message per day**, at 9:30 AM Pacific.

### Format

```
Ryker done | Logan done
Ryker done | Logan missed: teeth, plates
Ryker missed: pills | Logan missed: teeth, plates
```

### Force a test

```bash
# Send a test message directly through the relay:
curl -X POST http://34.208.73.189:8766/send-signal \
  -H "Content-Type: application/json" \
  -H "X-Relay-Token: your_token_here" \
  -d '{"message": "Ryker done | Logan missed: teeth, plates"}'
```

---

## Part 7 — Daily Reset Verification

The 3:00 AM reset wipes all task state. To verify without waiting:

```bash
# Check current state
curl http://34.208.73.189:8765/state | python3 -m json.tool

# Manually wipe state (on EC2):
ssh -i ~/.ssh/the-pem-key.pem ubuntu@34.208.73.189 \
  "echo '{}' > ~/task-tracker/state.json && sudo systemctl restart task-tracker"

# State should reload fresh for today
curl http://34.208.73.189:8765/state | python3 -m json.tool
```

---

## Troubleshooting

| Symptom | Check |
|---|---|
| Button plays three clicks always | Is it outside 6–9:30 AM window? Check EC2 server time |
| Button plays nothing | Check WiFi — button may not be reaching server |
| Display shows stale data | Check EC2 server is running: `curl http://34.208.73.189:8765/health` |
| Display shows "Good morning!" during active hours | Server may be down or display can't reach EC2 |
| No Signal message at 9:30 | Check server logs for relay errors; verify signal relay is running |
| Signal relay returns 401 | Token mismatch — verify same RELAY_TOKEN on server and relay |
| signal-cli not found | Update SIGNAL_CLI path in signal_relay.py or env var |
| State resets unexpectedly | Corrupt state.json — server auto-recovers on restart |
| HTTP requests from buttons fail silently | Ensure `verify_ssl: false` is in `.base-button.yaml` http_request config |

---

## Infrastructure Reference

```
EC2 Instance: 34.208.73.189
  SSH: ssh -i ~/.ssh/the-pem-key.pem ubuntu@34.208.73.189
  Services:
    task-tracker (port 8765) — Flask server, systemd
    signal-relay (port 8766) — signal-cli relay, systemd
  Security group: ports 22, 8765, 8766 open

WiFi: Avalon (home network)
  Buttons and display connect via WiFi, POST/GET to EC2 over internet
```

## File Reference

```
task-tracker/
├── esphome/
│   ├── secrets.yaml.template   ← copy → secrets.yaml, fill in values
│   ├── .base-common.yaml       ← WiFi/API/OTA shared config
│   ├── .base-button.yaml       ← button behavior (HTTP POST, buzzer feedback)
│   ├── .base-display.yaml      ← display SPI/fonts/polling base
│   ├── button-*.yaml           ← one per physical button (7 total)
│   └── display-front-door.yaml ← e-ink display config + render lambda
├── server/
│   ├── server.py               ← Flask server (runs on EC2)
│   ├── requirements.txt        ← pip deps
│   └── task-tracker.service    ← systemd unit (reference — actual is on EC2)
├── ec2/
│   └── signal_relay.py         ← Signal relay Flask app
└── docs/
    └── *.md                    ← documentation
```
