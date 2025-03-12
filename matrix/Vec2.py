import math

class Vec2:
    def __init__(self, x, y):
        self._x = x
        self._y = y
    
    def get_x(self):
        return self._x
    
    def get_y(self):
        return self._y
    
    def add_Vec2(self, other):
        return Vec2(self._x + other.get_x(), self._x + other.get_y())
    
    def mul_scalar(self, scalar):
        return Vec2(self._x * scalar, self._y * scalar)
    
    def dot(self, other):
        return self._x * other.get_x() + self._y * other.get_y()
    
    def len(self):
        return math.sqrt(self.dot(self))
    
    def get_angle(self):
        return math.atan2(self._y, self._x)
    
    def unit(self):
        return self.mul_scalar(1 / self.len())
    
    def angle_with(self, other):
        return math.acos(self.unit().dot(other.unit()))
    
    def isfinite(self):
        return math.isfinite(self._x) and not math.isnan(self._x) and math.isfinite(self._y) and not math.isnan(self._y)
    
    def proj(self, projectee):
        return self.mul_scalar(self.dot(projectee) / self.dot(self))
    
    def get_perpendicular(self):
        return Vec2(1, -self._y / self._x)