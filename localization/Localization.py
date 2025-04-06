from abc import ABC, abstractmethod
from matrix import Vec2
from functools import reduce
import math

class LocalizationData(ABC):
    @abstractmethod
    def get_position_probability(self, pos):
        pass

    @abstractmethod
    def get_position_probability_dx(self, pos, ignore_roots):
        pass

    @abstractmethod
    def get_position_probability_dy(self, pos, ignore_roots):
        pass

    @abstractmethod
    def get_positional_probability_dx_gradient(self, pos, ignore_roots):
        pass

    @abstractmethod
    def get_position_probability_dy_gradient(self, pos, ignore_roots):
        pass

    @abstractmethod
    def get_rotation_probability(self, rot):
        pass

    @abstractmethod
    def get_rotation_probability_dx(self, rot, ignore_roots):
        pass

    @abstractmethod
    def get_rotation_probability_dx2(self, rot, ignore_roots):
        pass

    
class AbstractFinDiffLocalization(LocalizationData):
    def __init__(self, epsilon):
        self._epsilon = epsilon

    def get_position_probability_dx(self, pos, ignore_roots):
        def calculations(b):
            if b is not None:
                _negative_center = pos.mul(-1)
                _epsilon_vec = Vec2(self.epsilon, self.epsilon)
                while True:
                    if(math.isfinite(_product) is not True):
                        _diff = _negative_center.add(b)
                        _factor = 1.0 / (_diff.dot(_diff) + 1.0) - 1.0
                        _product = 1.0 / _factor
                        _negative_center = _negative_center.add(_epsilon_vec)
                    else:
                        return _product
            else:
                return 1.0
        ignore_root_factor = list(reduce(lambda x,y : x*y ,map(calculations, ignore_roots)))
        return (self.get_position_probability(pos.add(Vec2(self._epsilon, 0))) - self.get_position_probability(pos)) / self._epsilon * ignore_root_factor
    
    def get_position_probability_dy(self, pos, ignore_roots):
        return (self.get_position_probability(pos.add(Vec2(0, self._epsilon))) - self.get_position_probability_dy(pos)) / self._epsilon
    
    def get_positional_probability_dx_gradient(self, pos, ignore_roots):
        z = self.get_position_probability_dx(pos, ignore_roots)
        wrtX = (self.get_position_probability_dx(pos.add(Vec2(self._epsilon, 0)), ignore_roots) - z) / self._epsilon
        wrtY = (self.get_position_probability_dx(pos.add(Vec2(0, self._epsilon)), ignore_roots) - z) / self._epsilon
        return Vec2(wrtX, wrtY)

    def get_position_probability_dy_gradient(self, pos, ignore_roots):
        z = self.get_position_probability_dy(pos, ignore_roots)
        wrtX = (self.get_position_probability_dy(pos.add(Vec2(self._epsilon, 0)), ignore_roots) - z)
        wrtY = (self.get_position_probability_dy(pos.add(Vec2(0, self._epsilon))) - z)
        return Vec2(wrtX, wrtY)
    
    def get_rotation_probability_dx(self, rot, ignore_roots):
        def calculate(a, b):
            if (a is not None and b is not None):
                _x = rot
                while True:
                    if not math.isfinite(_product):
                        _product = a / (_x - b)
                        _x = _x + self._epsilon
                    else:
                        return _product
            else:
                return 1.0
        ignore_root_factor = list(reduce(lambda x,y: calculate(x,y), ignore_roots))
        # Question: in the code it just says get_rotational_probability, does it need to be with respect to x or y or some other thing?
        return (self.get_rotational_probability(rot + self._epsilon) - self.get_rotational_probability(rot)) / self._epsilon * ignore_root_factor

class LocalizationSource(ABC):
    @abstractmethod
    def canLocalizePosition():
        pass

    @abstractmethod
    def canLocalizeRotation():
        pass

    @abstractmethod
    def collectData():
        pass


class RobotLocalizer(ABC):
    @abstractmethod
    def invalidateCache():
        pass

    @abstractmethod
    def registerSource(source):
        pass

    @abstractmethod
    def resolveTransform():
        pass

    @abstractmethod
    def resolvePosition():
        pass

    @abstractmethod
    def resolveRotation():
        pass

    class SqFalloffLocalizationData(AbstractFinDiffLocalization):
        def __init__(self, _epsilon, transform, accuracy, _position_precision, _rotation_precision):
            super().__init__(_epsilon)
            self._transform = transform
            self._accuracy = accuracy
            self._position_precision = _position_precision
            self._rotation_precision = _rotation_precision

        def get_position_probability(self, pos):
            diff = self._transform.get_translation().mul(-1).add(pos)
            return self._accuracy / ((diff.dot(diff) * self._position_precision) + 1)

        def get_rotation_probability(self, rot):
            diff = rot - self._transform.get_direction().get_angle()
            return self._accuracy / (diff * diff * self._rotation_precision + 1)

