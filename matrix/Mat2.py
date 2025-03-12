from math import sin
from math import cos
from math import isfinite
from numbers import Number

class Mat2:
    def __init__(self, m00, m10, m01, m11):
        self._mat = [m00, m10, m01, m11]

    @classmethod
    def from_angle(cls, angle):
        return Mat2(cos(angle), -sin(angle), sin(angle), cos(angle))

    def mul(self, other):
        if isinstance(other, Mat2):
            return Mat2(
                self._mat[0] * other._mat[0] + self._mat[1] * other._mat[2],
                self._mat[0] * other._mat[1] + self._mat[1] * other._mat[3],
                self._mat[2] * other._mat[0] + self._mat[3] * other._mat[2],
                self._mat[2] * other._mat[1] + self._mat[3] * other._mat[3]
            )
        elif isinstance(other, Vec2):
            return Vec2(
                self._mat[0] * other.getX() + self._mat[1] * other.get_y(),
                self._mat[2] * other.getX() + self._mat[3] * other.get_y()
            )
        elif isinstance(other, Number):
            return Mat2(*(e * other) for e in self._mat)
        else:
            raise ValueError('Invalid multiplicand type.')

    def det(self):
        return self._mat[0] * self._mat[3] - self._mat[1] * self._mat[2]

    def inv(self):
        d = det()
        return Mat2(
            self._mat[3] / d,
            -self._mat[2] / d,
            -self._mat[1] / d,
            self._mat[0] / d
        )
    
    def is_finite(self):
        return all(isfinite(e) for e in self._mat)

    def col(self, num):
        return Vec2(self._mat[num], self._mat[num + 2])

    def elem(self, x, y):
        return self._mat[y * 2 + x]

