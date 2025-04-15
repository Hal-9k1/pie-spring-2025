import math
import time


class Motor:
    """Wraps a PiE KoalaBear-controlled motor."""
    def __init__(self, robot, logger, controller_id, motor):
        self._controller = controller_id
        self._motor = motor
        self._robot = robot
        self._is_inverted = False
        self._logger = logger
    def set_invert(self, invert):
        #self._set("invert", invert)
        self._set("invert", False)
        self._is_inverted = invert
        return self
    def set_deadband(self, deadband):
        self._set("deadband", deadband)
        return self
    def set_pid(self, p, i, d):
        if not (p and i and d):
            self._set("pid_enabled", False) # if unspecified or incomplete set, disable
            return self
        self._set("pid_enabled", True)
        self._set("pid_kp", p)
        self._set("pid_ki", i)
        self._set("pid_kd", d)
        return self
    def set_velocity(self, velocity):
        self._set("velocity", velocity * (-1 if self._is_inverted else 1))
        return self
    def get_velocity(self):
        return self._get("velocity")
    def get_encoder(self):
        return self._get("enc") * (-1 if self._is_inverted else 1)
    def get_angle(self, ticks_per_rot):
        return self.get_encoder() / ticks_per_rot * 2 * math.pi
    def reset_encoder(self):
        self._set("enc", 0)
    def _set(self, key, value):
        self._robot.set_value(self._controller, f"{key}_{self._motor}", value)
    def _get(self, key):
        return self._robot.get_value(self._controller, f"{key}_{self._motor}")


class PidMotor(Motor):
    """Adds custom PID control to a Motor since PiE's implementation is weird."""
    def __init__(self, robot, controller_id, motor):
        super().__init__(robot, controller_id, motor)
        super().set_pid(None, None, None)
        self._clear_samples()
        self._max_samples = 200
        self._derivative_samples = 20
        self._held_position = None
        self._last_timestamp = None
        self._coeffs = None
    def set_velocity(self, velocity):
        self._held_position = None # force clear on next hold_position call
        super().set_velocity(velocity)
        return self
    def set_pid(self, p, i, d):
        if not (p and i and d):
            self._coeffs = None # unspecified or incomplete set
        else:
            self._coeffs = (p, i, d)
        return self
    def set_position(self, pos):
        self._clear_samples()
        self._held_position = pos
        return self
    def hold_position(self):
        if not self._coeffs:
            raise RuntimeError("PID coefficients not set.")
        self._record_sample()
        super().set_velocity(self._calc_proportional(self._held_position)
            + self._calc_integral(self._held_position) + self._calc_derivative())
        return self
    def _record_sample(self):
        self._enc_samples[self._cur_sample] = self.get_encoder()
        timestamp = time.time()
        self._time_samples[self._cur_sample] = timestamp - (self._last_timestamp or 0)
        self._last_timestamp = timestamp
        self._cur_sample += 1
        if self._cur_sample == self._max_samples:
            self._cur_sample = 0
    def _clear_samples(self):
        self._enc_samples = []
        self._time_samples = []
        self._cur_sample = 0
    def _calc_proportional(self):
        return self._coeffs[0] * (self.get_encoder() - self._held_position)
    def _calc_integral(self):
        return self._coeffs[1] * sum((enc - self._held_position) * time for (enc, time)
            in zip(self._enc_samples, self._time_samples))
    def _calc_derviative(self):
        avg_deriv = sum(
            ((self._enc_samples[self._cur_sample] - self._enc_samples[self._cur_sample - i])
            / (self._time_samples[self._cur_sample] - self._time_samples[self._cur_sample - i]))
            for i in range(self._deriv_samples)) / self._deriv_samples
        return self._coeffs[2] * avg_deriv


class MotorPair(Motor):
    """Drives a pair of Motors together as if they were one."""
    def __init__(self, robot, controller_id, motor_suffix, paired_controller_id,
        paired_motor_suffix, paired_motor_inverted):
        super().__init__(robot, controller_id, motor_suffix)
        self._paired_motor = Motor(robot, paired_controller_id,
            paired_motor_suffix).set_invert(paired_motor_inverted)
        self._inverted = False
    def set_invert(self, invert):
        if invert != self._inverted:
            self._inverted = invert
            super().set_invert(not self._get("invert"))
            self._paired_motor.set_invert(not self._paired_motor.get("invert"))
        return self
    def set_deadband(deadband):
        super().set_deadband(self, deadband)
        self._paired_motor.set_deadband(deadband)
        return self
    def set_pid(self, p, i, d):
        super().set_pid(p, i, d)
        self._paired_motor.set_pid(p, i, d)
        return self
    def set_velocity(self, velocity):
        super().set_velocity(velocity)
        self._paired_motor.set_velocity(velocity)
        return self


class Servo:
    """Wraps a PiE servo."""
    def __init__(self, robot, controller, servo):
        self._controller = controller
        self._servo = servo
        self._robot = robot
    def set_position(self, position):
        self._robot.set_value(self._controller, "servo" + self._servo, position)
