from abc import ABC
from abc import abstractmethod
from matrix import Vec2


class Obstacle(ABC):
    @abstractmethod
    def get_distance_to(self, point):
        raise NotImplementedError


class RectObstacle(Obstacle):
    def __init__(self, transform, size, invert=False):
        self._transform = transform
        self._size = size
        self._invert = False

    def get_distance_to(self, point):
        p = self._transform.inv().mul(point)
        tl = self._size / -2
        br = self._size / 2
        tlp = tl - p
        brp = p - br
        d = Vec2(max(tlp.get_x(), brp.get_x()), max(tlp.get_y(), brp.get_y()))
        corner = Vec2(max(0, d.get_x()), max(0, d.get_y()))
        edge = min(0, max(d.get_x(), d.get_y()))
        return corner.len() + edge


class CircleObstacle(Obstacle):
    def __init__(self, center, radius):
        self._center = center
        self._radius = radius

    def get_distance_to(self, point):
        return (point - self._center).len() - self._radius

