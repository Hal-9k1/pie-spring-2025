from abc import ABC
from abc import abstractmethod
from functools import reduce
from layer import Layer
from matrix import Vec2
from task.sensory import LocalizationTask
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

    
class AbstractFinDiffLocalizationData(LocalizationData):
    def __init__(self, epsilon):
        self._epsilon = epsilon

    def get_position_probability_dx(self, pos, ignore_roots):
        def calculations(b):
            if b is not None:
                negative_center = pos.mul(-1)
                epsilon_vec = Vec2(self.epsilon, self.epsilon)
                while True:
                    if math.isfinite(product) is not True:
                        diff = negative_center.add(b)
                        factor = 1.0 / (_diff.dot(_diff) + 1.0) - 1.0
                        product = 1.0 / _factor
                        negative_center = negative_center.add(epsilon_vec)
                    else:
                        return product
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
            if a is not None and b is not None:
                x = rot
                while True:
                    if not math.isfinite(product):
                        product = a / (_x - b)
                        x = x + self._epsilon
                    else:
                        return product
            else:
                return 1.0
        ignore_root_factor = list(reduce(lambda x,y: calculate(x,y), ignore_roots))
        # Question: in the code it just says get_rotational_probability, does it need to be with respect to x or y or some other thing?
        return (self.get_rotational_probability(rot + self._epsilon) - self.get_rotational_probability(rot)) / self._epsilon * ignore_root_factor


class LocalizationSource(ABC):
    @abstractmethod
    def can_localize_position():
        raise NotImplementedError

    @abstractmethod
    def can_localize_rotation():
        raise NotImplementedError

    @abstractmethod
    def collect_data():
        raise NotImplementedError


class SqFalloffLocalizationData(AbstractFinDiffLocalization):
    def __init__(self, epsilon, transform, accuracy, position_precision, rotation_precision):
        super().__init__(epsilon)
        self._transform = transform
        self._accuracy = accuracy
        self._position_precision = position_precision
        self._rotation_precision = rotation_precision

    def get_position_probability(self, pos):
        diff = self._transform.get_translation().mul(-1).add(pos)
        return self._accuracy / ((diff.dot(diff) * self._position_precision) + 1)

    def get_rotation_probability(self, rot):
        diff = rot - self._transform.get_direction().get_angle()
        return self._accuracy / (diff * diff * self._rotation_precision + 1)


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
