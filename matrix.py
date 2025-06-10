from math import acos
from math import atan2
from math import cos
from math import isfinite
from math import floor
from math import sin
from math import sqrt
from numbers import Number

class Mat2:
    def __init__(self, m00, m10, m01, m11):
        self._mat = [m00, m10, m01, m11]

    @classmethod
    def identity(cls):
        return Mat2(1, 0, 0, 1)

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
                self._mat[0] * other.x + self._mat[1] * other.y,
                self._mat[2] * other.x + self._mat[3] * other.y
            )
        elif isinstance(other, Number):
            return Mat2(*((e * other) for e in self._mat))
        else:
            return NotImplemented

    def det(self):
        return self._mat[0] * self._mat[3] - self._mat[1] * self._mat[2]

    def inv(self):
        d = self.det()
        return Mat2(
            self._mat[3] / d,
            -self._mat[1] / d,
            -self._mat[2] / d,
            self._mat[0] / d
        )

    def is_finite(self):
        return all(isinstance(e, Number) and isfinite(e) for e in self._mat)

    def col(self, num):
        self._check_dim(num, True)
        return Vec2(self._mat[num], self._mat[num + 2])

    def row(self, num):
        self._check_dim(num, False)
        return Vec2(self._mat[num * 2], self._mat[num * 2 + 1])

    def elem(self, x, y):
        self._check_dim(x, True)
        self._check_dim(y, False)
        return self._mat[y * 2 + x]

    def _check_dim(self, num, col):
        option = 'column' if col else 'row'
        if not isinstance(num, int) or num < 0 or num > 1:
            raise ValueError(f'Bad {option} number {num}')

    def __mul__(self, other):
        return self.mul(other)

    def __eq__(self, other):
        return isinstance(other, Mat2) and self._mat == other._mat

    def __hash__(self):
        return hash(self._mat)

    def __repr__(self):
        return f'Mat2({", ".join(repr(e) for e in self._mat)})'

class Mat3:
    def __init__(self, m00, m10, m20, m01, m11, m21, m02, m12, m22):
        self._mat = [
            m00, m10, m20,
            m01, m11, m21,
            m02, m12, m22
        ]

    @classmethod
    def identity(cls):
        return Mat3(1, 0, 0, 0, 1, 0, 0, 0, 1)

    @classmethod
    def from_transform(self, rot, pos):
        return Mat3(
            rot.elem(0, 0), rot.elem(1, 0), pos.x,
            rot.elem(0, 1), rot.elem(1, 1), pos.y,
            0.0, 0.0, 1.0
        )

    def mul(self, other):
        if isinstance(other, Mat3):
            # Yes, the order of for clauses is correct for an outer row loop and inner col loop.
            # Comprehensions are dumb.
            return Mat3(
                *(self.row(row).dot(other.col(col)) for row in range(3) for col in range(3))
            )
        elif isinstance(other, Vec2):
            extended = Vec3(other.x, other.y, 1.0)
            return Vec2(
                 self.row(0).dot(extended),
                 self.row(1).dot(extended)
            )
        elif isinstance(other, Vec3):
            return Vec3(*(self.row(i).dot(other) for i in range(3)))
        elif isinstance(other, Number):
            return Mat3(*(x * other for x in self._mat))
        else:
            return NotImplemented

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
         return self.cofactor().transpose().mul(1 / self.det())

    def is_finite(self):
        return all(isinstance(e, Number) and isfinite(e) for e in self._mat)

    def col(self, num):
        self._check_dim(num, True)
        return Vec3(self._mat[num], self._mat[num + 3], self._mat[num + 6])

    def row(self, num):
        self._check_dim(num, False)
        return Vec3(self._mat[num * 3], self._mat[num * 3 + 1], self._mat[num * 3 + 2])

    def transpose(self):
        return Mat3(
           self._mat[0], self._mat[3], self._mat[6],
           self._mat[1], self._mat[4], self._mat[7],
           self._mat[2], self._mat[5],self._mat[8]
        )

    def minor(self, col, row):
        self._check_dim(row, False)
        self._check_dim(col, True)
        col0 = 1 if col == 0 else 0
        col1 = col0 + (2 if col == 1 else 1)
        row0 = 1 if row == 0 else 0
        row1 = row0 + (2 if row == 1 else 1)
        return Mat2(
            self.elem(col0, row0), self.elem(col1, row0),
            self.elem(col0, row1), self.elem(col1, row1)
        )

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

    def elem(self, col, row):
        self._check_dim(col, True)
        self._check_dim(row, False)
        return self._mat[row * 3 + col]

    def get_translation(self):
        return Vec2(self._mat[2], self._mat[5])

    def get_direction(self):
        return self.minor(2, 2).mul(Vec2(1, 0))

    def _check_dim(self, num, col):
        option = 'column' if col else 'row'
        if not isinstance(num, int) or num < 0 or num > 2:
            raise ValueError(f'Bad {option} number {num}')

    def __mul__(self, other):
        return self.mul(other)

    def __eq__(self, other):
        return isinstance(other, Mat3) and self._mat == other._mat

    def __hash__(self):
        return hash(self._mat)

    def __repr__(self):
        return f'Mat3({", ".join(repr(e) for e in self._mat)})'

class Vec2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def zero(cls):
        return cls._ZERO

    def add(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x + other.x, self.y + other.y)
        elif isinstance(other, Number):
            return Vec2(self.x + other, self.y + other)
        else:
            return NotImplemented

    def mul(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x * other.x, self.y * other.y)
        elif isinstance(other, Number):
            return Vec2(self.x * other, self.y * other)
        else:
            return NotImplemented

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def len(self):
        return sqrt(self.dot(self))

    def get_angle(self):
        return atan2(self.y, self.x)

    def unit(self):
        return self.mul(1 / self.len())

    def angle_with(self, other):
        return acos(self.unit().dot(other.unit()))

    def is_finite(self):
        return isfinite(self.x) and isfinite(self.y)

    def proj(self, projectee):
        return self.mul(self.dot(projectee) / self.dot(self))

    def get_perpendicular(self):
        return Vec2(1, -self.x / self.y) if self.y else Vec2(1, 0)

    def __add__(self, other):
        return self.add(other)

    def __radd__(self, other):
        return self.add(other)

    def __sub__(self, other):
        return self.add(-other)

    def __rsub__(self, other):
        return self.mul(-1).add(other)

    def __neg__(self):
        return self.mul(-1)

    def __mul__(self, other):
        return self.mul(other)

    def __rmul__(self, other):
        return self.mul(other)

    def __truediv__(self, other):
        return self.mul(1 / other)

    def __rtruediv__(self, other):
        return Vec2(other / self.x, other / self.y)

    def __floor__(self):
        return Vec2(int(floor(self.x)), int(floor(self.y)))

    def __eq__(self, other):
        return isinstance(other, Vec2) and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f'Vec2({repr(self.x)}, {repr(self.y)})'

Vec2._ZERO = Vec2(0, 0)

class Vec3:
    def __init__(self, x, y, z):
        self._vec = [x, y, z]

    @classmethod
    def zero(cls):
        return Vec3(0, 0, 0)

    def get_x(self):
        return self._vec[0]

    def get_y(self):
        return self._vec[1]

    def get_z(self):
        return self._vec[2]

    def add(self, other):
        return Vec3(*(a + b for a, b in zip(self._vec, other._vec)))

    def dot(self, other):
        return sum(a * b for a, b in zip(self._vec, other._vec))

    def get(self, index):
        if not isinstance(index, int) or index < 0 or index > 2:
            raise ValueError(f'Bad index {index}')
        return self._vec[index]

    def __add__(self, other):
        return self.add(other)

    def __mul__(self, other):
        return self.mul(other)

    def __eq__(self, other):
        return isinstance(other, Vec3) and self._vec == other._vec

    def __hash__(self):
        return hash(self._vec)

    def __repr__(self):
        return f'Vec3({", ".join(repr(e) for e in self._vec)})'
