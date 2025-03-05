class WinLayer(Task):
    def __init__(self):
        self.emittedWin = False

    def setup(self, setupInfo):
        pass

    def update(self, iter(completed)):
        self.emittedWin = True
        return iter([WinTask()])

    def acceptTask(self, Task):
        raise ValueError(Task)
