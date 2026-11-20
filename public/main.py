"""Heli FOB: a side-scrolling Pyxel helicopter landing game."""

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
WATER_STEP = 8
WATER_SPRING = 0.018
WATER_DAMPING = 0.12
WATER_SPREAD = 0.045
WATER_END_FORCE = 0.14
WATER_START_AMPLITUDE = 0.47
WATER_END_AMPLITUDE = 6.0
WATER_END_X = WORLD_LENGTH - 20
PLATFORM_HALF_WIDTH = 34
RESCUE_TARGET_X = 980
RESCUE_FRAMES = 180
# A load ahead of the mast noses the helicopter down. Positive pitch is nose-down.
SLING_TORQUE = 0.00009
LOOK_AHEAD = 14.0
SPOTLIGHT_BIAS = 0.50
SPOTLIGHT_SPREAD = 0.38
SPOTLIGHT_RANGE = 176
ROTOR_NOTES = ("a1", "b1", "c2", "d2", "e2", "f2", "g2", "a2", "b2", "c3", "d3")

TREE_LINE = (
    (220, 48),
    (390, 64),
    (560, 38),
    (750, 72),
    (930, 48),
    (1120, 66),
    (1310, 42),
    (1470, 75),
)
# The open gap is where the gust is still building. The tall pair sits in it.
WIND_TREES = (
    (340, 34),
    (560, 46),
    (860, 40),
    (1280, 76),
    (1435, 68),
    (1580, 58),
)
# Spacing is longer than the spotlight, and the last tree walls off the pad.
NIGHT_TREES = (
    (280, 62),
    (470, 28),
    (690, 70),
    (980, 34),
    (1180, 76),
    (1390, 40),
    (1565, 84),
)
TUTORIAL_OBSTACLES = ((150, 28), (205, 42))
CROSSWIND_WIRE_Y = (76, 98, 84, 104, 80, 96, 88)

LEVELS = (
    "tutorial",
    "mission1",
    "mission2",
    "mission3",
    "mission4",
    "mission5",
    "mission6",
    "mission7",
)
LEVEL_INFO = {
    "tutorial": {
        "title": "TUTORIAL",
        "card": "FLIGHT SCHOOL",
        "brief": "LIFT, STEER, CLEAR TREES, LAND",
        "trees": TUTORIAL_OBSTACLES,
        "goal": TUTORIAL_GOAL_X,
    },
    "mission1": {
        "title": "MISSION 1",
        "card": "TREE LINE",
        "brief": "CLIMB THE GAPS. LAND SOFT ON H",
        "trees": TREE_LINE,
        "goal": GOAL_PAD_X,
    },
    "mission2": {
        "title": "MISSION 2",
        "card": "WIND RUN",
        "brief": "GUSTS PEAK AT THE TALL TREES",
        "trees": WIND_TREES,
        "goal": GOAL_PAD_X,
    },
    "mission3": {
        "title": "NIGHT MISSION",
        "card": "NIGHT RUN",
        "brief": "THE BEAM FOLLOWS YOUR NOSE",
        "trees": NIGHT_TREES,
        "goal": GOAL_PAD_X,
    },
    "mission4": {
        "title": "SEA CROSSING",
        "card": "ROUGH SEAS",
        "brief": "WAVES BUILD. STAY OVER THE CRESTS",
        "trees": (),
        "goal": GOAL_PAD_X,
    },
    "mission5": {
        "title": "MOTORWAY",
        "card": "MOTORWAY",
        "brief": "THREAD THE WIRES. CARS OWN THE ROAD",
        "trees": (),
        "goal": GOAL_PAD_X,
    },
    "mission6": {
        "title": "SEA RESCUE",
        "card": "SEA RESCUE",
        "brief": "PUT THE HOOK ON THEM, THEN RETURN",
        "trees": (),
        "goal": GOAL_PAD_X,
    },
    "mission7": {
        "title": "CROSSWIND",
        "card": "WIRE WIND",
        "brief": "CROSSWIND. DO NOT MEET THE WIRES",
        "trees": (),
        "goal": GOAL_PAD_X,
    },
}
WIND_LEVELS = ("mission2", "mission4", "mission6", "mission7")
VERTICAL_WIND_LEVELS = ("mission2", "mission4", "mission7")
RESTARTABLE = (
    "ready",
    "flying",
    "landed",
    "crashed",
    "tutorial_complete",
    "mission_complete",
)
CRASH_LINES = {
    "tree": "HIT A TREE",
    "wave": "HIT A WAVE",
    "wire": "HIT A WIRE",
    "car": "HIT A CAR",
    "hard": "HARD LANDING",
    "tipped": "TIPPED OVER",
    "fuel": "FUEL OUT",
    "pad": "MISSED THE PAD",
}
CRASH_SOUNDS = {
    "tree": 2,
    "pad": 2,
    "hard": 2,
    "fuel": 2,
    "wire": 3,
    "wave": 4,
    "car": 5,
    "tipped": 9,
}
LAND_SOUND = 7
HOIST_SOUND = 8
SPUTTER_SOUND = 6


def storage_get(key):
    if window is None:
        return None
    try:
        value = window.localStorage.getItem(key)
    except Exception:
        return None
    if value is None:
        return None
    text = str(value)
    if text in ("None", "null", "undefined"):
        return None
    return text


def storage_set(key, value):
    if window is None:
        return
    try:
        window.localStorage.setItem(key, value)
    except Exception:
        return


def format_seconds(seconds):
    tenths = int(round(max(0.0, seconds) * 10))
    return "%d.%ds" % (tenths // 10, tenths % 10)


def format_score(prefix, result):
    return "%s %s  FUEL %d  SOFT %d" % (
        prefix,
        format_seconds(result["time"]),
        int(round(result["fuel"])),
        int(round(result["soft"])),
    )


class ChopperGame:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="CHOPPER RUN", fps=30)
        self.init_audio()
        self.reset()
        pyxel.run(self.update, self.draw)

    def init_audio(self):
        pyxel.sounds[2].set("d2a1f1c1", "n", "7642", "f", 8)
        pyxel.sounds[3].set("e3c3a2f1", "s", "7653", "f", 6)
        pyxel.sounds[4].set("c2c2a1f1", "n", "7764", "f", 7)
        pyxel.sounds[5].set("f1c1c1", "n", "775", "f", 9)
        pyxel.sounds[6].set("c3rc2ra1", "s", "535", "f", 8)
        pyxel.sounds[7].set("c2g2", "p", "64", "f", 6)
        pyxel.sounds[8].set("c3e3g3c4", "t", "5664", "n", 6)
        pyxel.sounds[9].set("a1f1d1", "s", "654", "f", 8)
        self.rotor_playing = False
        self.rotor_note = ""
        self.wind_playing = False
        self.wind_band = -1

    def reset(self):
        self.level = "tutorial"
        self.last_result = None
        self.load_progress()
        self.reset_flight()
        self.reset_water()
        self.selected_mission = 0
        for index, level in enumerate(LEVELS):
            if self.is_unlocked(index) and not self.cleared[level]:
                self.selected_mission = index
                break

    def load_progress(self):
        self.cleared = {}
        self.bests = {}
        for level in LEVELS:
            self.cleared[level] = storage_get("chopper-run-%s-complete" % level) == "1"
            self.bests[level] = self.parse_best(storage_get("chopper-run-%s-best" % level))

    def parse_best(self, raw):
        if not raw:
            return None
        parts = raw.split(",")
        if len(parts) != 3:
            return None
        try:
            return {
                "time": float(parts[0]),
                "fuel": float(parts[1]),
                "soft": float(parts[2]),
            }
        except ValueError:
            return None

    def reset_flight(self):
        self.x, self.y = float(START_PAD_X), float(PAD_SURFACE_Y - GEAR_OFFSET)
        self.vx, self.vy = 0.0, 0.0
        self.pitch = 0.0
        self.pitch_rate = 0.0
        self.collective = 0.0
        self.rotor_lift = 0.0
        self.disk_tilt = 0.0
        self.camera = 0.0
        self.look_ahead = 0.0
        self.fuel = 100.0
        self.state = "intro"
        self.rotor = 0
        self.wind = 0.0
        self.high_wind = 0.0
        self.fuel_burn_rate = 0.0
        self.rescue_progress = 0
        self.survivor = False
        self.fuel_starved = False
        self.crash_reason = ""
        self.flight_frames = 0
        self.water_splash = 0
        self.hook_x = self.x
        self.hook_y = self.y + 40
        self.hook_vx = 0.0
        self.hook_vy = 0.0

    def start_level(self, level):
        self.level = level
        self.reset_flight()
        self.reset_water()
        self.state = "ready"

    def level_goal_x(self):
        return LEVEL_INFO[self.level]["goal"]

    def level_obstacles(self):
        return LEVEL_INFO[self.level]["trees"]

    def level_index(self, level=None):
        return LEVELS.index(self.level if level is None else level)

    def is_unlocked(self, index):
        if index <= 0:
            return True
        return self.cleared[LEVELS[index - 1]]

    def is_night(self):
        return self.level == "mission3"

    def is_sea_mission(self):
        return self.level == "mission4"

    def is_motorway_mission(self):
        return self.level in ("mission5", "mission7")

    def is_rescue_mission(self):
        return self.level == "mission6"

    def is_water_mission(self):
        return self.is_sea_mission() or self.is_rescue_mission()

    def powerline_count(self):
        return 7 if self.level == "mission7" else 6

    def on_sea_platform(self):
        return (
            self.is_sea_mission()
            and abs(self.x - self.level_goal_x()) <= PLATFORM_HALF_WIDTH
        )

    def on_landing_pad(self):
        pads = [START_PAD_X]
        if not self.is_rescue_mission():
            pads.append(self.level_goal_x())
        return any(abs(self.x - pad_x) < 24 for pad_x in pads)

    def distance_target(self):
        if self.is_rescue_mission():
            return RESCUE_TARGET_X if not self.survivor else START_PAD_X
        return self.level_goal_x()

    def reset_water(self):
        water_start = self.sea_start_x()
        water_end = WATER_END_X + WATER_STEP
        self.water_base_y = GROUND_Y
        self.water_heights = [
            float(self.water_base_y)
            for _ in range((water_end - water_start) // WATER_STEP + 1)
        ]
        self.water_velocities = [0.0] * len(self.water_heights)
        self.water_time = 0
        center = len(self.water_heights) // 3
        self.water_velocities[center] = -0.75

    def update_water(self):
        if not self.is_water_mission():
            return
        self.water_time += 1
        heights = self.water_heights
        velocities = self.water_velocities
        next_heights = heights[:]
        next_velocities = velocities[:]
        for index in range(1, len(heights) - 1):
            column_progress = index / (len(heights) - 1)
            displacement = heights[index] - self.water_base_y
            neighbor_force = heights[index - 1] + heights[index + 1] - 2 * heights[index]
            swell_force = (
                WATER_END_FORCE
                * (0.12 + 0.88 * column_progress**2)
                * (
                    0.48
                    + 0.34 * math.sin(self.water_time / 23 + index / 4)
                    + 0.18 * math.sin(self.water_time / 37 - index / 7)
                )
            )
            acceleration = (
                -WATER_SPRING * displacement
                - WATER_DAMPING * velocities[index]
                + WATER_SPREAD * neighbor_force
                - swell_force
            )
            next_velocities[index] = velocities[index] + acceleration
            next_heights[index] = heights[index] + next_velocities[index]
        pulse_index = 2 + (self.water_time // 90) % (len(heights) - 4)
        if self.water_time % 90 == 0:
            next_velocities[pulse_index] -= 0.38
        self.water_heights = next_heights
        self.water_velocities = next_velocities

    def water_amplitude(self, world_x):
        progress = (world_x - self.sea_start_x()) / (GOAL_PAD_X - self.sea_start_x())
        progress = max(0.0, min(1.0, progress))
        return WATER_START_AMPLITUDE + (
            WATER_END_AMPLITUDE - WATER_START_AMPLITUDE
        ) * progress

    def spotlight_origin(self):
        return int(self.x - self.camera), int(self.y) - 4

    def spotlight_aim(self):
        return self.pitch + SPOTLIGHT_BIAS

    def in_spotlight(self, sx, sy, ox, oy):
        dx = sx - ox
        dy = sy - oy
        if dx * dx + dy * dy > SPOTLIGHT_RANGE * SPOTLIGHT_RANGE:
            return False
        if dx * dx + dy * dy <= 16:
            return True
        angle = math.atan2(dy, dx)
        delta = angle - self.spotlight_aim()
        delta = (delta + math.pi) % (2 * math.pi) - math.pi
        return abs(delta) < SPOTLIGHT_SPREAD

    def spotlight_ray(self, ox, oy, angle):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        length = float(SPOTLIGHT_RANGE)
        if sin_a > 0.02:
            ground_t = (GROUND_Y - oy) / sin_a
            if 0 < ground_t < length:
                length = ground_t
        return int(ox + cos_a * length), int(oy + sin_a * length)

    def wind_progress(self):
        progress = (self.x - START_PAD_X) / (GOAL_PAD_X - START_PAD_X)
        return max(0.0, min(1.0, progress))

    def wind_force(self):
        if self.level not in WIND_LEVELS:
            return 0.0
        progress = self.wind_progress()
        intensity = 0.8 + 3.2 * progress
        if self.level == "mission6":
            intensity = 1.2
        elif self.level == "mission7":
            intensity = 0.6 + 2.4 * progress
        gust = 0.65 * math.sin(self.rotor / 48) + 0.35 * math.sin(self.rotor / 19)
        return intensity * gust

    def vertical_wind_force(self):
        if self.level not in VERTICAL_WIND_LEVELS:
            return 0.0
        progress = self.wind_progress()
        intensity = 0.8 + 3.2 * progress
        if self.level == "mission7":
            intensity = 0.35 + 1.1 * progress
        gust = 0.65 * math.sin(self.rotor / 37) + 0.35 * math.sin(self.rotor / 16)
        return intensity * gust

    def high_wind_force(self):
        if self.y > HEIGHT * 0.15:
            return 0.0
        gust = math.sin(self.rotor / 11) + 0.55 * math.sin(self.rotor / 29)
        return 4.5 * gust

    def rescue_target_x(self):
        return RESCUE_TARGET_X

    def moving_car_x(self, index):
        return 180 + index * 220 + math.sin(self.rotor / (18 + index * 3)) * 28

    def motorway_powerline_x(self, index):
        if self.level == "mission7":
            return 280 + index * 180
        return 220 + index * 230

    def motorway_powerline_y(self, index):
        if self.level == "mission7":
            return CROSSWIND_WIRE_Y[index]
        return 82 + (index % 2) * 8

    def sea_start_x(self):
        return START_PAD_X + 180

    def sea_wave_top(self, world_x):
        relative_x = max(
            0.0,
            min(WATER_END_X - self.sea_start_x(), world_x - self.sea_start_x()),
        )
        position = relative_x / WATER_STEP
        left_index = min(int(position), len(self.water_heights) - 2)
        blend = position - left_index
        height = (
            self.water_heights[left_index] * (1 - blend)
            + self.water_heights[left_index + 1] * blend
        )
        displacement = height - self.water_base_y
        return max(
            8,
            min(
                HEIGHT - 1,
                int(self.water_base_y + displacement * self.water_amplitude(world_x)),
            ),
        )

    def hover_throttle_required(self):
        fuel_efficiency = 0.75 + 0.25 * (self.fuel / 100)
        return min(1.0, GRAVITY / (MAX_ROTOR_THRUST * fuel_efficiency))

    def altitude_geometry(self):
        warning_altitude = GROUND_Y - GEAR_OFFSET - 38
        max_altitude = warning_altitude / 0.85
        altitude = max(0.0, min(max_altitude, GROUND_Y - GEAR_OFFSET - self.y))
        burn_altitude = GROUND_Y - GEAR_OFFSET - HIGH_ALTITUDE_Y
        return altitude, max_altitude, burn_altitude

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        if pyxel.btnp(pyxel.KEY_R) and self.state in RESTARTABLE:
            self.start_level(self.level)
        elif self.state == "intro":
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.state = "mission_select"
        elif self.state == "mission_select":
            self.update_mission_select()
        elif self.state in ("tutorial_complete", "mission_complete"):
            self.update_water()
            if pyxel.btnp(pyxel.KEY_SPACE):
                self.continue_after_clear()
        else:
            self.update_water()
            if self.state == "crashed":
                self.update_crash()
                if pyxel.btnp(pyxel.KEY_SPACE):
                    self.start_level(self.level)
            elif self.state in ("ready", "landed"):
                if pyxel.btnp(pyxel.KEY_SPACE):
                    # Start every new flight with enough collective to clear the pad.
                    self.reset_flight()
                    self.state = "flying"
                    self.collective = 0.60
                    self.rotor_lift = 0.60
            elif self.state == "flying":
                self.update_flight()
        self.update_audio()

    def update_mission_select(self):
        if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(pyxel.KEY_DOWN):
            direction = -1 if pyxel.btnp(pyxel.KEY_UP) else 1
            self.selected_mission = (self.selected_mission + direction) % len(LEVELS)
        if pyxel.btnp(pyxel.KEY_SPACE) and self.is_unlocked(self.selected_mission):
            self.start_level(LEVELS[self.selected_mission])

    def continue_after_clear(self):
        index = self.level_index() + 1
        if index < len(LEVELS):
            self.selected_mission = index
            self.start_level(LEVELS[index])
        else:
            self.state = "mission_select"
            self.selected_mission = len(LEVELS) - 1

    def clear_hint(self):
        index = self.level_index() + 1
        if index >= len(LEVELS):
            return "SPACE FOR MISSION SELECT"
        if index == 1:
            return "SPACE FOR MISSION 1"
        return "SPACE FOR MISSION %d" % index

    def update_flight(self):
        self.flight_frames += 1
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
        if self.survivor:
            self.pitch_rate += (self.hook_x - self.x) * SLING_TORQUE
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
                self.start_crash(GROUND_Y, "car")
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
        if self.fuel <= 0 and not self.fuel_starved:
            self.fuel_starved = True
            self.play_cue(SPUTTER_SOUND)
        self.x += self.vx
        self.y += self.vy
        self.x = max(8, min(WORLD_LENGTH - 20, self.x))
        self.update_camera()
        self.update_hook()

        hit = self.obstacle_hit()
        if hit is not None:
            self.start_crash(hit[0], hit[1])
            return
        if (
            self.is_water_mission()
            and not self.on_sea_platform()
            and self.sea_start_x() <= self.x < WATER_END_X
        ):
            wave_step = 4
            wave_index = round((self.x - self.sea_start_x()) / wave_step)
            wave_x = self.sea_start_x() + wave_index * wave_step
            if abs(self.x - wave_x) <= wave_step and self.y + GEAR_OFFSET >= self.sea_wave_top(wave_x):
                self.start_crash(self.sea_wave_top(wave_x), "wave")
                return

        self.update_rescue()
        self.resolve_touchdown()

    def update_camera(self):
        target = max(-28.0, min(36.0, self.vx * LOOK_AHEAD))
        self.look_ahead += (target - self.look_ahead) * 0.08
        self.camera = max(0, min(WORLD_LENGTH - WIDTH, self.x - 78 + self.look_ahead))

    def update_hook(self):
        if not self.is_rescue_mission() or self.state != "flying":
            return
        anchor_x = self.x
        anchor_y = self.y + 4
        rest = 18 if self.survivor else 40
        rest_x = anchor_x + self.wind * 5.5
        rest_y = anchor_y + rest
        self.hook_vx += (rest_x - self.hook_x) * 0.045 + self.wind * 0.012
        self.hook_vy += (rest_y - self.hook_y) * 0.06
        self.hook_vx *= 0.84
        self.hook_vy *= 0.84
        self.hook_x += self.hook_vx
        self.hook_y += self.hook_vy
        dx = self.hook_x - anchor_x
        dy = self.hook_y - anchor_y
        dist = math.hypot(dx, dy)
        limit = rest + 8
        if dist > limit and dist > 0:
            scale = limit / dist
            self.hook_x = anchor_x + dx * scale
            self.hook_y = anchor_y + dy * scale
            self.hook_vx *= 0.5
            self.hook_vy *= 0.5

    def hook_on_survivor(self):
        wave = self.sea_wave_top(self.rescue_target_x())
        return (
            abs(self.hook_x - self.rescue_target_x()) < 9
            and abs(self.hook_y - (wave - 3)) < 10
        )

    def hover_steady(self):
        wave = self.sea_wave_top(self.x)
        return (
            abs(self.vx) < 0.4
            and abs(self.vy) < 0.4
            and self.y + GEAR_OFFSET < wave - 8
            and 96 < self.y < 138
        )

    def update_rescue(self):
        if not self.is_rescue_mission() or self.survivor or self.state != "flying":
            return
        if self.hook_on_survivor() and self.hover_steady():
            self.rescue_progress += 1
            if self.rescue_progress >= RESCUE_FRAMES:
                self.survivor = True
                self.play_cue(HOIST_SOUND)
        else:
            self.rescue_progress = 0

    def touchdown_reason(self, on_pad):
        upright = math.cos(self.pitch) > 0.92 and abs(self.disk_tilt) < 0.2
        gentle = abs(self.vy) < 0.8 and abs(self.vx) < 0.8
        if on_pad and upright and gentle:
            return None
        if self.fuel_starved or self.fuel <= 0:
            return "fuel"
        if not on_pad:
            return "pad"
        if not upright:
            return "tipped"
        return "hard"

    def landing_softness(self):
        worst = max(
            abs(self.vy) / 0.8,
            abs(self.vx) / 0.8,
            abs(self.pitch) / 0.40,
            abs(self.disk_tilt) / 0.2,
        )
        return int(round(max(0.0, min(1.0, 1.0 - worst)) * 100))

    def plant_skids(self, surface_y):
        self.y = surface_y - GEAR_OFFSET
        self.vx = 0.0
        self.vy = 0.0
        self.pitch_rate = 0.0

    def record_result(self, softness):
        result = {
            "time": self.flight_frames / 30,
            "fuel": round(self.fuel, 1),
            "soft": softness,
        }
        self.last_result = result
        best = self.bests.get(self.level)
        if best is None:
            best = dict(result)
        else:
            best = {
                "time": min(best["time"], result["time"]),
                "fuel": max(best["fuel"], result["fuel"]),
                "soft": max(best["soft"], result["soft"]),
            }
        self.bests[self.level] = best
        self.cleared[self.level] = True
        storage_set("chopper-run-%s-complete" % self.level, "1")
        storage_set(
            "chopper-run-%s-best" % self.level,
            "%.2f,%.1f,%d" % (best["time"], best["fuel"], int(best["soft"])),
        )

    def resolve_touchdown(self):
        if self.state != "flying":
            return
        on_pad = self.on_landing_pad()
        surface_y = PAD_SURFACE_Y if on_pad else GROUND_Y
        if self.y < surface_y - GEAR_OFFSET:
            return
        reason = self.touchdown_reason(on_pad)
        # The ship is always a safe deck. It only completes the rescue once
        # the survivor is on the hook.
        if reason is None and self.is_rescue_mission() and not self.survivor:
            self.plant_skids(surface_y)
            self.play_cue(LAND_SOUND)
            self.state = "landed"
            return
        if reason is None:
            softness = self.landing_softness()
            self.plant_skids(surface_y)
            self.record_result(softness)
            self.play_cue(LAND_SOUND)
            self.state = (
                "tutorial_complete" if self.level == "tutorial" else "mission_complete"
            )
            return
        self.start_crash(surface_y, reason)

    def obstacle_hit(self):
        if self.is_motorway_mission():
            for i in range(self.powerline_count()):
                pole_x = self.motorway_powerline_x(i)
                wire_y = self.motorway_powerline_y(i)
                if abs(self.x - pole_x) < 7 and self.y + GEAR_OFFSET >= wire_y:
                    return wire_y, "wire"
                if pole_x - 4 <= self.x <= pole_x + 64 and abs(self.y + GEAR_OFFSET - wire_y) < 5:
                    return wire_y, "wire"
                far_pole = pole_x + 62
                if abs(self.x - far_pole) < 7 and self.y + GEAR_OFFSET >= wire_y + 3:
                    return wire_y, "wire"
        for tree_x, tree_height in self.level_obstacles():
            tree_top = GROUND_Y - tree_height
            if abs(self.x - tree_x) < 11 and self.y + GEAR_OFFSET >= tree_top:
                return tree_top, "tree"
        return None

    def start_crash(self, impact_surface_y, reason):
        self.crash_reason = reason
        self.y = impact_surface_y - GEAR_OFFSET
        self.collective = 0.0
        if self.is_water_mission() and impact_surface_y < GROUND_Y:
            self.water_splash = 8
        impact_direction = 1 if self.vx >= 0 else -1
        self.pitch_rate += impact_direction * (0.012 + abs(self.vy) * 0.018)
        self.state = "crashed"
        self.play_crash_sound(reason)

    def play_crash_sound(self, reason):
        pyxel.play(2, CRASH_SOUNDS[reason])

    def play_cue(self, sound_id):
        pyxel.play(3, sound_id)

    def update_crash(self):
        """Simulate a tumbling wreck after an impact."""
        self.rotor += 1
        self.water_splash = max(0, self.water_splash - 1)
        self.collective = 0.0
        self.rotor_lift *= 0.94
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        self.pitch += self.pitch_rate
        self.vx *= 0.992
        self.pitch_rate *= 0.996
        self.x = max(8, min(WORLD_LENGTH - 20, self.x))
        self.update_camera()

        on_pad = self.on_landing_pad()
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

    def update_audio(self):
        rotor_on = self.state == "flying" and self.fuel > 0
        if not rotor_on:
            if self.rotor_playing:
                pyxel.stop(0)
                self.rotor_playing = False
                self.rotor_note = ""
        else:
            index = int(self.collective * (len(ROTOR_NOTES) - 1))
            index = max(0, min(len(ROTOR_NOTES) - 1, index))
            note = ROTOR_NOTES[index]
            if note != self.rotor_note:
                self.rotor_note = note
                self.rotor_playing = True
                pyxel.sounds[0].set(note + note, "t", "55", "v", 18)
                pyxel.play(0, 0, loop=True)

        wind_on = self.state == "flying" and abs(self.wind) > 0.35
        if not wind_on:
            if self.wind_playing:
                pyxel.stop(1)
                self.wind_playing = False
                self.wind_band = -1
        else:
            band = max(1, min(7, int(abs(self.wind) * 1.7)))
            if band != self.wind_band:
                self.wind_band = band
                self.wind_playing = True
                pyxel.sounds[1].set("c0", "n", str(band), "n", 14)
                pyxel.play(1, 1, loop=True)

    def draw(self):
        pyxel.cls(1)
        night = self.is_night()
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
            if self.level in WIND_LEVELS and abs(self.wind) > 0.2:
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
        if not self.is_water_mission():
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
        terrain_color = 12 if self.is_water_mission() else (1 if night else 11)
        horizon_color = 0 if night else 10
        pyxel.rect(0, GROUND_Y, WIDTH - 1, HEIGHT - GROUND_Y, terrain_color)
        if not self.is_water_mission():
            pyxel.line(0, GROUND_Y, WIDTH, GROUND_Y, horizon_color)
        if self.is_water_mission():
            shoreline_screen = int(self.sea_start_x() - self.camera)
            land_width = max(0, min(WIDTH, shoreline_screen))
            if land_width:
                pyxel.rect(0, GROUND_Y, land_width, HEIGHT - GROUND_Y, 11)
                pyxel.line(0, GROUND_Y, land_width, GROUND_Y, 10)
        for wx in range(0, WORLD_LENGTH, 36):
            sx = int(wx - self.camera)
            if -4 <= sx < WIDTH:
                if not self.is_water_mission():
                    pyxel.line(sx, GROUND_Y + 5, sx - 5, GROUND_Y + 9, 1 if night else 3)
        if self.is_water_mission():
            self.draw_water()
        if self.is_motorway_mission():
            self.draw_motorway()

        hx, hy = int(self.x - self.camera), int(self.y)
        if night:
            ox, oy = self.spotlight_origin()
            aim = self.spotlight_aim()
            left = self.spotlight_ray(ox, oy, aim - SPOTLIGHT_SPREAD)
            right = self.spotlight_ray(ox, oy, aim + SPOTLIGHT_SPREAD)
            pyxel.tri(ox, oy, left[0], left[1], right[0], right[1], 5)

        self.draw_trees(night, hx, hy)
        self.draw_pads(night, hx, hy)
        if self.is_motorway_mission():
            self.draw_landing_vehicles()
        self.draw_helicopter(hx, hy)
        if self.water_splash:
            splash_width = 4 + (8 - self.water_splash) * 2
            splash_y = hy + GEAR_OFFSET + 1
            pyxel.line(hx - splash_width, splash_y, hx - 2, splash_y - 3, 7)
            pyxel.line(hx + 2, splash_y - 3, hx + splash_width, splash_y, 7)
        if self.is_rescue_mission():
            self.draw_rescue(hx, hy)
        self.draw_hud()
        self.draw_state_overlay()

    def draw_water(self):
        wave_step = 4
        for wave_world_x in range(self.sea_start_x(), WATER_END_X + wave_step, wave_step):
            wave_x = int(wave_world_x - self.camera)
            if wave_x < -wave_step or wave_x > WIDTH:
                continue
            wave_top = self.sea_wave_top(wave_world_x)
            pyxel.rect(
                wave_x,
                wave_top,
                wave_step,
                HEIGHT - wave_top,
                1,
            )
            wave_index = min(
                len(self.water_heights) - 2,
                max(0, int((wave_world_x - self.sea_start_x()) / WATER_STEP)),
            )
            next_wave_top = self.sea_wave_top(wave_world_x + WATER_STEP)
            slope = next_wave_top - wave_top
            next_top = self.sea_wave_top(wave_world_x + wave_step)
            velocity = (
                abs(self.water_velocities[wave_index])
                * self.water_amplitude(wave_world_x)
            )
            # Depth bands and moving glints give the water a clear near-field
            # surface, while the broken crest follows the actual wave slope.
            band_y = min(HEIGHT - 1, wave_top + 4 + (wave_world_x // 20) % 3)
            pyxel.line(wave_x, band_y, wave_x + wave_step - 1, band_y, 5)
            if (wave_world_x // 12 + self.water_time // 5) % 7 < 3:
                glint_y = min(HEIGHT - 1, wave_top + 10 + (wave_world_x // 16) % 5)
                pyxel.line(wave_x + 1, glint_y, wave_x + 3, glint_y, 12)
            if (wave_world_x // 8 + self.water_time // 3) % 5 == 0:
                deep_y = min(HEIGHT - 1, wave_top + 20 + (wave_world_x // 24) % 7)
                pyxel.line(wave_x, deep_y, wave_x + 2, deep_y, 5)
            breaking = slope < -0.42 or (slope < -0.18 and velocity > 0.20)
            if breaking:
                foam_y = max(0, wave_top - 1)
                pyxel.line(wave_x, foam_y, wave_x + wave_step, foam_y, 7)
                if velocity > 0.32 or slope < -0.7:
                    spray_x = wave_x + (self.water_time // 2 + wave_world_x) % wave_step
                    pyxel.pset(spray_x, max(0, foam_y - 1 - int(velocity * 2)), 7)
            if slope < -0.6:
                inner_y = min(HEIGHT - 2, wave_top + 8)
                pyxel.line(wave_x, inner_y, wave_x + wave_step - 1, inner_y + 1, 6)
            elif next_top - wave_top > 1:
                pyxel.line(wave_x, wave_top + 2, wave_x + 2, wave_top + 3, 5)
        if not self.is_sea_mission():
            return
        platform_screen = int(self.level_goal_x() - self.camera)
        if -PLATFORM_HALF_WIDTH < platform_screen < WIDTH + PLATFORM_HALF_WIDTH:
            platform_left = platform_screen - PLATFORM_HALF_WIDTH
            platform_width = PLATFORM_HALF_WIDTH * 2 + 1
            pyxel.rect(platform_left, GROUND_Y - 5, platform_width, 3, 4)
            pyxel.line(
                platform_left,
                GROUND_Y - 2,
                platform_left + platform_width - 1,
                GROUND_Y - 2,
                10,
            )

    def draw_motorway(self):
        for i in range(self.powerline_count()):
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

    def draw_trees(self, night, hx, hy):
        # Tree obstacles create a climb-and-descend route to the destination.
        for tree_x, tree_height in self.level_obstacles():
            sx = int(tree_x - self.camera)
            if -16 <= sx <= WIDTH + 16:
                tree_top = GROUND_Y - tree_height
                pyxel.rect(sx - 2, tree_top + 12, 5, tree_height - 12, 1 if night else 4)
                pyxel.circ(sx, tree_top + 9, 12, 1 if night else 3)
                pyxel.circ(sx - 8, tree_top + 16, 9, 1 if night else 3)
                pyxel.circ(sx + 8, tree_top + 16, 9, 1 if night else 3)
                pyxel.circ(sx, tree_top + 15, 7, 1 if night else 11)
                if night:
                    ox, oy = self.spotlight_origin()
                    self.paint_rect_lit(sx - 2, tree_top + 12, 5, tree_height - 12, 4, ox, oy)
                    self.paint_circle_lit(sx, tree_top + 9, 12, 3, ox, oy)
                    self.paint_circle_lit(sx - 8, tree_top + 16, 9, 3, ox, oy)
                    self.paint_circle_lit(sx + 8, tree_top + 16, 9, 3, ox, oy)
                    self.paint_circle_lit(sx, tree_top + 15, 7, 11, ox, oy)

    def paint_rect_lit(self, x, y, width, height, color, ox, oy):
        for py in range(y, y + height):
            for px in range(x, x + width):
                if self.in_spotlight(px, py, ox, oy):
                    pyxel.pset(px, py, color)

    def paint_circle_lit(self, cx, cy, radius, color, ox, oy):
        for py in range(cy - radius, cy + radius + 1):
            half_width = int(math.sqrt(max(0, radius * radius - (py - cy) ** 2)))
            for px in range(cx - half_width, cx + half_width + 1):
                if self.in_spotlight(px, py, ox, oy):
                    pyxel.pset(px, py, color)

    def draw_pads(self, night, hx, hy):
        pads = [(START_PAD_X, "A")]
        if not self.is_rescue_mission():
            pads.append((self.level_goal_x(), "H"))
        ox, oy = self.spotlight_origin() if night else (0, 0)
        for pad_x, label in pads:
            pad_screen = int(pad_x - self.camera)
            if -40 < pad_screen < WIDTH + 40:
                if self.is_rescue_mission() and label == "A":
                    self.draw_ship(pad_screen)
                    continue
                pad_visible = not night or self.in_spotlight(
                    pad_screen, GROUND_Y - 14, ox, oy
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
                pyxel.text(pad_screen - 2, GROUND_Y - 14, label, 7 if pad_visible else 1)

    def draw_ship(self, pad_screen):
        pyxel.rect(pad_screen - 28, GROUND_Y - 1, 56, HEIGHT - GROUND_Y + 1, 5)
        pyxel.rect(pad_screen - 22, GROUND_Y - 4, 44, 3, 6)
        pyxel.rect(pad_screen - 20, GROUND_Y - 14, 2, 10, 7)
        pyxel.rect(pad_screen + 12, GROUND_Y - 11, 10, 7, 13)
        pyxel.rect(pad_screen + 14, GROUND_Y - 9, 6, 3, 7)
        pyxel.text(pad_screen - 8, GROUND_Y - 12, "A", 7)

    def draw_landing_vehicles(self):
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

    def draw_rescue(self, hx, hy):
        if not self.survivor:
            target_screen = int(self.rescue_target_x() - self.camera)
            if -20 < target_screen < WIDTH + 20:
                bob = self.sea_wave_top(self.rescue_target_x()) - 5
                pyxel.rect(target_screen - 1, bob, 3, 4, 8)
                pyxel.pset(target_screen, bob - 2, 7)
                pyxel.line(target_screen - 3, bob + 2, target_screen + 3, bob + 2, 8)
        hook_sx = int(self.hook_x - self.camera)
        hook_sy = int(self.hook_y)
        pyxel.line(hx, hy + 4, hook_sx, hook_sy, 7)
        if self.survivor:
            pyxel.rect(hook_sx - 1, hook_sy, 3, 4, 8)
            pyxel.pset(hook_sx, hook_sy - 2, 7)
        else:
            pyxel.circ(hook_sx, hook_sy, 2, 10)

    def draw_state_overlay(self):
        if self.state == "intro":
            self.draw_intro()
        elif self.state == "mission_select":
            self.draw_mission_select()
        elif self.state in ("ready", "landed"):
            self.draw_takeoff_card()
        elif self.state == "tutorial_complete":
            self.draw_debrief("TUTORIAL COMPLETE!", self.clear_hint())
        elif self.state == "mission_complete":
            title = (
                "CAMPAIGN COMPLETE!"
                if self.level_index() == len(LEVELS) - 1
                else "MISSION COMPLETE!"
            )
            self.draw_debrief(title, self.clear_hint())
        elif self.state == "crashed":
            self.draw_crash_card()

    def draw_takeoff_card(self):
        info = LEVEL_INFO[self.level]
        hint = "SPACE TO TAKE OFF" if self.state == "ready" else "SPACE TO FLY AGAIN"
        lines = [(info["title"], 10), (info["brief"], 7)]
        best = self.bests.get(self.level)
        if best:
            lines.append((format_score("BEST", best), 11))
        lines.append((hint, 7))
        self.draw_text_panel(lines, 50)

    def draw_debrief(self, title, hint):
        lines = [(title, 10)]
        if self.last_result:
            lines.append((format_score("TIME", self.last_result), 7))
        best = self.bests.get(self.level)
        if best:
            lines.append((format_score("BEST", best), 11))
        lines.append((hint, 11))
        self.draw_text_panel(lines, 48)

    def draw_crash_card(self):
        reason = CRASH_LINES.get(self.crash_reason, "CRASH")
        self.draw_text_panel([(reason, 8), ("SPACE RESTART", 7)], 46)

    def draw_text_panel(self, lines, y):
        width = max(len(text) for text, _color in lines) * 4 + 16
        width = min(WIDTH - 12, max(width, 108))
        height = 8 + 9 * len(lines)
        x = (WIDTH - width) // 2
        pyxel.rect(x, y, width, height, 0)
        pyxel.rectb(x, y, width, height, 7)
        for index, (text, color) in enumerate(lines):
            pyxel.text((WIDTH - len(text) * 4) // 2, y + 5 + index * 9, text, color)

    def draw_mission_select(self):
        pyxel.cls(1)
        pyxel.rect(8, 4, 240, 152, 0)
        pyxel.rectb(8, 4, 240, 152, 7)
        title = "MISSION SELECT"
        pyxel.text((WIDTH - len(title) * 4) // 2, 8, title, 10)
        for index, level in enumerate(LEVELS):
            info = LEVEL_INFO[level]
            column = index % 2
            row = index // 2
            self.draw_mission_card(
                index,
                16 + column * 116,
                22 + row * 28,
                info["title"] if level == "tutorial" else "MISSION %d" % index,
                info["card"],
                self.is_unlocked(index),
            )
        hint = "UP/DOWN SELECT  SPACE LAUNCH"
        pyxel.text((WIDTH - len(hint) * 4) // 2, 142, hint, 6)

    def draw_mission_card(self, index, x, y, title, subtitle, unlocked):
        selected = self.selected_mission == index
        border = 10 if selected else 5
        pyxel.rectb(x, y, 108, 24, border)
        marker = ">" if selected else " "
        status = subtitle if unlocked else "LOCKED"
        pyxel.text(x + 7, y + 4, marker + " " + title, 10 if unlocked else 13)
        pyxel.text(x + 15, y + 14, status, 7 if unlocked else 8)

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
        altitude, max_altitude, burn_altitude = self.altitude_geometry()
        in_burn = self.state == "flying" and self.y < HIGH_ALTITUDE_Y
        pyxel.text(10, 11, "ALT", 9 if in_burn else 7)
        pyxel.rect(31, 11, 52, 6, 5)
        altitude_ratio = altitude / max_altitude
        altitude_warning_x = 31 + int(52 * 0.85)
        burn_x = 31 + int(52 * burn_altitude / max_altitude)
        altitude_marker = 31 + int(50 * altitude_ratio)
        pyxel.line(burn_x, 17, 83, 17, 9)
        pyxel.line(burn_x, 11, burn_x, 17, 9)
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
        distance = max(0, int(abs(self.distance_target() - self.x)))
        pyxel.text(166, 2, "DST:%04d" % distance, 10)
        burn_hot = self.state == "flying" and (
            self.y < HIGH_ALTITUDE_Y
            or self.rotor_lift > 0.95
            or self.y <= HEIGHT * 0.15
        )
        pyxel.text(210, 11, "BRN:%1.1f" % self.fuel_burn_rate, 8 if burn_hot else 6)
        pyxel.rect(0, 24, WIDTH, 12, 1)
        self.draw_warning_pattern(altitude_warning_x, 11, 52 - int(52 * 0.85), 6)
        pyxel.text(10, 27, "WIND", 7)
        pyxel.text(42, 27, "%+.1f" % self.wind, 6)
        pyxel.text(78, 27, "SPD:%+.1f" % self.vx, 6)
        if self.is_rescue_mission() and self.state == "flying":
            if self.survivor:
                pyxel.text(166, 27, "LOAD", 11)
            else:
                pyxel.text(
                    166,
                    27,
                    "RES:%02d%%" % int(self.rescue_progress * 100 / RESCUE_FRAMES),
                    7,
                )
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
        if self.y < HIGH_ALTITUDE_Y:
            return "TOO HIGH. FUEL BURNS FAST"
        if self.x < 95:
            return "STEP 1: HOLD UP TO LIFT"
        if self.x < 145:
            return "STEP 2: STEER WITH LEFT / RIGHT"
        if self.x < 205:
            return "STEP 3: CLEAR THE TREES"
        return "STEP 4: LAND ON THE H PAD"


ChopperGame()
