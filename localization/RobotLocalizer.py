from Localization import *

from abc import ABC
from abc import abstractmethod

class RobotLocalizer(ABC):
    @abstractmethod
    def invalidate_cache():
        pass

    @abstractmethod
    def register_source(source: LocalizationData):
        pass

    @abstractmethod
    def resolve_transform():
        pass

    @abstractmethod
    def resolve_position():
        pass

    @abstractmethod
    def resolve_rotation():
        pass