from abc import ABC
from abc import abstractmethod
from log import Logger
import math
import time


class DeviceConf(ABC):
    @abstractmethod
    def can_configure(self, cls) -> bool:
        raise NotImplementedError


class Device(ABC):
    @abstractmethod
    def load_conf(self, robot, conf: DeviceConf, logger: Logger) -> None:
        raise NotImplementedError


class MotorConf:
    def __init__(self, controller_id, channel, invert, encoder_invert,
            internal_gearing, deadband=None, pid=None):
        self._controller = controller_id
        self._channel = channel
        self._invert = invert
        self._encoder_invert = encoder_invert
        self._deadband = deadband
        self._pid = pid

    def can_configure(self, cls):
        return cls == Motor or issubclass(cls, Motor)


class Motor(Device):
    """Wraps a PiE KoalaBear-controlled motor."""

    def load_conf(self, robot, conf, logger):
        self._logger = logger
        self._robot = robot
        self._controller = conf._controller
        self._motor = conf._channel
        self.set_invert(conf._invert)
        self.set_encoder_invert(conf._encoder_invert)
        if conf._deadband != None:
            self.set_deadband(conf._deadband)
        if conf._pid:
            self.set_pid(*conf._pid)
        else:
            self.set_pid(None, None, None)

    def set_invert(self, invert):
        self._set("invert", False)
        self._is_inverted = invert
        return self

    def set_encoder_invert(self, invert):
        self._is_encoder_inverted = invert
        return self

    def set_deadband(self, deadband):
        self._set("deadband", deadband)
        return self

    def set_pid(self, p, i, d):
        if not all(p, i, d):
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
        return (self._get("enc") * (-1 if self._is_inverted else 1)
            * (-1 if self._is_encoder_inverted else 1))

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

    def __init__(self, robot=None, controller_id=None, motor=None, conf=None):
        raise NotImplementedError('Need to change this to use hardware configuration')
        super().__init__(robot, controller_id, motor, conf)
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
        if not all(p, i, d):
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

    def __init__(self, robot=None, controller_id=None, motor_suffix, paired_controller_id,
            paired_motor_suffix, paired_motor_inverted):
        raise NotImplementedError('Need to change this to use hardware configuration')
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


class ServoConf(DeviceConf):
    def __init__(self, controller, channel):
        self._controller = controller
        self._channel = chanenl

    def can_configure(self, cls):
        return cls == Servo


class Servo(Device):
    """Wraps a PiE servo."""

    def load_conf(self, robot, conf, logger):
        self._logger = logger
        self._robot = robot
        self._controller = conf._controller
        self._servo = conf._channel

    def set_position(self, position):
        self._robot.set_value(self._controller, "servo" + self._servo, position)


class DistanceSensorConf(DeviceConf):
    def __init__(self, device_id, noise_threshold):
        self._id = device_id
        self._noise_threshold = noise_threshold

    def can_configure(self, cls):
        return cls == DistanceSensor


class DistanceSensor(Device):
    def load_conf(self, robot, conf, logger):
        self._logger = logger
        self._robot = robot
        self._device = conf._id
        self._low_threshold = self._noise_threshold

    def can_read(self):
        return self.get_distance() > self._low_threshold

    def get_distance(self):
        return self._robot.get_value(self._device, "distance")
