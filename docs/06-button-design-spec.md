# Button Unit Design Specification

Last updated: 2026-02-26

## Design Philosophy

Each button is a standalone wall-mounted unit placed at the location where a task is completed (toothbrush button in the bathroom, dishes button by the sink, etc.). The button press itself should be the reward — a big satisfying palm-slap with an audible confirmation sound that makes boring routines feel like an event.

## Form Factor

### Plunger / Hit Target
- **Diameter**: ~55mm (full palm slap, not finger poke)
- **Shape**: Dome or mushroom cap — convex top surface that invites hitting
- **Travel**: 3-5mm of vertical plunger movement before bottoming out on tact switch
- **Spring-back**: Printed living hinge or captive flexure arms return plunger to resting position after press
- **Surface**: Per-task icon embossed or recessed into top face (see Visual Identity below)
- **Feel**: Solid *thonk* at bottom of travel, immediate snap-back

### Enclosure / Base
- **Shape**: Round or rounded-square base that matches plunger aesthetic
- **Diameter/width**: ~65-70mm (provides rim around plunger)
- **Depth**: ~20-25mm (houses all electronics)
- **Wall mount**: Flat back with Command strip recess or keyhole slot
- **USB-C access**: Port opening on bottom edge for charging/flashing (gravity keeps dust out)
- **Sound**: Open slot or grille for buzzer audio to escape enclosure

### Internal Layout (top to bottom)
```
[Plunger cap — 55mm dome, 3-5mm travel]
        ↓ (presses down on)
[Tact switch — 6×6×5mm, mounted on internal post]
[Buzzer — 12mm passive piezo, mounted to side wall]
[XIAO ESP32-C6 — 21×17.8mm, USB-C port aligned to enclosure opening]
[LiPo battery — 5×20×35mm, below or beside XIAO]
```

## Mechanical Design

### Plunger Mechanism
The plunger is a separate printed piece that moves vertically inside the base. It does NOT click on its own — all tactile feedback comes from the real tact switch at the bottom of travel.

**Travel amplification**: The tact switch has only ~0.25mm of its own travel. The plunger adds 3-5mm of free travel before contact, creating anticipation, then the switch click provides the payoff at the bottom.

**Return mechanism options** (choose during prototyping):
1. **Living hinge arms** (simplest): 2-4 thin PLA/PETG flexure arms connecting plunger to base, pre-loaded to push plunger up. Risk: fatigue over thousands of cycles.
2. **Captive silicone o-ring**: Plunger slides on a central post, compressed o-ring provides return force. More durable, slightly more complex assembly.
3. **Printed leaf springs**: Angled tabs that flex and return. Good middle ground.

**Plunger guides**: Central post or rail system prevents wobble and keeps press straight regardless of where on the dome the kid's hand lands.

### Tact Switch Mounting
- Switch sits on a raised printed post at the bottom of the plunger cavity
- Post height calibrated so switch actuates at the bottom of plunger travel
- Two wires (GPIO + GND) route from switch down to XIAO

### Durability
- Target: 10,000+ presses minimum (roughly 3+ years of daily use)
- PETG preferred over PLA for the plunger and return mechanism (better fatigue resistance)
- PLA acceptable for the base enclosure

## Audio Feedback

### Hardware
- Passive piezo buzzer (~12mm), 2 pins soldered to XIAO GPIO + GND
- Mounted inside enclosure with sound slot/grille in wall for audio escape

### Behavior (configured in ESPHome)
- **On press**: Immediate confirmation tone (short beep or custom sound)
- **Possible enhancements** (implement after MVP):
  - Different tone per task (brush teeth = high sparkle, take out trash = low bonk)
  - Ascending pitch as kid completes more tasks in the morning
  - Victory jingle when all tasks complete
  - Sad trombone if pressed after deadline (just kidding... maybe)

### ESPHome Config Pattern

> **LEDC/rtttl does NOT work** on ESP32-C6 with esp-idf framework (outputs 0V). Use plain GPIO toggle instead — produces audible clicks on the passive buzzer.

```yaml
output:
  - platform: gpio
    pin: GPIO2    # D2 on XIAO ESP32-C6
    id: buzzer_out

# Feedback via GPIO toggle patterns (on/off with delays):
# - Two clicks = success
# - One long click = already done
# - Three quick clicks = outside window / error
```

## Visual Identity

### Per-Task Icons
Each button has an icon embossed or recessed into the plunger face so kids (and adults) can instantly identify the task. Icons designed in OpenSCAD as 2D profiles extruded into the dome surface.

Candidate icons (finalize with kids):
| Task | Icon Idea |
|------|-----------|
| Brush teeth | Toothbrush or tooth |
| Get dressed | T-shirt or hanger |
| Make bed | Bed or pillow |
| Put away dishes | Plate + fork |
| Dirty clothes in hamper | Laundry basket |
| Backpack ready | Backpack |
| Wednesday: Take out trash | Trash can |
| Wednesday: Extra chore TBD | TBD |

### Color Coding
Since buttons are placed at task locations (not grouped by kid), and both kids do the same tasks, there are two approaches:

**Option A: Shared buttons** — one button per task location, either kid can press it, system tracks who via HA logic (e.g., alternating presses, or a "who are you" toggle). Fewer buttons, simpler install.

**Option B: Paired buttons** — two buttons per task location, one per kid, different colors. More buttons (18 instead of 9), but zero ambiguity. Color per kid (e.g., Ryker = blue, Logan = green).

**Recommendation**: Start with Option B (paired). It's more hardware but eliminates all "whose turn" confusion. 18 buttons = 18 XIAO boards... except we only have 9. So either:
- Option A with shared buttons (9 boards, need identification mechanism)
- Option B with 9 boards covering one kid, expand later
- Revisit architecture

> **DECISION NEEDED**: Shared vs paired buttons. This affects board count and enclosure design.

## Mounting

### Location Strategy
Buttons mounted as close to task completion point as possible:
- Bathroom wall (brush teeth)
- Near laundry hamper/chute (dirty clothes)
- Near kitchen sink (dishes)
- Bedroom wall (make bed, get dressed)
- Near front door (backpack)
- Near trash/recycling (Wednesday tasks)

### Attachment
- **Primary**: Command strips (3M damage-free, removable, re-positionable)
- **Backup**: Small screws into wall if Command strips don't hold
- Flat back surface with recessed area for Command strip adhesive
- Button should be at kid-reachable height (~36-42" from floor depending on kid)

## Charging

- USB-C port accessible on bottom edge of enclosure
- Plug in any USB-C cable to charge (XIAO onboard charger handles LiPo)
- Charging frequency: estimated every few months (15µA deep sleep + brief wake per press)
- No indicator LED needed — XIAO has onboard charge LED visible through enclosure gap or translucent section

## GPIO Allocation (XIAO ESP32-C6)

| GPIO | XIAO Pin | Function |
|------|----------|----------|
| GPIO1 | D1 | Tact switch input (internal pull-up, active LOW) |
| GPIO2 | D2 | Passive buzzer output (plain GPIO toggle) |
| GPIO15 | (onboard) | Status LED (active low) |
| BAT+ | pad near D5 | LiPo positive |
| BAT- | pad near D8 | LiPo negative |
| USB-C | — | Charging + flashing |

> **Pin mapping**: D0=GPIO0, D1=GPIO1, D2=GPIO2, D3=GPIO21, D4=GPIO22, D5=GPIO23. GPIO3 is RF switch power (board-internal, do NOT use).

## Prototype Plan

1. **Mechanical prototype first**: Print plunger + base without electronics. Test travel feel, spring-back, palm-slap satisfaction.
2. **Electronics test**: Solder one complete unit (XIAO + battery + switch + buzzer). Confirm ESPHome config, deep sleep wake, buzzer tones.
3. **Integrated prototype**: Combine mechanical + electronics in one unit. Wall-mount test.
4. **Iterate**: Refine based on kid feedback before building all 9.

## Open Questions

- [ ] Shared vs paired buttons (see Visual Identity section)
- [ ] Specific plunger return mechanism (living hinge vs o-ring vs leaf spring) — decide during prototyping
- [ ] Icon designs — involve kids in choosing
- [x] ~~Exact GPIO pin assignments for switch and buzzer~~ — resolved: D1/GPIO1 (switch), D2/GPIO2 (buzzer)
- [ ] PETG color filament availability for kid-specific colors
