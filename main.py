from challenges import *
import opmodes
from mockrobot import MockRobot
from mockrobot import MockGamepad
from mockrobot import MockKeyboard
from log import FilterBackend
from log import Logger
from log import LoggerProvider
from log import StdioBackend

auto_opmode = opmodes.NoopAutonomousOpmode()
teleop_opmode = opmodes.TwoWheelDriveTeleopOpmode()

FORCE_MOCK_ROBOT = False
FORCE_MOCK_GAMEPAD = False
FORCE_MOCK_KEYBOARD = False

def get_robot_interfaces(use_input, robot_spec):
    is_dawn_environment = True
    gamepad = None
    keyboard = None

    logger_provider = LoggerProvider()
    logger_provider.add_backend(
        FilterBackend(StdioBackend(), True)
            .add_exception(Logger.TRACE_SEVERITY)
    )

    mock_robot_logger_provider = logger_provider

    try:
        Robot
    except NameError:
        is_dawn_environment = False

    robot = (
        Robot if is_dawn_environment and not FORCE_MOCK_ROBOT
        else MockRobot(robot_spec, mock_robot_logger_provider)
    )

    if use_input:
        gamepad = Gamepad if is_dawn_environment and not FORCE_MOCK_GAMEPAD else MockGamepad()
        keyboard = Keyboard if is_dawn_environment and not FORCE_MOCK_KEYBOARD else MockKeyboard()

    return (logger_provider, robot, gamepad, keyboard)

@_PREP_ENTRY_POINT
def autonomous():
    auto_opmode.setup(*get_robot_interfaces(False, auto_opmode.get_robot_spec()))
    while True:
        auto_opmode.loop()

@_PREP_ENTRY_POINT
def autonomous_setup():
    auto_opmode.setup(*get_robot_interfaces(False, auto_opmode.get_robot_spec()))

@_PREP_ENTRY_POINT
def autonomous_main():
    auto_opmode.loop()

@_PREP_ENTRY_POINT
def teleop():
    teleop_opmode.setup(*get_robot_interfaces(True, teleop_opmode.get_robot_spec()))
    while True:
        teleop_opmode.loop()

@_PREP_ENTRY_POINT
def teleop_setup():
    teleop_opmode.setup(*get_robot_interfaces(True, teleop_opmode.get_robot_spec()))

@_PREP_ENTRY_POINT
def teleop_main():
    teleop_opmode.loop()
