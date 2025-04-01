from abc import ABC
from abc import abstractmethod
from log import LoggerProvider
from controller import RobotController

class AbstractOpmode(ABC):
    @abstractmethod
    def get_layers(self):
        pass

    def post_setup(self):
        pass

    def get_localizer(self):
        return None

    def configure_logger(self, logger):
        pass

    def run(self, robot, gamepad, keyboard):
        controller = RobotController()

        logger_provider = LoggerProvider()
        self.configure_logger(logger_provider)
        logger = logger_provider.get_logger('AbstractOpmode')

        localizer = self.get_localizer()

        controller.setup(
            robot,
            localizer,
            self.get_layers(),
            gamepad,
            keyboard,
            logger_provider
        )

        while True:
            if controller.update():
                logger.log('Opmode finished.')
                break
