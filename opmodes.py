from abc import ABC
from abc import abstractmethod
from controller import LayerGraph
from controller import RobotController
from log import LoggerProvider
from matrix import Mat2
from matrix import Mat3
from matrix import Vec2
import layer
import layer.drive
import layer.input
import layer.mapping
import layer.peripheral
import layer.strategy
import localization
import math
import task.drive
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
        zelda = layer.mapping.ZeldaDriveMapping()
        lg.add_chain([
            layer.input.GamepadInputGenerator(gamepad),
            zelda,
            layer.drive.TwoWheelDrive()
        ])
        lg.add_connection(layer.input.KeyboardInputGenerator(keyboard), zelda)
        return lg

    def get_robot_spec(self):
        return {
            'koalabear': 2,
        }


class TWDPeripheralsTeleopOpmode(AbstractOpmode):
    def get_layers(self, gamepad, keyboard):
        lg = LayerGraph()
        zelda = layer.mapping.ZeldaDriveMapping()
        belt_map = layer.mapping.DpadBeltMapping(False)
        front_belt_map = layer.mapping.DpadBeltMapping(True)
        pusher_map = layer.mapping.ButtonPusherMapping()
        gp = layer.input.GamepadInputGenerator(gamepad)
        kb = layer.input.KeyboardInputGenerator(keyboard)
        lg.add_connections([
            (gp, zelda),
            (kb, zelda),
            (gp, belt_map),
            (kb, belt_map),
            (gp, front_belt_map),
            (kb, front_belt_map),
            (gp, pusher_map),
            (kb, pusher_map),
            (zelda, layer.drive.TwoWheelDrive()),
            (belt_map, layer.peripheral.BeltLayer()),
            (front_belt_map, layer.peripheral.WheelBeltLayer()),
            (pusher_map, layer.peripheral.ButtonPusherLayer()),
        ])
        return lg

    def get_robot_spec(self):
        return {
            'koalabear': 3,
        }


class SampleAutonomousOpmode(AbstractOpmode):
    def get_layers(self, gamepad, keyboard):
        lg = LayerGraph()
        lg.add_chain([
            layer.WinLayer(),
            layer.strategy.SampleProgrammedDriveLayer(),
            layer.drive.TwoWheelDrive(),
        ])
        return lg

    def get_robot_spec(self):
        return {
            'koalabear': 2,
            'servocontroller': 2,
        }


class RatAutonomousOpmode(AbstractOpmode):
    def get_layers(self, gamepad, keyboard):
        lg = LayerGraph()
        lg.add_chain([
            layer.WinLayer(),
            layer.strategy.RatStrategy(),
            layer.drive.TwoWheelDrive(),
        ])
        return lg

    def get_robot_spec(self):
        return {
            'koalabear': 1,
            'distancesensor': 1,
        }

# 0 rotation = rightwards from starting point. positive angles are ccw
# +x = 0 rotation direction
# +y = pi/2 radians rotation direction
class EscapeTestAutonomousOpmode(AbstractOpmode):
    def get_layers(self, gamepad, keyboard):
        lg = LayerGraph()
        pathfinder = layer.pathfinding.DynwinPathfinder(task.drive.TankDriveTask)
        drive = layer.drive.TwoWheelDrive()
        localizer = localization.RobotLocalizer(Mat3.from_transform(
            Mat2.from_angle(0),
            Vec2(1.087, 0.356)
        ))
        persistence_loc_src = localization.PersistenceLocalizationSource()
        localizer.register_source(persistence_loc_src)
        localizer.register_source(localization.EncoderLocalizationSource(drive))
        lg.add_chain([
            layer.WinLayer(),
            layer.strategy.EscapeTestStrategy(),
            pathfinder,
            drive,
        ])
        lg.add_connection(localizer, pathfinder)
        lg.add_connection(localizer, persistence_loc_src)
        return lg

    def get_robot_spec(self):
        return {
            'koalabear': 1,
            'distancesensor': 1,
        }


class NoopAutonomousOpmode(AbstractOpmode):
    def get_layers(self, gamepad, keyboard):
        return LayerGraph()

    def get_robot_spec(self):
        return {}
