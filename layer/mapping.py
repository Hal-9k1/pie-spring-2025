from layer import AbstractFunctionLayer
from task.drive import HolonomicDriveTask
from task.drive import TankDriveTask
from task.input import GamepadInputTask
from task.input import KeyboardInputTask
from task.peripheral import BeltTask


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
        fwd = self._gp_fwd if abs(self._gp_fwd > self._kb_fwd) else self._kb_fwd
        ccw = self._gp_ccw if abs(self._gp_ccw > self._kb_ccw) else self._kb_ccw
        left = fwd - ccw
        right = fwd + ccw
        return TankDriveTask(left, right)


class DpadBeltMapping(AbstractFunctionLayer):
    def get_input_tasks(self):
        return {GamepadInputTask, KeyboardInputTask}

    def get_output_tasks(self):
        return {BeltTask}

    def map(self, task):
        if isinstance(task, GamepadInputTask):
            return DriveBeltTask(task.dpad.up - task.dpad.down)
        elif isinstance(task, KeyboardInputTask):
            return DriveBeltTask(task.get('o') - task.get('p'))
        else:
            raise TypeError(f'Bad task type of {task}')

# left trigger drives quickly, right trigger drives slowly
class TriggerBeltMapping(AbstractFunctionLayer):
    def get_input_tasks(self):
        return {GamepadInputTask}

    def get_output_tasks(self):
        return {BeltTask}

    def map(self, task):
        return DriveBeltTask(max(task.triggers.left * 1.up - task.dpad.down)
