from math import inf
from math import nan
from math import pi
from matrix import Mat2
from matrix import Mat3
from matrix import Vec2
from matrix import Vec3
from unittest import TestCase

def _assert_matrix_almost_equal(a, b, data_getter, test_case):
    test_case.longMessage = True
    for c, d in zip(data_getter(a), data_getter(b)):
        test_case.assertAlmostEqual(c, d, msg=f'{repr(a)} !~= {repr(b)}')

class TestMat2(TestCase):
    def test_create(self):
        self.assertIsInstance(Mat2.identity(), Mat2)

    def test_eq(self):
        self.assertEqual(Mat2(1, 2, 3, 4), Mat2(1, 2, 3, 4))

    def test_from_angle(self):
        _assert_matrix_almost_equal(
            Mat2.from_angle(pi / 2),
            Mat2(0, -1, 1, 0),
            lambda mat: mat._mat,
            self
        )

    def test_mul_mat(self):
        self.assertEqual(
            Mat2(1, -2, 3, 1).mul(Mat2(3, 1, 0, -1)),
            Mat2(3, 3, 9, 2)
        )

    def test_mul_vec(self):
        self.assertEqual(
            Mat2(1, 2, 2, 1).mul(Vec2(3, 5)),
            Vec2(13, 11)
        )

    def test_mul_scalar(self):
        self.assertEqual(
            Mat2(1, 1, 1, 1).mul(4),
            Mat2(4, 4, 4, 4)
        )
        self.assertEqual(
            Mat2(1, 1, 1, 1).mul(4.0),
            Mat2(4, 4, 4, 4)
        )

    def test_mul_nonfinite_is_nonfinite(self):
        self.assertFalse(Mat2(1, 1, 1, 1).mul(inf).is_finite())
        self.assertFalse(Mat2(1, 1, 1, 1).mul(nan).is_finite())

    def test_mul_type(self):
        with self.assertRaises(ValueError):
            Mat2(1, 1, 1, 1).mul(None)
        with self.assertRaises(ValueError):
            Mat2(1, 1, 1, 1).mul('foobar')
        with self.assertRaises(ValueError):
            Mat2(1, 1, 1, 1).mul(Vec3.zero())
        with self.assertRaises(ValueError):
            Mat2(1, 1, 1, 1).mul(Mat3.identity())

    def test_det(self):
        self.assertEqual(
            Mat2(1, 2, 3, 4).det(),
            -2
        )

    def test_inv(self):
        _assert_matrix_almost_equal(
            Mat2(1, 5, 0, 1).inv(),
            Mat2(1, -5, 0, 1),
            lambda mat: mat._mat,
            self
        )

    def test_is_finite(self):
        self.assertTrue(Mat2(-5, 0, -2, 1).is_finite())
        self.assertFalse(Mat2('foobar', 0, 3, 8).is_finite())
        self.assertFalse(Mat2(0, inf, 1, 0).is_finite())
        self.assertFalse(Mat2(nan, -8, 0, 2).is_finite())
    
    def test_col(self):
        self.assertEqual(
            Mat2(0, 1, 2, 3).col(0),
            Vec2(0, 2)
        )

    def test_col_negative_idx(self):
        with self.assertRaises(ValueError):
            Mat2(0, 1, 2, 3).col(-1)

    def test_col_large_idx(self):
        with self.assertRaises(ValueError):
            Mat2(0, 1, 2, 3).col(2)

    def test_col_idx_type(self):
        with self.assertRaises(ValueError):
            Mat2(0, 1, 2, 3).col(1.0)
        with self.assertRaises(ValueError):
            Mat2(0, 1, 2, 3).col('potato')

    def test_row(self):
        self.assertEqual(
            Mat2(0, 1, 2, 3).row(0),
            Vec2(0, 1)
        )

    def test_row_negative_idx(self):
        with self.assertRaises(ValueError):
            Mat2(0, 1, 2, 3).row(-1)

    def test_row_large_idx(self):
        with self.assertRaises(ValueError):
            Mat2(0, 1, 2, 3).row(2)

    def test_row_idx_type(self):
        with self.assertRaises(ValueError):
            Mat2(0, 1, 2, 3).row(1.0)
        with self.assertRaises(ValueError):
            Mat2(0, 1, 2, 3).row('potato')

    def test_elem(self):
        self.assertEqual(
            Mat2(0, 1, 2, 3).elem(1, 1),
            3
        )

class TestMat3(TestCase):
    def test_create(self):
        self.assertIsInstance(Mat3.identity(), Mat3)

    def test_eq(self):
        self.assertEqual(Mat3(*range(9)), Mat3(*range(9)))

    def test_from_transform(self):
        self.assertEqual(
            Mat3.from_transform(Mat2.identity(), Vec2(0, 0)),
            Mat3.identity()
        )
    
    def test_mul_mat(self):
        self.assertEqual(
            Mat3(*range(9)).mul(Mat3.identity()),
            Mat3(*range(9))
        )

    def test_mul_vec(self):
        self.assertEqual(
            Mat3.identity().mul(Vec3(1, 2, 3)),
            Vec3(1, 2, 3)
        )

    def test_mul_scalar(self):
        self.assertEqual(
            Mat3(*range(9)).mul(4),
            Mat3(*range(0, 36, 4))
        )
        self.assertEqual(
            Mat3(*range(9)).mul(4.0),
            Mat3(*range(0, 36, 4))
        )

    def test_mul_nonfinite_is_nonfinite(self):
        self.assertFalse(Mat3(*range(9)).mul(inf).is_finite())
        self.assertFalse(Mat3(*range(9)).mul(nan).is_finite())

    def test_mul_type(self):
        with self.assertRaises(ValueError):
            Mat3(*range(9)).mul(None)
        with self.assertRaises(ValueError):
            Mat3(*range(9)).mul('foobar')
        with self.assertRaises(ValueError):
            Mat3(*range(9)).mul(Mat2.identity())

    def test_det(self):
        self.assertEqual(
            Mat3(2, 0, 0, 0, 4, 0, 0, 0, 6).det(),
            48
        )

    def test_inv(self):
        self.assertEqual(
            Mat3.identity().inv(),
            Mat3.identity()
        )

    def test_is_finite(self):
        self.assertTrue(Mat3.identity().is_finite())
        self.assertFalse(Mat3('foobar', *range(8)).is_finite())
        self.assertFalse(Mat3(0, inf, *range(7)).is_finite())
        self.assertFalse(Mat3(nan, *range(8)).is_finite())

    def test_col(self):
        self.assertEqual(
            Mat3(*range(9)).col(0),
            Vec3(0, 3, 6)
        )

    def test_col_negative_idx(self):
        with self.assertRaises(ValueError):
            Mat3.identity().col(-1)

    def test_col_large_idx(self):
        with self.assertRaises(ValueError):
            Mat3.identity().col(3)

    def test_col_idx_type(self):
        with self.assertRaises(ValueError):
            Mat3.identity().col(1.0)
        with self.assertRaises(ValueError):
            Mat3.identity().col('potato')

    def test_row(self):
        self.assertEqual(
            Mat3(*range(9)).row(0),
            Vec3(0, 1, 2)
        )

    def test_row_negative_idx(self):
        with self.assertRaises(ValueError):
            Mat3.identity().row(-1)

    def test_row_large_idx(self):
        with self.assertRaises(ValueError):
            Mat3.identity().row(3)

    def test_row_idx_type(self):
        with self.assertRaises(ValueError):
            Mat3.identity().row(1.0)
        with self.assertRaises(ValueError):
            Mat3.identity().row('potato')

    def test_elem(self):
        self.assertEqual(
            Mat3(*range(9)).elem(1, 1),
            4
        )

    def test_transpose(self):
        self.assertEqual(
            Mat3(*range(9)).transpose(),
            Mat3(
                0, 3, 6,
                1, 4, 7,
                2, 5, 8
            )
        )

    def test_minor(self):
        self.assertEqual(
            Mat3(*range(9)).minor(1, 1),
            Mat2(0, 2, 6, 8)
        )

    def test_cofactor(self):
        self.assertEqual(
            Mat3(1, 0, -1, 3, 1, 2, 0, -2, 1).cofactor(),
            Mat3(5, -3, -6, 2, 1, 2, 1, -5, 1)
        )

    def test_get_translation(self):
        self.assertEqual(
            Mat3.from_transform(Mat2.identity(), Vec2(5, 6)).get_translation(),
            Vec2(5, 6)
        )

    def test_get_direction(self):
        self.assertAlmostEqual(
            Mat3.from_transform(
                Mat2.from_angle(pi / 4),
                Vec2(123, 345)
            ).get_direction().angle_with(Vec2(1, 1)),
            0
        )

class TestVec2(TestCase):
    def test_create(self):
        self.assertIsInstance(Vec2.zero(), Vec2)

    def test_eq(self):
        self.assertEqual(Vec2(1, 2), Vec2(1, 2))

    def test_x(self):
        self.assertEqual(Vec2(1, 2).get_x(), 1)

    def test_y(self):
        self.assertEqual(Vec2(1, 2).get_y(), 2)

    def test_add(self):
        self.assertEqual(
            Vec2(13, 2).add(Vec2(4, -5)),
            Vec2(17, -3)
        )

    def test_mul(self):
        self.assertEqual(
            Vec2(-2, 5).mul(4),
            Vec2(-8, 20)
        )

    def test_dot(self):
        self.assertEqual(Vec2(4, 4).dot(Vec2(-2, 2)), 0)

    def test_len(self):
        self.assertEqual(Vec2(3, 4).len(), 5)

    def get_angle(self):
        self.assertEqual(Vec2(1, 0), 0)
        self.assertEqual(Vec2(0, 1), pi / 2)
        self.assertEqual(Vec2(-1, 0), pi)
        self.assertEqual(Vec2(0, -1), 3 * pi / 2)

    def test_unit_len(self):
        self.assertEqual(Vec2(134214, -89173).unit().len(), 1)

    def test_angle_with(self):
        self.assertEqual(Vec2(0, 1).angle_with(Vec2(1, 0)), pi / 2)
        self.assertEqual(Vec2(1, 0).angle_with(Vec2(-1, 0)), pi)
    
    def test_is_finite(self):
        self.assertTrue(Vec2(1, -1).is_finite())
        self.assertFalse(Vec2(nan, 0).is_finite())
        self.assertFalse(Vec2(0, -inf).is_finite())

    def test_proj(self):
        self.assertEqual(Vec2(1, 0).proj(Vec2(5, -7)), Vec2(5, 0))

    def test_perpendicular(self):
        self.assertEqual(Vec2(123, 456).get_perpendicular().dot(Vec2(123, 456)), 0)

class TestVec3(TestCase):
    def test_create(self):
        self.assertIsInstance(Vec3.zero(), Vec3)

    def test_eq(self):
        self.assertEqual(Vec3(1, 2, 3), Vec3(1, 2, 3))

    def test_x(self):
        self.assertEqual(Vec3(1, 2, 3).get_x(), 1)

    def test_y(self):
        self.assertEqual(Vec3(1, 2, 3).get_y(), 2)

    def test_z(self):
        self.assertEqual(Vec3(1, 2, 3).get_z(), 3)

    def test_add(self):
        self.assertEqual(
            Vec3(1, 2, 3).add(Vec3(6, 5, 4)),
            Vec3(7, 7, 7)
        )

    def test_dot(self):
        self.assertEqual(
            Vec3(1, 1, 1).dot(Vec3(-1, 0, 1)),
            0
        )

    def test_get(self):
        self.assertEqual(Vec3(1, 2, 3).get(1), 2)

    def test_get_range(self):
        with self.assertRaises(ValueError):
            Vec3(1, 2, 3).get(-1)
        with self.assertRaises(ValueError):
            Vec3(1, 2, 3).get(3)

    def test_get_type(self):
        with self.assertRaises(ValueError):
            Vec3(1, 2, 3).get(1.0)
        with self.assertRaises(ValueError):
            Vec3(1, 2, 3).get('foo')
