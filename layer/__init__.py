from abc import ABC
from abc import abstractmethod

class Layer(ABC):
    @abstractmethod
    def setup(self, setup):
        pass

    @abstractmethod
    def isTaskDone(self):
        pass

    @abstractmethod
    def update(self, completed):
        pass

    @abstractmethod
    def acceptTask(self, task):
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
        return iter([task])


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
        # Is a list
        self._layers = layers

        # is a iterator
        self._layer_iter = None

        # Top level layer being operated on.
        self._layer = None

        self._logger = None

    def is_task_done(self):
        if has_next(self._layer_iter) and self._layer.is_task_done():
            return True
        else:
            return False

    def setup(self, setup_info):
        name = []

        for elem in self._layers:
            name.append(elem.__class__)
            elem.setup(setupInfo)
        
        self._logger = setup_info.get_logger(f'TopLayerSequence[{name.join(", ")}]')

        self._layer_iter = iter(self._layers)
        layer = next(self._layer_iter)

    def update(self, completed):
        subtasks = self._layer.update(iter(completed))
        if(self._layer.is_task_done() and has_next(self._layer_iter)):
            self._layer = self._layer_iter.next()
        return subtasks

    def has_next(self, layerIter):
        if layerIter.next() == None:
            return False
        else:
            return True

class WinLayer(Task):
    def __init__(self):
        self._emittedWin = False

    def setup(self, setupInfo):
        pass

    def update(self, iter(completed)):
        self._emittedWin = True
        return iter([WinTask()])

    def accept_task(self, Task):
        raise ValueError(Task)
