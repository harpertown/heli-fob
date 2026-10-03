"""Chopper Run: a tiny side-scrolling Pyxel landing demo."""

import math

import pyxel


WIDTH, HEIGHT = 256, 160
GROUND_Y = 139
WORLD_LENGTH = 1800
START_PAD_X = 42
GOAL_PAD_X = WORLD_LENGTH - 90
GRAVITY = 0.07
MAX_ROTOR_THRUST = 0.13
MAX_DISK_TILT = 0.48
PAD_SURFACE_Y = GROUND_Y - 2
GEAR_OFFSET = 7
HIGH_ALTITUDE_Y = HEIGHT // 2
HIGH_ALTITUDE_FUEL_MULTIPLIER = 7.0
TREE_OBSTACLES = (
    (220, 48),
    (390, 64),
    (560, 38),
    (750, 72),
    (930, 48),
    (1120, 66),
    (1310, 42),
    (1470, 75),
)


class ChopperGame:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="CHOPPER RUN", fps=30)
        self.reset()
        pyxel.run(self.update, self.draw)

    def reset(self):
        self.x, self.y = float(START_PAD_X), float(PAD_SURFACE_Y - GEAR_OFFSET)
        self.vx, self.vy = 0.0, 0.0
        self.pitch = 0.0
        self.pitch_rate = 0.0
        self.collective = 0.0
        self.rotor_lift = 0.0
        self.disk_tilt = 0.0
        self.camera = 0.0
        self.fuel = 100.0
        self.state = "ready"
        self.rotor = 0

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        if pyxel.btnp(pyxel.KEY_R):
            self.reset()
        if self.state == "crashed":
            self.update_crash()
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.reset()
            return
        if self.state in ("ready", "landed"):
            if pyxel.btnp(pyxel.KEY_SPACE):
                # Start every new flight with enough collective to clear the pad.
                self.reset()
                self.state = "flying"
                self.collective = 0.60
                self.rotor_lift = 0.60
            return

        self.rotor += 1
        raise_throttle = (
            pyxel.btn(pyxel.KEY_SPACE)
            or pyxel.btn(pyxel.KEY_UP)
            or pyxel.btn(pyxel.KEY_W)
        )
        lower_throttle = pyxel.btn(pyxel.KEY_DOWN) or pyxel.btn(pyxel.KEY_S)
        if raise_throttle:
            self.collective = min(1.0, self.collective + 0.012)
        elif lower_throttle:
            self.collective = max(0.0, self.collective - 0.018)

        # Collective stays where the pilot leaves it; rotor lift spools toward
        # that setting rather than changing in the same frame.
        self.rotor_lift += (self.collective - self.rotor_lift) * 0.025

        pitch_input = 0
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
            pitch_input -= 1
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
            pitch_input += 1
        # Stability augmentation: cyclic asks for a disc angle, and the disc
        # servo moves toward it instead of reacting instantly to every frame.
        desired_disk_tilt = pitch_input * MAX_DISK_TILT
        disc_response = 0.08 if pitch_input else 0.06
        self.disk_tilt += (desired_disk_tilt - self.disk_tilt) * disc_response

        engine_power = self.rotor_lift if self.fuel > 0 else 0.0
        # A tilted, powered rotor pulls the body around with angular inertia.
        # The rate damper settles rotation promptly after cyclic is released.
        self.pitch_rate += self.disk_tilt * engine_power * 0.005
        self.pitch_rate *= 0.985 if pitch_input else 0.94
        self.pitch_rate = max(-0.04, min(0.04, self.pitch_rate))
        self.pitch += self.pitch_rate

        # Thrust follows the rotor disc, not the fuselage. As the disc tips
        # forward, its upward component falls and forward acceleration rises.
        rotor_thrust = engine_power * MAX_ROTOR_THRUST
        thrust_angle = self.pitch + self.disk_tilt
        self.vx += rotor_thrust * math.sin(thrust_angle)
        self.vy += GRAVITY - rotor_thrust * math.cos(thrust_angle)
        # The fuselage also influences the flight path. A nose-down attitude
        # produces a gentle dive; a nose-up attitude adds a gentle climb. The
        # aerodynamic part strengthens as forward speed builds.
        attitude_force = 0.012 + min(abs(self.vx), 2.0) * 0.008
        self.vy += math.sin(self.pitch) * attitude_force
        height_above_ground = max(0.0, GROUND_Y - GEAR_OFFSET - self.y)
        if height_above_ground < 28:
            ground_effect = rotor_thrust * (1.0 - height_above_ground / 28) * 0.16
            self.vy -= ground_effect * max(0.0, math.cos(thrust_angle))
        # Vertical-speed damping creates a controllable hover. Horizontal drag
        # is stronger near hover and eases as the helicopter gains speed.
        self.vx *= 0.975 if abs(self.vx) < 0.9 else 0.993
        self.vy *= 0.97
        self.vx = max(-2.2, min(2.6, self.vx))
        self.vy = max(-1.1, min(1.3, self.vy))
        fuel_multiplier = HIGH_ALTITUDE_FUEL_MULTIPLIER if self.y < HIGH_ALTITUDE_Y else 1.0
        self.fuel = max(0.0, self.fuel - engine_power * 0.0018 * fuel_multiplier)
        self.x += self.vx
        self.y += self.vy
        self.x = max(8, min(WORLD_LENGTH - 20, self.x))
        self.camera = max(0, min(WORLD_LENGTH - WIDTH, self.x - 78))

        tree_top = self.tree_collision_top()
        if tree_top is not None:
            self.start_crash(tree_top)
            return

        # A gentle touchdown on either marked pad is safe; anywhere else is a crash.
        on_pad = any(abs(self.x - pad_x) < 24 for pad_x in (START_PAD_X, GOAL_PAD_X))
        surface_y = PAD_SURFACE_Y if on_pad else GROUND_Y
        if self.y >= surface_y - GEAR_OFFSET:
            upright = math.cos(self.pitch) > 0.92 and abs(self.disk_tilt) < 0.2
            if on_pad and upright and abs(self.vy) < 0.8 and abs(self.vx) < 0.8:
                self.y = surface_y - GEAR_OFFSET
                self.vx = 0.0
                self.vy = 0.0
                self.pitch_rate = 0.0
                self.state = "landed"
            else:
                self.start_crash(surface_y)

    def tree_collision_top(self):
        for tree_x, tree_height in TREE_OBSTACLES:
            tree_top = GROUND_Y - tree_height
            if abs(self.x - tree_x) < 11 and self.y + GEAR_OFFSET >= tree_top:
                return tree_top
        return None

    def start_crash(self, impact_surface_y):
        self.y = impact_surface_y - GEAR_OFFSET
        self.collective = 0.0
        impact_direction = 1 if self.vx >= 0 else -1
        self.pitch_rate += impact_direction * (0.012 + abs(self.vy) * 0.018)
        self.state = "crashed"

    def update_crash(self):
        """Simulate a tumbling wreck after an impact."""
        self.rotor += 1
        self.collective = 0.0
        self.rotor_lift *= 0.94
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        self.pitch += self.pitch_rate
        self.vx *= 0.992
        self.pitch_rate *= 0.996
        self.x = max(8, min(WORLD_LENGTH - 20, self.x))
        self.camera = max(0, min(WORLD_LENGTH - WIDTH, self.x - 78))

        on_pad = any(abs(self.x - pad_x) < 24 for pad_x in (START_PAD_X, GOAL_PAD_X))
        surface_y = PAD_SURFACE_Y if on_pad else GROUND_Y
        if self.y >= surface_y - GEAR_OFFSET:
            self.y = surface_y - GEAR_OFFSET
            if self.vy > 0.12:
                impact_direction = 1 if self.vx >= 0 else -1
                self.vy *= -0.24
                self.vx *= 0.72
                self.pitch_rate += impact_direction * min(0.05, 0.012 + self.vy * -0.025)
            else:
                self.vy = 0.0
                self.vx *= 0.86
                self.pitch_rate *= 0.93

    def draw(self):
        pyxel.cls(1)
        # Distant sky bands and moving clouds
        pyxel.rect(0, 0, WIDTH, 77, 12)
        pyxel.rect(0, 77, WIDTH, 16, 6)
        for i in range(7):
            cx = (i * 73 - int(self.camera * 0.22)) % (WIDTH + 45) - 22
            cy = 22 + (i * 17) % 40
            pyxel.rect(cx, cy, 18, 4, 7)
            pyxel.rect(cx + 5, cy - 3, 10, 4, 7)

        # Scrolling hills and ground
        for i in range(9):
            hx = i * 42 - int(self.camera * 0.48) % 42
            pyxel.circ(hx, 118 + (i % 3) * 4, 20, 3)
        pyxel.rect(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y, 11)
        pyxel.line(0, GROUND_Y, WIDTH, GROUND_Y, 10)
        for wx in range(0, WORLD_LENGTH, 36):
            sx = int(wx - self.camera)
            if -4 <= sx < WIDTH:
                pyxel.line(sx, GROUND_Y + 5, sx - 5, GROUND_Y + 9, 3)

        # Tree obstacles create a climb-and-descend route to the destination.
        for tree_x, tree_height in TREE_OBSTACLES:
            sx = int(tree_x - self.camera)
            if -16 <= sx <= WIDTH + 16:
                tree_top = GROUND_Y - tree_height
                pyxel.rect(sx - 2, tree_top + 12, 5, tree_height - 12, 4)
                pyxel.circ(sx, tree_top + 9, 12, 3)
                pyxel.circ(sx - 8, tree_top + 16, 9, 3)
                pyxel.circ(sx + 8, tree_top + 16, 9, 3)
                pyxel.circ(sx, tree_top + 15, 7, 11)

        # Start and destination landing pads
        for pad_x, label in ((START_PAD_X, "A"), (GOAL_PAD_X, "H")):
            pad_screen = int(pad_x - self.camera)
            if -40 < pad_screen < WIDTH + 40:
                pyxel.rect(pad_screen - 19, GROUND_Y - 2, 38, 3, 10)
                pyxel.line(pad_screen - 12, GROUND_Y - 5, pad_screen + 12, GROUND_Y - 5, 7)
                # A Pyxel glyph is four pixels wide, so offset it by two to
                # align its centre with the centre of the pad.
                pyxel.text(pad_screen - 2, GROUND_Y - 14, label, 7)

        hx, hy = int(self.x - self.camera), int(self.y)
        self.draw_helicopter(hx, hy)
        self.draw_hud()
        if self.state in ("ready", "landed"):
            title = "CHOPPER RUN" if self.state == "ready" else "SAFE LANDING!"
            width = len(title) * 4
            pyxel.rect(47, 57, 162, 40, 0)
            pyxel.rectb(47, 57, 162, 40, 7)
            pyxel.text((WIDTH - width) // 2, 65, title, 10)
            hint = "SPACE TO TAKE OFF" if self.state == "ready" else "SPACE TO FLY AGAIN"
            pyxel.text((WIDTH - len(hint) * 4) // 2, 80, hint, 7)
        elif self.state == "crashed":
            pyxel.rect(74, 30, 108, 10, 0)
            pyxel.text(78, 33, "CRASH - SPACE RESTART", 8)

    def draw_helicopter(self, x, y):
        # A single filled fuselage that rotates with pitch.
        def point(local_x, local_y):
            cos_pitch = math.cos(self.pitch)
            sin_pitch = math.sin(self.pitch)
            return (
                int(x + local_x * cos_pitch - local_y * sin_pitch),
                int(y + local_x * sin_pitch + local_y * cos_pitch),
            )

        tail_top, nose_top = point(-10, -4), point(5, -5)
        nose, nose_bottom = point(11, 0), point(5, 5)
        tail_bottom = point(-10, 4)
        pyxel.tri(*tail_top, *nose_top, *nose, 8)
        pyxel.tri(*tail_top, *nose, *tail_bottom, 8)
        pyxel.tri(*tail_bottom, *nose, *nose_bottom, 8)

        # Cockpit window, tail boom, and skids are each drawn once.
        window_top, window_bottom = point(4, -3), point(8, 1)
        pyxel.line(*window_top, *window_bottom, 10)
        boom_start, boom_end = point(-10, 0), point(-17, 0)
        pyxel.line(*boom_start, *boom_end, 8)
        skid_left, skid_right = point(-6, 7), point(7, 7)
        pyxel.line(*skid_left, *skid_right, 0)
        pyxel.line(*point(-5, 4), *skid_left, 0)
        pyxel.line(*point(4, 4), *skid_right, 0)

        mast_base, rotor_hub = point(0, -4), point(0, -9)
        rotor_angle = self.pitch + self.disk_tilt
        rotor_left = (
            int(rotor_hub[0] - 12 * math.cos(rotor_angle)),
            int(rotor_hub[1] - 12 * math.sin(rotor_angle)),
        )
        rotor_right = (
            int(rotor_hub[0] + 12 * math.cos(rotor_angle)),
            int(rotor_hub[1] + 12 * math.sin(rotor_angle)),
        )
        pyxel.line(*mast_base, *rotor_hub, 0)
        pyxel.line(*rotor_left, *rotor_right, 7)
        span = 5 if (self.rotor // 3) % 2 else 12
        tail_rotor = point(-18, 0)
        pyxel.line(tail_rotor[0], tail_rotor[1] - span // 2, tail_rotor[0], tail_rotor[1] + span // 2, 7)

    def draw_hud(self):
        # Short, fixed labels keep both collective values readable.
        pyxel.rect(5, 5, 246, 22, 0)
        pyxel.text(10, 9, "FUEL", 7)
        pyxel.rect(31, 9, 52, 6, 5)
        fuel_color = 11 if self.fuel > 25 else 8
        pyxel.rect(32, 10, int(50 * self.fuel / 100), 4, fuel_color)
        pyxel.text(94, 9, "THR", 7)
        pyxel.rect(110, 9, 52, 6, 5)
        pyxel.rect(111, 10, int(50 * self.collective), 4, 9)
        pyxel.text(94, 18, "ACT", 6)
        pyxel.rect(110, 18, 52, 6, 5)
        pyxel.rect(111, 19, int(50 * self.rotor_lift), 4, 11)
        distance = max(0, int(GOAL_PAD_X - self.x))
        pyxel.text(178, 9, "DST:%04d" % distance, 10)
        pyxel.text(178, 18, "SPD:%+.1f" % self.vx, 6)


ChopperGame()
