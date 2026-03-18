// display-frame.scad
// Freestanding frame for Waveshare 7.5" V2 e-ink display
// with ESP32 driver board and LiPo battery enclosed behind.

// ── Display panel ───────────────────────────────────────
disp_w = 170.2;       // mm, horizontal
disp_h = 111.2;       // mm, vertical
disp_t = 1.18;        // mm, thickness
active_w = 163.2;     // mm, visible area width
active_h = 97.92;     // mm, visible area height

// ── Driver board ────────────────────────────────────────
pcb_w = 48.25;        // mm
pcb_h = 29.46;        // mm
pcb_t = 1.6;          // mm (standard PCB)

// ── Battery ─────────────────────────────────────────────
bat_w = 51.36;        // mm
bat_h = 51.36;        // mm
bat_t = 9.83;         // mm

// ── Frame parameters ────────────────────────────────────
wall = 2.0;           // mm, wall thickness
bezel = 3.5;          // mm, front bezel overlap around display
tol = 0.4;            // mm, tolerance/clearance per side
back_depth = bat_t + pcb_t + 4;  // mm, rear cavity depth (battery + board + clearance)

// ── Derived dimensions ──────────────────────────────────
// Outer shell
outer_w = disp_w + 2*tol + 2*wall;
outer_h = disp_h + 2*tol + 2*wall;
outer_d = wall + disp_t + tol + back_depth + wall;  // front wall + display + gap + cavity + back wall

// Display pocket (front, recessed into front face)
pocket_w = disp_w + 2*tol;
pocket_h = disp_h + 2*tol;
pocket_d = disp_t + tol;

// Front window (exposes active area)
win_w = active_w + 2;  // slight margin
win_h = active_h + 2;

// Ribbon cable slot — display ribbon exits bottom edge
ribbon_slot_w = 30;
ribbon_slot_h = 5;

// ── Kickstand ───────────────────────────────────────────
stand_angle = 15;     // degrees from vertical
stand_w = 40;
stand_t = 3;
stand_len = outer_h * 0.7;

// ── Main frame ──────────────────────────────────────────
module frame() {
    difference() {
        // Outer shell — rounded box
        translate([0, 0, outer_d/2])
            cube([outer_w, outer_h, outer_d], center=true);

        // Front display pocket (from front face)
        translate([0, 0, -0.01])
            translate([0, 0, wall + pocket_d/2])
                cube([pocket_w, pocket_h, pocket_d + 0.02], center=true);

        // Front window (through front wall, exposing active area)
        translate([0, 0, -0.01])
            cube([win_w, win_h, wall + 0.02 + pocket_d], center=true);

        // Rear cavity (from back, for driver board + battery)
        translate([0, 0, outer_d - wall - back_depth/2 + 0.01])
            cube([outer_w - 2*wall, outer_h - 2*wall, back_depth + 0.02], center=true);

        // Ribbon cable slot — bottom edge, connecting front pocket to rear cavity
        translate([0, -outer_h/2 + wall/2, wall + pocket_d + (outer_d - wall - pocket_d - wall)/2])
            cube([ribbon_slot_w, wall + 2, outer_d], center=true);

        // USB access hole — bottom edge, for charging
        translate([outer_w/2 - wall/2 - 15, -outer_h/2 - 0.01, outer_d - wall - 8])
            cube([12, wall + 0.02, 8]);
    }
}

// ── Back cover (snap-on or friction fit) ────────────────
module back_cover() {
    lip = 1.5;  // mm, lip that inserts into cavity

    translate([0, 0, 0]) {
        difference() {
            union() {
                // Flat cover plate
                cube([outer_w, outer_h, wall], center=true);
                // Lip to fit inside cavity
                translate([0, 0, -wall/2 - lip/2])
                    cube([outer_w - 2*wall - tol, outer_h - 2*wall - tol, lip], center=true);
            }

            // USB access hole matching frame
            translate([outer_w/2 - wall/2 - 15 - outer_w/2, -outer_h/2 + wall - outer_h/2 + outer_h/2 - 0.01, -wall/2 - lip - 0.01])
                cube([12, wall + 0.02, wall + lip + 0.02]);

            // Ventilation slots
            for (i = [-2:2]) {
                translate([i * 20, 0, 0])
                    cube([10, 40, wall + 0.02], center=true);
            }
        }
    }
}

// ── Kickstand ───────────────────────────────────────────
module kickstand() {
    difference() {
        union() {
            // Main strut
            cube([stand_w, stand_t, stand_len], center=true);
            // Hinge tab (top)
            translate([0, 0, stand_len/2])
                cylinder(h=stand_t, r=stand_w/6, center=true, $fn=30);
        }
        // Hinge hole
        translate([0, 0, stand_len/2])
            cylinder(h=stand_t + 0.1, r=1.6, center=true, $fn=20);
    }
}

// ── Assembly ────────────────────────────────────────────
// Uncomment the part you want to export:

// Main frame
frame();

// Back cover — offset for printing
translate([outer_w + 10, 0, wall/2])
    back_cover();

// Kickstand — offset for printing
translate([0, outer_h + 10, stand_t/2])
    kickstand();
