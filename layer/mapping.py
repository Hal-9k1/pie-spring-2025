from layer import AbstractFunctionLayer
from task.drive import HolonomicDriveTask
from task.drive import TankDriveTask
from task.input import GamepadInputTask
from task.input import KeyboardInputTask
from task.manipulator import DriveBeltTask
from task.manipulator import DriveWheelBeltTask
from task.manipulator import DriveButtonPusherTask


class TankDriveMapping(AbstractFunctionLayer):
    def get_input_tasks(self):
        return {GamepadInputTask, KeyboardInputTask}

    def get_output_tasks(self):
        return {TankDriveTask}

    def map(self, task):
        if isinstance(task, GamepadInputTask):
            return TankDriveTask(task.joysticks.left.y, task.joysticks.right.y)
        else:
            return TankDriveTask(task.get('w') - task.get('s'), task.get('i') - task.get('k'))


class ZeldaDriveMapping(AbstractFunctionLayer):
    def setup(self, setup_info):
        self._logger = setup_info.get_logger('ZeldaDriveMapping')
        self._gp_fwd = 0
        self._gp_ccw = 0
        self._kb_fwd = 0
        self._kb_ccw = 0

    def get_input_tasks(self):
        return {GamepadInputTask, KeyboardInputTask}

    def get_output_tasks(self):
        return {TankDriveTask}

    def map(self, task):
        if isinstance(task, GamepadInputTask):
            self._gp_fwd = task.joysticks.left.y
            self._gp_ccw = -task.joysticks.left.x
        elif isinstance(task, KeyboardInputTask):
            self._kb_fwd = task.get('w') - task.get('s')
            self._kb_ccw = task.get('a') - task.get('d')
        else:
            raise TypeError(f'Bad task type of {task}')
        fwd = self._gp_fwd if abs(self._gp_fwd) > abs(self._kb_fwd) else self._kb_fwd
        ccw = self._gp_ccw if abs(self._gp_ccw) > abs(self._kb_ccw) else self._kb_ccw
        left = fwd - ccw
        right = fwd + ccw
        return TankDriveTask(left, right)


class DpadBeltMapping(AbstractFunctionLayer):
    def __init__(self, is_wheel_belt):
        super().__init__()
        self._is_wheel_belt = is_wheel_belt
        self._output_task_type = DriveWheelBeltTask if is_wheel_belt else DriveBeltTask

    def setup(self, setup_info):
        self._gp = 0
        self._kb = 0

    def get_input_tasks(self):
        return {GamepadInputTask, KeyboardInputTask}

    def get_output_tasks(self):
        return {self._output_task_type}

    def map(self, task):
        if isinstance(task, GamepadInputTask):
            self._gp = ((task.dpad.left - task.dpad.right)
                if self._is_wheel_belt
                else (task.dpad.up - task.dpad.down)
            )
        elif isinstance(task, KeyboardInputTask):
            self._kb = ((task.get('i') - task.get('o'))
                if self._is_wheel_belt
                else (task.get('u') - task.get('j'))
            )
        else:
            raise TypeError(f'Bad task type of {task}')
        return self._output_task_type(self._gp if abs(self._gp) > abs(self._kb) else self._kb)


class TriggerBeltMapping(AbstractFunctionLayer):
    MAX_SPEED = 1
    LOW_SPEED = 0.5

    def get_input_tasks(self):
        return {GamepadInputTask}

    def get_output_tasks(self):
        return {DriveBeltTask}

    def map(self, task):
        return DriveBeltTask(max(
            task.triggers.left * self.MAX_SPEED,
            task.triggers.right * self.LOW_SPEED
        ))


class ButtonPusherMapping(AbstractFunctionLayer):
    def setup(self, setup_info):
        self._is_high = True
        self._gp_down = False
        self._kb_down = False

    def get_input_tasks(self):
        return {GamepadInputTask, KeyboardInputTask}

    def get_output_tasks(self):
        return {DriveButtonPusherTask}

    def map(self, task):
        if isinstance(task, GamepadInputTask):
            gp_down = task.buttons.a
            triggered = gp_down and not self._gp_down
            self._gp_down = gp_down
        elif isinstance(task, KeyboardInputTask):
            kb_down = task.get('e')
            triggered = kb_down and not self._kb_down
            self._kb_down = kb_down
        else:
            raise TypeError(f'Bad task type of {task}')
        if triggered:
            self._is_high = not self._is_high
        return DriveButtonPusherTask(triggered, self._is_high)
