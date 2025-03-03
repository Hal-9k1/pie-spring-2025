import time
import logging

logger = logging.getLogger(__name__)


class MockRobot:
    """Simulates a robot with connected peripherals.

    A Robot-like object that simulates a limited number of connected peripherals. A limit for each
    type of peripheral is supplied upon initialization, and peripherals are "initialized" on their
    first use or raise an error if this would break the limit for that type. Simulated KoalaBear
    motor controllers will update encoder positions linearly from motor velocities.
    """

    _default_device_properties = {
        "koalabear": {
            "velocity_a": 0.0,
            "deadband_a": 0.05,
            "invert_a": False,
            "pid_enabled_a": True,
            "pid_kp_a": 0.05,
            "pid_ki_a": 0.035,
            "pid_kd_a": 0.0,
            "enc_a": 0,
            "velocity_b": 0.0,
            "deadband_b": 0.05,
            "invert_b": False,
            "pid_enabled_b": True,
            "pid_kp_b": 0.05,
            "pid_ki_b": 0.035,
            "pid_kd_b": 0.0,
            "enc_b": 0
        },
        "servocontroller": {
            "servo0": 0.0,
            "servo1": 0.0
        }
    }

    def __init__(self, max_devices, motor_ticks_per_sec=2000, start_pos="left"):
        logger.warn("NOTICE: MockRobot instance constructed.")
        self._devices = {}
        self._device_types = {}
        self._max_devices = max_devices
        self._device_counts = {}
        self._motor_ticks_per_sec = motor_ticks_per_sec
        self.start_pos = start_pos
        for device_type in self._default_device_properties:
            self._device_counts[device_type] = 0

    def get_value(self, device_id, value_name):
        self._check_property(device_id, value_name)
        if self._device_types[device_id] == "koalabear":
            self._update_koalabear(device_id)
        logger.debug(f"get:{device_id},{value_name}={self._devices[device_id][value_name]}")
        return self._devices[device_id][value_name]

    def set_value(self, device_id, value_name, value):
        self._check_property(device_id, value_name)
        logger.info(f"set:{device_id},{value_name}={str(value)}")
        if self._device_types[device_id] == "koalabear":
            self._update_koalabear(device_id)
        expected_type = type(self._devices[device_id][value_name])
        if expected_type == float and type(value) == int:
            value = float(value)
        if expected_type != type(value):
            raise TypeError(f"Expected value of type {expected_type.__name__} for property"
                f" {value_name}, got {type(value).__name__}.")
        self._devices[device_id][value_name] = value

    def _check_property(self, device_id, value_name):
        if not device_id in self._devices:
            for device_type, default_props in self._default_device_properties.items():
                if value_name in default_props:
                    break # Skips for-else clause
            else:
                raise ValueError(f"Unrecognized device property {value_name}.")
            if not device_type in self._max_devices or (self._device_counts[device_type] >= self._max_devices[device_type]):
                raise ValueError(f"Cannot initialize more devices of type {device_type}. Check the id for typos.")
            self._device_counts[device_type] += 1
            device = {}
            device.update(self._default_device_properties[device_type])
            if device_type == "koalabear":
                device["_LAST_UPDATED"] = time.time()
            self._devices[device_id] = device
            self._device_types[device_id] = device_type
        if not value_name in self._devices[device_id]:
            raise ValueError(f"Property {value_name} not found on device of type {self._device_types[device_id]}.")

    def _update_koalabear(self, device_id):
        device = self._devices[device_id]
        timestamp = time.time()
        dt = timestamp - device["_LAST_UPDATED"]
        device["_LAST_UPDATED"] = timestamp
        if abs(device["velocity_a"]) > 1:
            raise ValueError("Koalabear velocity a is out of bounds.")
        if abs(device["velocity_b"]) > 1:
            raise ValueError("Koalabear velocity b is out of bounds.")
        device["enc_a"] += device["velocity_a"] * dt * self._motor_ticks_per_sec * (-1 if device["invert_a"] else 1)
        device["enc_b"] += device["velocity_b"] * dt * self._motor_ticks_per_sec * (-1 if device["invert_b"] else 1)
