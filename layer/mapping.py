from layer import AbstractFunctionLayer
from task.drive import HolonomicDriveTask
from task.drive import TankDriveTask
from task.input import GamepadInputTask
from task.input import KeyboardInputTask


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
    def get_input_tasks(self):
        return {GamepadInputTask, KeyboardInputTask}

    def get_output_tasks(self):
        return {TankDriveTask}

    def map(self, task):
        if isinstance(task, GamepadInputTask):
            fwd = task.joysticks.left.y
            cw = task.joysticks.left.x
        elif isinstance(task, KeyboardInputTask):
            fwd = task.get('w') - task.get('s')
            cw = task.get('d') - task.get('a')
        else:
            raise TypeError(f'Bad task type of {task}')
        left = fwd + cw
        right = fwd - cw
        return TankDriveTask(left, right)
