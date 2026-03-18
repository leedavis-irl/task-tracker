# Task Tracker System Architecture

## System Overview

A multi-child chore completion tracker using physical IoT buttons, a centralized e-ink status display, and Signal notifications. Designed for Ryker and Logan, expandable to additional children and tasks.

## Core Design Principles

**Physical-first interaction.** Kids press a real button when they complete a task. No apps, no screens to unlock, no accounts to manage. The button is the interface.

**Passive visibility.** The e-ink display at the front door shows current status without power draw, without screens lighting up, without anyone needing to check anything. You see it when you walk past.

**Notification where people look.** Signal was chosen over Slack because more household members check Signal. Technical elegance loses to actual eyeballs.

**One task = one button per child.** Shared tasks (laundry, teeth, plates) get separate buttons with stickers for each kid. No press-counting, no NFC tags, no conventions a 7-year-old has to remember at 7am.

## Hardware Inventory

| Device | Qty | Role | Location |
|---|---|---|---|
| Seeed XIAO ESP32-C6 IoT Button | 2 | Laundry (Ryker + Logan) | Hall laundry chute |
| Seeed XIAO ESP32-C6 IoT Button | 2 | Teeth (Ryker + Logan) | Bathroom |
| Seeed XIAO ESP32-C6 IoT Button | 2 | Plates (Ryker + Logan) | Kitchen sink area |
| Seeed XIAO ESP32-C6 IoT Button | 1 | AM Pills (Ryker only) | Pill case |
| ESP32 dev board + Waveshare 7.5" e-ink | 1 | Status display | Front door |

**Total: 8 devices, ~$110-120**

## Data Flow

```
┌─────────────┐     HTTP POST /press     ┌───────────────────┐
│  IoT Button  │────────────────────────▶│  Flask Server      │
│  (ESP32-C6)  │                         │  (EC2, port 8765)  │
└─────────────┘                          └────────┬──────────┘
                                                   │
                                         ┌─────────┴─────────┐
                                         │                     │
                              GET /state │                     │ 9:30 AM summary
                                         ▼                     ▼
                                  ┌─────────────┐    ┌──────────────┐
                                  │  E-Ink       │    │  Signal Relay │
                                  │  Display     │    │  (EC2 :8766)  │
                                  │  (ESPHome)   │    └──────┬───────┘
                                  └─────────────┘           │
                                                             ▼
                                                    ┌──────────────┐
                                                    │  Signal      │
                                                    │  → Favalon   │
                                                    └──────────────┘
```

### Step-by-step flow for a single button press:

1. **Button press** → ESP32-C6 wakes from deep sleep
2. **ESPHome firmware** → Connects to WiFi, sends HTTP POST to Flask server with `{"owner": "ryker", "task": "teeth"}`
3. **Flask server checks** → Is the active window open (6:00–9:30 AM)? Is this task already done?
4. **Server updates state** → Marks task as done in `state.json`, returns `{"status": "ok"}`
5. **Button buzzer feedback** → Two clicks (success), one long click (already done), three quick clicks (outside window / error)
6. **Display polls** → Every 60 seconds, the e-ink display GETs `/state` from the server
7. **E-ink refreshes** → Redraws two-column checklist with updated checkmarks

### Daily reset flow:

1. **APScheduler job** → Fires at 3:00 AM Pacific
2. **Reset all states** → `state.json` wiped and rebuilt with today's tasks
3. **Display polls** → Picks up fresh state on next 60-second cycle

### 9:30 AM Signal summary:

1. **APScheduler job** → Fires at 9:30 AM Pacific
2. **Build summary** → Checks which tasks each child completed/missed
3. **POST to Signal relay** → Sends message to EC2 Signal relay on port 8766
4. **Signal delivery** → `signal-cli` sends message to Favalon group

## Component Responsibilities

### ESPHome (runs on all 8 devices)

**On buttons:**
- Deep sleep management (wake on button press)
- WiFi connection
- HTTP POST to Flask server with owner/task payload
- Buzzer feedback based on server response (success / already done / outside window)
- Battery voltage reporting (if battery-powered)

**On display:**
- Polls Flask server every 60 seconds via HTTP GET `/state`
- Parses flat JSON response into boolean globals
- Renders two-column layout via display lambda
- Three display modes: outside window, active checklist, all-done celebration

### Flask Server (runs on EC2)

- **Task registry** → Defines all tasks and owners in Python (DAILY_TASKS)
- **State machine** → Tracks completion status per child per task per day in `state.json`
- **Active window** → Only accepts button presses between 6:00–9:30 AM Pacific
- **API endpoints** → `/press` (POST), `/state` (GET), `/health` (GET)
- **Daily reset** → APScheduler clears all states at 3:00 AM Pacific
- **Signal summary** → APScheduler sends one summary at 9:30 AM Pacific via EC2 relay

### Signal Relay (runs on EC2, port 8766)

- Receives summary message from Flask server via HTTP POST
- Sends to Favalon Signal group via `signal-cli`
- Authenticated with shared `RELAY_TOKEN` header

## Server State Model

State is stored in `state.json` on disk. The `/state` endpoint returns a flat JSON object for the display:

```json
{
  "active_window": true,
  "both_done": false,
  "ryker_laundry": false,
  "ryker_teeth": true,
  "ryker_plates": false,
  "ryker_pills": false,
  "ryker_done": false,
  "logan_laundry": false,
  "logan_teeth": false,
  "logan_plates": false,
  "logan_done": false
}
```

## Network Topology

```
Internet
├── EC2 (34.208.73.189)
│   ├── Flask task-tracker server (:8765) — systemd service
│   └── Signal relay (:8766) — signal-cli
│
WiFi Network (Avalon)
├── 7× Seeed XIAO ESP32-C6 buttons (HTTP POST to EC2)
└── 1× ESP32 + e-ink display (HTTP GET from EC2, polls every 60s)
```

All button and display devices communicate with the EC2 server over the internet via HTTP. No local server required. No Home Assistant involvement.

## Expansion Points

**New task:** Add button hardware + ESPHome config + update `DAILY_TASKS` (or `WEDNESDAY_TASKS` for day-specific tasks, currently empty) in `server.py` + update display lambda. Follow the task template in `04-task-template.md`.

**New child:** Add stickered buttons for shared tasks + child-specific buttons. Add new owner to server task definitions. Update display lambda for additional column (display supports up to 3-4 columns at 7.5").

**New notification channel:** Modify `job_morning_summary()` in `server.py` to send via additional channels.

**Schedule changes:** Modify task definitions in `server.py`. The `tasks_for_today()` function makes day-of-week logic trivial to adjust.

## Key Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Server location | AWS EC2 | Always-on, no dependency on local hardware being awake |
| Communication | HTTP (not ESPHome native API) | Buttons POST directly to server; no HA intermediary needed |
| State storage | JSON file on disk | Simple, inspectable, survives restarts |
| Display update | Polling (60s interval) | Simpler than push; e-ink refresh rate makes real-time unnecessary |
| Display tech | E-ink via ESPHome | Always visible unpowered, wall-mounts cleanly |
| Notification | Signal via signal-cli on EC2 | Household actually checks Signal; one summary per day, not per-task |
| Button hardware | Seeed XIAO ESP32-C6 | $10/ea, deep sleep support, ESPHome compatible |
| Config management | ESPHome packages | DRY configs, base templates + per-device overrides |
| Timezone handling | `zoneinfo` Pacific | Server runs on UTC EC2 but all logic uses America/Los_Angeles |
