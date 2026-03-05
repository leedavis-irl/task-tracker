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
| Seeed XIAO ESP32-C6 IoT Button | 1 | Flute (Ryker, Wed only) | Flute case |
| Seeed XIAO ESP32-C6 IoT Button | 1 | Trumpet (Logan, Wed only) | Trumpet case |
| ESP32 dev board + Waveshare 7.5" e-ink | 1 | Status display | Front door |

**Total: 10 devices, ~$130-140**

## Data Flow

```
┌─────────────┐     ┌───────────────┐     ┌──────────────────┐
│  IoT Button  │────▶│   ESPHome     │────▶│  Home Assistant   │
│  (ESP32-C6)  │     │  (firmware)   │     │  (state machine)  │
└─────────────┘     └───────────────┘     └────────┬─────────┘
                                                    │
                                          ┌─────────┴─────────┐
                                          │                     │
                                          ▼                     ▼
                                   ┌─────────────┐    ┌──────────────┐
                                   │  E-Ink       │    │  Signal      │
                                   │  Display     │    │  Notification│
                                   │  (ESPHome)   │    │  (REST API)  │
                                   └─────────────┘    └──────────────┘
```

### Step-by-step flow for a single button press:

1. **Button press** → ESP32-C6 wakes from deep sleep
2. **ESPHome firmware** → Connects to WiFi, fires a `button_press` event to HA via native API
3. **HA automation triggers** → Checks: Is this task already done today? Is this the right day (Wednesday check for instruments)?
4. **HA updates state** → Sets `input_boolean.task_{child}_{task}` to `on`, records timestamp in `input_datetime`
5. **HA notifies display** → Pushes updated state to ESPHome display device via `homeassistant.service`
6. **E-ink refreshes** → Redraws two-column checklist with updated checkmarks
7. **HA sends Signal** → Calls `notify.signal` with completion message to household group
8. **Button LED** → ESPHome blinks LED green (confirmation) or red (already done / error)

### Daily reset flow:

1. **Time trigger** → HA automation fires at 3:00 AM
2. **Reset all states** → All `input_boolean.task_*` entities set to `off`
3. **Clear timestamps** → All `input_datetime.task_*` entities cleared
4. **Refresh display** → Push blank checklist to e-ink

## Component Responsibilities

### ESPHome (runs on all 10 devices)

**On buttons:**
- Deep sleep management (wake on button press)
- WiFi connection and HA native API registration
- Button press event emission
- LED feedback (green = success, red = duplicate/error)
- Battery voltage reporting (if battery-powered)

**On display:**
- Subscribe to HA text sensors containing display data
- Render two-column layout via display lambda
- Handle partial vs full refresh cycles
- Report WiFi signal strength

### Home Assistant (central brain)

- **Task registry** → Defines all tasks, owners, schedules, locations
- **State machine** → Tracks completion status per child per task per day
- **Schedule logic** → Knows which tasks apply on which days (daily vs Wednesday-only)
- **Automation engine** → Responds to button events, triggers display updates and notifications
- **Daily reset** → Clears all states at 3 AM

### Signal Messenger REST API (Docker container)

- Receives notification requests from HA
- Delivers messages to household Signal group
- Runs as `bbernhard/signal-cli-rest-api` container in `json-rpc` mode

## HA Entity Model

### Per-task entities (example: Ryker's laundry)

| Entity ID | Type | Purpose |
|---|---|---|
| `input_boolean.task_ryker_laundry` | Boolean | Completion state (on/off) |
| `input_datetime.task_ryker_laundry_time` | DateTime | Completion timestamp |

### System entities

| Entity ID | Type | Purpose |
|---|---|---|
| `input_boolean.task_system_enabled` | Boolean | Master enable/disable |
| `sensor.task_ryker_remaining` | Template | Count of incomplete tasks |
| `sensor.task_logan_remaining` | Template | Count of incomplete tasks |
| `sensor.task_display_payload` | Template | Formatted string for e-ink |

### Automation naming

| Automation | Trigger | Action |
|---|---|---|
| `task_button_ryker_laundry` | Button press event | Update state, notify, refresh display |
| `task_button_logan_laundry` | Button press event | Update state, notify, refresh display |
| `task_daily_reset` | Time: 3:00 AM | Reset all booleans and timestamps |
| `task_display_refresh` | Any task state change | Push updated layout to display |

## Network Topology

```
WiFi Network
├── Home Assistant server (hub)
├── Signal REST API (Docker, same host or separate)
├── 9x Seeed XIAO ESP32-C6 buttons (deep sleep, wake-on-press)
└── 1x ESP32 + e-ink display (always connected)
```

All devices communicate over WiFi using ESPHome's native API (encrypted). No MQTT broker required. Signal REST API is accessed via HTTP from HA on the local network.

## Expansion Points

**New task:** Add button hardware + ESPHome config + HA entities + automation. Follow the task template in `04-task-template.md`.

**New child:** Add stickered buttons for shared tasks + child-specific buttons. Create new entity set. Update display lambda for additional column (display supports up to 3-4 columns at 7.5").

**New notification channel:** Add additional `notify` service calls in HA automations alongside Signal.

**Schedule changes:** Modify conditions in HA automations. Task registry pattern makes day-of-week logic trivial to adjust.

## Key Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Communication protocol | ESPHome native API | Simpler than MQTT, auto-discovery in HA, encrypted |
| State storage | HA input_boolean/input_datetime | Simple, inspectable, survives restarts |
| Display tech | E-ink via ESPHome | Always visible unpowered, wall-mounts cleanly |
| Notification | Signal via REST API | Household actually checks Signal |
| Button hardware | Seeed XIAO ESP32-C6 | $10/ea, deep sleep support, ESPHome compatible |
| Config management | ESPHome packages | DRY configs, base templates + per-device overrides |
