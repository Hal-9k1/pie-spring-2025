from localization.source import AbstractStaticObstacleLocalizationSource
from array import array
from matrix import Mat2
from matrix import Vec2
from multiprocessing import Pool
from units import convert
import math


class _ImageG8:
    def __init__(self, width, height, data=None):
        self._width = width
        self._height = height
        self._data = array('B', data or [0] * width * height)

    def get_interp(self, x, y):
        x_norm = max(0, min(self._width - 1, x * (self._width - 1)))
        y_norm = max(0, min(self._height - 1, y * (self._height - 1)))
        x_frac = x_norm % 1
        x_comp = 1 - x_frac
        y_frac = y_norm % 1
        y_comp = 1 - y_frac
        x_high = min(self._width, int(math.floor(x_norm + 1)))
        x_low = int(x_norm)
        y_high = min(self._height, int(math.floor(y_norm + 1)))
        y_low = int(y_norm)
        p00 = self._data[self._index(x_low, y_low)]
        p10 = self._data[self._index(x_high, y_low)]
        p01 = self._data[self._index(x_low, y_high)]
        p11 = self._data[self._index(x_high, y_high)]
        return (
            p00 * x_comp * y_comp +
            p10 * x_frac * y_comp +
            p01 * x_comp * y_frac +
            p11 * x_frac * y_frac
        )

    def _draw_chunk(self, kernel, userdata, result, start, end):
        for i in range(start, end):
            yf = i // self._width / self._height
            xf = (i % self._width) / self._width
            res = kernel(xf, yf, userdata) if userdata else kernel(xf, yf)
            result[i - start] = int(res)
        return result

    def draw(self, kernel, num_threads=1, userdata=None):
        total_px = self._width * self._height
        if num_threads == 1:
            self._draw_chunk(kernel, userdata, self._data, 0, total_px)
        else:
            self._data = array('B')
            px_per_chunk = total_px // num_threads
            last_px_per_chunk = total_px - (num_threads - 1) * px_per_chunk
            def to_args(i):
                is_last_chunk = i == num_threads - 1
                num_px = last_px_per_chunk if is_last_chunk else px_per_chunk
                buf = array('B', [0] * num_px)
                start = px_per_chunk * i
                end = total_px if is_last_chunk else start + px_per_chunk
                return (self, kernel, userdata, buf, start, end)
            with Pool(num_threads) as pool:
                for chunk in pool.starmap(type(self)._draw_chunk, [to_args(i) for i in range(num_threads)]):
                    self._data.extend(chunk)

    def _template_match_chunk(self, template, result, start, end):
        result_width = self._width - template._width
        result_height = self._height - template._height
        template_px = template._width * template._height
        for i in range(start, end):
            ay = i // result_width
            ax = i % result_width
            err = 0
            for by in range(template._height):
                for bx in range(template._width):
                    a = self._data[self._index(ax + bx, ay + by)]
                    b = template._data[template._index(bx, by)]
                    err += abs(a - b)
            # Use ceil so 0 error always means exact match
            result[i - start] = math.ceil(
                -255 * (math.exp(-err / 2 / template_px / 64) - 1)
            )
        return result

    def template_match(self, template, num_threads=1):
        result_width = self._width - template._width
        result_height = self._height - template._height
        result = _ImageG8(result_width, result_height)
        total_px = result_width * result_height
        if num_threads == 1:
            self._template_match_chunk(template, result._data, 0, total_px)
        else:
            result._data = array('B')
            px_per_chunk = total_px // num_threads
            last_px_per_chunk = total_px - (num_threads - 1) * px_per_chunk
            def to_args(i):
                is_last_chunk = i == num_threads - 1
                num_px = last_px_per_chunk if is_last_chunk else px_per_chunk
                buf = array('B', [0] * num_px)
                start = px_per_chunk * i
                end = total_px if is_last_chunk else start + px_per_chunk
                return (self, template, buf, start, end)
            with Pool(num_threads) as pool:
                for chunk in pool.starmap(type(self)._template_match_chunk, [to_args(i) for i in range(num_threads)]):
                    result._data.extend(chunk)
        return result

    def _convolve_chunk(self, kernel, result, start, end):
        cxl = kernel._width // 2
        cyl = kernel._height // 2
        for i in range(start, end):
            ay = i // self._width
            ax = i % self._width
            v = 0
            for by in range(kernel._height):
                ayi = min(self._height - 1, max(0, ay - cyl + by))
                for bx in range(kernel._width):
                    axi = min(self._width - 1, max(0, ax - cxl + bx))
                    d = self._data[self._index(axi, ayi)]
                    w = kernel._data[kernel._index(bx, by)] / 128 - 1
                    v += d * w
            result[i - start] = int(max(0, min(255, v)))
        return result

    def convolve(self, kernel, num_threads=1):
        result = type(self)(self._width, self._height)
        total_px = self._width * self._height
        if num_threads == 1:
            self._convolve_chunk(kernel, result._data, 0, total_px)
        else:
            result._data = array('B')
            px_per_chunk = total_px // num_threads
            last_px_per_chunk = total_px - (num_threads - 1) * px_per_chunk
            def to_args(i):
                is_last_chunk = i == num_threads - 1
                num_px = last_px_per_chunk if is_last_chunk else px_per_chunk
                buf = array('B', [0] * num_px)
                start = px_per_chunk * i
                end = total_px if is_last_chunk else start + px_per_chunk
                return (self, kernel, buf, start, end)
            with Pool(num_threads) as pool:
                for chunk in pool.starmap(type(self)._convolve_chunk, [to_args(i) for i in range(num_threads)]):
                    result._data.extend(chunk)
        return result

    def square_blur(self, size, num_threads=1):
        return self.convolve(
            _ImageG8(size, size, [int(128 / size**2 + 128)] * size**2),
            num_threads=num_threads
        )

    def gaussian_blur(self, size, num_threads=1):
        kernel = type(self)(size, size)
        kernel.draw(
            type(self)._gaussian_kernel_draw_kernel,
            num_threads=num_threads,
            userdata=size
        )
        return self.convolve(
            kernel,
            num_threads=num_threads
        )

    def _gaussian_kernel_draw_kernel(x, y, userdata):
        size = userdata
        x = size * (x - 0.5)
        y = size * (y - 0.5)
        s = size / 4
        return 128 * (1 + math.exp(-(x*x + y*y) / (2 * s * s)) / (2 * math.pi * s * s))

    def rotate(self, angle, anchor, fill, num_threads=1):
        result = _ImageG8(self._width, self._height)
        tfm = Mat2.from_angle(-angle)
        anchor_norm = Vec2(anchor.get_x() / self._width, anchor.get_y() / self._height)
        result.draw(
            type(self)._draw_transformed_kernel,
            num_threads=num_threads,
            userdata=(self, tfm, anchor_norm, fill)
        )
        return result

    def _draw_transformed_kernel(x, y, userdata):
        self, tfm, anchor, fill = userdata
        pos = tfm * (Vec2(x * self._width, y * self._height) - anchor) + anchor
        rx = pos.get_x()
        ry = pos.get_y()
        if rx < 0 or rx >= self._width or ry < 0 or ry >= self._height:
            return fill
        return self.get_interp(rx / (self._width - 1), ry / (self._height - 1))

    def _index(self, x, y):
        return self._width * y + x


class TemplateMatchingLocalizationSource(AbstractStaticObstacleLocalizationSource):
    DETECTION_LIFETIME = 1
    PX_PER_M = 50
    FIELD_OUTLINE_RADIUS_CM = 8
    MAX_DETECTION_DIST_CM = 100
    DETECTION_RADIUS_CM = 2
    FIELD_DRAW_THREADS = 8
    DETECTIONS_DRAW_THREADS = 8
    ROTATION_VARIANTS = 16

    def __init__(self, field, field_img=None):
        super().__init__(self.DETECTION_LIFETIME)
        self._size_m = field.get_size()
        self._size_px = math.floor(self._size_m * self.PX_PER_M)
        self.FIELD_OUTLINE_RADIUS_PX = self.FIELD_OUTLINE_RADIUS_CM / 100 * self.PX_PER_M
        self.DETECTION_RADIUS_PX = self.DETECTION_RADIUS_CM / 100 * self.PX_PER_M
        if field_img:
            self._field_img = field_img
        else:
            self._field_img = _ImageG8(self._size_px.get_x(), self._size_px.get_y())
            obstacles = field.get_pathfinding_obstacles()
            self._field_img.draw(
                type(self)._draw_field_kernel,
                num_threads=self.FIELD_DRAW_THREADS,
                userdata=(self, obstacles)
            )

    def get_field_image(self):
        return self._field_img

    def _localize_from_detections(self, dets):
        detection_dist_px = int(self.MAX_DETECTION_DIST_CM / 100 * self.PX_PER_M)
        template = _ImageG8(2 * detection_dist_px, detection_dist_px)
        points = [
            convert(Vec2(
                det.get_distance() * (1 + math.cos(det.get_angle())),
                det.get_distance() * math.sin(det.get_angle())
            ), 'cm', 'm')
            for det in dets if det.get_distance() < self.MAX_DETECTION_DIST_CM
        ]
        template.draw(
            type(self)._draw_detections_kernel,
            num_threads=self.DETECTIONS_DRAW_THREADS,
            userdata=(self, points)
        )
        return template
        match_results = [
            self._field_img.template_match(
                template.rotate(
                    2 * math.pi * i / self.ROTATION_VARIANTS,
                )
            )
            for i in range(self.ROTATION_VARIANTS)
        ]
        # get localization data from match_results

    def _draw_field_kernel(x, y, userdata):
        self, obstacles = userdata
        radius_m = self.FIELD_OUTLINE_RADIUS_PX / self.PX_PER_M
        point = Vec2(x * self._size_m.get_x(), y * self._size_m.get_y())
        sum_abs_dist = sum([
            min(
                abs(o.get_distance_to(point)),
                radius_m
            )
            for o in obstacles
        ])
        norm_dist = max(0, min(1, sum_abs_dist / radius_m - len(obstacles) + 1))
        return (1 - norm_dist) * 255

    def _draw_detections_kernel(x, y, userdata):
        self, points = userdata
        radius_m = self.DETECTION_RADIUS_PX / self.PX_PER_M
        sum_abs_dist = sum([
            (point - Vec2(x * self._size_m.get_x(), y * self._size_m.get_y())).len()
            for point in points
        ])
        norm_dist = max(0, min(1, sum_abs_dist / radius_m - len(points) + 1))
        return (1 - norm_dist) * 255
