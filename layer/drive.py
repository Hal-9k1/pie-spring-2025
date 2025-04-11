from abc import abstractmethod
from actuators import Motor
from layer import Layer
from layer import LayerSetupInfo
from math import copysign
from mechanisms import Wheel
from task.drive import AxialMovementTask
from task.drive import TankDriveTask
from task.drive import TurnTask
from units import convert


class TwoWheelDrive(Layer):
    """Drive layer for a two-wheel drive robot."""

    LEFT_DRIVE_MOTOR_NAME = 'left_front_drive'
    RIGHT_DRIVE_MOTOR_NAME = 'right_front_drive'
    WHEEL_RADIUS = 0.42
    GEAR_RATIO = 1
    WHEEL_SPAN_RADIUS = convert(15.0 / 2, 'in', 'm')
    SLIPPING_CONSTANT = 1
    INTERNAL_GEARING = 30
    TICKS_PER_REV = 160

    def __init__(self):
        self._left_wheel = None
        self._right_wheel = None
        self._left_start_pos = 0
        self._right_start_pos = 0
        self._left_goal_delta = 0
        self._right_goal_delta = 0
        self._current_task_done = True

    def setup(self, setup_info):
        self._right_wheel = Wheel(
            setup_info.get_logger('Right wheel'),
            Motor(
                setup_info.get_robot(),
                setup_info.get_logger('Right wheel motor'),
                self.RIGHT_DRIVE_MOTOR_NAME,
                'a'
            ),
            self.WHEEL_RADIUS,
            self.INTERNAL_GEARING
        )
        self._left_wheel = Wheel(
            setup_info.get_logger('Left wheel'),
            Motor(
                setup_info.get_robot(),
                setup_info.get_logger('Left wheel motor'),
                self.LEFT_DRIVE_MOTOR_NAME,
                'b'
            ),
            self.WHEEL_RADIUS,
            self.INTERNAL_GEARING
        )
        self._is_direct_control = True
        self._left_start_pos = 0
        self._right_start_pos = 0
        self._left_goal_delta = 0
        self._right_goal_delta = 0
        self._should_request_task = True

    def get_input_tasks(self):
        return {AxialMovementTask, TurnTask, TankDriveTask}

    def get_output_tasks(self):
        return set()

    def process(self, ctx):
        if self._should_request_task:
            ctx.request_task()
        else:
            left_delta = self._left_wheel.get_distance() - self._left_start_pos
            left_done = ((left_delta < 0) == (self._left_goal_delta < 0)
                and abs(left_delta) >= abs(self._left_goal_delta))
            right_delta = self._right_wheel.get_distance() - self._right_start_pos
            right_done = ((right_delta < 0) == (self._right_goal_delta < 0)
                and abs(right_delta) >= abs(self._right_goal_delta))
            if left_done and right_done:
                self._should_request_task = True
                self._left_wheel.set_velocity(0)
                self._right_wheel.set_velocity(0)

    def accept_task(self, task):
        if isinstance(task, TankDriveTask):
            self._should_request_task = True
            max_abs_power = max(abs(task.get_left()), abs(task.get_right()), 1)
            self._left_wheel.set_velocity(task.left / max_abs_power)
            self._right_wheel.set_velocity(task.right / max_abs_power)
        elif isinstance(task, AxialMovementTask):
            self._should_request_task = False
            self._left_goal_delta = task.get_distance() * self.GEAR_RATIO * self.SLIPPING_CONSTANT
            self._right_goal_delta = task.get_distance() * self.GEAR_RATIO * self.SLIPPING_CONSTANT
        elif isinstance(task, TurnTask):
            self._should_request_task = False
            self._left_goal_delta = (-task.get_angle() * self.WHEEL_SPAN_RADIUS * self.GEAR_RATIO
                * self.SLIPPING_CONSTANT)
            self._right_goal_delta = (task.get_angle() * self.WHEEL_SPAN_RADIUS * self.GEAR_RATIO
                * self.SLIPPING_CONSTANT)

        if not self._should_request_task:
            self._left_start_pos = self._left_wheel.get_distance()
            self._right_start_pos = self._right_wheel.get_distance()
            self._left_wheel.set_velocity(copysign(1, self._left_goal_delta))
            self._right_wheel.set_velocity(copysign(1, self._right_goal_delta))
