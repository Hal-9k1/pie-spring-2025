import math
from Mat2 import Mat2

class Mat3:
    def __init___(self, m00, m10, m20, m01, m11, m21, m02, m12, m22):
        self.mat = [m00, m10, m20, m01, m11, m21, m02, m12, m22]

    def from_transform(self, rot, pos):
        return Mat3(
            rot.elem(0, 0), rot.elem(1, 0), pos.get_X(),
            rot.elem(0, 1), rot.elem(1, 1), pos.get_Y(),
            0.0, 0.0, 1.0
        )

    def mul_mat(self, other):
            return Mat3(
                    Mat3.row(0).dot(other.col(0)),
                    Mat3.row(0).dot(other.col(1)),
                    Mat3.row(0).dot(other.col(2)),
                    Mat3.row(1).dot(other.col(0)),
                    Mat3.row(1).dot(other.col(1)),
                    Mat3.row(1).dot(other.col(2)),
                    Mat3.row(2).dot(other.col(0)),
                    Mat3.row(2).dot(other.col(1)),
                    Mat3.row(2).dot(other.col(2))
            )
    
    def mul_vec2(self, other):
        extended = Vec3(other.get_X(), other.get_Y(), 0.0)
        return Vec2(
             Mat3.row(0).dot(extended),
             Mat3.row(1).dot(extended)
        )
    
    def mul_vec3(self, other):
         return Vec3(
              Mat3.row(0).dot(other),
              Mat3.row(1).dot(other),
              Mat3.row(2).dot(other)
            )
    
    def mul_scalar(self, num):
         return Mat3(
           self.mat[0] * num,
           self.mat[1] * num,
           self.mat[2] * num,
           self.mat[3] * num,
           self.mat[4] * num,
           self.mat[5] * num,
           self.mat[6] * num,
           self.mat[7] * num,
           self.mat[8] * num
        )
    
    def det(self):
         return self.mat[0] *self.mat[4] *self.mat[8] + self.mat[1] *self.mat[5] *self.mat[6] + self.mat[2] *self.mat[3] *self.mat[7] - self.mat[2] *self.mat[4] *self.mat[6] - self.mat[0] *self.mat[5] *self.mat[7] - self.mat[1] *self.mat[3] *self.mat[8]
    
    def inv(self):
         return cofactor().transpose().mul(1 / det())
    
    def col(self, num):
        Mat3.checkDim(num, True)
        return Vec3(mat[num],self.mat[num + 3],self.mat[num + 6])

    def row(self, num):    
        Mat3.checkDim(num, False)
        return Vec3(self.mat[num * 3], self.mat[num * 3 + 1], self.mat[num * 3 + 2])
    
    def transpose(self):
        return Mat3(
                    self.mat[0], self.mat[3], self.mat[6],
                   self.mat[1],self.mat[4], self.mat[7],
                   self.mat[2],self.mat[5],self.mat[8]
                )
    
    def minor(self, col, row):
        Mat3.checkDim(row, False)
        Mat3.checkDim(col, True)
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
         return Mat3(
            Mat3.minor(0, 0).det(),
            -Mat3.minor(1, 0).det(),
            Mat3.minor(2, 0).det(),
            -Mat3.minor(0, 1).det(),
            Mat3.minor(1, 1).det(),
            -Mat3.minor(2, 1).det(),
            Mat3.minor(0, 2).det(),
            -Mat3.minor(1, 2).det(),
            Mat3.minor(2, 2).det()
        )

