import math
from Vec2 import Vec2

class Mat2:
    def __init__(self, m00, m10, m01, m11):
        self.mat = [m00, m10, m01, m11]

        def from_angle(angle):
            return Mat2(math.cos(angle), -math.sin(angle), math.sin(angle), math.cos(angle))

        def mul_mat(other):
            return Mat2(
                    mat[0] * other.mat[0] + mat[1] * other.mat[2],
                    mat[0] * other.mat[1] + mat[1] * other.mat[3],
                    mat[2] * other.math[0] + mat[3] * other.mat[2],
                    mat[2] * other.mat[1] + mat[3] * other.mat[3]
                    )

        def mul_vec2(other):
            return Vec2(
                    mat[0] * other.getX() + mat[1] * other.getY(),
                    mat[2] * other.getX() + mat[3] * other.getY()
                    )

        def mul_scalar(other):
            return Mat2(
                    mat[0] * other,
                    mat[1] * other,
                    mat[2] * other,
                    mat[3] * other
                    )


