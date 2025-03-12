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

class Mat3:
    def __init___(self, m00, m10, m20, m01, m11, m21, m02, m12, m22):
        self._mat = [
            m00, m10, m20,
            m01, m11, m21,
            m02, m12, m22
        ]

    @classmethod
    def from_transform(self, rot, pos):
        return Mat3(
            rot.elem(0, 0), rot.elem(1, 0), pos.get_x(),
            rot.elem(0, 1), rot.elem(1, 1), pos.get_y(),
            0.0, 0.0, 1.0
        )

    def mul(self, other):
        if isinstance(other, Mat3):
            return Mat3(
                self.row(0).dot(other.col(0)),
                self.row(0).dot(other.col(1)),
                self.row(0).dot(other.col(2)),
                self.row(1).dot(other.col(0)),
                self.row(1).dot(other.col(1)),
                self.row(1).dot(other.col(2)),
                self.row(2).dot(other.col(0)),
                self.row(2).dot(other.col(1)),
                self.row(2).dot(other.col(2))
            )
        elif isinstance(other, Vec2):
            extended = Vec3(other.get_x(), other.get_y(), 0.0)
            return Vec2(
                 self.row(0).dot(extended),
                 self.row(1).dot(extended)
            )
        elif isinstance(other, Vec3):
            return Vec3(
                self.row(0).dot(other),
                self.row(1).dot(other),
                self.row(2).dot(other)
            )
        elif isinstance(other, Number):
            return Mat3(
                self._mat[0] * other,
                self._mat[1] * other,
                self._mat[2] * other,
                self._mat[3] * other,
                self._mat[4] * other,
                self._mat[5] * other,
                self._mat[6] * other,
                self._mat[7] * other,
                self._mat[8] * other
            )
        else:
            raise ValueError('Invalid multiplicand type.')
    
    def det(self):
         return (
             self._mat[0] * self._mat[4] * self._mat[8]
             + self._mat[1] * self._mat[5] * self._mat[6]
             + self._mat[2] * self._mat[3] * self._mat[7]
             - self._mat[2] * self._mat[4] * self._mat[6]
             - self._mat[0] * self._mat[5] * self._mat[7]
             - self._mat[1] * self._mat[3] * self._mat[8]
         )
    
    def inv(self):
         return self.cofactor().transpose().mul(1 / det())
    
    def col(self, num):
        self._check_dim(num, True)
        return Vec3(mat[num], self._mat[num + 3], self._mat[num + 6])

    def row(self, num):    
        self._check_dim(num, False)
        return Vec3(self._mat[num * 3], self._mat[num * 3 + 1], self._mat[num * 3 + 2])
    
    def transpose(self):
        return Mat3(
           self._mat[0], self._mat[3], self._mat[6],
           self._mat[1],self._mat[4], self._mat[7],
           self._mat[2],self._mat[5],self._mat[8]
        )
    
    def minor(self, col, row):
        self._check_dim(row, False)
        self._check_dim(col, True)
        col0 = 1 if col == 0 else 0;
        col1 = col0 + (2 if col == 1 else 1);
        row0 = 1 if row == 0 else 0;
        row1 = row0 + (2 if row == 1 else 1);
        return new Mat2(
            elem(col0, row0), elem(col1, row0),
            elem(col0, row1), elem(col1, row1)
        );
    
    def cofactor(self):
         return Mat3(
            self.minor(0, 0).det(),
            -self.minor(1, 0).det(),
            self.minor(2, 0).det(),
            -self.minor(0, 1).det(),
            self.minor(1, 1).det(),
            -self.minor(2, 1).det(),
            self.minor(0, 2).det(),
            -self.minor(1, 2).det(),
            self.minor(2, 2).det()
        )

