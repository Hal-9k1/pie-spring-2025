from task import Task


class Joystick:
    """Represents a joystick with x and y axes."""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class Joysticks:
    """Represents a pair of joysticks."""
    def __init__(self, left: Joystick, right: Joystick):
        self.left = left
        self.right = right


class ButtonPair:
    """Represents a pair of buttons, such as bumpers or triggers."""
    def __init__(self, left: bool, right: bool):
        self.left = left
        self.right = right


class DirectionalPad:
    """Represents the directional pad (D-pad) on a gamepad."""
    def __init__(self, up: bool, right: bool, down: bool, left: bool):
        self.up = up
        self.right = right
        self.down = down
        self.left = left


class Buttons:
    """Represents individual buttons on a gamepad."""
    def __init__(self, a: bool, b: bool, x: bool, y: bool):
        self.a = a
        self.b = b
        self.x = x
        self.y = y


class GamepadInputTask:
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
        self.joysticks = Joysticks(Joystick(joystick_left_x, joystick_left_y), Joystick(joystick_right_x, joystick_right_y))
        self.bumpers = ButtonPair(bumper_left, bumper_right)
        self.triggers = ButtonPair(
            trigger_left if isinstance(trigger_left, bool) else trigger_left >= self.TRIGGER_MIN,
            trigger_right if isinstance(trigger_right, bool) else trigger_right >= self.TRIGGER_MIN
        )
        self.dpad = DirectionalPad(dpad_up, dpad_right, dpad_down, dpad_left)
        self.buttons = Buttons(button_a, button_b, button_x, button_y)


class KeyboardInputTask:
    def __init__(self, input_dict):
        self._input_dict = input_dict

    def get(self, key):
        return self._input_dict[key]
