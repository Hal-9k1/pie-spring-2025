import math
from Vec2 import Vec2

class Mat2:
    def __init__(self, m00, m10, m01, m11):
        self._mat = [m00, m10, m01, m11]

        def from_angle(self, angle):
            return Mat2(math.cos(angle), -math.sin(angle), math.sin(angle), math.cos(angle))

        def mul_mat(self, other):
            return Mat2(
                    self._mat[0] * other.mat[0] + self._mat[1] * other.mat[2],
                    self._mat[0] * other.mat[1] + self._mat[1] * other.mat[3],
                    self._mat[2] * other.math[0] + self._mat[3] * other.mat[2],
                    self._mat[2] * other.mat[1] + self._mat[3] * other.mat[3]
                    )

        def mul_vec2(self, other):
            return Vec2(
                    self._mat[0] * other.get_x() + self._mat[1] * other.get_y(),
                    self._mat[2] * other.get_x() + self._mat[3] * other.get_y()
                    )

        def mul_scalar(self, other):
            return Mat2(
                    self._mat[0] * other,
                    self._mat[1] * other,
                    self._mat[2] * other,
                    self._mat[3] * other
                    )

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
            return math.isfinite(self._mat[0]) and math.isfinite(self._mat[1]) and math.isfinite(self._mat[2]) and math.isfinite(self._mat[3])

        def col(self, num):
            if num is 0:
                return Vec2(self._mat[0], self._mat[2])
            elif num is 1:
                return Vec2(self._mat[1], self._mat[3])
            else:
                raise ValueError(f"Bad row number {num}")

        def elem(self, x, y):
            return self._mat[y * 2 + x]

