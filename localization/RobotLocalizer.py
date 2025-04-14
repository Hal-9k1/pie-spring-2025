from abc import ABC
from abc import abstractmethod
from task.sensory import LocalizationTask

class RobotLocalizer(Layer):
    def setup(self, setup_info):
        setup_info.add_update_listener(lambda: self.invalidate_cache())

    def get_input_tasks(self):
        return set()

    def get_output_tasks(self):
        return {LocalizationTask}

    def complete_task(self, task):
        if task == self._emitted_task:
            self._should_emit = True

    def process(self, ctx):
        if self._should_emit:
            ctx.emit_subtask(LocalizationTask(self._resolve_transform()))

    def accept_task(self):
        raise TypeError

    @abstractmethod
    def resolve_transform(self):
        raise NotImplementedError

    @abstractmethod
    def invalidate_cache():
        pass

    @abstractmethod
    def register_source(self, source: LocalizationSource):
        pass
