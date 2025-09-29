"""
----------------------------------
Documented controller for the myoelectric-driven sterilization task.
- Two-channel EMG → intents (with hysteresis, debounce, cooldown)
- Finite-state machine (FSM) for safe, deterministic motions
- Modular motion primitives and centralized constants

Replace SDK stubs with Quanser QArm/QLabs Python bindings in your environment.
"""

from dataclasses import dataclass
from enum import Enum, auto
from time import time, sleep
from typing import Tuple

# ===================== SDK STUBS (REPLACE IN YOUR ENV) =====================
class QArm:
    """Stub for type hints. Replace with Quanser QArm binding."""
    def move_pose(self, x, y, z, yaw=0.0, pitch=0.0, roll=0.0, speed=0.5): ...
    def open_gripper(self): ...
    def close_gripper(self): ...
    def home(self): ...
    def read_pose(self) -> Tuple[float, float, float, float, float, float]: ...

def read_emg_channels() -> Tuple[float, float]:
    """Return normalized EMG values in [0,1] for two channels.
    Replace with your DAQ/serial/QLabs acquisition code.
    """
    return (0.0, 0.0)
# ===========================================================================

# ------------------------------ Utilities ----------------------------------
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

# ----------------------------- Parameters ----------------------------------
@dataclass(frozen=True)
class Thresholds:
    emg_on: float = 0.65      # contraction threshold
    emg_off: float = 0.35     # release threshold (hysteresis)
    deadband: float = 0.05    # ignore tiny fluctuations
    debounce_s: float = 0.15  # gesture must persist this long
    cooldown_s: float = 0.35  # min time between intents
    longpress_s: float = 1.20 # sustained contraction → ABORT

@dataclass(frozen=True)
class Speeds:
    move: float = 0.6
    approach: float = 0.4
    retract: float = 0.6
    door: float = 0.3
    grip_time_s: float = 0.50

@dataclass(frozen=True)
class Waypoints:
    # Tune to your workspace; units in meters
    home: Tuple[float, float, float] = (0.38, 0.00, 0.20)
    autoclave: Tuple[float, float, float] = (0.45, -0.12, 0.12)
    bins: Tuple[Tuple[float, float, float], ...] = (
        (0.30,  0.18, 0.08),  # R
        (0.32,  0.00, 0.08),  # G
        (0.30, -0.18, 0.08),  # B
    )

# --------------------------- FSM Definitions -------------------------------
class State(Enum):
    IDLE = auto()
    SELECT_BIN = auto()
    APPROACH = auto()
    GRIP = auto()
    LIFT = auto()
    TRANSIT = auto()
    OPEN_AUTOCLAVE = auto()
    PLACE = auto()
    CLOSE_AUTOCLAVE = auto()
    HOME = auto()
    ABORT = auto()

class Intent(Enum):
    NONE = auto()
    START = auto()       # also used to cycle bin selection
    GRIP = auto()
    RELEASE = auto()
    OPEN_DOOR = auto()
    CLOSE_DOOR = auto()
    ABORT = auto()

# --------------------------- Gesture Decoder --------------------------------
class GestureDecoder:
    """Two-channel EMG → high-level intents with hysteresis, debounce, cooldown, long-press."""
    def __init__(self, thresholds: Thresholds):
        self.t = thresholds
        self._on = [False, False]
        self._t_change = [0.0, 0.0]
        self._last_intent_time = 0.0
        self._press_start = [None, None]

    def update(self, ch1: float, ch2: float) -> None:
        now = time()
        for i, v in enumerate((ch1, ch2)):
            # deadband
            v = 0.0 if abs(v) < self.t.deadband else v
            # hysteresis
            if not self._on[i] and v >= self.t.emg_on:
                self._on[i] = True
                self._t_change[i] = now
                self._press_start[i] = now
            elif self._on[i] and v <= self.t.emg_off:
                self._on[i] = False
                self._t_change[i] = now
                self._press_start[i] = None

    def intent(self) -> Intent:
        now = time()
        # cooldown
        if now - self._last_intent_time < self.t.cooldown_s:
            return Intent.NONE

        # long-press abort on channel 2
        if self._press_start[1] is not None and (now - self._press_start[1]) >= self.t.longpress_s:
            self._last_intent_time = now
            return Intent.ABORT

        # debounced contractions
        active = [self._on[i] and (now - self._t_change[i] >= self.t.debounce_s) for i in (0,1)]

        # mapping
        if active[0] and not active[1]:
            self._last_intent_time = now
            return Intent.START              # cycle/select/start
        if active[1] and not active[0]:
            self._last_intent_time = now
            return Intent.GRIP               # press to grip, subsequent press interpreted as release in state logic
        if active[0] and active[1]:
            self._last_intent_time = now
            return Intent.OPEN_DOOR          # toggled in state logic
        return Intent.NONE

# -------------------------- Controller (FSM) --------------------------------
class SterilizationController:
    def __init__(self, arm: QArm, wp: Waypoints, spd: Speeds, thresholds: Thresholds):
        self.arm = arm
        self.wp = wp
        self.spd = spd
        self.dec = GestureDecoder(thresholds)
        self.state = State.IDLE
        self.selected_bin = 0
        self.door_open = False
        self._last_grip_action_close = False

    # ---- Motion primitives
    def move_to(self, xyz: Tuple[float, float, float], speed: float) -> None:
        x, y, z = xyz
        self.arm.move_pose(x, y, z, speed=clamp(speed, 0.1, 1.0))

    def grip(self, close: bool) -> None:
        (self.arm.close_gripper if close else self.arm.open_gripper)()
        sleep(self.spd.grip_time_s)
        self._last_grip_action_close = close

    def toggle_door(self) -> None:
        # Replace with actual IO/servo control; we dwell for effect
        sleep(0.4 if not self.door_open else 0.3)
        self.door_open = not self.door_open

    # ---- State machine tick
    def tick(self, intent: Intent) -> None:
        s = self.state

        if intent == Intent.ABORT:
            self.state = State.ABORT

        if s == State.IDLE:
            if intent == Intent.START:
                self.state = State.SELECT_BIN

        elif s == State.SELECT_BIN:
            if intent == Intent.START:
                self.selected_bin = (self.selected_bin + 1) % len(self.wp.bins)
            elif intent == Intent.GRIP:
                self.state = State.APPROACH

        elif s == State.APPROACH:
            self.move_to(self.wp.bins[self.selected_bin], self.spd.approach)
            self.state = State.GRIP

        elif s == State.GRIP:
            if intent == Intent.GRIP:
                # first press → close, next press in PLACE state will open
                self.grip(close=True)
                self.state = State.LIFT

        elif s == State.LIFT:
            x, y, z = self.wp.bins[self.selected_bin]
            self.move_to((x, y, z + 0.10), self.spd.retract)
            self.state = State.TRANSIT

        elif s == State.TRANSIT:
            self.move_to(self.wp.autoclave, self.spd.move)
            self.state = State.OPEN_AUTOCLAVE

        elif s == State.OPEN_AUTOCLAVE:
            if intent == Intent.OPEN_DOOR:
                self.toggle_door()
                self.state = State.PLACE

        elif s == State.PLACE:
            ax, ay, az = self.wp.autoclave
            self.move_to((ax, ay, az - 0.05), self.spd.approach)
            # release on next grip intent
            if intent == Intent.GRIP and self._last_grip_action_close:
                self.grip(close=False)
                self.state = State.CLOSE_AUTOCLAVE

        elif s == State.CLOSE_AUTOCLAVE:
            if self.door_open and intent == Intent.OPEN_DOOR:
                self.toggle_door()
                self.state = State.HOME

        elif s == State.HOME:
            self.move_to(self.wp.home, self.spd.move)
            self.state = State.IDLE

        elif s == State.ABORT:
            try:
                self.arm.home()
            finally:
                self.state = State.IDLE

    # ---- Main loop
    def run(self, runtime_s: float = 180.0, loop_hz: float = 50.0) -> None:
        t0 = time()
        dt = 1.0 / max(1.0, loop_hz)
        while time() - t0 < runtime_s:
            ch1, ch2 = read_emg_channels()
            self.dec.update(ch1, ch2)
            intent = self.dec.intent()
            self.tick(intent)
            sleep(dt)

# ------------------------------ Entrypoint ----------------------------------
if __name__ == "__main__":
    # Replace QArm() with actual sim/hardware binding
    arm = QArm()
    thresholds = Thresholds()
    speeds = Speeds()
    waypoints = Waypoints()
    ctl = SterilizationController(arm, waypoints, speeds, thresholds)
    try:
        ctl.run()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            arm.home()
        except Exception:
            pass
