from unittest import TestCase
from matrix import Mat2
from matrix import Mat3
from matrix import Vec2
from matrix import Vec3

class TestMat2(TestCase):
    def test_create(self):
        self.assertIsInstance(Mat2(1, 0, 0, 1), Mat2)

    def test_eq(self):
        self.assertEqual(Mat2(1, 2, 3, 4), Mat2(1, 2, 3, 4))

    def test_mul(self):
        self.assertEqual(
            Mat2(1, -2, 3, 1).mul(Mat2(3, 1, 0, -1)),
            Mat2(3, 3, 9, 2)
        )
        self.assertEqual(
            Mat2(1, 2, 2, 1).mul(Vec2(3, 5)),
            Vec2(13, 11)
        )
        self.assertEqual(
            Mat2(1, 1, 1, 1).mul(4),
            Mat2(4, 4, 4, 4)
        )

    def test_det(self):
        self.assertEqual(
            Mat2(1, 2, 3, 4).det(),
            -2
        )

    def test_inv(self):
        self.assertEqual(
            Mat2(1, 5, 0, 1).inv(),
            Mat2(1, -5, 0, 1)
        )

    def test_isfinite(self):
        self.assertTrue(Mat2(-5, 0, -2, 1).isfinite())
        self.assertFalse(Mat2('foobar', 0, 3, 8).isfinite())
        self.assertFalse(Mat2(0, float('inf'), 1, 0).isfinite())
        self.assertFalse(Mat2(float('nan'), -8, 0, 2).isfinite())
    
    def test_col(self):
        self.assertEqual(
            Mat2(0, 1, 2, 3).col(0),
            Vec2(0, 2)
        )
        with self.assertThrows(ValueError):
            Mat2(0, 1, 2, 3).col(-1)
        with self.assertThrows(ValueError):
            Mat2(0, 1, 2, 3).col(2)
        with self.assertThrows(ValueError):
            Mat2(0, 1, 2, 3).col(1.0)
        with self.assertThrows(ValueError):
            Mat2(0, 1, 2, 3).col('potato')

    def test_row(self):
        self.assertEqual(
            Mat2(0, 1, 2, 3).row(0),
            Vec2(0, 1)
        )
        with self.assertThrows(ValueError):
            Mat2(0, 1, 2, 3).row(-1)
        with self.assertThrows(ValueError):
            Mat2(0, 1, 2, 3).row(2)
        with self.assertThrows(ValueError):
            Mat2(0, 1, 2, 3).row(1.0)
        with self.assertThrows(ValueError):
            Mat2(0, 1, 2, 3).row('potato')

    def test_elem(self):
        self.assertEqual(
            Mat2(0, 1, 2, 3).elem(1, 1),
            3
        )

class TestMat3(TestCase):
    pass

class TestVec2(TestCase):
    pass

class TestVec3(TestCase):
    pass
