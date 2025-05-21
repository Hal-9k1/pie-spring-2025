from abc import ABC
from abc import abstractmethod
from layer import Layer
from matrix import Mat3
import math
import time


class LocalizationData(ABC):
    @abstractmethod
    def get_position_probability(self, pos):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dx(self, pos):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dy(self, pos):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dx_gradient(self, pos):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dy_gradient(self, pos):
        raise NotImplementedError

    @abstractmethod
    def get_rotation_probability(self, rot):
        raise NotImplementedError

    @abstractmethod
    def get_rotation_probability_dx(self, rot):
        raise NotImplementedError

    @abstractmethod
    def get_rotation_probability_dx2(self, rot):
        raise NotImplementedError


class LocalizationSource(ABC):
    def on_start(self, start_pos: Mat3):
        pass

    def on_update(self):
        pass

    @abstractmethod
    def has_data(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def collect_data(self) -> LocalizationData:
        raise NotImplementedError


class RobotLocalizer(Layer):
    def __init__(self, initial_transform):
        self._init = True
        self._should_emit = True
        self._sources = []
        self._init_tfm = initial_transform

    def setup(self, setup_info):
        setup_info.add_update_listener(lambda: self._on_update())

    def get_input_tasks(self):
        return set()

    def get_output_tasks(self):
        return {LocalizationTask}

    def complete_task(self, task):
        if task == self._emitted_task:
            self._should_emit = True

    def process(self, ctx):
        if self._init:
            self._init = False
            for source in self._sources:
                source.on_start(self._init_tfm)
        if self._should_emit:
            ctx.emit_subtask(LocalizationTask(self.resolve_transform()))

    def accept_task(self):
        raise TypeError

    def register_source(self, source):
        self._sources.append(source)

    def _on_update(self):
        self.invalidate_cache()
        for source in self._sources:
            source.on_update()

    def _get_sources(self):
        return self._sources

    @abstractmethod
    def resolve_transform(self):
        raise NotImplementedError

    @abstractmethod
    def invalidate_cache(self):
        raise NotImplementedError
