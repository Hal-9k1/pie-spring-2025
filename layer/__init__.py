from abc import ABC
from abc import abstractmethod
from task import UnsupportedTaskError
from task import WinTask

class Layer(ABC):
    @abstractmethod
    def setup(self, setup):
        pass

    @abstractmethod
    def is_task_done(self):
        pass

    @abstractmethod
    def update(self, completed):
        pass

    @abstractmethod
    def accept_task(self, task):
        pass


class LayerSetupInfo:
    def __init__(self, robot_controller, robot_localizer, gamepad0, gamepad1, logger_provider):
        self._robot_controller = robot_controller
        self._robot_localizer = robot_localizer
        self._gamepad0 = gamepad0
        self._gamepad1 = gamepad1
        self._logger_provider = logger_provider
    
    def get_localizer(self):
        return self._robot_localizer

    def get_gamepad(self, index):
        if index == 0:
            return self._gamepad0
        elif index == 1:
            return self._gamepad1
        else:
            raise ValueError(f'Invalid gamepad index {index}')

    def get_logger_provider(self):
        return self._logger_provider.clone()

    def get_logger(self, label):
        return self._logger_provider.get_logger(label)

    def add_update_listener(self, listener):
        self._robot_controller.add_update_listener(listener)

    def add_teardown_listener(self, listener):
        self._robot_controller.add_teardown_listener(listener)


class AbstractFunctionLayer(Layer):
    def __init__(self):
        self._emitted_subtask = True
        self._subtask = None

    def is_task_done(self):
        return self._emitted_subtask

    def update(self, completed):
        if self._emitted_subtask:
            raise RuntimeError("No more subtasks!")
        self._emitted_subtask = True
        return iter([self._subtask])

    def accept_task(self, task):
        self._subtask = self.map(task)
        self._emitted_subtask = False

    @abstractmethod
    def map(self):
        raise NotImplementedError


class AbstractQueuedLayer(Layer):
    def __init__(self):
        self._subtask_iter = None
        self._next_subtask = None

    def setup(self, setup_info):
        pass

    def is_task_done(self):
        return self._get_next_subtask() == None

    def update(self, completed):
        subtask = self._get_next_subtask()
        self._next_subtask = None
        return subtask

    def _get_next_subtask(self):
        if self._next_subtask == None:
            self._next_subtask = next(self._subtask_iter, None)
        return self._next_subtask


class TopLayerSequence(Layer):
    def __init__(self, layers):
        self._layers = layers
        self._layer_iter = None
        self._layer = None
        self._logger = None

    def setup(self, setup_info):
        name = []
        for elem in self._layers:
            name.append(elem.__class__)
            elem.setup(setup_info)
        self._logger = setup_info.get_logger(f'TopLayerSequence[{name.join(", ")}]')

        self._layer_iter = iter(self._layers)
        self._next_layer = None
        self._layer = self._get_next_layer(True)

    def is_task_done(self):
        if self._get_next_layer(False) == None and self._layer.is_task_done():
            return True
        else:
            return False

    def update(self, completed):
        subtasks = self._layer.update(iter(completed))
        if self._layer.is_task_done() and self._get_next_layer(False) != None:
            self._layer = self._get_next_layer(True)
        return subtasks

    def _get_next_layer(self, consume):
        if self._next_layer == None:
            self._next_layer = next(self._layer_iter, None)
        layer = self._next_layer
        if consume:
            self._next_layer = None
        return layer

class WinLayer(Task):
    def __init__(self):
        self._emitted_win = False

    def setup(self, setup_info):
        pass

    def update(self, completed):
        self._emitted_win = True
        return iter([WinTask()])

    def accept_task(self, task):
        raise UnsupportedTaskError(self, task)
