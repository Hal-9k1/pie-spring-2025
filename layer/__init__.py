from abc import ABC
from abc import abstractmethod
from task import Task
from task import WinTask


class LayerSetupInfo:
    def __init__(self, robot, robot_controller, robot_localizer, gamepad, keyboard, logger_provider):
        self._robot = robot
        self._robot_controller = robot_controller
        self._robot_localizer = robot_localizer
        self._gamepad = gamepad
        self._keyboard = keyboard
        self._logger_provider = logger_provider
    
    def get_robot(self):
        return self._robot

    def get_localizer(self):
        return self._robot_localizer

    def get_gamepad(self):
        return self._gamepad

    def get_logger_provider(self):
        return self._logger_provider.clone()

    def get_logger(self, label):
        return self._logger_provider.get_logger(label)

    def add_update_listener(self, listener):
        self._robot_controller.add_update_listener(listener)

    def add_teardown_listener(self, listener):
        self._robot_controller.add_teardown_listener(listener)


class LayerProcessContext:
    def __init__(self, emit_subtask_hook, complete_task_hook, request_task_hook):
        self._emit_subtask_hook = emit_subtask_hook
        self._complete_task_hook = complete_task_hook

    def emit_subtask(self, subtask):
        self._emit_subtask_hook(subtask)

    def complete_task(self, task):
        self._complete_task_hook()

    def request_task(self):
        self._request_task_hook()


class Layer(ABC):
    def setup(self, setup_info: LayerSetupInfo) -> None:
        pass

    @abstractmethod
    def get_input_tasks(self) -> set[Task]:
        raise NotImplementedError

    @abstractmethod
    def get_output_tasks(self) -> set[Task]:
        raise NotImplementedError

    def subtask_completed(self, task: Task) -> None:
        pass

    @abstractmethod
    def process(self, ctx: LayerProcessContext) -> None:
        raise NotImplementedError

    @abstractmethod
    def accept_task(self, task: Task) -> None:
        raise NotImplementedError


class AbstractFunctionLayer(Layer):
    def __init__(self):
        self._emitted_subtask = True
        self._subtask_completed = True
        self._subtask = None
        self._task = None

    def subtask_completed(self, task):
        self._subtask_completed = True

    def process(self, ctx):
        if self._subtask_completed:
            if self._task:
                ctx.complete_task(self._task)
                self._task = None
            ctx.request_task()
        if not self._emitted_subtask:
            ctx.emit_subtask(self._subtask)
            self._emitted_subtask = True

    def accept_task(self, task):
        self._task = task
        self._subtask = self.map(task)
        self._emitted_subtask = False
        self._subtask_completed = False

    @abstractmethod
    def map(self):
        raise NotImplementedError


class AbstractQueuedLayer(Layer):
    def __init__(self):
        self._subtask_iter = None
        self._next_subtask = None
        self._task = None

    def subtask_completed(self, task):
        self._advance()

    def _advance(self):
        self._next_subtask = next(self._subtask_iter, None)
        if not self._next_subtask:
            self._subtask_iter = None

    def process(self, ctx):
        if not self._subtask_iter:
            if self._task:
                ctx.complete_task(self._task)
                self._task = None
            ctx.request_task()
        if self._next_subtask:
            ctx.emit_subtask(self._next_subtask)
            self._next_subtask = None

    def accept_task(self, task):
        self._subtask_iter = iter(self.map_to_subtasks(task))
        self._advance()

    @abstractmethod
    def map_to_subtasks(self, task):
        raise NotImplementedError


class SequenceLayer(Layer):
    def __init__(self, layers):
        self._layers = layers
        self._layer = None
        self._logger = None

    def setup(self, setup_info):
        for l in self._layers:
            l.setup(setup_info)

    def subtask_completed(self, task):
        self._layer.subtask_completed(task)

    def process(self, ctx):
        if not self._layer:
            self._layer = next(self._layer_iter, None)
            if not self._layer:
                if self._task:
                    ctx.complete_task(self._task)
                return
        wrapped_ctx = LayerProcessContext(
            lambda t: ctx.emit_subtask(t),
            lambda t: self._advance(),
        )
        self._layer.process(wrapped_ctx)

    def _advance(self):
        self._layer = None

    def accept_task(self, task):
        self._task = task
        for layer in self._layers:
            self._layers.accept_task(task)
        self._layer_iter = iter(self._layers)

    def __repr__(self):
        return f'SequenceLayer({self._layers})'

    def __str__(self):
        return f'SequenceLayer({[str(l) for l in self._layers]})'


class WinLayer(Layer):
    def __init__(self):
        self._emitted_win = False
        self._completed_win = False

    def get_input_tasks(self):
        return set()

    def get_output_tasks(self):
        return {WinTask}

    def subtask_completed(self, task):
        self._completed_win = True

    def process(self, ctx):
        if not self._emitted_win:
            ctx.emit_subtask(WinTask())
        if self._completed_win:
            ctx.complete_task(None)

    def accept_task(self, task):
        raise ValueError

