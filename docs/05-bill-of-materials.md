# Bill of Materials

Last updated: 2026-02-26

## On Hand

- 9× Seeed XIAO ESP32-C6 boards
- 1× Waveshare 7.5" e-ink raw panel (800×480, B/W)
- 1× Waveshare e-Paper ESP32 Driver Board ([B07M5CNP3B](https://www.amazon.com/dp/B07M5CNP3B))
- Bambu Lab 3D printers + filament (PLA/PETG)
- Soldering iron + solder
- USB-C cables for flashing/charging
- Command strips for wall mounting

## To Purchase

### 1. Passive Piezo Buzzers
- **Product**: Cylewet 5V 2-pin passive electromagnetic buzzer, 10-pack
- **Quantity**: 1 pack (need 9, rest are spares)
- **Price**: ~$6
- **Specs**: 2-pin, passive, ~12mm diameter, 3-5V operating range
- **Link**: Search "Cylewet 10pcs 5V passive buzzer electromagnetic beeper" on Amazon
- **Notes**: Passive (not active) — allows PWM tone control via ESPHome LEDC output. Solder one pin to GPIO, one to GND. Works at 3.3V. Enables per-task sounds, victory jingles, ascending scales as tasks complete.

### 2. LiPo Batteries — Button Units
- **Product**: Liter 3.7V 400mAh 502035 LiPo
- **Quantity**: 10 (9 units + 1 spare)
- **Price**: ~$8 each, ~$80 total
- **Dimensions**: 5mm × 20mm × 35mm
- **Connector**: JST PH 2.0mm (cut off, solder bare wires to XIAO BAT+/BAT- pads)
- **Link**: Search "Liter 502035 400mAh" on Amazon
- **Notes**: XIAO BAT- pad near D8 silkscreen, BAT+ near D5. Built-in USB-C charging on XIAO handles recharging.

### 3. LiPo Battery — E-ink Display
- **Product**: Liter 3.7V 3000mAh 105050 LiPo
- **Quantity**: 1
- **Price**: ~$10
- **Dimensions**: 9.9mm × 50mm × 48mm (fits behind 170×111mm panel)
- **Connector**: JST PH 2.0mm (cut off, solder to TP4056 battery pads)
- **Link**: [B09FL7QD88](https://www.amazon.com/dp/B09FL7QD88)
- **Notes**: Verify polarity with multimeter before connecting. Some units ship with red/black swapped on JST.

### 4. TP4056 USB-C LiPo Charger Modules
- **Product**: HiLetgo TP4056 Type-C USB 5V 1A 18650 Lithium Battery Charger Module
- **Quantity**: 3-pack
- **Price**: ~$6
- **Link**: Search "HiLetgo TP4056 Type-C 3pcs" on Amazon
- **Notes**: Get version WITH protection (DW01 chip) for overdischarge protection. Wiring: USB-C → TP4056 → battery → Waveshare 5V/GND pins. Only needed for e-ink display (XIAO boards have built-in charging).

### 5. Tactile Pushbutton Switches
- **Product**: DAOKI 6×6×5mm tactile switches, 100-pack
- **Quantity**: 1 pack (need 9, rest are spares)
- **Price**: ~$6
- **Specs**: Through-hole, 4-pin, momentary, DC12V 50mA rated
- **Link**: [B01CGMP9GY](https://www.amazon.com/dp/B01CGMP9GY)
- **Notes**: Solder two wires per switch (GPIO + GND). Mount under 3D-printed plunger cap for kid-friendly feel. 5mm button height provides good tactile feedback.

### 6. Hookup Wire
- **Product**: BNTECHGO 22 AWG Silicone Wire (red + black, 10ft each)
- **Quantity**: 1 kit
- **Price**: ~$6
- **Specs**: 22 gauge stranded tinned copper, 60 strands × 0.08mm, 1.7mm OD, silicone insulation
- **Link**: Search "BNTECHGO 22 AWG silicone red black" on Amazon
- **Notes**: Silicone insulation rated -60°C to +200°C, won't melt during soldering. Use for switch-to-GPIO and battery-to-pad connections.

### 7. Heat Shrink Tubing
- **Product**: Heat shrink tubing assortment kit (580pcs, 11 sizes)
- **Quantity**: 1 kit
- **Price**: ~$7
- **Primary sizes needed**:
  - 1/12" (2.1mm): for battery wire solder joints
  - 1/8" (3.2mm): for 22 AWG hookup wire joints
- **Link**: Search "580pcs heat shrink tubing assortment" on Amazon
- **Notes**: Critical for LiPo safety — insulate all battery solder connections.

## Cost Summary

| Category | Est. Cost |
|----------|-----------|
| Passive piezo buzzers (10-pack) | $6 |
| Button unit batteries (10×) | $80 |
| E-ink display battery (1×) | $10 |
| TP4056 charger modules (3-pack) | $6 |
| Tactile switches (100-pack) | $6 |
| Hookup wire | $6 |
| Heat shrink tubing | $7 |
| **Total** | **~$121** |

## Power Architecture

### Button Units (×9)
```
[3.7V 400mAh LiPo] → solder to XIAO BAT+/BAT- pads
                       ↕ (USB-C plugged in = charges battery via XIAO onboard charger)
[XIAO ESP32-C6] → deep sleep 15µA → months between charges
```

### E-ink Display (×1)
```
[USB-C] → [TP4056 w/ protection] → [3.7V 3000mAh LiPo] → [Waveshare 5V/GND pins]
           (charging)                (storage)               (power)
```

## 3D-Printed Components (designed in OpenSCAD, printed on Bambu Lab)

- **Button unit enclosure**: Houses XIAO + battery + tact switch + buzzer. USB-C port access for charging/flashing. Wall-mountable. Color-coded or labeled per kid.
- **Button plunger cap**: Large kid-friendly dome/palm-slap target (~55mm diameter) with 3-5mm printed travel and spring-back mechanism. Presses down on 6×6mm tact switch at bottom of travel.
- **E-ink display frame**: Mounts 7.5" panel + driver board + battery + TP4056. Wall-mountable at front door.
