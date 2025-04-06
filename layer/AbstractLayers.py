from layer import Layer

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
