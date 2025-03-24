from challenges import *
from opmodes import *
from mock_robot import MockRobot

auto_opmode = opmodes.AbstractOpmode()
teleop_opmode = opmodes.AbstractOpmode()

FORCE_MOCK_ROBOT = False
FORCE_MOCK_GAMEPAD = False
FORCE_MOCK_KEYBOARD = False

def get_robot_interfaces(use_input):
    is_dawn_environment = True
    gamepad = None
    keyboard = None

    try:
        Robot
    except NameError:
        is_dawn_environment = False

    robot = Robot if is_dawn_environment and not FORCE_MOCK_ROBOT else MockRobot()

    if use_input:
        gamepad = Gamepad if is_dawn_environment and not FORCE_MOCK_GAMEPAD else MockGamepad()
        keyboard = Keyboard if is_dawn_environment and not FORCE_MOCK_KEYBOARD else MockKeyboard()

    return (robot, gamepad, keyboard)

def autonomous():
    auto_opmode.run(*get_robot_interfaces(False))

def teleop():
    teleop_opmode.run(*get_robot_interfaces(True))
