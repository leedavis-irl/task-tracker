# Button Build Guide
### AM Routine Tracker — Avalon Household

**Print this doc. Build one button at a time. Don't skip steps.**

---

## Before You Start

### Tools needed
- Soldering iron + solder
- Wire strippers
- Multimeter
- Heat gun (or lighter) for heat shrink
- USB-C cable (for flashing)
- Laptop with ESPHome dashboard open
- Tweezers
- Isopropyl alcohol + cotton swab (flux cleanup)

### Parts per button unit
| Part | Notes |
|------|-------|
| 1× Seeed XIAO ESP32-C6 | The brains |
| 1× 3.7V 400mAh LiPo (Liter 502035) | 5×20×35mm |
| 1× 6×6×5mm tactile pushbutton switch | 4-pin through-hole |
| 1× Passive piezo buzzer (~12mm, 2-pin) | NOT active — must be passive |
| ~15cm red 22 AWG silicone wire | Switch wire |
| ~15cm black 22 AWG silicone wire | Switch GND wire |
| ~10cm red wire | Buzzer wire |
| ~10cm black wire | Buzzer GND wire |
| 2× small heat shrink pieces | Battery solder joints |
| 1× 3D-printed enclosure + plunger | Print before assembly |

---

## GPIO Pin Assignments

These are fixed. Use them. Don't improvise.

| Function | XIAO Pin Label | GPIO # |
|----------|---------------|--------|
| Tact switch input | D1 | GPIO3 |
| Passive buzzer PWM | D2 | GPIO4 |
| Battery positive | BAT+ pad | near D5 silkscreen |
| Battery negative | BAT- pad | near D8 silkscreen |
| Built-in LED | (onboard) | GPIO15 |

---

## Step 1 — Inspect the XIAO board

- [ ] No bent pins, no visible damage
- [ ] USB-C port is clean
- [ ] Find the **BAT+** pad (small gold pad near D5 label on back of board)
- [ ] Find the **BAT-** pad (small gold pad near D8 label on back of board)

> These pads are small. Use a magnifier if needed. Soldering to the wrong pad will damage the board.

---

## Step 2 — Prep the LiPo battery

⚠️ **SAFETY FIRST.** LiPo batteries can catch fire if shorted or punctured. Work carefully.

1. The battery has a JST connector — **cut it off** leaving ~5cm of wire attached to the battery
2. Strip ~4mm of insulation from both wires
3. Tin both wire ends with solder
4. Slide heat shrink tubing onto each wire **before** soldering to the board

---

## Step 3 — Solder battery to XIAO

1. Tin the BAT+ and BAT- pads on the back of the XIAO
2. **Verify polarity with your multimeter** before soldering:
   - Red wire = positive = BAT+ pad
   - Black wire = negative = BAT- pad
   - Some LiPo units ship with reversed JST colors — measure, don't assume
3. Solder red wire to BAT+ pad
4. Solder black wire to BAT- pad
5. Slide heat shrink over each joint and shrink with heat gun
6. Tug gently on each wire — joints should not move

> ✅ Check: Plug in USB-C. The orange charge LED on the XIAO should light up.

---

## Step 4 — Prep the tact switch

The 6×6mm tact switch has 4 pins arranged in a square. Pins are connected in pairs — one pair per side.

1. Cut two lengths of 22 AWG wire, ~15cm each (one red, one black)
2. Strip 4mm from both ends of each wire
3. Solder one wire to **any pin on one side** of the switch
4. Solder the other wire to **any pin on the opposite side**
5. (The other two pins on each side are internally connected — ignore them)

> The switch is momentary (spring-loaded). Pressing it connects the two wires. Releasing opens them.

---

## Step 5 — Solder switch to XIAO

1. Solder the **red wire** from the switch to the **D1** pin on the XIAO
2. Solder the **black wire** from the switch to any **GND** pin on the XIAO

> ✅ Check: With a multimeter in continuity mode, probe D1 and GND. Press the switch — you should hear a beep. Release — silence.

---

## Step 6 — Prep the buzzer

The passive buzzer has 2 pins. One may be marked `+` or have a longer lead.

1. Cut two short lengths of wire, ~10cm each
2. Solder red wire to the `+` pin (or longer lead)
3. Solder black wire to the other pin

---

## Step 7 — Solder buzzer to XIAO

1. Solder **red wire** from buzzer to **D2** pin on the XIAO
2. Solder **black wire** from buzzer to any **GND** pin on the XIAO

---

## Step 8 — Visual inspection before flashing

Before connecting USB or powering on:

- [ ] No solder bridges between adjacent pins
- [ ] Battery polarity correct (double-check)
- [ ] All joints look shiny and solid (no cold joints)
- [ ] No bare wire touching anything it shouldn't
- [ ] Clean flux residue with isopropyl + cotton swab

---

## Step 9 — Flash ESPHome firmware

1. Open ESPHome dashboard on your laptop
2. Copy the correct YAML file from the repo into your ESPHome config dir:
   - e.g., `button-ryker-laundry.yaml`
3. Make sure `secrets.yaml` is filled in with your WiFi credentials and API key
4. Click **Install** → **Plug into this computer**
5. Connect XIAO via USB-C
6. Wait for compile + flash (~2-3 minutes)
7. Watch the ESPHome logs — you should see:
   - WiFi connected
   - API connected
   - `Button press handler registered`
8. Disconnect USB-C

> If the flash fails: hold the BOOT button on the XIAO while connecting USB-C to force bootloader mode.

---

## Step 10 — First press test (before enclosure)

With the XIAO still loose (not yet in enclosure):

1. Watch ESPHome logs on your laptop
2. **Press the tact switch**
3. You should see in logs:
   - `Button pressed`
   - `HTTP POST sent to Pi server`
   - `Response: {"status": "ok"}` (Pi server must be running)
4. The onboard LED should briefly light green
5. The buzzer should make a short beep
6. The XIAO should go back to deep sleep within 10 seconds

> ⚠️ If you see `{"status": "outside_window"}` — that's fine, the server is working. Just means it's not between 6–9:30 AM.

> ⚠️ If you see `{"status": "already_done"}` — the LED will flash red. Press again tomorrow or ask Iji to reset the state.

---

## Step 11 — Assemble in enclosure

*(Do this after enclosure is 3D printed and tested mechanically)*

1. Place XIAO in its slot, USB-C port aligned with enclosure opening
2. Route battery alongside or below XIAO
3. Mount tact switch under the plunger post — confirm switch actuates at bottom of plunger travel
4. Mount buzzer against inside wall, sound hole aligned with enclosure grille
5. Close enclosure (screws or snap-fit depending on print design)
6. **Press the plunger** — confirm tact switch clicks at bottom of travel

---

## Step 12 — Label and mount

1. Apply kid sticker + task icon to plunger face
2. Test WiFi signal at intended mounting location (hold button there, check ESPHome logs)
3. Clean wall surface with isopropyl alcohol
4. Peel Command strip backing, press to back of enclosure
5. Press button to wall for 30 seconds
6. **Do one final press test from mounted position** — watch logs to confirm

---

## Per-Button Checklist

Run this for every button before calling it done.

```
Button: _______________________   Date: __________

[ ] Board inspected, no damage
[ ] Battery polarity verified with multimeter
[ ] Battery soldered to BAT+/BAT-
[ ] Battery solder joints heat-shrunk
[ ] Tact switch soldered to D1 + GND
[ ] Buzzer soldered to D2 + GND
[ ] Continuity check passed (D1–GND with switch press)
[ ] ESPHome firmware flashed successfully
[ ] WiFi connects in logs
[ ] Button press event reaches Pi server
[ ] Server returns {"status": "ok"} or expected response
[ ] LED flashes green on success
[ ] Buzzer beeps on success
[ ] XIAO enters deep sleep after press
[ ] Enclosure assembled, plunger travel feels good
[ ] Sticker applied (correct kid + task)
[ ] Mounted at correct location and height
[ ] Final press test from wall
```

---

## Build Order (recommended)

Build in this order. Test each one fully before moving on.

1. **Ryker — Teeth** *(bathroom, easy location, good first test)*
2. **Logan — Teeth** *(same room, do both while you have the iron hot)*
3. **Ryker — Plates**
4. **Logan — Plates**
5. **Ryker — Laundry**
6. **Logan — Laundry**
7. **Ryker — Pills**
8. **Ryker — Flute** *(Wednesday only)*
9. **Logan — Trumpet** *(Wednesday only)*

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| XIAO won't boot | Bad battery joint / short | Check polarity, inspect solder |
| Won't connect to WiFi | Wrong SSID/password | Check secrets.yaml |
| Flash fails | Not in bootloader mode | Hold BOOT + connect USB |
| No HTTP POST in logs | Pi server not running | Start Pi server, check IP |
| LED flashes red | Task already done today | Expected — or ask Iji to reset |
| No buzzer sound | Wrong pin / active buzzer | Confirm D2, confirm passive buzzer |
| Button not detected | Cold solder joint on switch | Reflow D1 or GND joint |
| Deep sleep too fast | run_duration too short | Check ESPHome config |

---

## Display Build

See separate guide once enclosure design is finalized. The display (Waveshare 7.5" + ESP32 driver board) does not use battery power — it's wall-mounted with USB-C. Assembly is simpler: just mount panel to driver board and flash firmware.

---

*Last updated: 2026-03-05*
