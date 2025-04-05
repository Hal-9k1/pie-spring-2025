import math
import time


class Wheel:
    """Encapsulates a Motor attached to a wheel that can calculate distance travelled given the
    motor's ticks per rotation and the wheel's radius."""
    def __init__(self, logger, motor, radius, ticks_per_rotation):
        self._logger = logger
        self._motor = motor
        self._radius = radius
        self._ticks_per_rot = ticks_per_rotation
    def get_distance(self):
        """Interpreting the motor as being attached to a wheel, converts the encoder readout of the
        motor to a distance traveled by the wheel."""
        return self._motor.get_angle(self._ticks_per_rot) * self._radius
    def set_velocity(self, velocity):
        """Sets the velocity of the underlying motor."""
        self._motor.set_velocity(velocity)


class Arm:
    """Encapsulates a Motor attached to an arm that can calculate the height of the arm's end
    relative to the motor and detect out-of-bounds movement given the motor's ticks per rotation,
    the arm's length, and the maximum angle."""
    def __init__(self, motor, length, ticks_per_rotation, max_height):
        self._motor = motor
        self._length = length
        self._ticks_per_rot = ticks_per_rotation
        self._max_height = max_height
        self._zero_height = 0 # bootstrap for get_height
        self._zero_height = self.get_height()
    def get_height(self):
        """Interpreting the motor as being attached to an arm, converts the encoder readout of the
        motor to the vertical position of the arm's tip relative to the motor."""
        return (math.sin(self._motor.get_angle(self._ticks_per_rot)) * self._length
            - self._zero_height)
    def set_velocity(self, velocity):
        """Sets the velocity of the underlying motor."""
        if not velocity and self._motor.get_velocity():
            self._motor.set_position(self._motor.get_encoder())
            pass
        elif not velocity:
            #self._motor.hold_position()
            pass
        self._motor.set_velocity(velocity)
    def get_normalized_position(self):
        """Returns a number in the range [0, 1] where 0 is linearly mapped to an encoder position of
        0 and 1 is linearly mapped to the encoder position corrosponding to the arm's maximum
        angle."""
        return self.get_height() / (self._max_height - self._zero_height)
    def is_velocity_safe(self, velocity):
        """Checks if the arm is currently within its defined safe bounds. If in of bounds, returns
        True. Otherwise returns whether the given velocity is in the right direction to return the
        arm to its safe bounds."""
        height = self.get_height()
        if height > self._max_height:
            return velocity < 0
        elif height < 0:
            return velocity > 0
        else:
            return True


class Hand:
    """A Motor connected to a hand that can toggle its open/closed state given the maximum width
    and hand length, optionally stopping when encountering resistance."""
    _MAX_HISTORY_LENGTH = 40000
    _STRUGGLE_THRESHOLD = 0.02 # meters. hand must move this far in struggle_duration seconds.
    def __init__(self, motor, ticks_per_rotation, max_width, hand_offset, hand_length,
            struggle_duration, start_open):
        # disable struggle checking if struggle_duration == 0
        self._motor = motor
        self._ticks_per_rot = ticks_per_rotation
        self._hand_offset = hand_offset
        self._hand_length = hand_length
        self._struggle_duration = struggle_duration
        self._init_enc = self._motor.get_encoder()
        max_enc = ((math.asin(max_width / 2 / hand_length) + math.asin(hand_offset / hand_length))
            / 2 / math.pi * ticks_per_rotation)
        if start_open:
            self._open_enc = self._init_enc
            self._close_enc = self._init_enc - max_enc
        else:
            self._open_enc = self._init_enc + max_enc
            self._close_enc = self._init_enc
        self._state = start_open
        self._width_history = [0, None] * self._MAX_HISTORY_LENGTH
        self._hist_pos = 0
        self._finished = True
        #print(f"Inititlized hand. open_enc = {self._open_enc} close_enc = {self._close_enc} "
        #    + f"init_enc = {self._init_enc}")
    def toggle_state(self):
        """Swaps the hand's state between open and closed and starts moving accordingly."""
        self._state = not self._state
        #print("about to toggle state")
        self._finished = False
        #print(f"Toggled hand state to {self._state} hand velocity {self._motor.get_velocity()}")
    def tick(self):
        """Stops the hand's movement if necessary. Returns whether the hand has just finished
        moving."""
        if not self._finished:
            enc = self._motor.get_encoder()
            reached_end = (self._state and enc > self._open_enc) or (not self._state and
                enc < self._close_enc)
            # don't check if struggle duration is 0
            if self._struggle_duration:
                lookbehind = self._get_hist_lookbehind()
                struggling = (bool(lookbehind) and abs(lookbehind - self._get_width())
                    < self._STRUGGLE_THRESHOLD)
            else:
                struggling = False
            if reached_end or struggling:
                self._finished = True
                self._motor.set_velocity(0)
                return True
            self._record_history()
            self._motor.set_velocity(self._get_hand_speed() * (1 if self._state else -1))
        return False
    def _get_width(self):
        angle = (self._motor.get_encoder() - self._init_enc) / self._ticks_per_rot * 2 * math.pi
        return math.sin(angle) * self._hand_length
    def _get_hand_speed(self):
        mid = (self._open_enc + self._close_enc) / 2
        enc = self._motor.get_encoder()
        # -1 furthest from goal, 0 at midpoint, 1 closest to goal:
        nearness = 2 * (enc - mid) / mid * (-1 if self._state else 1)
        return (1 - max(nearness, 0)) * 0.125 + 0.375
    def _get_hist_time(self, i):
        return self._width_history[i * 2]
    def _get_hist_width(self, i):
        return self._width_history[i * 2 + 1]
    def _set_hist_time(self, i, x):
        self._width_history[i * 2] = x
    def _set_hist_width(self, i, x):
        self._width_history[i * 2 + 1] = x
    def _record_history(self):
        self._set_hist_time(self._hist_pos, time.time())
        self._set_hist_width(self._hist_pos, self._get_width())
        self._hist_pos = (self._hist_pos + 1) % self._MAX_HISTORY_LENGTH
    def _get_hist_lookbehind(self):
        min_idx = self._hist_pos
        max_idx = self._hist_pos + self._MAX_HISTORY_LENGTH - 1
        goal_time = time.time() - self._struggle_duration
        while True:
            mid_idx = math.floor((min_idx + max_idx) / 2)
            hist_idx = mid_idx % self._MAX_HISTORY_LENGTH
            if self._get_hist_time(hist_idx) < goal_time:
                min_idx = mid_idx + 1
            elif self._get_hist_time(hist_idx) > goal_time:
                max_idx = mid_idx - 1
            if min_idx == max_idx:
                return self._get_hist_width(hist_idx)
