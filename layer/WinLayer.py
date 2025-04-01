from Task import Task
# Import WinTask

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
