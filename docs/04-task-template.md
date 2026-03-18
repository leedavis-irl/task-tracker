# Task Template: Adding a New Task

Use this template every time you add a new task to the system. Fill out the definition, then follow the steps in order.

---

## Task Definition (fill this out first)

```
Task name:         _______________  (e.g., "laundry", "teeth", "vitamins")
Task owner:        _______________  (e.g., "ryker", "logan")
Schedule:          _______________  (e.g., "daily", "wednesday-only")
Location:          _______________  (e.g., "hall laundry chute", "bathroom")
Button placement:  _______________  (describe exact spot)
```

### Derived names (auto-fill from above)

```
Device name:       button-{owner}-{task}
ESPHome file:      button-{owner}-{task}.yaml
Server dict:       DAILY_TASKS["{owner}"] (or WEDNESDAY_TASKS["{owner}"] for day-specific)
```

---

## Step 1: Create ESPHome Device Config

Create `esphome/button-{owner}-{task}.yaml`:

```yaml
substitutions:
  device_name: button-{owner}-{task}
  owner: {owner}
  task: {task}
  pi_ip: !secret pi_ip

packages:
  common: !include .base-common.yaml
  button: !include .base-button.yaml
```

**Verify:** `esphome compile button-{owner}-{task}.yaml` completes without error.

## Step 2: Flash Firmware

1. Connect Seeed XIAO ESP32-C6 via USB
2. Flash firmware: `esphome run button-{owner}-{task}.yaml --device /dev/cu.usbmodem*`
3. Watch serial logs — verify WiFi connects and boot feedback (two clicks)
4. Disconnect USB

## Step 3: Add Task to Server

Edit `server.py` on EC2:

**For daily tasks**, add to `DAILY_TASKS`:
```python
DAILY_TASKS = {
    "ryker": ["laundry", "teeth", "plates", "pills", "{task}"],
    ...
}
```

**For day-specific tasks**, add to `WEDNESDAY_TASKS` (or create a new dict for other days):
```python
WEDNESDAY_TASKS = {
    "ryker": ["{task}"],
    ...
}
```

Restart the server: `sudo systemctl restart task-tracker`

**Verify:** `curl http://34.208.73.189:8765/state` shows the new task field.

## Step 4: Update Display Lambda

Add the new task to the e-ink display rendering in `display-front-door.yaml`:

1. Add a new global boolean for the task state
2. Add parsing in the `poll_state` lambda to read the new field
3. Add a `draw_task()` call in the display lambda

**Verify:** Display shows the new task row in the correct child's column.

## Step 5: Flash Display

Recompile and OTA-flash the display:

```bash
esphome upload display-front-door.yaml --device display-front-door.local
```

## Step 6: Run Commissioning Test

Execute the full per-button commissioning checklist from `03-project-process.md`:

- [ ] Button press reaches server (check server logs)
- [ ] State updates correctly (`/state` endpoint)
- [ ] Display shows new task
- [ ] Duplicate press returns "already_done" (one long click)
- [ ] Included in daily reset (check after 3 AM or manual reset)
- [ ] Included in 9:30 AM Signal summary

## Step 7: Physical Deployment

1. Apply sticker (kid identifier + task icon)
2. Test WiFi signal at mounting location
3. Clean surface, apply Command strip
4. Mount and verify press from wall
5. Take photo for documentation

## Step 8: Commit and Document

1. Git add all changed files
2. Commit: `feat(button): add {owner} {task} button`
3. Update hardware inventory table in `01-architecture.md` if needed

---

## Quick Reference: Schedule Configuration

Tasks are scheduled by which Python dict they belong to in `server.py`:

**Daily tasks:** Add to `DAILY_TASKS` dict — applies every day.

**Wednesday only:** Add to `WEDNESDAY_TASKS` dict — server checks `datetime.now(PACIFIC).weekday() == 2`. (Currently empty — no Wednesday-only tasks are configured.)

**Other day-specific tasks:** Create a new dict (e.g., `MONDAY_TASKS`) and update `tasks_for_today()` to include it.

---

## Example: Completed Template for Ryker's Laundry

```
Task name:         laundry
Task owner:        ryker
Schedule:          daily
Location:          hall laundry chute
Button placement:  wall next to chute opening, 3 feet height
```

```
Device name:       button-ryker-laundry
ESPHome file:      button-ryker-laundry.yaml
Server dict:       DAILY_TASKS["ryker"]
```
