from actuators import Motor
from layer import Layer
from layer import LayerSetupInfo
from math import copysign
from mechanisms import Wheel
from task.drive import AxialMovementTask
from task.drive import TankDriveTask
from task.drive import TurnTask
from task import UnsupportedTaskError
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

    def setup(self, init_info):
        self._right_wheel = Wheel(
            setup_info.get_logger('Right wheel'),
            Motor(
                setup_info.get_robot(),
                setup_info.get_logger('Right wheel motor'),
                self.RIGHT_DRIVE_MOTOR_NAME,
                'insert a or b here'
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
                'insert a or b here'
            ),
            self.WHEEL_RADIUS,
            self.INTERNAL_GEARING
        )
        self._left_start_pos = 0
        self._right_start_pos = 0
        self._left_goal_delta = 0
        self._right_goal_delta = 0
        self._current_task_done = True

    def is_task_done(self):
        return self._current_task_done

    def update(self, completed):
        left_delta = self._left_wheel.get_distance() - self._left_start_pos
        left_done = ((left_delta < 0) == (self._left_goal_delta < 0)
            and abs(left_delta) >= abs(self._left_goal_delta))
        right_delta = self._right_wheel.get_distance() - self._right_start_pos
        right_done = ((right_delta < 0) == (self._right_goal_delta < 0)
            and abs(right_delta) >= abs(self._right_goal_delta))

        is_teleop_task = self._left_goal_delta == 0 and self._right_goal_delta == 0
        self._current_task_done = left_done and right_done

        if self._current_task_done and not is_teleop_task:
            self._left_wheel.set_velocity(0)
            self._right_wheel.set_velocity(0)

        return None  # Placeholder for adaptive velocity control

    def accept_task(self, task):
        if isinstance(task, AxialMovementTask):
            self._left_goal_delta = task.distance * self.GEAR_RATIO * self.SLIPPING_CONSTANT
            self._right_goal_delta = task.distance * self.GEAR_RATIO * self.SLIPPING_CONSTANT
        elif isinstance(task, TurnTask):
            self._left_goal_delta = (-task.angle * self.WHEEL_SPAN_RADIUS * self.GEAR_RATIO
                * self.SLIPPING_CONSTANT)
            self._right_goal_delta = (task.angle * self.WHEEL_SPAN_RADIUS * self.GEAR_RATIO
                * self.SLIPPING_CONSTANT)
        elif isinstance(task, TankDriveTask):
            self._left_goal_delta = 0
            self._right_goal_delta = 0
            max_abs_power = max(abs(task.left), abs(task.right), 1)
            self._left_wheel.set_velocity(task.left / max_abs_power)
            self._right_wheel.set_velocity(task.right / max_abs_power)
            return
        else:
            raise UnsupportedTaskError(self, task)

        self._current_task_done = False
        self._left_start_pos = self._left_wheel.get_distance()
        self._right_start_pos = self._right_wheel.get_distance()
        self._left_wheel.set_velocity(copysign(1, self._left_goal_delta))
        self._right_wheel.set_velocity(copysign(1, self._right_goal_delta))
