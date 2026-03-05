# Task Template: Adding a New Task

Use this template every time you add a new task to the system. Fill out the definition, then follow the steps in order.

---

## Task Definition (fill this out first)

```
Task name:         _______________  (e.g., "laundry", "teeth", "flute")
Task owner:        _______________  (e.g., "ryker", "logan")
Schedule:          _______________  (e.g., "daily", "wednesday", "monday,friday")
Location:          _______________  (e.g., "hall laundry chute", "bathroom")
Button placement:  _______________  (describe exact spot)
Signal message:    _______________  (e.g., "✅ Ryker put laundry in the chute!")
All-done message:  _______________  (e.g., "🎉 Ryker finished all morning tasks!")
```

### Derived names (auto-fill from above)

```
Device name:       button-{owner}-{task}
Entity boolean:    input_boolean.task_{owner}_{task}
Entity datetime:   input_datetime.task_{owner}_{task}_time
Automation name:   task_button_{owner}_{task}
ESPHome file:      button-{owner}-{task}.yaml
```

---

## Step 1: Create ESPHome Device Config

Create `esphome/button-{owner}-{task}.yaml`:

```yaml
substitutions:
  device_name: button-{owner}-{task}
  friendly_name: "{Owner} {Task} Button"
  task_owner: {owner}
  task_name: {task}

packages:
  common: !include .base-common.yaml
  button: !include .base-button.yaml
```

**Verify:** ESPHome dashboard shows new device, compiles without error.

## Step 2: Flash Firmware

1. Connect Seeed XIAO ESP32-C6 via USB
2. Flash initial firmware from ESPHome dashboard
3. Disconnect USB
4. Verify device appears in ESPHome dashboard as online
5. Verify device auto-discovered in HA (Settings → Devices & Integrations)
6. Assign to correct HA Area

## Step 3: Create HA Entities

Add to `input_booleans.yaml`:

```yaml
task_{owner}_{task}:
  name: "{Owner} {Task}"
  icon: mdi:checkbox-marked-circle-outline
```

Add to `input_datetimes.yaml`:

```yaml
task_{owner}_{task}_time:
  name: "{Owner} {Task} Time"
  has_date: true
  has_time: true
```

**Action:** Restart Home Assistant to pick up new entities.

**Verify:** New entities appear in Developer Tools → States.

## Step 4: Create Button Automation

Add to `automations/task_button_automations.yaml`:

```yaml
- alias: "task_button_{owner}_{task}"
  description: "Handle {Owner} {task} button press"
  trigger:
    - platform: event
      event_type: esphome.task_button_press
      event_data:
        owner: "{owner}"
        task: "{task}"
  condition:
    - condition: state
      entity_id: input_boolean.task_{owner}_{task}
      state: "off"
    # ADD THIS BLOCK ONLY for non-daily tasks:
    # - condition: time
    #   weekday:
    #     - wed    # or whatever day(s) apply
  action:
    - service: input_boolean.turn_on
      entity_id: input_boolean.task_{owner}_{task}
    - service: input_datetime.set_datetime
      entity_id: input_datetime.task_{owner}_{task}_time
      data:
        datetime: "{{ now().strftime('%Y-%m-%d %H:%M:%S') }}"
    - service: notify.signal
      data:
        message: "{signal_message}"
```

**Action:** Reload automations in HA (Developer Tools → YAML → Reload Automations).

**Verify:** Automation appears in Settings → Automations.

## Step 5: Update Remaining-Count Sensor

Add the new task to the relevant child's template sensor:

```yaml
# In templates.yaml, update the task list:
{% set tasks = ['laundry', 'teeth', 'plates', 'pills', '{task}'] %}
```

Also add the new entity to the daily reset automation's entity list.

**Action:** Reload template entities.

## Step 6: Update Display Lambda

Add the new task to the e-ink display rendering. The display lambda references HA text sensors, so add the new task to the display payload template sensor that feeds the e-ink.

**Verify:** Display shows the new task row in the correct child's column.

## Step 7: Update Daily Reset

Add new entities to the daily reset automation:

```yaml
# In task_reset.yaml, add:
- service: input_boolean.turn_off
  entity_id: input_boolean.task_{owner}_{task}
- service: input_datetime.set_datetime
  entity_id: input_datetime.task_{owner}_{task}_time
  data:
    datetime: "1970-01-01 00:00:00"
```

**Verify:** Trigger reset manually, confirm new entities clear.

## Step 8: Run Commissioning Test

Execute the full per-button commissioning checklist from `03-project-process.md`:

- [ ] Button press event reaches HA
- [ ] State toggles correctly
- [ ] Signal notification received
- [ ] Display updates
- [ ] Duplicate press blocked
- [ ] LED feedback works
- [ ] Device sleeps after press
- [ ] Included in daily reset
- [ ] Remaining count accurate

## Step 9: Physical Deployment

1. Apply sticker (kid identifier + task icon)
2. Test WiFi signal at mounting location
3. Clean surface, apply Command strip
4. Mount and verify press from wall
5. Take photo for documentation

## Step 10: Commit and Document

1. Git add all changed files
2. Commit: `feat(button): add {owner} {task} button`
3. Update hardware inventory table in `01-architecture.md` if needed

---

## Quick Reference: Schedule Conditions

For tasks that only run on specific days, add this condition block:

**Wednesday only (instruments):**
```yaml
- condition: time
  weekday:
    - wed
```

**Weekdays only:**
```yaml
- condition: time
  weekday:
    - mon
    - tue
    - wed
    - thu
    - fri
```

**Specific days:**
```yaml
- condition: time
  weekday:
    - mon
    - thu
```

---

## Example: Completed Template for Ryker's Laundry

```
Task name:         laundry
Task owner:        ryker
Schedule:          daily
Location:          hall laundry chute
Button placement:  wall next to chute opening, 3 feet height
Signal message:    ✅ Ryker put laundry in the chute!
All-done message:  🎉 Ryker finished all morning tasks!
```

```
Device name:       button-ryker-laundry
Entity boolean:    input_boolean.task_ryker_laundry
Entity datetime:   input_datetime.task_ryker_laundry_time
Automation name:   task_button_ryker_laundry
ESPHome file:      button-ryker-laundry.yaml
```
