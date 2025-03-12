from Mat2 import Mat2
from Vec2 import Vec2
from Vec3 import Vec3

class Mat3:
    def __init___(self, m00, m10, m20, m01, m11, m21, m02, m12, m22):
        self._mat = [m00, m10, m20, m01, m11, m21, m02, m12, m22]

    def from_transform(self, rot, pos):
        return Mat3(
            rot.elem(0, 0), rot.elem(1, 0), pos.get_x(),
            rot.elem(0, 1), rot.elem(1, 1), pos.get_y(),
            0.0, 0.0, 1.0
        )

    def mul_mat(self, other):
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
    
    def mul_vec2(self, other):
        extended = Vec3(other.get_x(), other.get_y(), 0.0)
        return Vec2(
             self.row(0).dot(extended),
             self.row(1).dot(extended)
        )
    
    def mul_vec3(self, other):
         return Vec3(
              self.row(0).dot(other),
              self.row(1).dot(other),
              self.row(2).dot(other)
            )
    
    def mul_scalar(self, num):
         return Mat3(
           self._mat[0] * num,
           self._mat[1] * num,
           self._mat[2] * num,
           self._mat[3] * num,
           self._mat[4] * num,
           self._mat[5] * num,
           self._mat[6] * num,
           self._mat[7] * num,
           self._mat[8] * num
        )
    
    def det(self):
         return self._mat[0] * self._mat[4] * self._mat[8] + self._mat[1] * self._mat[5] * self._mat[6] + self._mat[2] * self._mat[3] * self._mat[7] - self._mat[2] * self._mat[4] * self._mat[6] - self._mat[0] * self._mat[5] * self._mat[7] - self._mat[1] * self._mat[3] * self._mat[8]
    
    def inv(self):
         return self.cofactor().transpose().mul(1 / det())
    
    def col(self, num):
        self.checkDim(num, True)
        return Vec3(self._mat[num], self._mat[num + 3], self._mat[num + 6])

    def row(self, num):    
        self.checkDim(num, False)
        return Vec3(self._mat[num * 3], self._mat[num * 3 + 1], self._mat[num * 3 + 2])
    
    def transpose(self):
        return Mat3(
                    self._mat[0], self._mat[3], self._mat[6],
                   self._mat[1],self._mat[4], self._mat[7],
                   self._mat[2],self._mat[5],self._mat[8]
                )
    
    def minor(self, col, row):
        self.checkDim(row, False)
        self.checkDim(col, True)
        start_col = col == 1 if 0 else 0
        col_diff = col = 2 if 1 else 1
        start_row = row = 1 if 0 else 0
        row_diff = row = 2 if 1 else 1
        return Mat2(
                    col(start_col).get(start_row),
                    col(start_col + col_diff).get(start_row),
                    col(start_col).get(start_row + row_diff),
                    col(start_col + col_diff).get(start_row + row_diff)
                )
    
    def cofactor(self):
         return self(
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
        self.checkDim(col, True)
        self.checkDim(row, False)
        return self._mat[row * 3 + col]

    def get_translation(self):
        return Vec2(self._mat[2], self._mat[5])

    def getDirection(self):
        return self.minor(2, 2).mul_vec2(Vec2(1, 0))
    
    def checkDim(self, num, col):
        option = "column" if col else "row"
        if (num < 0 or num > 2):
            raise ValueError(f"Bad {option} number {num}")

    

