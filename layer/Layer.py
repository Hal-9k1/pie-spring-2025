from abc import ABC

class Layer(ABC):
    @abstractmethod
    def setup(self, setup):
        pass

    @abstractmethod
    def isTaskDone(self):
        pass

    @abstractmethod
    def update(self, Iter(completed)):
        pass

    @abstractmethod
    def acceptTask(self, task):
        pass