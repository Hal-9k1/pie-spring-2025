class Joystick:
    """Represents a joystick with x and y axes."""
    def __init__(self, x: float, y: float):
        self._x = x
        self._y = y

class Joysticks:
    """Represents a pair of joysticks."""
    def __init__(self, left: Joystick, right: Joystick):
        self._left = left
        self._right = right

class ButtonPair:
    """Represents a pair of buttons, such as bumpers or triggers."""
    def __init__(self, left: bool, right: bool):
        self._left = left
        self._right = right

class DirectionalPad:
    """Represents the directional pad (D-pad) on a gamepad."""
    def __init__(self, up: bool, right: bool, down: bool, left: bool):
        self._up = up
        self._right = right
        self._down = down
        self._left = left

class Buttons:
    """Represents individual buttons on a gamepad."""
    def __init__(self, a: bool, b: bool, x: bool, y: bool):
        self._a = a
        self._b = b
        self._x = x
        self._y = y

class GamepadInput:
    """Represents the input state of a gamepad."""
    TRIGGER_MIN = 0.3  # Threshold for triggers to be considered "pressed"

    def __init__(
        self,
        joystick_left_x: float,
        joystick_left_y: float,
        bumper_left: bool,
        trigger_left: float,
        joystick_right_x: float,
        joystick_right_y: float,
        bumper_right: bool,
        trigger_right: float,
        dpad_up: bool,
        dpad_right: bool,
        dpad_down: bool,
        dpad_left: bool,
        button_a: bool,
        button_b: bool,
        button_x: bool,
        button_y: bool,
    ):
        self._joysticks = Joysticks(Joystick(joystick_left_x, joystick_left_y), Joystick(joystick_right_x, joystick_right_y))
        self._bumpers = ButtonPair(bumper_left, bumper_right)
        self._triggers = ButtonPair(trigger_left >= self._TRIGGER_MIN, trigger_right >= self._TRIGGER_MIN)
        self._dpad = DirectionalPad(dpad_up, dpad_right, dpad_down, dpad_left)
        self._buttons = Buttons(button_a, button_b, button_x, button_y)

class GamepadInputTask:
    """Holds a snapshot of input from all connected gamepads."""
    def __init__(self, gamepad0: GamepadInput = None, gamepad1: GamepadInput = None):
        self._gamepad0 = gamepad0
        self._gamepad1 = gamepad1
