from abc import ABC, abstractmethod
from matrix import Vec2
from functools import reduce
import math

class LocalizationData:
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
        # What is the equiivalent of the reduce function in python?
        ignore_root_factor = list(map(calculations(b), ignore_roots))
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
        # placehoeder
        pass