from layer import Layer
from task.input import GamepadInputTask
from task.input import KeyboardInputTask


class GamepadInputGenerator(Layer):
    def __init__(self, gamepad):
        self._gamepad = gamepad

    def get_input_tasks(self):
        return set()

    def get_output_tasks(self):
        return {GamepadInputTask}

    def process(self, ctx):
        ctx.emit_subtask(GamepadInputTask(
            self._gamepad.get_value('joystick_left_x'),
            self._gamepad.get_value('joystick_left_y'),
            self._gamepad.get_value('l_bumper'),
            self._gamepad.get_value('l_trigger'),
            self._gamepad.get_value('joystick_right_x'),
            self._gamepad.get_value('joystick_right_y'),
            self._gamepad.get_value('r_bumper'),
            self._gamepad.get_value('r_trigger'),
            self._gamepad.get_value('dpad_up'),
            self._gamepad.get_value('dpad_right'),
            self._gamepad.get_value('dpad_down'),
            self._gamepad.get_value('dpad_left'),
            self._gamepad.get_value('button_a'),
            self._gamepad.get_value('button_b'),
            self._gamepad.get_value('button_x'),
            self._gamepad.get_value('button_y'),
        ))

    def accept_task(self, task):
        raise TypeError


class XboxGamepadInputGenerator(Layer):
    def __init__(self, gamepad):
        self._gamepad = gamepad

    def get_input_tasks(self):
        return set()

    def get_output_tasks(self):
        return {GamepadInputTask}

    def process(self, ctx):
        ctx.emit_subtask(GamepadInputTask(
            self._gamepad.get_value('joystick_left_x'),
            -self._gamepad.get_value('joystick_left_y'),
            self._gamepad.get_value('l_bumper'),
            self._gamepad.get_value('l_trigger'),
            self._gamepad.get_value('joystick_right_x'),
            -self._gamepad.get_value('joystick_right_y'),
            self._gamepad.get_value('r_bumper'),
            self._gamepad.get_value('r_trigger'),
            self._gamepad.get_value('dpad_up'),
            self._gamepad.get_value('dpad_right'),
            self._gamepad.get_value('dpad_down'),
            self._gamepad.get_value('dpad_left'),
            self._gamepad.get_value('button_a'),
            self._gamepad.get_value('button_b'),
            self._gamepad.get_value('button_x'),
            self._gamepad.get_value('button_y'),
        ))

    def accept_task(self, task):
        raise TypeError


class KeyboardInputGenerator(Layer):
    KEYS = list("abcdefghijklmnopqrstuvwxyz0123456789,./;'[]") + [
        'left_arrow',
        'right_arrow',
        'up_arrow',
        'down_arrow'
    ]

    def __init__(self, keyboard):
        self._keyboard = keyboard
        self._last_log = 0

    def get_input_tasks(self):
        return set()

    def get_output_tasks(self):
        return {GamepadInputTask}

    def process(self, ctx):
        ctx.emit_subtask(KeyboardInputTask({k: self._keyboard.get_value(k) for k in self.KEYS}))
        if time.time() - self._last_log > 1:
            self._last_log = time.time()
            for k in self.KEYS:
                print(self._keyboard.get_value(k))

    def accept_task(self, task):
        raise TypeError
