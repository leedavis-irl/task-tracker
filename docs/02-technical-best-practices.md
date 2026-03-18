# Technical Best Practices

## ESPHome Configuration

### File Organization

Use ESPHome's packages system to keep configs DRY. The structure:

```
esphome/
├── secrets.yaml                    # WiFi, API keys, server IP
├── .base-common.yaml               # WiFi, API, OTA, logger (all devices)
├── .base-button.yaml               # Button-specific: HTTP POST, buzzer feedback
├── .base-display.yaml              # Display-specific: SPI, fonts, polling base
├── button-ryker-laundry.yaml       # Per-device config
├── button-ryker-teeth.yaml
├── button-logan-laundry.yaml
├── ...
└── display-front-door.yaml
```

Dot-prefix on base files (`.base-*`) keeps them grouped at top of directory listings and signals "don't flash this directly."

### Base Common Config (.base-common.yaml)

Every device inherits this. Contains:

```yaml
wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password
  ap:
    ssid: "${device_name} Fallback"
    password: "fallback1234"

api:
  encryption:
    key: !secret api_encryption_key

ota:
  - platform: esphome
    password: !secret ota_password

logger:
  level: INFO
```

### Per-Device Config Pattern

Each device YAML is minimal — just substitutions and package includes:

```yaml
substitutions:
  device_name: button-ryker-laundry
  owner: ryker
  task: laundry
  pi_ip: !secret pi_ip

packages:
  common: !include .base-common.yaml
  button: !include .base-button.yaml
```

This means adding a new button = copying a 10-line file and changing 4 substitution values.

### Substitutions as the Interface

Substitutions are the contract between base configs and per-device configs:

| Substitution | Used In | Example |
|---|---|---|
| `${device_name}` | Common (hostname, AP name) | `button-ryker-laundry` |
| `${owner}` | Button base (HTTP POST body) | `ryker` |
| `${task}` | Button base (HTTP POST body) | `laundry` |
| `${pi_ip}` | Button/display base (server URL) | `34.208.73.189` |

### Naming Conventions (ESPHome)

**Device names:** `{type}-{owner}-{task}` using hyphens (RFC1912 compliant)
- `button-ryker-laundry`
- `button-logan-teeth`
- `display-front-door`

### Deep Sleep for Buttons

Buttons spend 99.9% of their time asleep. Config pattern:

```yaml
deep_sleep:
  id: deep_sleep_control
  run_duration: 10s        # Max awake time per press
  sleep_duration: 0s       # Sleep indefinitely (wake on pin)
  wakeup_pin:
    number: GPIO1
    mode: INPUT_PULLUP
    inverted: true
```

Key rules:
- **10 second max awake time** — connect WiFi, send HTTP POST, get response, sleep
- **No periodic wake** — only wake on physical button press
- **Fallback** — if WiFi fails within 10s, sleep anyway (don't drain battery)

> **Note:** Deep sleep is currently disabled due to ESP-IDF 5.1.5 sleep crash on ESP32-C6. Will be re-enabled in a future firmware update.

### Buzzer Feedback Pattern

```yaml
output:
  - platform: gpio
    pin: GPIO2    # D2 on XIAO ESP32-C6
    id: buzzer_out

# Feedback via GPIO toggle patterns (on/off with delays):
# - Two clicks = success ("ok" from server)
# - One long click = already done today
# - Three quick clicks = outside window / error
```

> **LEDC/rtttl does NOT work** on ESP32-C6 with esp-idf framework (outputs 0V). Use plain GPIO toggle instead.

### HTTP Request Configuration

Both buttons and display use the `http_request` component. Critical setting:

```yaml
http_request:
  useragent: "ESPHome Task Button"
  timeout: 5s
  verify_ssl: false    # Required — without this, HTTP requests fail silently on esp-idf
```

The `verify_ssl: false` is needed even for plain HTTP on the esp-idf framework. Without it, requests will silently fail with no error in logs.

### E-Ink Display Best Practices

**Pin configuration for Waveshare 7.5" V2 with ESP32 driver board:**

```yaml
spi:
  clk_pin: GPIO13
  mosi_pin: GPIO14

display:
  - platform: waveshare_epaper
    id: eink_display
    model: 7.50inV2
    cs_pin: GPIO15
    dc_pin: GPIO27
    busy_pin:
      number: GPIO25
      inverted: true      # REQUIRED for 7.50in V2 — prevents display damage
    reset_pin: GPIO26
    update_interval: never  # Only update after receiving new state from server
    lambda: |-
      // Display rendering code here
```

**Critical rules:**
- `busy_pin: inverted: true` is MANDATORY for 7.50in V2 models. Omitting this can damage the display.
- Set `update_interval: never` — the poll script calls `epaper.update()` after receiving new state
- Keep fonts to 2-3 sizes max to conserve flash memory
- Use ASCII glyphs only ([X], ( ), -) — Unicode markers (✓, ○, ⚠) require special font files
- Restrict glyph sets to only the characters actually used to minimize flash usage

### Secrets Management

Single `secrets.yaml` in the ESPHome config directory:

```yaml
wifi_ssid: "YourNetworkName"
wifi_password: "YourWiFiPassword"
api_encryption_key: "base64-encoded-32-byte-key"
ota_password: "OtaUpdatePassword"
pi_ip: "34.208.73.189"
relay_token: "your_shared_secret"
```

**Rules:**
- Never commit secrets.yaml to version control
- Generate API encryption key with: `python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"`
- All devices share the same API key
- OTA password is separate from API key
- `pi_ip` is the EC2 server address (misnamed for historical reasons — it's not a Pi)

## Server Configuration

### Task Definitions

Tasks are defined in `server.py` as Python dicts:

```python
DAILY_TASKS = {
    "ryker": ["laundry", "teeth", "plates", "pills"],
    "logan": ["laundry", "teeth", "plates"],
}

WEDNESDAY_TASKS = {
    "ryker": [],
    "logan": [],
}
```

To add a new task, add it to the appropriate dict and restart the server.

### Timezone Handling

The server runs on EC2 (UTC system clock) but all time-dependent logic uses Pacific time:

```python
from zoneinfo import ZoneInfo
PACIFIC = ZoneInfo("America/Los_Angeles")

# All datetime.now() calls use:
now = datetime.now(PACIFIC)
```

This applies to: active window check, weekday calculation for day-specific tasks, and daily reset scheduling (APScheduler uses `timezone="America/Los_Angeles"`).

### Signal Integration

Signal messages are sent via a relay endpoint on EC2 (port 8766) using `signal-cli`. The task tracker server sends one summary per day at 9:30 AM Pacific:

```
Ryker done | Logan missed: teeth, plates
```

The relay authenticates via `X-Relay-Token` header (shared secret between task tracker server and signal relay).

## Version Control

### What to track in Git

```
task-tracker/
├── esphome/
│   ├── .base-common.yaml
│   ├── .base-button.yaml
│   ├── .base-display.yaml
│   ├── button-*.yaml           (one per physical button)
│   └── display-front-door.yaml
├── server/
│   ├── server.py
│   ├── requirements.txt
│   └── task-tracker.service
├── ec2/
│   └── signal_relay.py
├── docs/
│   └── *.md
└── .gitignore
```

### .gitignore

```
secrets.yaml
.esphome/
buzzer-test.yaml
*-flash.yaml
*.pyc
```

### Commit Conventions

- `feat(button): add Ryker vitamins daily button`
- `fix(display): correct column alignment for two-child layout`
- `docs: update task template with schedule configuration notes`
- `refactor(esphome): extract LED feedback to shared package`

## Error Handling

### Button fails to connect to WiFi
ESPHome's 10-second run_duration ensures the button goes back to sleep. Battery is preserved. Task simply doesn't register — kid can press again.

### Display stops updating
E-ink retains last image. Stale data is visible and obvious (yesterday's tasks still shown). Check EC2 server is running: `systemctl status task-tracker`.

### Server goes down
Buttons will get HTTP errors and play the three-click error pattern. Display retains last rendered image. Restart with `sudo systemctl restart task-tracker` on EC2.

### Signal relay fails
Summary message fails silently. Tasks still register on the server and display. Signal is a nice-to-have, not a critical path.

### Duplicate button press
Server checks if task is already done and returns `"already_done"`. Button plays one long click. State is not modified.
