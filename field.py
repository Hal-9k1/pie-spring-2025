from abc import ABC
from abc import abstractmethod
from layer.pathfinding import Obstacle as PathfindingObstacle
from layer.pathfinding import StaticObstacle
from matrix import Mat2
from matrix import Mat3
from matrix import Vec2
from units import convert
import math


class FieldObject(ABC):
    @abstractmethod
    def get_bounding_rect(self) -> tuple[Vec2, Vec2]:
        raise NotImplementedError

    @abstractmethod
    def to_pathfinding(self) -> PathfindingObstacle:
        raise NotImplementedError


class FieldRect(FieldObject):
    def __init__(self, data, is_bounds=False):
        self._center = data[0]
        self._size = data[1]
        self._angle = data[2]
        self._is_inverted = is_bounds

    def get_bounding_rect(self):
        mat = Mat2.from_angle(self._angle)
        tl = mat * (self._center - self._size * 0.5)
        br = mat * (self._center + self._size * 0.5)
        return (
            Vec2(min(tl.get_x(), br.get_x()), min(tl.get_y(), br.get_y())),
            Vec2(max(tl.get_x(), br.get_x()), max(tl.get_y(), br.get_y()))
        )

    def to_pathfinding(self):
        return StaticObstacle(
            Mat3.from_transform(
                Mat2.from_angle(self._angle),
                self._center
            ),
            self._size,
            self._is_inverted
        )


class FieldBounds(FieldRect):
    def __init__(self, data):
        super().__init__(data, True)
                

class Field:
    TYPES = {
        'rect': FieldRect,
        'bounds': FieldBounds,
    }

    def __init__(self, data):
        self._obstacles = []
        for obstacle in data:
            if obstacle[0] not in self.TYPES:
                raise ValueError(f'Invalid field object type {obstacle[0]}')
            self._obstacles.append(self.TYPES[obstacle[0]](obstacle[1:]))

    def get_pathfinding_obstacles(self):
        return [o.to_pathfinding() for o in self._obstacles]

    def get_bounding_rect(self):
        tl = Vec2(math.inf, math.inf)
        br = Vec2(-math.inf, -math.inf)
        for o in self._obstacles:
            otl, obr = o.get_bounding_rect()
            tl = Vec2(min(tl.get_x(), otl.get_x()), min(tl.get_y(), otl.get_y()))
            br = Vec2(max(br.get_x(), obr.get_x()), max(br.get_y(), obr.get_y()))
        return (tl, br) if tl.is_finite() and br.is_finite() else (Vec2.zero(), Vec2.zero())

    def get_size(self):
        tl, br = self.get_bounding_rect()
        return br + tl * -1


spring_2025 = Field([
    ('bounds', convert(Vec2(9, 12), 'ft', 'm') * 0.5, convert(Vec2(9, 12), 'ft', 'm'), 0),
])
