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
- Laptop with terminal open
- Tweezers
- Isopropyl alcohol + cotton swab (flux cleanup)

### Parts per button unit
| Part | Notes |
|------|-------|
| 1x Seeed XIAO ESP32-C6 | The brains |
| 1x 3.7V 400mAh LiPo (Liter 502035) | 5x20x35mm |
| 1x 6x6x5mm tactile pushbutton switch | 4-pin through-hole |
| 1x Passive piezo buzzer (~12mm, 2-pin) | NOT active — must be passive |
| ~15cm red 22 AWG silicone wire | Switch wire |
| ~15cm black 22 AWG silicone wire | Switch GND wire |
| ~10cm red wire | Buzzer wire |
| ~10cm black wire | Buzzer GND wire |
| 2x small heat shrink pieces | Battery solder joints |
| 1x 3D-printed enclosure + plunger | Print before assembly |

---

## GPIO Pin Assignments

These are fixed. Use them. Don't improvise.

| Function | XIAO Pin Label | GPIO # |
|----------|---------------|--------|
| Tact switch input | D1 | GPIO1 |
| Passive buzzer output | D2 | GPIO2 |
| Battery positive | BAT+ pad | near D5 silkscreen |
| Battery negative | BAT- pad | near D8 silkscreen |
| Built-in status LED | (onboard) | GPIO15 (active low) |

> **WARNING — Pin numbering**: The XIAO ESP32-C6 pin labels (D0, D1, D2...) do NOT match GPIO numbers above D2. The mapping is: D0=GPIO0, D1=GPIO1, D2=GPIO2, D3=GPIO21, D4=GPIO22, D5=GPIO23. Do NOT use GPIO3 — it is the RF switch power pin (board-internal).

> **Buzzer note**: LEDC PWM and rtttl do NOT work on ESP32-C6 with the esp-idf framework (outputs 0V). The firmware uses plain GPIO toggle to produce audible clicks on the passive buzzer. This is a known platform limitation.

---

## Step 1 — Inspect the XIAO board

- [ ] No bent pins, no visible damage
- [ ] USB-C port is clean
- [ ] Find the **BAT+** pad (small gold pad near D5 label on back of board)
- [ ] Find the **BAT-** pad (small gold pad near D8 label on back of board)

> These pads are small. Use a magnifier if needed. Soldering to the wrong pad will damage the board.

---

## Step 2 — Prep the LiPo battery

**SAFETY FIRST.** LiPo batteries can catch fire if shorted or punctured. The two bare wire ends must never touch each other.

1. The battery has a JST connector — **cut it off** leaving ~5cm of wire attached to the battery
2. **Immediately** slide a piece of heat shrink over each wire end and shrink it down — leave only ~4mm of wire exposed at the tip. Do this before anything else. Both ends insulated before you proceed.
3. Strip the 4mm tips
4. Tin both wire tips with solder

---

## Step 3 — Solder battery to XIAO

1. Tin the BAT+ and BAT- pads on the back of the XIAO
2. **Verify polarity with your multimeter** before soldering:
   - Red wire = positive = BAT+ pad
   - Black wire = negative = BAT- pad
   - Some LiPo units ship with reversed JST colors — measure, don't assume
3. Solder red wire to BAT+ pad
4. Solder black wire to BAT- pad
5. Check that no wire strands are poking sideways toward adjacent pads
6. Tug gently on each wire — joints should not move

> Note: there's no joint to heat-shrink on the board side — the solder pad itself is the joint. The heat shrink you applied in Step 2 protects the battery-end wires from shorting against each other.

> **TEST**: Plug in USB-C. The orange charge LED on the XIAO should light up. If it doesn't, STOP — check polarity and solder joints before continuing.

---

## Step 4 — Flash firmware BEFORE soldering more components

Flash now while USB-C access is easy and no other wires are in the way.

1. Connect the XIAO to your laptop via USB-C
2. Verify the board is detected:
   ```
   ls /dev/cu.usbmodem*
   ```
3. Create the device YAML (copy from `button-ryker-teeth.yaml` and change substitutions):
   ```yaml
   substitutions:
     device_name: button-KIDNAME-TASK
     owner: KIDNAME
     task: TASK
     pi_ip: !secret pi_ip

   packages:
     common: !include .base-common.yaml
     button: !include .base-button.yaml
   ```
4. Make sure `secrets.yaml` has your WiFi credentials, API key, OTA password, and `pi_ip`
5. Clean and flash:
   ```
   cd ~/task-tracker/esphome
   esphome clean button-KIDNAME-TASK.yaml
   esphome run button-KIDNAME-TASK.yaml --device /dev/cu.usbmodem*
   ```
6. Watch the logs — you should see:
   - WiFi connected
   - API connected
   - Two clicks from the status LED toggling (boot feedback)
7. Disconnect USB-C

> If flashing fails: hold the BOOT button on the XIAO while connecting USB-C to force bootloader mode. Some USB-C cables are charge-only — use a data cable.

> **TEST**: After flashing, the onboard LED (GPIO15) should blink briefly on boot. If you hear two faint clicks from the board area, that's the boot success feedback — the buzzer will be louder once connected.

---

## Step 5 — Prep and solder the tact switch

The 6x6mm tact switch has 4 pins arranged in a square. Pins are connected in pairs — one pair per side.

1. Cut two lengths of 22 AWG wire, ~15cm each (one red, one black)
2. Strip 4mm from both ends of each wire
3. Tin the wire tips
4. Solder one wire to **any pin on one side** of the switch
5. Solder the other wire to **any pin on the opposite side**
6. Solder the **red wire** from the switch to the **D1** pin on the XIAO
7. Solder the **black wire** from the switch to any **GND** pin on the XIAO

> You can twist bare wire around the tact switch pins before soldering — this gives a stronger mechanical connection. Don't over-twist (2-3 wraps max).

> **TEST**: Power on the XIAO (USB or battery). Open ESPHome logs:
> ```
> esphome logs button-KIDNAME-TASK.yaml --device 192.168.x.x
> ```
> Press the switch — you should see `Binary sensor 'Task Button' changed to ON` in the logs. If the server is running, you'll also see the HTTP response.

---

## Step 6 — Prep and solder the buzzer

The passive buzzer has 2 pins. One may be marked `+` or have a longer lead.

1. Cut two short lengths of wire, ~10cm each
2. Tin the wire tips
3. Solder red wire to the `+` pin (or longer lead)
4. Solder black wire to the other pin

> **TEST the buzzer before soldering to the XIAO**: Touch the buzzer wires to a 3V3 source (the 3V3 pin on the XIAO while powered) and GND. You should hear a click when you touch and release. If no click, the buzzer is dead — swap it.

5. Solder **red wire** from buzzer to **D2** pin on the XIAO
6. Solder **black wire** from buzzer to any **GND** pin on the XIAO (can share the switch's GND pin)

> **TEST**: Power on the XIAO. On boot, you should hear two short clicks (the success feedback pattern). If the server is running, press the button — you'll hear the response pattern:
> - **Two clicks** = success ("ok")
> - **One long click** = already done today
> - **Three quick clicks** = outside window / error

---

## Step 7 — Visual inspection before enclosure

Before closing up:

- [ ] No solder bridges between adjacent pins
- [ ] Battery polarity correct (double-check)
- [ ] All joints look shiny and solid (no cold joints)
- [ ] No bare wire touching anything it shouldn't
- [ ] Clean flux residue with isopropyl + cotton swab
- [ ] Tug-test all solder joints — nothing should move

---

## Step 8 — Full integration test

With all components soldered and the XIAO powered:

1. Watch ESPHome logs on your laptop (via USB or OTA):
   ```
   esphome logs button-KIDNAME-TASK.yaml --device 192.168.x.x
   ```
2. **Boot test**: Power cycle the XIAO — should hear two clicks (success pattern)
3. **Button test**: Press the tact switch:
   - Logs should show: button press detected, HTTP POST sent, response received
   - Buzzer should click with the appropriate pattern
4. **Server response test** (if between 6-9:30 AM): Should get "ok" response and two clicks
5. **Voltage check**: Measure battery voltage across BAT+/BAT- — should be 3.5-4.2V

> If you see `outside_window` — that's correct, it just means it's not between 6-9:30 AM. Three clicks confirms the full chain is working.

---

## Step 9 — Assemble in enclosure

*(Do this after enclosure is 3D printed and tested mechanically)*

1. Place XIAO in its slot, USB-C port aligned with enclosure opening
2. Route battery alongside or below XIAO — keep wires away from the plunger path
3. Mount tact switch under the plunger post — confirm switch actuates at bottom of plunger travel
4. Mount buzzer against inside wall, sound hole aligned with enclosure grille
5. Close enclosure (screws or snap-fit depending on print design)
6. **Press the plunger** — confirm tact switch clicks at bottom of travel

---

## Step 10 — Label and mount

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
[ ] Charge LED lights when USB-C plugged in
[ ] Firmware flashed via USB-C
[ ] WiFi connects (check logs)
[ ] Tact switch soldered to D1 + GND
[ ] Button press appears in logs
[ ] Buzzer tested standalone (click on 3V3 touch)
[ ] Buzzer soldered to D2 + GND
[ ] Boot feedback: two clicks heard
[ ] Button press: buzzer clicks with response pattern
[ ] HTTP POST reaches server (check server logs)
[ ] All solder joints tug-tested
[ ] No solder bridges or stray wires
[ ] Enclosure assembled, plunger travel feels good
[ ] Sticker applied (correct kid + task)
[ ] Mounted at correct location and height
[ ] Final press test from wall
```

---

## Creating a New Button YAML

For each new button, create a file like `button-KIDNAME-TASK.yaml`:

```yaml
substitutions:
  device_name: button-KIDNAME-TASK
  owner: KIDNAME
  task: TASK
  pi_ip: !secret pi_ip

packages:
  common: !include .base-common.yaml
  button: !include .base-button.yaml
```

That's it. All the logic lives in `.base-button.yaml` and `.base-common.yaml`. The only things that change per button are `device_name`, `owner`, and `task`.

### secrets.yaml

Must contain (example values — use your own):

```yaml
wifi_ssid: "YourNetwork"
wifi_password: "YourPassword"
api_encryption_key: "base64-encoded-key"
ota_password: "your-ota-password"
pi_ip: "192.168.1.232"
```

---

## OTA Updates (after first flash)

Once a button is flashed and on WiFi, you can update it over the air:

```
esphome run button-KIDNAME-TASK.yaml --device 192.168.x.x
```

Find the device IP in your router's DHCP table or ESPHome logs.

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
| Won't connect to WiFi | Wrong SSID/password in secrets.yaml | Check `secrets.yaml` |
| Flash fails via USB | Bad USB cable (charge-only) | Try a different USB-C data cable |
| No HTTP POST in logs | Server not running | Start server, check `pi_ip` in secrets.yaml |
| Two clicks on press | Server returned "ok" | Working correctly |
| One long click on press | Task already done today | Expected — resets at 3 AM |
| Three clicks on press | Outside 6-9:30 AM window or error | Check time or server logs |
| No buzzer sound | Bad solder on D2 or GND | Reflow joints; test buzzer standalone with 3V3 |
| Button not detected | Cold joint on D1 or GND | Reflow D1/GND; check logs for binary_sensor |
| Boot hangs / crashes | Empty pi_ip or bad config | Verify secrets.yaml has all keys |
| `esphome run` uses cached build | Stale build cache | Run `esphome clean` first |

### Known platform limitations
- **LEDC/rtttl PWM does not work** on ESP32-C6 with esp-idf framework. Buzzer uses plain GPIO toggle (clicks, not tones). This is a known issue — do not attempt to use `platform: ledc` or `rtttl:` components.
- **Deep sleep** is currently disabled due to ESP-IDF 5.1.5 sleep crash. Will be re-enabled in a future firmware update.
- **GPIO3** is the RF switch power pin on the XIAO ESP32-C6. Never use it for user I/O.

---

## Display Build

See separate guide once enclosure design is finalized. The display (Waveshare 7.5" + ESP32 driver board) does not use battery power — it's wall-mounted with USB-C. Assembly is simpler: just mount panel to driver board and flash firmware.

---

*Last updated: 2026-03-08*
