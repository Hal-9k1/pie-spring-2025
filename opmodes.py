from abc import ABC
from abc import abstractmethod
from controller import LayerGraph
from controller import RobotController
from layer import AbstractQueuedLayer
from layer import WinLayer
from layer.drive import TwoWheelDrive
from layer.input import GamepadInputGenerator
from layer.mapping import TankDriveMapping
from layer.mapping import ZeldaDriveMapping
from log import LoggerProvider
from task import WinTask
from task.drive import AxialMovementTask
from task.drive import TurnTask
import math

class AbstractOpmode(ABC):
    @abstractmethod
    def get_layers(self, gamepad, keyboard):
        pass

    def post_setup(self):
        pass

    def get_localizer(self):
        return None

    def configure_logger(self, logger):
        pass

    @abstractmethod
    def get_robot_spec(self):
        pass

    def run(self, logger_provider, robot, gamepad, keyboard):
        controller = RobotController()

        lp = logger_provider.clone()
        self.configure_logger(lp)
        logger = lp.get_logger('AbstractOpmode')

        localizer = self.get_localizer()

        controller.setup(
            robot,
            self.get_layers(gamepad, keyboard),
            lp
        )

        while True:
            if controller.update():
                logger.warn('Opmode finished.')
                break


class TwoWheelDriveTeleopOpmode(AbstractOpmode):
    def get_layers(self, gamepad, keyboard):
        lg = LayerGraph()
        lg.add_chain([GamepadInputGenerator(gamepad), ZeldaDriveMapping(), TwoWheelDrive()])
        return lg

    def get_robot_spec(self):
        return {
            'koalabear': 2,
        }


class SampleAutonomousOpmode(AbstractOpmode):
    def get_layers(self, gamepad, keyboard):
        lg = LayerGraph()
        lg.add_chain([WinLayer(), SampleProgrammedDriveLayer(), TwoWheelDrive()])
        return lg

    def get_robot_spec(self):
        return {
            'koalabear': 2,
            'servocontroller': 2,
        }

class SampleProgrammedDriveLayer(AbstractQueuedLayer):
    def get_input_tasks(self):
        return {WinTask}

    def get_output_tasks(self):
        return {TurnTask, AxialMovementTask}

    def map_to_subtasks(self, task):
        assert(isinstance(task, WinTask))
        return [AxialMovementTask(1), TurnTask(math.pi / 2)] * 4
