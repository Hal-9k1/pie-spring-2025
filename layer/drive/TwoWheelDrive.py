from actuators import Motor
from layer import Layer
from mechanisms import Wheel
from task import AxialMovementTask, TankDriveTask, TurnTask, UnsupportedTaskError
from units import convert
from math import copysign
from LayerSetupInfo import *


class TwoWheelDrive(Layer):
    """Drive layer for a two-wheel drive robot."""

    LEFT_DRIVE_MOTOR_NAME = "left_front_drive"
    RIGHT_DRIVE_MOTOR_NAME = "right_front_drive"
    WHEEL_RADIUS = 0.42
    GEAR_RATIO = 1
    WHEEL_SPAN_RADIUS = convert(15.0 / 2, "in", "m")
    SLIPPING_CONSTANT = 1

    def __init__(self):
        self.left_wheel = None
        self.right_wheel = None
        self.left_start_pos = 0
        self.right_start_pos = 0
        self.left_goal_delta = 0
        self.right_goal_delta = 0
        self.current_task_done = True

    def setup(self, init_info):
        self.right_wheel = Motor(setup_info.get_robot(), setup_info.get_logger_provider(), self.RIGHT_DRIVE_MOTOR_NAME,
                                'insert a or b here')
        self.left_wheel = Motor(setup_info.get_robot(), setup_info.get_logger_provider(), self.LEFT_DRIVE_MOTOR_NAME,
                                'insert a or b here')
        self.left_start_pos = 0
        self.right_start_pos = 0
        self.left_goal_delta = 0
        self.right_goal_delta = 0
        self.current_task_done = True

    def is_task_done(self):
        return self.current_task_done

    def update(self, completed):
        left_delta = self.left_wheel.get_distance() - self.left_start_pos
        left_done = (left_delta < 0) == (self.left_goal_delta < 0) and abs(left_delta) >= abs(self.left_goal_delta)
        right_delta = self.right_wheel.get_distance() - self.right_start_pos
        right_done = (right_delta < 0) == (self.right_goal_delta < 0) and abs(right_delta) >= abs(self.right_goal_delta)

        is_teleop_task = self.left_goal_delta == 0 and self.right_goal_delta == 0
        self.current_task_done = left_done and right_done

        if self.current_task_done and not is_teleop_task:
            self.left_wheel.set_velocity(0)
            self.right_wheel.set_velocity(0)

        return None  # Placeholder for adaptive velocity control

    def accept_task(self, task):
        if isinstance(task, AxialMovementTask):
            self.left_goal_delta = task.distance * self.GEAR_RATIO * self.SLIPPING_CONSTANT
            self.right_goal_delta = task.distance * self.GEAR_RATIO * self.SLIPPING_CONSTANT
        elif isinstance(task, TurnTask):
            self.left_goal_delta = -task.angle * self.WHEEL_SPAN_RADIUS * self.GEAR_RATIO * self.SLIPPING_CONSTANT
            self.right_goal_delta = task.angle * self.WHEEL_SPAN_RADIUS * self.GEAR_RATIO * self.SLIPPING_CONSTANT
        elif isinstance(task, TankDriveTask):
            self.left_goal_delta = 0
            self.right_goal_delta = 0
            max_abs_power = max(abs(task.left), abs(task.right), 1)
            self.left_wheel.set_velocity(task.left / max_abs_power)
            self.right_wheel.set_velocity(task.right / max_abs_power)
            return
        else:
            raise UnsupportedTaskError(self, task)

        self.current_task_done = False
        self.left_start_pos = self.left_wheel.get_distance()
        self.right_start_pos = self.right_wheel.get_distance()
        self.left_wheel.set_velocity(copysign(1, self.left_goal_delta))
        self.right_wheel.set_velocity(copysign(1, self.right_goal_delta))
