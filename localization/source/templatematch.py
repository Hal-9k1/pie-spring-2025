from localization.source import AbstractStaticObstacleLocalizationSource
from array import array
from matrix import Mat2
from matrix import Mat3
from matrix import Vec2
from multiprocessing import Pool
from units import convert
import math


class ImageG8:
    GAUSSIAN_KERNELS = {}

    def __init__(self, width, height, data=None):
        self._width = width
        self._height = height
        self._data = array('B', data or [0] * width * height)

    def get_norm(self, x, y):
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

    def get(self, x, y):
        return self._data[self._index(x, y)]

    def _draw_chunk(self, kernel, userdata, result, start, end):
        for i in range(start, end):
            yf = i // self._width / self._height
            xf = (i % self._width) / self._width
            res = kernel(xf, yf, userdata) if userdata else kernel(xf, yf)
            result[i - start] = int(res)
        return result

    def draw(self, kernel, num_threads=1, process_pool=None, userdata=None):
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
            args = [to_args(i) for i in range(num_threads)]
            try:
                pool = process_pool or Pool(num_threads)
                for chunk in pool.starmap(type(self)._draw_chunk, args):
                    self._data.extend(chunk)
            finally:
                if not process_pool:
                    pool.terminate()

    def _paste_chunk(self, location, image, result, start, end):
        for i in range(start, end):
            y = i // image._width
            x = i % image._width
            ay = y + location.get_y()
            ax = x + location.get_x()
            if ax < self._width and ay < self._height:
                result[i - start] = min(
                    255,
                    image._data[image._index(x, y)] + self._data[self._index(ax, ay)]
                )

    def paste(self, location, image, num_threads=1, process_pool=None):
        total_px = image._width * image._height
        if num_threads == 1:
            result = array('B', [0] * total_px)
            self._paste_chunk(location, image, result, 0, total_px)
        else:
            result = array('B')
            px_per_chunk = total_px // num_threads
            last_px_per_chunk = total_px - (num_threads - 1) * px_per_chunk
            def to_args(i):
                is_last_chunk = i == num_threads - 1
                num_px = last_px_per_chunk if is_last_chunk else px_per_chunk
                buf = array('B', [0] * num_px)
                start = px_per_chunk * i
                end = total_px if is_last_chunk else start + px_per_chunk
                return (self, location, image, buf, start, end)
            args = [to_args(i) for i in range(num_threads)]
            try:
                pool = process_pool or Pool(num_threads)
                for chunk in pool.starmap(type(self)._paste_chunk, args):
                    result.extend(chunk)
            finally:
                if not process_pool:
                    pool.terminate()
        for row in range(image._height):
            s = self._index(location.get_x(), location.get_y() + row)
            e = self._index(location.get_x() + image._width, location.get_y() + row)
            self._data[s:e] = result[row * image._width:(row + 1) * image._width]

    def _template_match_chunk(self, template, mask, result, start, end):
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
                    mask_fac = mask._data[mask._index(bx, by)] if mask else 1
                    err += abs(a - b) * mask_fac
            # Use ceil so 0 error always means exact match
            result[i - start] = math.ceil(
                -255 * (math.exp(-err / 2 / template_px / 64) - 1)
            )
        return result

    def template_match(self, template, num_threads=1, process_pool=None, mask=None):
        result_width = self._width - template._width
        result_height = self._height - template._height
        result = ImageG8(result_width, result_height)
        total_px = result_width * result_height
        if num_threads == 1:
            self._template_match_chunk(template, mask, result._data, 0, total_px)
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
                return (self, template, mask, buf, start, end)
            args = [to_args(i) for i in range(num_threads)]
            try:
                pool = process_pool or Pool(num_threads)
                for chunk in pool.starmap(type(self)._template_match_chunk, args):
                    result._data.extend(chunk)
            finally:
                if not process_pool:
                    pool.terminate()
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

    def convolve(self, kernel, num_threads=1, process_pool=None):
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
            args = [to_args(i) for i in range(num_threads)]
            try:
                pool = process_pool or Pool(num_threads)
                for chunk in process_pool.starmap(type(self)._convolve_chunk, args):
                    result._data.extend(chunk)
            finally:
                if not process_pool:
                    pool.terminate()
        return result

    def square_blur(self, size, num_threads=1, process_pool=None):
        return self.convolve(
            ImageG8(size, size, [int(128 / size**2 + 128)] * size**2),
            num_threads=num_threads,
            process_pool=process_pool
        )

    def gaussian_blur(self, size, num_threads=1, process_pool=None, cache_kernel=True):
        if size in self.GAUSSIAN_KERNELS:
            kernel = self.GAUSSIAN_KERNELS[size]
        else:
            kernel = type(self)(size, size)
            kernel.draw(
                type(self)._gaussian_kernel_draw_kernel,
                num_threads=num_threads,
                userdata=(size, (size / 4) ** 2)
            )
            if cache_kernel:
                self.GAUSSIAN_KERNELS[size] = kernel
        return self.convolve(
            kernel,
            num_threads=num_threads,
            process_pool=process_pool
        )

    def _gaussian_kernel_draw_kernel(x, y, userdata):
        size, s2 = userdata
        x = size * (x - 0.5)
        y = size * (y - 0.5)
        return 128 * (1 + math.exp(-(x*x + y*y) / (2 * s2)) / (2 * math.pi * s2))

    def rotate(self, angle, anchor, fill, num_threads=1, process_pool=None):
        tfm = (
            Mat3.from_transform(Mat2.from_angle(angle), anchor)
            * Mat3.from_transform(Mat2.identity(), -anchor)
        )
        corners = [
            tfm * Vec2(x * self._width, y * self._height)
            for x, y in [(0, 0), (1, 0), (0, 1), (1, 1)]
        ]
        xs = [corner.get_x() for corner in corners]
        ys = [corner.get_y() for corner in corners]
        result_width = max(xs) - min(xs)
        result_height = max(ys) - min(ys)
        offset_norm = Vec2(min(xs) / result_width, min(ys) / result_height)
        print(f'anchor {anchor} offset {offset_norm}')
        result = ImageG8(int(result_width), int(result_height))
        reverse_tfm = (
            Mat3.from_transform(Mat2.from_angle(-angle), anchor)
            * Mat3.from_transform(Mat2.identity(), -anchor)
        )
        result.draw(
            type(self)._draw_transformed_kernel,
            userdata=(self, reverse_tfm, offset_norm, result._width, result._height, fill),
            num_threads=num_threads,
            process_pool=process_pool
        )
        return result

    def _draw_transformed_kernel(x, y, userdata):
        self, tfm, offset_norm, result_width, result_height, fill = userdata
        x += offset_norm.get_x()
        y += offset_norm.get_y()
        pos = tfm * Vec2(x * result_width, y * result_height)
        rx = pos.get_x()
        ry = pos.get_y()
        if rx < 0 or rx >= self._width or ry < 0 or ry >= self._height:
            return fill
        return self.get_norm(rx / (self._width), ry / (self._height))

    def norm_to_px(self, norm):
        return Vec2(norm.get_x() * self._width, norm.get_y() * self._height)

    def _index(self, x, y):
        return self._width * y + x


class TemplateMatchingLocalizationSource(AbstractStaticObstacleLocalizationSource):
    DETECTION_LIFETIME = 1
    PX_PER_M = 50
    FIELD_OUTLINE_RADIUS_PX = 4
    MAX_DETECTION_DIST_M = 0.1
    DETECTION_RADIUS_PX = 4
    FIELD_DRAW_THREADS = 8
    DETECTION_DRAW_THREADS = 8
    TEMPLATE_MATCH_THREADS = 8
    ROTATION_VARIANTS = 16

    def __init__(self, field, field_img=None, detection_img=None):
        super().__init__(self.DETECTION_LIFETIME)
        self._size_m = field.get_size()
        self._size_px = math.floor(self._size_m * self.PX_PER_M)
        if (field_img
                and field_img[0] == self.PX_PER_M
                and field_img[1] == self.FIELD_OUTLINE_RADIUS_PX):
            self._field_img = field_img[2]
        else:
            self._field_img = ImageG8(self._size_px.get_x(), self._size_px.get_y())
            obstacles = field.get_pathfinding_obstacles()
            self._field_img.draw(
                type(self)._draw_field_kernel,
                num_threads=self.FIELD_DRAW_THREADS,
                userdata=(
                    self,
                    obstacles,
                    self.FIELD_OUTLINE_RADIUS_PX / self.PX_PER_M,
                    len(obstacles) - 1
                )
            )
        if detection_img and detection_img[0] == self.DETECTION_RADIUS_PX:
            self._detection_img = detection_img[1]
        else:
            detection_diameter = self.DETECTION_RADIUS_PX * 2
            self._detection_img = ImageG8(detection_diameter, detection_diameter)
            self._detection_img.draw(
                type(self)._draw_detection_kernel,
                num_threads=self.DETECTION_DRAW_THREADS
            )

    def get_field_image(self):
        return (self.PX_PER_M, self.FIELD_OUTLINE_RADIUS_PX, self._field_img)

    def get_detection_image(self):
        return (self.DETECTION_RADIUS_PX, self._detection_img)

    def _localize_from_detections(self, dets):
        detection_dist_px = int(self.MAX_DETECTION_DIST_M * self.PX_PER_M)
        template = ImageG8(2 * detection_dist_px, detection_dist_px)
        points = [
            Vec2(
                det.get_distance() * math.cos(det.get_angle()) + self.MAX_DETECTION_DIST_M,
                self.MAX_DETECTION_DIST_M - det.get_distance() * math.sin(det.get_angle())
            )
            for det in dets if det.get_distance() < self.MAX_DETECTION_DIST_M
        ]
        detection_rr = Vec2(self.DETECTION_RADIUS_PX, self.DETECTION_RADIUS_PX)
        with Pool(self.TEMPLATE_MATCH_THREADS):
            for point in points:
                template.paste(
                    math.floor(point * self.PX_PER_M) - detection_rr,
                    self._detection_img,
                    num_threads=self.TEMPLATE_MATCH_THREADS,
                    process_pool=pool
                )
            for i in range(self.ROTATION_VARIANTS):
                angle = 2 * math.pi * i / self.ROTATION_VARIANTS
                rotated = template.rotate(
                    angle,
                    Vec2(detection_dist_px, detection_dist_px),
                    0,
                    num_threads=self.TEMPLATE_MATCH_THREADS,
                    process_pool=pool
                )
                match_results.append(self._field_img.template_match(
                    rotated,
                    mask=rotated,
                    num_threads=self.TEMPLATE_MATCH_THREADS,
                    process_pool=pool
                ))
        # get localization data from match_results
        return match_results

    def _draw_field_kernel(x, y, userdata):
        self, obstacles, radius_m, obstacles_len_minus_one = userdata
        point = Vec2(x * self._size_m.get_x(), y * self._size_m.get_y())
        sum_abs_dist = sum([
            min(
                abs(o.get_distance_to(point)),
                radius_m
            )
            for o in obstacles
        ])
        norm_dist = max(0, min(1, sum_abs_dist / radius_m - obstacles_len_minus_one))
        return (1 - norm_dist) * 255

    def _draw_detection_kernel(x, y):
        dist = math.sqrt((x - 0.5) ** 2 + (y - 0.5) ** 2)
        norm = min(0.5, dist) / 0.5
        return (1 - norm) * 255
