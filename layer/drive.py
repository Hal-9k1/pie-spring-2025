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
import time


class TwoWheelDrive(Layer):
    """Drive layer for a two-wheel drive robot."""

    LEFT_DRIVE_MOTOR_NAME = '6_5011048539317462848' #'6_3008899486804881237'
    RIGHT_DRIVE_MOTOR_NAME = '6_5011048539317462848' #'6_3008899486804881237'
    WHEEL_RADIUS = convert(2, 'in', 'm')
    # Wheel teeth / hub teeth:
    GEAR_RATIO = 84 / 36
    WHEEL_SPAN_RADIUS = convert(18, 'cm', 'm') #convert(14.5 / 2, 'in', 'm')
    # Encoder fac = required wheel distance / distance calculated from task
    LEFT_ENCODER_FAC = 1
    RIGHT_ENCODER_FAC = 1

    # Encoder fac = multiplied by power
    LEFT_POWER_FAC = 0.75
    RIGHT_POWER_FAC = 1

    LEFT_INTERNAL_GEARING = 70
    RIGHT_INTERNAL_GEARING = 70
    TICKS_PER_REV = 16

    def __init__(self):
        self._left_wheel = None
        self._right_wheel = None
        self._left_start_pos = 0
        self._right_start_pos = 0
        self._left_goal_delta = 0
        self._right_goal_delta = 0
        self._current_task_done = True
        self._last_printed = 0

    def setup(self, setup_info):
        self._right_wheel = Wheel(
            setup_info.get_logger('Right wheel'),
            Motor(
                setup_info.get_robot(),
                setup_info.get_logger('Right wheel motor'),
                self.RIGHT_DRIVE_MOTOR_NAME,
                'b'
            ).set_invert(False).set_encoder_invert(True),
            self.WHEEL_RADIUS,
            self.RIGHT_INTERNAL_GEARING * self.TICKS_PER_REV
        )
        self._left_wheel = Wheel(
            setup_info.get_logger('Left wheel'),
            Motor(
                setup_info.get_robot(),
                setup_info.get_logger('Left wheel motor'),
                self.LEFT_DRIVE_MOTOR_NAME,
                'a'
            ).set_invert(False),
            self.WHEEL_RADIUS,
            self.LEFT_INTERNAL_GEARING * self.TICKS_PER_REV
        )
        self._logger = setup_info.get_logger('TwoWheelDrive')
        self._is_direct_control = True
        self._left_start_pos = 0
        self._right_start_pos = 0
        self._left_goal_delta = 0
        self._right_goal_delta = 0
        self._should_request_task = True
        self._task = None

    def get_input_tasks(self):
        return {AxialMovementTask, TurnTask, TankDriveTask}

    def get_output_tasks(self):
        return set()

    def process(self, ctx):
        if self._should_request_task:
            if self._task:
                ctx.complete_task(self._task)
                self._task = None
            ctx.request_task()
        else:
            left_delta = self._left_wheel.get_distance() - self._left_start_pos
            left_done = ((left_delta < 0) == (self._left_goal_delta < 0)
                and abs(left_delta) >= abs(self._left_goal_delta))
            right_delta = self._right_wheel.get_distance() - self._right_start_pos
            right_done = True or ((right_delta < 0) == (self._right_goal_delta < 0)
                and abs(right_delta) >= abs(self._right_goal_delta))
            if time.time() - self._last_printed > 1:
                self._last_printed = time.time()
                self._logger.info(f'left {left_delta} left goal {self._left_goal_delta} right {right_delta} right goal {self._right_goal_delta}')
            if left_done and right_done:
                self._should_request_task = True
                self._logger.info(f'finished task {self._task} left {self._left_wheel._motor.get_encoder()} right {self._right_wheel._motor.get_encoder()}')
                self._left_wheel.set_velocity(0)
                self._right_wheel.set_velocity(0)

    def accept_task(self, task):
        self._task = task
        if isinstance(task, TankDriveTask):
            self._should_request_task = True
            left = task.get_left()
            right = task.get_right()
            max_abs_power = max(abs(left), abs(right), 1)
            self._left_wheel.set_velocity(left * self._get_left_max_velocity() / max_abs_power)
            self._right_wheel.set_velocity(right * self._get_right_max_velocity() / max_abs_power)
        elif isinstance(task, AxialMovementTask):
            self._should_request_task = False
            self._left_goal_delta = task.get_distance() * self.GEAR_RATIO * self.LEFT_ENCODER_FAC
            self._right_goal_delta = task.get_distance() * self.GEAR_RATIO * self.RIGHT_ENCODER_FAC
        elif isinstance(task, TurnTask):
            self._should_request_task = False
            self._left_goal_delta = (-task.get_angle() * self.WHEEL_SPAN_RADIUS * self.GEAR_RATIO
                * self.LEFT_ENCODER_FAC)
            self._right_goal_delta = (task.get_angle() * self.WHEEL_SPAN_RADIUS * self.GEAR_RATIO
                * self.RIGHT_ENCODER_FAC)

        if not self._should_request_task:
            self._logger.info(f'task {task} left {self._left_goal_delta} right {self._right_goal_delta}')
            self._logger.info(f'enc left {self._left_wheel._motor.get_encoder()} right {self._right_wheel._motor.get_encoder()}')
            self._left_start_pos = self._left_wheel.get_distance()
            self._right_start_pos = self._right_wheel.get_distance()
            self._left_wheel.set_velocity(
                copysign(self._get_left_max_velocity(), self._left_goal_delta)
            )
            self._right_wheel.set_velocity(
                copysign(self._get_right_max_velocity(), self._right_goal_delta)
            )

    def _get_left_max_velocity(self):
        return (self.LEFT_POWER_FAC * self.LEFT_ENCODER_FAC * self.LEFT_INTERNAL_GEARING
            / max(self.LEFT_INTERNAL_GEARING, self.RIGHT_INTERNAL_GEARING))

    def _get_right_max_velocity(self):
        return (self.RIGHT_POWER_FAC * self.RIGHT_ENCODER_FAC * self.RIGHT_INTERNAL_GEARING
            / max(self.LEFT_INTERNAL_GEARING, self.RIGHT_INTERNAL_GEARING))
