"""Chopper Run: a tiny side-scrolling Pyxel landing demo."""

import math

import pyxel

try:
    from js import window
except ImportError:
    window = None


WIDTH, HEIGHT = 256, 160
GROUND_Y = 152
WORLD_LENGTH = 1800
START_PAD_X = 42
GOAL_PAD_X = WORLD_LENGTH - 90
TUTORIAL_GOAL_X = 230
GRAVITY = 0.07
MAX_ROTOR_THRUST = 0.13
MAX_DISK_TILT = 0.48
CHOPPER_SCALE = 2 / 3
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
TUTORIAL_OBSTACLES = ((150, 28), (205, 42))


class ChopperGame:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="CHOPPER RUN", fps=30)
        self.reset()
        pyxel.run(self.update, self.draw)

    def reset(self):
        self.level = "mission1"
        self.reset_flight()
        self.mission_unlocked = True
        self.mission_two_unlocked = True
        self.mission_three_unlocked = True
        self.mission_four_unlocked = True
        self.mission_five_unlocked = True
        self.mission_six_unlocked = True
        self.selected_mission = 1

    def reset_flight(self):
        self.x, self.y = float(START_PAD_X), float(PAD_SURFACE_Y - GEAR_OFFSET)
        self.vx, self.vy = 0.0, 0.0
        self.pitch = 0.0
        self.pitch_rate = 0.0
        self.collective = 0.0
        self.rotor_lift = 0.0
        self.disk_tilt = 0.0
        self.camera = 0.0
        self.fuel = 100.0
        self.state = "intro"
        self.rotor = 0
        self.wind = 0.0
        self.high_wind = 0.0
        self.fuel_burn_rate = 0.0
        self.rescue_progress = 0

    def start_level(self, level):
        self.level = level
        self.reset_flight()
        self.state = "ready"

    def level_goal_x(self):
        return TUTORIAL_GOAL_X if self.level == "tutorial" else GOAL_PAD_X

    def level_obstacles(self):
        if self.level == "tutorial":
            return TUTORIAL_OBSTACLES
        if self.level in ("mission1", "mission2", "mission3"):
            return TREE_OBSTACLES
        return ()

    def is_sea_mission(self):
        return self.level == "mission4"

    def is_motorway_mission(self):
        return self.level == "mission5"

    def is_rescue_mission(self):
        return self.level == "mission6"

    def spotlight_bounds(self, y, hx, spotlight_top_y):
        delta = y - spotlight_top_y
        if delta < 0:
            return None
        return (
            hx + delta / 1.75,
            hx + delta / 0.625,
        )

    def draw_lit_circle(self, cx, cy, radius, color, hx, spotlight_top_y):
        for y in range(cy - radius, cy + radius + 1):
            half_width = int(math.sqrt(max(0, radius * radius - (y - cy) ** 2)))
            bounds = self.spotlight_bounds(y, hx, spotlight_top_y)
            if bounds is None:
                continue
            left = max(cx - half_width, int(bounds[0]))
            right = min(cx + half_width, int(bounds[1]))
            if right >= left:
                pyxel.rect(left, y, right - left + 1, 1, color)

    def wind_force(self):
        if self.level not in ("mission2", "mission4", "mission6"):
            return 0.0
        progress = (self.x - START_PAD_X) / (GOAL_PAD_X - START_PAD_X)
        progress = max(0.0, min(1.0, progress))
        intensity = 0.8 + 3.2 * progress
        if self.level == "mission6":
            intensity = 1.2
        gust = 0.65 * math.sin(self.rotor / 48) + 0.35 * math.sin(self.rotor / 19)
        return intensity * gust

    def vertical_wind_force(self):
        if self.level not in ("mission2", "mission4"):
            return 0.0
        progress = (self.x - START_PAD_X) / (GOAL_PAD_X - START_PAD_X)
        progress = max(0.0, min(1.0, progress))
        intensity = 0.8 + 3.2 * progress
        gust = 0.65 * math.sin(self.rotor / 37) + 0.35 * math.sin(self.rotor / 16)
        return intensity * gust

    def high_wind_force(self):
        if self.y > HEIGHT * 0.15:
            return 0.0
        gust = math.sin(self.rotor / 11) + 0.55 * math.sin(self.rotor / 29)
        return 4.5 * gust

    def rescue_target_x(self):
        return GOAL_PAD_X - 120

    def moving_car_x(self, index):
        return 180 + index * 220 + math.sin(self.rotor / (18 + index * 3)) * 28

    def motorway_powerline_x(self, index):
        return 220 + index * 230

    def motorway_powerline_y(self, index):
        return 82 + (index % 2) * 8

    def sea_start_x(self):
        return START_PAD_X + 180

    def sea_wave_top(self, world_x):
        progress = (world_x - self.sea_start_x()) / (GOAL_PAD_X - self.sea_start_x())
        progress = max(0.0, min(1.0, progress))
        amplitude = 4.0 + 108.0 * progress
        phase = (self.rotor / 20 + world_x / 72) % math.tau
        shoulder = math.exp(-((phase - 1.55) / 1.05) ** 2)
        curling_face = math.exp(-((phase - 2.25) / 0.42) ** 2)
        wave_height = amplitude * (0.12 + 0.70 * shoulder + 0.42 * curling_face)
        return GROUND_Y - int(wave_height)

    def hover_throttle_required(self):
        fuel_efficiency = 0.75 + 0.25 * (self.fuel / 100)
        return min(1.0, GRAVITY / (MAX_ROTOR_THRUST * fuel_efficiency))

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        if pyxel.btnp(pyxel.KEY_R):
            self.start_level(self.level)
        if self.state == "intro":
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.state = "mission_select"
            return
        if self.state == "mission_select":
            if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.KEY_DOWN):
                direction = -1 if pyxel.btnp(pyxel.KEY_UP) else 1
                self.selected_mission = (self.selected_mission + direction) % 7
            if pyxel.btnp(pyxel.KEY_SPACE):
                levels = (
                    "tutorial",
                    "mission1",
                    "mission2",
                    "mission3",
                    "mission4",
                    "mission5",
                    "mission6",
                )
                self.start_level(levels[self.selected_mission])
            return
        if self.state == "tutorial_complete":
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.state = "mission_select"
                self.selected_mission = 1
            return
        if self.state == "mission_complete":
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.state = "mission_select"
                if self.level == "mission1":
                    self.selected_mission = 2
            return
        if self.state == "crashed":
            self.update_crash()
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.start_level(self.level)
            return
        if self.state in ("ready", "landed"):
            if pyxel.btnp(pyxel.KEY_SPACE):
                # Start every new flight with enough collective to clear the pad.
                self.reset_flight()
                self.state = "flying"
                self.collective = 0.60
                self.rotor_lift = 0.60
            return

        self.rotor += 1
        raise_throttle = pyxel.btn(pyxel.KEY_UP)
        lower_throttle = pyxel.btn(pyxel.KEY_DOWN)
        if raise_throttle:
            self.collective = min(1.0, self.collective + 0.012)
        elif lower_throttle:
            self.collective = max(0.0, self.collective - 0.018)

        # Collective stays where the pilot leaves it; rotor lift spools toward
        # that setting rather than changing in the same frame.
        self.rotor_lift += (self.collective - self.rotor_lift) * 0.025

        pitch_input = 0
        if pyxel.btn(pyxel.KEY_LEFT):
            pitch_input -= 1
        if pyxel.btn(pyxel.KEY_RIGHT):
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
        fuel_efficiency = 0.75 + 0.25 * (self.fuel / 100)
        rotor_thrust = engine_power * MAX_ROTOR_THRUST * fuel_efficiency
        thrust_angle = self.pitch + self.disk_tilt
        self.vx += rotor_thrust * math.sin(thrust_angle)
        self.vy += GRAVITY - rotor_thrust * math.cos(thrust_angle)
        self.wind = self.wind_force()
        self.high_wind = self.high_wind_force()
        self.wind += self.high_wind
        self.vx += self.wind * (0.02 if self.high_wind else 0.012)
        self.vy += self.vertical_wind_force() * 0.012
        if self.is_motorway_mission() and self.y > GROUND_Y - 28:
            if any(abs(self.x - self.moving_car_x(i)) < 14 for i in range(7)):
                self.start_crash(GROUND_Y)
                return
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
        high_throttle_ratio = max(0.0, (engine_power - 0.95) / 0.05)
        high_throttle_multiplier = 1.0 + 19.0 * high_throttle_ratio**2
        high_wind_multiplier = 7.0 if self.y <= HEIGHT * 0.15 else 1.0
        fuel_burn = (
            engine_power
            * 0.018
            * fuel_multiplier
            * high_throttle_multiplier
            * high_wind_multiplier
        )
        self.fuel_burn_rate = fuel_burn * 30
        self.fuel = max(0.0, self.fuel - fuel_burn)
        self.x += self.vx
        self.y += self.vy
        self.x = max(8, min(WORLD_LENGTH - 20, self.x))
        self.camera = max(0, min(WORLD_LENGTH - WIDTH, self.x - 78))

        tree_top = self.tree_collision_top()
        if tree_top is not None:
            self.start_crash(tree_top)
            return
        if self.is_sea_mission() and self.sea_start_x() <= self.x < GOAL_PAD_X - 40:
            wave_step = 4
            wave_index = round((self.x - self.sea_start_x()) / wave_step)
            wave_x = self.sea_start_x() + wave_index * wave_step
            if abs(self.x - wave_x) <= wave_step and self.y + GEAR_OFFSET >= self.sea_wave_top(wave_x):
                self.start_crash(self.sea_wave_top(wave_x))
                return

        if self.is_rescue_mission():
            steady = (
                abs(self.x - self.rescue_target_x()) < 14
                and 48 < self.y < 78
                and abs(self.vx) < 0.45
                and abs(self.vy) < 0.45
            )
            self.rescue_progress = self.rescue_progress + 1 if steady else 0
            if self.rescue_progress >= 180:
                self.state = "mission_complete"
                return

        # A gentle touchdown on either marked pad is safe; anywhere else is a crash.
        on_pad = any(abs(self.x - pad_x) < 24 for pad_x in (START_PAD_X, self.level_goal_x()))
        if self.is_rescue_mission():
            on_pad = False
        surface_y = PAD_SURFACE_Y if on_pad else GROUND_Y
        if self.y >= surface_y - GEAR_OFFSET:
            upright = math.cos(self.pitch) > 0.92 and abs(self.disk_tilt) < 0.2
            if on_pad and upright and abs(self.vy) < 0.8 and abs(self.vx) < 0.8:
                self.y = surface_y - GEAR_OFFSET
                self.vx = 0.0
                self.vy = 0.0
                self.pitch_rate = 0.0
                if self.level == "tutorial":
                    self.mission_unlocked = True
                    if window:
                        window.localStorage.setItem("chopper-run-tutorial-complete", "1")
                    self.state = "tutorial_complete"
                else:
                    if self.level == "mission1":
                        self.mission_two_unlocked = True
                        if window:
                            window.localStorage.setItem("chopper-run-mission1-complete", "1")
                    self.state = "mission_complete"
            else:
                self.start_crash(surface_y)

    def tree_collision_top(self):
        if self.is_motorway_mission():
            for i in range(6):
                pole_x = self.motorway_powerline_x(i)
                wire_y = self.motorway_powerline_y(i)
                if abs(self.x - pole_x) < 7 and self.y + GEAR_OFFSET >= wire_y:
                    return wire_y
                if pole_x - 4 <= self.x <= pole_x + 64 and abs(self.y + GEAR_OFFSET - wire_y) < 5:
                    return wire_y
        for tree_x, tree_height in self.level_obstacles():
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

        on_pad = any(abs(self.x - pad_x) < 24 for pad_x in (START_PAD_X, self.level_goal_x()))
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
        night = self.level == "mission3"
        if night:
            pyxel.rect(0, 0, WIDTH, 77, 0)
            pyxel.rect(0, 77, WIDTH, 16, 1)
        else:
            # Distant sky bands and moving clouds
            pyxel.rect(0, 0, WIDTH, 77, 12)
            pyxel.rect(0, 77, WIDTH, 16, 6)
            for i in range(7):
                cx = (i * 73 - int(self.camera * 0.22)) % (WIDTH + 45) - 22
                cy = 22 + (i * 17) % 40
                pyxel.rect(cx, cy, 18, 4, 7)
                pyxel.rect(cx + 5, cy - 3, 10, 4, 7)
            if self.level == "mission2":
                wind_strength = abs(self.wind)
                direction = 1 if self.wind >= 0 else -1
                for i in range(9):
                    y = 16 + (i * 13) % 58
                    x = (i * 37 + int(self.rotor * self.wind * 2)) % (WIDTH + 24) - 12
                    length = 4 + int(wind_strength * 7)
                    pyxel.line(x, y, x + direction * length, y, 7)
        if self.high_wind:
            direction = 1 if self.high_wind >= 0 else -1
            for i in range(7):
                y = 4 + (i * 3) % 20
                x = (i * 43 + int(self.rotor * self.high_wind * 2)) % (WIDTH + 30) - 15
                length = 8 + int(abs(self.high_wind) * 4)
                pyxel.line(x, y, x + direction * length, y, 7)

        # Scrolling hills and ground
        if not self.is_sea_mission():
            for i in range(9):
                hx = i * 42 - int(self.camera * 0.48) % 42
                pyxel.circ(hx, 118 + (i % 3) * 4, 20, 1 if night else 3)
            if self.is_motorway_mission():
                for i in range(8):
                    hill_x = i * 72 - int(self.camera * 0.28) % 72
                    hill_y = 126 + (i % 3) * 5
                    pyxel.circ(hill_x, hill_y, 34, 3)
                    pyxel.circ(hill_x + 18, hill_y + 5, 27, 3)
                pyxel.line(0, 145, WIDTH, 145, 11)
        terrain_color = 12 if self.is_sea_mission() else (1 if night else 11)
        horizon_color = 0 if night else 10
        pyxel.rect(0, GROUND_Y, WIDTH - 1, HEIGHT - GROUND_Y, terrain_color)
        if not self.is_sea_mission():
            pyxel.line(0, GROUND_Y, WIDTH, GROUND_Y, horizon_color)
        if self.is_sea_mission():
            shoreline_screen = int(self.sea_start_x() - self.camera)
            land_width = max(0, min(WIDTH, shoreline_screen))
            if land_width:
                pyxel.rect(0, GROUND_Y, land_width, HEIGHT - GROUND_Y, 11)
                pyxel.line(0, GROUND_Y, land_width, GROUND_Y, 10)
        for wx in range(0, WORLD_LENGTH, 36):
            sx = int(wx - self.camera)
            if -4 <= sx < WIDTH:
                if not self.is_sea_mission():
                    pyxel.line(sx, GROUND_Y + 5, sx - 5, GROUND_Y + 9, 1 if night else 3)
        if self.is_sea_mission() or self.is_rescue_mission():
            if self.is_sea_mission():
                wave_step = 4
                for wave_world_x in range(self.sea_start_x(), GOAL_PAD_X + wave_step, wave_step):
                    wave_x = int(wave_world_x - self.camera)
                    if wave_x < -wave_step or wave_x > WIDTH:
                        continue
                    wave_top = self.sea_wave_top(wave_world_x)
                    pyxel.rect(
                        wave_x,
                        wave_top,
                        wave_step,
                        HEIGHT - wave_top,
                        12,
                    )
                    phase = (self.rotor / 20 + wave_world_x / 72) % math.tau
                    curling_face = math.exp(-((phase - 2.25) / 0.42) ** 2)
                    shoulder = math.exp(-((phase - 1.55) / 1.05) ** 2)
                    if shoulder > 0.32:
                        foam_y = max(0, wave_top - 1)
                        pyxel.line(wave_x, foam_y, wave_x + wave_step, foam_y, 7)
                    if curling_face > 0.28:
                        inner_y = min(GROUND_Y - 3, wave_top + int(5 + curling_face * 9))
                        pyxel.line(wave_x, inner_y, wave_x + wave_step, inner_y, 6)
                        pyxel.line(
                            wave_x,
                            inner_y + 1,
                            wave_x + wave_step,
                            min(GROUND_Y - 2, inner_y + 3),
                            6,
                        )
                        if curling_face > 0.72:
                            pyxel.line(
                                wave_x + 1,
                                max(0, foam_y - 1),
                                wave_x + 3,
                                max(0, foam_y - 3),
                                7,
                            )
                            pyxel.pset(wave_x + 2, max(0, foam_y - 5), 7)
            else:
                for i in range(12):
                    wave_x = (i * 31 - int(self.camera * 0.4)) % (WIDTH + 20) - 10
                    wave_y = GROUND_Y + 6 + (i % 3) * 5
                    pyxel.line(wave_x, wave_y, wave_x + 12, wave_y, 5)
        if self.is_motorway_mission():
            for i in range(6):
                powerline_x = int(self.motorway_powerline_x(i) - self.camera)
                wire_y = self.motorway_powerline_y(i)
                if -70 < powerline_x < WIDTH + 20:
                    pyxel.rect(powerline_x - 2, wire_y, 4, GROUND_Y - wire_y, 4)
                    pyxel.rect(powerline_x + 62, wire_y + 3, 4, GROUND_Y - wire_y - 3, 4)
                    pyxel.line(powerline_x, wire_y, powerline_x + 64, wire_y + 3, 10)
                    pyxel.line(powerline_x, wire_y + 3, powerline_x + 64, wire_y, 10)
            pyxel.rect(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y, 5)
            pyxel.line(0, GROUND_Y + 7, WIDTH, GROUND_Y + 7, 7)
            for road_x in range(-20, WIDTH + 20, 28):
                pyxel.rect(road_x - int(self.camera) % 28, GROUND_Y + 13, 12, 2, 7)
            for i in range(7):
                car_screen = int(self.moving_car_x(i) - self.camera)
                if -12 < car_screen < WIDTH + 12:
                    pyxel.rect(car_screen - 6, GROUND_Y + 2, 12, 5, 8 if i % 2 else 10)
                    pyxel.rect(car_screen - 4, GROUND_Y, 8, 3, 7)

        if night:
            hx, hy = int(self.x - self.camera), int(self.y)
            spotlight_top_y = hy - 4
            ground_delta = max(0, GROUND_Y - spotlight_top_y)
            spotlight_near_x = hx + int(ground_delta / 1.75)
            spotlight_far_x = hx + int(ground_delta / 0.625)
            pyxel.tri(
                hx,
                spotlight_top_y,
                spotlight_near_x,
                GROUND_Y,
                spotlight_far_x,
                GROUND_Y,
                5,
            )

        # Tree obstacles create a climb-and-descend route to the destination.
        for tree_x, tree_height in self.level_obstacles():
            sx = int(tree_x - self.camera)
            if -16 <= sx <= WIDTH + 16:
                tree_top = GROUND_Y - tree_height
                if night:
                    pyxel.rect(sx - 2, tree_top + 12, 5, tree_height - 12, 1)
                    for y in range(tree_top + 12, GROUND_Y):
                        bounds = self.spotlight_bounds(y, hx, spotlight_top_y)
                        if bounds is not None:
                            left = max(sx - 2, int(bounds[0]))
                            right = min(sx + 2, int(bounds[1]))
                            if right >= left:
                                pyxel.rect(left, y, right - left + 1, 1, 4)
                    self.draw_lit_circle(sx, tree_top + 9, 12, 3, hx, spotlight_top_y)
                    self.draw_lit_circle(sx - 8, tree_top + 16, 9, 3, hx, spotlight_top_y)
                    self.draw_lit_circle(sx + 8, tree_top + 16, 9, 3, hx, spotlight_top_y)
                    self.draw_lit_circle(sx, tree_top + 15, 7, 11, hx, spotlight_top_y)
                else:
                    pyxel.rect(sx - 2, tree_top + 12, 5, tree_height - 12, 4)
                    pyxel.circ(sx, tree_top + 9, 12, 3)
                    pyxel.circ(sx - 8, tree_top + 16, 9, 3)
                    pyxel.circ(sx + 8, tree_top + 16, 9, 3)
                    pyxel.circ(sx, tree_top + 15, 7, 11)

        # Start and destination landing pads
        for pad_x, label in ((START_PAD_X, "A"), (self.level_goal_x(), "H")):
            pad_screen = int(pad_x - self.camera)
            if -40 < pad_screen < WIDTH + 40:
                pad_visible = not night or (
                    spotlight_near_x <= pad_screen <= spotlight_far_x
                )
                pyxel.rect(pad_screen - 19, GROUND_Y - 2, 38, 3, 10 if pad_visible else 1)
                pyxel.line(
                    pad_screen - 12,
                    GROUND_Y - 5,
                    pad_screen + 12,
                    GROUND_Y - 5,
                    7 if pad_visible else 1,
                )
                # A Pyxel glyph is four pixels wide, so offset it by two to
                # align its centre with the centre of the pad.
                pyxel.text(pad_screen - 2, GROUND_Y - 14, label, 7)

        if self.is_motorway_mission():
            landing_screen = int(self.level_goal_x() - self.camera)
            if -70 < landing_screen < WIDTH + 70:
                for vehicle_x, vehicle_color, light_color in (
                    (landing_screen - 47, 8, 10),
                    (landing_screen + 47, 9, 8),
                ):
                    pyxel.rect(vehicle_x - 10, GROUND_Y - 8, 20, 7, vehicle_color)
                    pyxel.rect(vehicle_x - 6, GROUND_Y - 11, 12, 4, vehicle_color)
                    pyxel.rect(vehicle_x - 3, GROUND_Y - 10, 6, 2, 7)
                    pyxel.circ(vehicle_x - 6, GROUND_Y, 3, 0)
                    pyxel.circ(vehicle_x + 6, GROUND_Y, 3, 0)
                    pyxel.rect(vehicle_x - 2, GROUND_Y - 13, 4, 2, light_color)

        hx, hy = int(self.x - self.camera), int(self.y)
        self.draw_helicopter(hx, hy)
        if self.is_rescue_mission():
            target_screen = int(self.rescue_target_x() - self.camera)
            if -20 < target_screen < WIDTH + 20:
                pyxel.circ(target_screen, GROUND_Y - 1, 3, 8)
                pyxel.line(target_screen - 5, GROUND_Y - 1, target_screen + 5, GROUND_Y - 1, 8)
            rope_x = hx + int(self.wind * 2)
            rope_length = max(12, min(48, int(32 + self.wind * 5)))
            pyxel.line(hx, hy + 4, rope_x, hy + rope_length, 7)
            pyxel.circ(rope_x, hy + rope_length, 2, 10)
        self.draw_hud()
        if self.state == "intro":
            self.draw_intro()
        elif self.state == "mission_select":
            self.draw_mission_select()
        elif self.state in ("ready", "landed"):
            title = {
                "tutorial": "TUTORIAL",
                "mission1": "MISSION 1",
                "mission2": "MISSION 2",
                "mission3": "NIGHT MISSION",
                "mission4": "SEA CROSSING",
                "mission5": "MOTORWAY",
                "mission6": "SEA RESCUE",
            }[self.level]
            width = len(title) * 4
            pyxel.rect(47, 57, 162, 40, 0)
            pyxel.rectb(47, 57, 162, 40, 7)
            pyxel.text((WIDTH - width) // 2, 65, title, 10)
            hint = "SPACE TO TAKE OFF" if self.state == "ready" else "SPACE TO FLY AGAIN"
            pyxel.text((WIDTH - len(hint) * 4) // 2, 80, hint, 7)
        elif self.state == "tutorial_complete":
            self.draw_overlay("TUTORIAL COMPLETE!", "SPACE FOR MISSION 1")
        elif self.state == "mission_complete":
            self.draw_overlay("MISSION COMPLETE!", "SPACE TO REPLAY")
        elif self.state == "crashed":
            pyxel.rect(74, 30, 108, 10, 0)
            pyxel.text(78, 33, "CRASH - SPACE RESTART", 8)

    def draw_mission_select(self):
        pyxel.cls(1)
        pyxel.rect(8, 6, 240, 149, 0)
        pyxel.rectb(8, 6, 240, 149, 7)
        pyxel.text(76, 12, "MISSION SELECT", 10)
        missions = (
            ("TUTORIAL", "FLIGHT SCHOOL"),
            ("MISSION 1", "TREE LINE"),
            ("MISSION 2", "WIND RUN"),
            ("MISSION 3", "NIGHT RUN"),
            ("MISSION 4", "ROUGH SEAS"),
            ("MISSION 5", "MOTORWAY"),
            ("MISSION 6", "SEA RESCUE"),
        )
        unlocked = (
            True,
            self.mission_unlocked,
            self.mission_two_unlocked,
            self.mission_three_unlocked,
            self.mission_four_unlocked,
            self.mission_five_unlocked,
            self.mission_six_unlocked,
        )
        for index, (title, subtitle) in enumerate(missions):
            column = index % 2
            row = index // 2
            self.draw_mission_card(
                index,
                16 + column * 116,
                25 + row * 27,
                title,
                subtitle,
                unlocked[index],
            )
        pyxel.text(63, 143, "UP/DOWN SELECT  SPACE LAUNCH", 6)

    def draw_mission_card(self, index, x, y, title, subtitle, unlocked):
        selected = self.selected_mission == index
        border = 10 if selected else 5
        pyxel.rectb(x, y, 108, 22, border)
        marker = ">" if selected else " "
        status = subtitle if unlocked else "LOCKED - COMPLETE TUTORIAL"
        pyxel.text(x + 7, y + 3, marker + " " + title, 10 if unlocked else 13)
        pyxel.text(x + 15, y + 13, status, 7 if unlocked else 8)

    def draw_intro(self):
        pyxel.cls(0)
        pyxel.rect(24, 30, 208, 96, 0)
        pyxel.rectb(24, 30, 208, 96, 7)
        title = "HELI FOB"
        subtitle = "FLIGHT OPERATIONS"
        hint = "SPACE TO CONTINUE"
        pyxel.text((WIDTH - len(title) * 4) // 2, 52, title, 10)
        pyxel.text((WIDTH - len(subtitle) * 4) // 2, 70, subtitle, 7)
        pyxel.text((WIDTH - len(hint) * 4) // 2, 94, hint, 11)

    def draw_overlay(self, title, hint):
        pyxel.rect(42, 57, 172, 40, 0)
        pyxel.rectb(42, 57, 172, 40, 7)
        pyxel.text((WIDTH - len(title) * 4) // 2, 65, title, 10)
        pyxel.text((WIDTH - len(hint) * 4) // 2, 81, hint, 11)

    def draw_helicopter(self, x, y):
        # A single filled fuselage that rotates with pitch.
        def point(local_x, local_y):
            cos_pitch = math.cos(self.pitch)
            sin_pitch = math.sin(self.pitch)
            local_x *= CHOPPER_SCALE
            local_y *= CHOPPER_SCALE
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
            int(rotor_hub[0] - 12 * CHOPPER_SCALE * math.cos(rotor_angle)),
            int(rotor_hub[1] - 12 * CHOPPER_SCALE * math.sin(rotor_angle)),
        )
        rotor_right = (
            int(rotor_hub[0] + 12 * CHOPPER_SCALE * math.cos(rotor_angle)),
            int(rotor_hub[1] + 12 * CHOPPER_SCALE * math.sin(rotor_angle)),
        )
        pyxel.line(*mast_base, *rotor_hub, 0)
        pyxel.line(*rotor_left, *rotor_right, 7)
        span = int((5 if (self.rotor // 3) % 2 else 12) * CHOPPER_SCALE)
        tail_rotor = point(-18, 0)
        pyxel.line(tail_rotor[0], tail_rotor[1] - span // 2, tail_rotor[0], tail_rotor[1] + span // 2, 7)

    def draw_hud(self):
        # Short, fixed labels keep both collective values readable.
        pyxel.rect(0, 0, WIDTH, 38, 0)
        pyxel.text(10, 2, "FUEL", 7)
        pyxel.rect(31, 2, 52, 6, 5)
        fuel_color = 11 if self.fuel > 25 else 8
        pyxel.rect(32, 3, int(50 * self.fuel / 100), 4, fuel_color)
        pyxel.text(10, 11, "ALT", 7)
        pyxel.rect(31, 11, 52, 6, 5)
        warning_altitude = GROUND_Y - GEAR_OFFSET - 38
        max_altitude = warning_altitude / 0.85
        altitude = max(0.0, min(max_altitude, GROUND_Y - GEAR_OFFSET - self.y))
        altitude_ratio = altitude / max_altitude
        altitude_warning_x = 31 + int(52 * 0.85)
        altitude_marker = 31 + int(50 * altitude_ratio)
        pyxel.line(altitude_marker, 10, altitude_marker, 17, 10)
        pyxel.text(94, 2, "THR", 7)
        pyxel.rect(110, 2, 52, 6, 5)
        throttle_warning_x = 110 + int(52 * 0.95)
        pyxel.rect(111, 3, int(50 * self.collective), 4, 9)
        self.draw_warning_pattern(throttle_warning_x, 2, 52 - int(52 * 0.95), 6)
        hover_marker = 111 + int(50 * self.hover_throttle_required())
        pyxel.line(hover_marker, 1, hover_marker, 8, 10)
        pyxel.text(94, 11, "ACT", 6)
        pyxel.rect(110, 11, 52, 6, 5)
        pyxel.rect(111, 12, int(50 * self.rotor_lift), 4, 11)
        pyxel.line(hover_marker, 10, hover_marker, 17, 10)
        distance = max(0, int(GOAL_PAD_X - self.x))
        if self.level == "tutorial":
            distance = max(0, int(TUTORIAL_GOAL_X - self.x))
        pyxel.text(166, 2, "DST:%04d" % distance, 10)
        pyxel.text(210, 11, "BRN:%1.1f" % self.fuel_burn_rate, 6)
        pyxel.rect(0, 24, WIDTH, 12, 1)
        self.draw_warning_pattern(altitude_warning_x, 11, 52 - int(52 * 0.85), 6)
        pyxel.text(10, 27, "WIND", 7)
        pyxel.text(42, 27, "%+.1f" % self.wind, 6)
        pyxel.text(78, 27, "SPD:%+.1f" % self.vx, 6)
        if self.is_rescue_mission() and self.state == "flying":
            pyxel.text(166, 27, "RES:%02d%%" % int(self.rescue_progress * 100 / 180), 7)
        if self.level == "tutorial" and self.state == "flying":
            pyxel.rect(0, 40, WIDTH, 12, 0)
            pyxel.text(10, 43, self.tutorial_hint(), 7)

    def draw_warning_pattern(self, x, y, width, height):
        for cell_y in range(y, y + height, 2):
            for cell_x in range(x, x + width, 2):
                color = 8 if ((cell_x - x) // 2 + (cell_y - y) // 2) % 2 else 7
                pyxel.rect(
                    cell_x,
                    cell_y,
                    min(2, x + width - cell_x),
                    min(2, y + height - cell_y),
                    color,
                )

    def tutorial_hint(self):
        if self.x < 95:
            return "STEP 1: HOLD UP TO LIFT"
        if self.x < 145:
            return "STEP 2: STEER WITH LEFT / RIGHT"
        if self.x < 205:
            return "STEP 3: CLEAR THE TREES"
        return "STEP 4: LAND ON THE H PAD"


ChopperGame()
