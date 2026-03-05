# Project Process

## Development Phases

### Phase 1: Infrastructure (do once)

1. **Set up ESPHome environment** in Home Assistant
2. **Create base YAML files** (`.base-common.yaml`, `.base-button.yaml`, `.base-display.yaml`)
3. **Create `secrets.yaml`** with WiFi credentials, API keys, Signal numbers
4. **Deploy Signal REST API** Docker container and register phone number
5. **Configure HA Signal integration** in `configuration.yaml`
6. **Create HA entity files** (`input_booleans.yaml`, `input_datetimes.yaml`)
7. **Create HA template sensors** (remaining task counts per child)
8. **Create daily reset automation** (3 AM clear all states)
9. **Create display refresh automation** (trigger on any task state change)
10. **Set up Git repo** with initial commit of all config files

### Phase 2: First Button (prove the pattern)

Build ONE complete task end-to-end before replicating. Suggested: **Ryker laundry button**.

1. Flash ESPHome to one Seeed XIAO ESP32-C6
2. Verify it appears in HA
3. Create the button press automation in HA
4. Verify state toggles in HA
5. Verify Signal notification fires
6. Wire up display to show single task status
7. Test daily reset clears state
8. Test duplicate press protection

**Do not proceed to Phase 3 until this single button works completely.**

### Phase 3: Fleet Deployment (replicate the pattern)

For each remaining button:
1. Copy per-device YAML, change substitutions
2. Flash ESPHome firmware
3. Verify HA auto-discovers device
4. Create HA entities (input_boolean + input_datetime)
5. Create HA button press automation
6. Test button → state → display → Signal chain
7. Apply sticker, mount with Command strip

### Phase 4: Polish

1. Finalize display layout (both columns, all tasks)
2. Add "all tasks complete" celebration notification
3. Add Wednesday instrument logic
4. Test full day cycle: morning tasks → display updates → reset overnight
5. Document any deviations from best practices

## Development Workflow (per-session)

### Before starting work

1. Pull latest from Git
2. Check HA logs for any overnight errors
3. Verify Signal API container is running: `docker ps | grep signal`

### Making changes

1. **ESPHome changes:** Edit YAML → Validate in ESPHome dashboard → Install OTA
2. **HA automation changes:** Edit YAML → Reload automations (Developer Tools → YAML → Reload) → Test
3. **HA entity changes:** Edit YAML → Restart HA (entity changes require restart)

### After making changes

1. Test the specific change manually (press button, check state, check display, check Signal)
2. Commit to Git with descriptive message
3. Note any issues in project log

## Testing Checklist

### Per-button commissioning test

Run this for every new button before mounting:

- [ ] ESPHome firmware compiles without errors
- [ ] Device appears in ESPHome dashboard as online
- [ ] Device appears in HA integrations
- [ ] Button press event appears in HA Developer Tools → Events
- [ ] `input_boolean.task_{owner}_{task}` toggles to `on`
- [ ] `input_datetime.task_{owner}_{task}_time` records current time
- [ ] Signal notification received in household group
- [ ] E-ink display updates with checkmark
- [ ] Second button press does NOT re-trigger (duplicate protection)
- [ ] LED flashes green on successful press
- [ ] Device returns to deep sleep after press (check ESPHome logs)
- [ ] Battery voltage reporting works (if applicable)

### System-level tests (run after fleet changes)

- [ ] Daily reset clears all states at 3 AM (test by temporarily changing to current time)
- [ ] Display shows correct day's tasks (including/excluding Wednesday instruments)
- [ ] Remaining count sensor accurate for both children
- [ ] "All complete" notification fires when last task is done
- [ ] Display handles all tasks checked off (visual verification)
- [ ] Display handles zero tasks checked off (morning state)

### Edge case tests

- [ ] Button press while WiFi is down → button sleeps, no crash
- [ ] Button press while HA is restarting → press may be lost, no crash
- [ ] Multiple buttons pressed simultaneously → all register correctly
- [ ] Press instrument button on non-Wednesday → no state change, appropriate feedback
- [ ] Signal API container restart → notifications resume without HA restart

## Deployment Steps (mounting a button)

1. **Label the button** with kid's sticker and task icon/text
2. **Test one more time** in the mounting location (WiFi signal check)
3. **Clean surface** with isopropyl alcohol
4. **Apply Command strip** to button back
5. **Press to wall** for 30 seconds
6. **Verify press from mounted position** — watch HA logs to confirm event
7. **Take a photo** of mounted button for documentation
8. **Update inventory** in architecture doc if placement changed

## Rollback Procedures

### Bad ESPHome firmware flash

ESPHome devices have fallback AP mode. If a bad flash prevents WiFi connection:
1. Look for `{device_name} Fallback` WiFi network
2. Connect and navigate to `192.168.4.1`
3. Flash corrected firmware via web interface

### Bad HA automation

Automations can be disabled in HA UI instantly:
1. Settings → Automations → Find automation → Toggle off
2. Fix the YAML
3. Reload automations
4. Re-enable

### Signal API issues

Signal container can be rebuilt without losing registration:
1. `docker compose down`
2. `docker compose up -d`
3. Registration data is preserved in the `signal-cli-config` volume

## Monitoring

### Daily glance checks

- ESPHome dashboard: all devices showing "Online" (display should be always-on; buttons will show offline when sleeping — this is normal)
- HA developer tools: spot-check a few `input_boolean` entities for expected state
- Signal group: confirm notifications are flowing

### Weekly maintenance

- Check button batteries if not USB-powered
- Review HA logs for recurring warnings
- Verify display is rendering cleanly (e-ink ghosting check)
- Git commit any uncommitted changes

### Monthly review

- Are kids actually using it? Talk to them.
- Any tasks need adding/removing/changing?
- Any buttons fallen off walls? (Command strip refresh)
- Update ESPHome and HA if updates available (test in sequence, not simultaneously)
