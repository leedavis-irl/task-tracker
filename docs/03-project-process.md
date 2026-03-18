# Project Process

## Development Phases

### Phase 1: Infrastructure (do once)

1. **Set up ESPHome environment** on local machine (`pip install esphome`)
2. **Create base YAML files** (`.base-common.yaml`, `.base-button.yaml`, `.base-display.yaml`)
3. **Create `secrets.yaml`** with WiFi credentials, API keys, server IP
4. **Deploy Flask server** to EC2 with systemd service
5. **Deploy Signal relay** to EC2 with signal-cli
6. **Set up Git repo** with initial commit of all config files

### Phase 2: First Button (prove the pattern)

Build ONE complete task end-to-end before replicating. Suggested: **Ryker teeth button**.

1. Flash ESPHome to one Seeed XIAO ESP32-C6 via USB
2. Verify WiFi connects and button boots cleanly (two clicks)
3. Press button, verify HTTP POST reaches EC2 server
4. Verify server records the task (`/state` shows `true`)
5. Verify display picks up the change on next poll
6. Test daily reset clears state
7. Test duplicate press protection (one long click)

**Do not proceed to Phase 3 until this single button works completely.**

### Phase 3: Fleet Deployment (replicate the pattern)

For each remaining button:
1. Copy per-device YAML, change substitutions
2. Flash ESPHome firmware via USB
3. Verify WiFi connection and boot feedback
4. Test button → server → display chain
5. Apply sticker, mount with Command strip

### Phase 4: Polish

1. Finalize display layout (both columns, all tasks)
2. Test full day cycle: morning tasks → display updates → 9:30 AM summary → reset overnight
3. Verify day-specific tasks (if any) appear/hide correctly
4. Document any deviations from best practices

## Development Workflow (per-session)

### Before starting work

1. Pull latest from Git
2. Verify EC2 server is running: `curl http://34.208.73.189:8765/health`
3. Check server logs if needed: `ssh ubuntu@34.208.73.189 "sudo journalctl -u task-tracker --since '1 hour ago'"`

### Making changes

1. **ESPHome changes:** Edit YAML → compile (`esphome compile`) → flash OTA or USB (`esphome upload`)
2. **Server changes:** Edit `server.py` → deploy to EC2 → restart service (`sudo systemctl restart task-tracker`)
3. **Task definition changes:** Edit `DAILY_TASKS` (or `WEDNESDAY_TASKS` for day-specific tasks) in `server.py` → restart server → update display lambda if new task row needed

### After making changes

1. Test the specific change manually (press button, check state, check display)
2. Commit to Git with descriptive message
3. Note any issues in project log

## Testing Checklist

### Per-button commissioning test

Run this for every new button before mounting:

- [ ] ESPHome firmware compiles without errors
- [ ] Device connects to WiFi (check serial logs)
- [ ] Boot feedback: two clicks heard
- [ ] Button press: HTTP POST reaches EC2 server (check server logs)
- [ ] Server responds `"ok"` and task state updates
- [ ] Display shows updated state on next poll
- [ ] Second button press returns `"already_done"` (one long click)
- [ ] Device returns to deep sleep after press (when deep sleep is re-enabled)

### System-level tests (run after fleet changes)

- [ ] Daily reset clears all states at 3 AM (test by temporarily changing reset time)
- [ ] Display shows correct day's tasks (including any day-specific tasks if configured)
- [ ] 9:30 AM Signal summary sends correctly
- [ ] Display handles all tasks checked off (celebration screen)
- [ ] Display handles zero tasks checked off (morning state)

### Edge case tests

- [ ] Button press while WiFi is down → button sleeps, no crash
- [ ] Button press while server is down → three clicks (error), no crash
- [ ] Multiple buttons pressed simultaneously → all register correctly
- [ ] Press day-specific task button on wrong day → server returns `"not_today"`, three clicks
- [ ] Press outside 6–9:30 AM window → server returns `"outside_window"`, three clicks

## Deployment Steps (mounting a button)

1. **Label the button** with kid's sticker and task icon/text
2. **Test one more time** in the mounting location (WiFi signal check)
3. **Clean surface** with isopropyl alcohol
4. **Apply Command strip** to button back
5. **Press to wall** for 30 seconds
6. **Verify press from mounted position** — check EC2 server logs to confirm POST received
7. **Take a photo** of mounted button for documentation
8. **Update inventory** in architecture doc if placement changed

## Rollback Procedures

### Bad ESPHome firmware flash

ESPHome devices have fallback AP mode. If a bad flash prevents WiFi connection:
1. Look for `{device_name} Fallback` WiFi network
2. Connect and navigate to `192.168.4.1`
3. Flash corrected firmware via web interface

### Server issues

```bash
# SSH into EC2
ssh -i ~/.ssh/the-pem-key.pem ubuntu@34.208.73.189

# Check status
sudo systemctl status task-tracker

# View logs
sudo journalctl -u task-tracker -f

# Restart
sudo systemctl restart task-tracker
```

### Signal relay issues

```bash
# On EC2:
sudo systemctl status signal-relay
sudo systemctl restart signal-relay
```

## Monitoring

### Daily glance checks

- Server health: `curl http://34.208.73.189:8765/health`
- Current state: `curl http://34.208.73.189:8765/state | python3 -m json.tool`
- Signal group: confirm 9:30 AM summary arrived

### Weekly maintenance

- Check button batteries if not USB-powered
- Review EC2 server logs for recurring warnings
- Verify display is rendering cleanly (e-ink ghosting check)
- Git commit any uncommitted changes

### Monthly review

- Are kids actually using it? Talk to them.
- Any tasks need adding/removing/changing?
- Any buttons fallen off walls? (Command strip refresh)
- Update ESPHome if updates available
