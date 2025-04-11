from challenges import *
import opmodes
from mockrobot import MockRobot
from log import LoggerProvider
from log import StdioBackend

auto_opmode = opmodes.SampleAutonomousOpmode()
#teleop_opmode = opmodes.AbstractOpmode()

FORCE_MOCK_ROBOT = False
FORCE_MOCK_GAMEPAD = False
FORCE_MOCK_KEYBOARD = False

def get_robot_interfaces(use_input, robot_spec):
    is_dawn_environment = True
    gamepad = None
    keyboard = None

    logger_provider = LoggerProvider()
    logger_provider.add_backend(StdioBackend())

    try:
        Robot
    except NameError:
        is_dawn_environment = False

    robot = Robot if is_dawn_environment and not FORCE_MOCK_ROBOT else MockRobot(robot_spec, logger_provider)

    if use_input:
        gamepad = Gamepad if is_dawn_environment and not FORCE_MOCK_GAMEPAD else MockGamepad()
        keyboard = Keyboard if is_dawn_environment and not FORCE_MOCK_KEYBOARD else MockKeyboard()

    return (logger_provider, robot, gamepad, keyboard)

@_PREP_ENTRY_POINT
def autonomous():
    print(get_robot_interfaces(False, auto_opmode.get_robot_spec()))
    auto_opmode.run(*get_robot_interfaces(False, auto_opmode.get_robot_spec()))

@_PREP_ENTRY_POINT
def teleop():
    teleop_opmode.run(*get_robot_interfaces(True, teleop_opmode.get_robot_spec()))
