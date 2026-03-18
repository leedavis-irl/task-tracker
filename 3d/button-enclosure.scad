// button-enclosure.scad
// Enclosure for task-tracker button: XIAO ESP32-C6 + battery + buzzer + tact switch
// Flat back for surface adhesion. Large press cap over 6mm tact switch.
// Two pieces: base (open-top box) and lid (with integrated button cap).

// ── Measured component dimensions ───────────────────────
// XIAO ESP32-C6
xiao_l = 21.0;        // mm, length
xiao_w = 17.5;        // mm, width
xiao_h = 4.53;        // mm, total height (PCB + components)

// USB-C port (on xiao_w edge, centered)
usbc_w = 8.88;        // mm
usbc_h = 3.16;        // mm
usbc_protrude = 1.4;  // mm, sticks out from board edge

// Tact switch
sw_size = 6.0;        // mm, square body footprint
sw_pins = 7.5;        // mm, square channel size (pins + solder diagonal is 10.21mm)
sw_h = 1.66;          // mm, button press height

// Buzzer
buz_dia = 11.65;      // mm
buz_h = 7.77;         // mm (not counting prongs/solder)

// Battery
bat_w = 51.36;        // mm
bat_l = 51.36;        // mm
bat_h = 9.83;         // mm

// ── Enclosure parameters ────────────────────────────────
wall = 2.0;           // mm
tol = 0.3;            // mm, clearance
corner_r = 3.0;       // mm, rounded corners

// ── Layout ──────────────────────────────────────────────
// All components sit side by side on the floor.
// Pillar for tact switch rises from floor next to battery.
// XIAO board and buzzer also beside battery.
//
// Internal cavity sizing:
// Width: battery + pillar diameter + clearance gap
pillar_dia = sw_pins + 8;                 // 15.5mm — channel + walls
cav_w = bat_w + 2*tol + pillar_dia + 4;  // battery + gap + pillar + margin
cav_l = bat_l + 2*tol;                    // battery length + clearance
cav_h = max(bat_h, buz_h) + tol          // tallest floor component
      + sw_h + tol;                        // switch on top + clearance

// Outer dimensions
outer_w = cav_w + 2*wall;
outer_l = cav_l + 2*wall;
outer_h = cav_h + wall;   // base has floor (flat back), open top

// Pillar X offset — centered in the space beside the battery
pillar_x = (bat_w/2 + 2*tol + pillar_dia/2) / 2;

// Button cap
cap_dia = 30.0;       // mm, large press surface
cap_travel = 1.0;     // mm, how far it can depress
cap_post_dia = 5.5;   // mm, post that contacts tact switch (just under 6mm)

// Lid
lid_h = wall + cap_travel + 1.0;  // lid thickness + room for button travel

// ── Helper: rounded box ─────────────────────────────────
module rounded_box(w, l, h, r) {
    hull() {
        for (x = [-w/2+r, w/2-r])
            for (y = [-l/2+r, l/2-r])
                translate([x, y, 0])
                    cylinder(r=r, h=h, $fn=40);
    }
}

// ── Base ────────────────────────────────────────────────
module base() {
    difference() {
        // Outer shell
        rounded_box(outer_w, outer_l, outer_h, corner_r);

        // Inner cavity (open top)
        translate([0, 0, wall])
            rounded_box(cav_w, cav_l, cav_h + 0.01, corner_r - wall);

        // USB-C access hole — on -X edge (opposite side from pillar)
        // Board sits on the floor, USB port near the bottom
        usb_z = wall + 1;  // slightly above floor
        translate([-outer_w/2 - 0.01, -(usbc_w + 2*tol)/2, usb_z])
            cube([wall + 0.02, usbc_w + 2*tol, usbc_h + 2*tol]);

        // Buzzer sound holes — on -Y wall, buzzer sits on the floor
        for (i = [-2:2]) {
            translate([i * 4, -outer_l/2 - 0.01, wall + buz_h/2])
                rotate([-90, 0, 0])
                    cylinder(d=2.5, h=wall + 0.02, $fn=20);
        }
    }

    // Snap clip ledges — small ridges on inner walls near the top
    // The lid's flexible tabs catch under these when pressed down
    snap_w = 8;        // width of each ledge
    snap_depth = 0.8;  // how far ledge protrudes inward
    snap_h = 1.0;      // height of ledge
    snap_z = outer_h - snap_h - 0.5;  // just below top edge
    for (y = [-1, 1]) {
        translate([-(snap_w)/2, y * (cav_l/2 - snap_depth/2), snap_z])
            cube([snap_w, snap_depth, snap_h]);
    }

    // Switch mount — two rectangular towers, 6mm apart
    // Switch body sits between them, glued on both flat sides
    // Pins/wires extend freely out the open sides
    pillar_h = cav_h - sw_h;  // everything except the switch itself
    tower_w = 4;              // mm, thickness of each tower
    tower_l = sw_size + 4;    // mm, length (wider than switch for glue surface)
    gap = sw_size;            // mm, exactly 6mm between towers

    for (side = [-1, 1]) {
        translate([pillar_x + side * (gap/2 + tower_w/2) - tower_w/2, -tower_l/2, wall])
            cube([tower_w, tower_l, pillar_h]);
    }
}

// ── Lid ─────────────────────────────────────────────────
// The lid hole is sized for the cap stem to pass through, but NOT the flange.
// Assembly: insert button cap from underside of lid (flange catches on inside),
// then place lid on base. Cap is trapped — can't go up (flange) or down (base).
cap_stem_dia = cap_dia;           // stem passes through
flange_dia = cap_dia + 3;        // flange is wider, caught inside

// Snap clip dimensions (must match base ledges)
snap_w = 8;
snap_depth = 0.8;
snap_h = 1.0;
lip_len = 3.0;  // how far the lid lip extends into the base

module lid() {
    difference() {
        union() {
            // Lid plate
            rounded_box(outer_w, outer_l, wall, corner_r);

            // Friction-fit lip (inserts into base)
            translate([0, 0, -lip_len])
                rounded_box(cav_w - tol, cav_l - tol, lip_len, corner_r - wall);

            // Snap tabs — flexible arms on the lip that catch under base ledges
            // Angled tip helps them flex inward during insertion, then spring out
            for (y = [-1, 1]) {
                translate([-(snap_w)/2, y * (cav_l/2 - tol/2 - wall) + (y > 0 ? -snap_depth : 0), -lip_len])
                    cube([snap_w, snap_depth, lip_len]);
                // Catch nub at bottom of each tab
                translate([-(snap_w)/2, y * (cav_l/2 - tol/2 - wall) + (y > 0 ? -snap_depth : 0), -lip_len])
                    cube([snap_w, snap_depth + 0.5, snap_h]);
            }
        }

        // Through-hole for cap stem (offset to match pillar position)
        translate([pillar_x, 0, -lip_len - 0.01])
            cylinder(d=cap_stem_dia + 2*tol, h=wall + lip_len + 0.02, $fn=60);

        // Flange recess on underside of lid
        // Deep enough for flange thickness (1mm) + travel (1mm)
        translate([pillar_x, 0, -lip_len - 0.01])
            cylinder(d=flange_dia + 2*tol, h=1.0 + cap_travel + 0.01, $fn=60);
    }
}

// ── Button cap ──────────────────────────────────────────
// Assembled from underside of lid:
//   [post] → [flange] → [stem through lid] → [press surface on top]
module button_cap() {
    // Press surface — visible on top of lid
    cylinder(d=cap_stem_dia, h=2.0, $fn=60);

    // Flange — sits in recess under lid, prevents cap from coming out the top
    translate([0, 0, -1.0])
        cylinder(d=flange_dia, h=1.0, $fn=60);

    // Post underneath flange — reaches down to contact tact switch
    translate([0, 0, -1.0 - cap_travel - 3])
        cylinder(d=cap_post_dia, h=cap_travel + 3, $fn=30);
}

// ── Assembly view ───────────────────────────────────────
// Uncomment the section you want to export as STL.

// -- Full assembly --
base();

translate([outer_w + 20, 0, wall])
    rotate([180, 0, 0])
        lid();

translate([0, outer_l + 20, 2.0])
    rotate([180, 0, 0])
        button_cap();
