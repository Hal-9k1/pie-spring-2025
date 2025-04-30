from abc import ABC
from abc import abstractmethod
from controller import LayerGraph
from controller import RobotController
from layer import AbstractQueuedLayer
from layer import WinLayer
from layer.drive import TwoWheelDrive
from layer.input import KeyboardInputGenerator
from layer.input import GamepadInputGenerator
from layer.input import XboxGamepadInputGenerator
from layer.mapping import TankDriveMapping
from layer.mapping import ZeldaDriveMapping
from layer.strategy import RatStrategy
from log import LoggerProvider
from task import WinTask
from task.drive import AxialMovementTask
from task.drive import TurnTask
import math
import time


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

    def setup(self, logger_provider, robot, hw_conf, gamepad, keyboard):
        self._controller = RobotController()

        lp = logger_provider.clone()
        self.configure_logger(lp)
        self._logger = lp.get_logger('AbstractOpmode')

        localizer = self.get_localizer()

        self._controller.setup(
            robot,
            hw_conf,
            self.get_layers(gamepad, keyboard),
            lp
        )

        self._finished = False
        self._logger.log('Setup finished.')
        self._init_time = time.time()

    def loop(self):
        if self._init_time and time.time() - self._init_time > 5:
            self._logger.log('Robot is alive 5 seconds into opmode')
            self._init_time = None
        if not self._finished and self._controller.update():
            self._logger.warn('Opmode finished.')
            self._finished = True


class TwoWheelDriveTeleopOpmode(AbstractOpmode):
    def get_layers(self, gamepad, keyboard):
        lg = LayerGraph()
        zelda = ZeldaDriveMapping()
        lg.add_chain([GamepadInputGenerator(gamepad), zelda, TwoWheelDrive()])
        #lg.add_connection(KeyboardInputGenerator(keyboard), zelda)
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


class RatAutonomousOpmode(AbstractOpmode):
    def get_layers(self, gamepad, keyboard):
        lg = LayerGraph()
        lg.add_chain([WinLayer(), RatStrategy(), TwoWheelDrive()])
        return lg

    def get_robot_spec(self):
        return {
            'koalabear': 3,
            'distancesensor': 1,
        }


class NoopAutonomousOpmode(AbstractOpmode):
    def get_layers(self, gamepad, keyboard):
        return LayerGraph()

    def get_robot_spec(self):
        return {}
