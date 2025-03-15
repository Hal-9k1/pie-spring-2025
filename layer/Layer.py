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
