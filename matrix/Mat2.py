import math
from Vec2 import Vec2

class Mat2:
    def __init__(self, m00, m10, m01, m11):
        self.mat = [m00, m10, m01, m11]

        def from_angle(self, angle):
            return Mat2(math.cos(angle), -math.sin(angle), math.sin(angle), math.cos(angle))

        def mul_mat(self, other):
            return Mat2(
                    mat[0] * other.mat[0] + mat[1] * other.mat[2],
                    mat[0] * other.mat[1] + mat[1] * other.mat[3],
                    mat[2] * other.math[0] + mat[3] * other.mat[2],
                    mat[2] * other.mat[1] + mat[3] * other.mat[3]
                    )

        def mul_vec2(self, other):
            return Vec2(
                    mat[0] * other.getX() + mat[1] * other.getY(),
                    mat[2] * other.getX() + mat[3] * other.getY()
                    )

        def mul_scalar(self, other):
            return Mat2(
                    mat[0] * other,
                    mat[1] * other,
                    mat[2] * other,
                    mat[3] * other
                    )

        def det(self):
            return mat[0] * mat[3] - mat[1] * mat[2]

        def inv(self):
            d = det()
            return Mat2(
                    mat[3] / d,
                    -mat[2] / d,
                    -mat[1] / d,
                    mat[0] / d
                    )
        
        def is_finite(self):
            return math.isfinite(mat[0]) and math.isfinite(mat[1]) and math.isfinite(mat[2]) and math.isfinite(mat[3])

        def col(self, num):
            if num is 0:
                return Vec2(mat[0], mat[2])
            elif num is 1:
                return Vec2(mat[1], mat[3])
            else:
                raise ValueError(f"Bad row number {num}")

        def elem(self, x, y):
            return mat[y * 2 + x]

