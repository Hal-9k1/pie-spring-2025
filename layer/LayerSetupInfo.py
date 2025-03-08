from layer import Layer

class LayerSetupInfo:
    def __init__(self, robot_controller, robot_localizer, gamepad0, gamepad1, logger_provider):
        self._robot_controller = robot_controller
        self._robot_localizer = robot_localizer
        self._gamepad0 = gamepad0
        self._gamepad1 = gamepad1
        self._logger_provider = logger_provider
    
    def get_localizer(self):
        return self._robot_localizer

    def get_gamepad0(self):
        return self._gamepad0

    def get_gamepad1(self):
        return self._gamepad1

    def get_logger_provider(self):
        return self._logger_provider.clone()

    def get_logger(self, label):
        return self._logger_provider.get_logger(label)

    def add_update_listener(self, listener):
        self._robot_controller.addUpdateListener(listener)

    def add_teardown_listener(self, listener):
        self._robot_controller.add_teardown_listener(listener)

