from abc import ABC
from abc import abstractmethod
from array import array
from layer import Layer
from localization import LocalizationSource
from localization import LocalizationData
from localization.data import SqFalloffLocalizationData
from task.sensory import LocalizationTask
from task.sensory import SensorTurretTask
from matrix import Mat2
from matrix import Mat3
from matrix import Vec2
from multiprocessing import Pool
import math


class AntiTeleportationLocalizationSource(Layer, LocalizationSource):
    FIN_DIFF_EPSILON = 0.0001
    POSITION_PRECISION = 1
    ROTATION_PRECISION = 1
    ACCURACY = 0.7

    def on_start(self, init_transform):
        self._data = SqFalloffLocalizationData(
            self.FIN_DIFF_EPSILON,
            init_transform,
            self.ACCURACY,
            self.POSITION_PRECISION,
            self.ROTATION_PRECISION
        )

    def get_input_tasks(self):
        return {LocalizationTask}

    def get_output_tasks(self):
        return set()

    def process(self, ctx):
        ctx.request_task()

    def accept_task(self, task):
        self._data = SqFalloffLocalizationData(
            self.FIN_DIFF_EPSILON,
            task.get_robot_field_transform(),
            self.ACCURACY,
            self.POSITION_PRECISION,
            self.ROTATION_PRECISION
        )

    def has_data(self):
        return True

    def collect_data(self):
        return self._data


class AbstractStaticObstacleLocalizationSource(Layer, LocalizationSource):
    def __init__(self, detection_lifetime):
        self._detections = []
        self._new_tasks = []
        self._lifetime = detection_lifetime

    def get_input_tasks(self):
        return {SensorTurretTask}

    def get_output_tasks(self):
        return set()

    def process(self, ctx):
        for t in self._new_tasks:
            ctx.complete_task(t)
        self._new_tasks.clear()
        ctx.request_task()
        while self._detections:
            head = self._detections[0]
            if time.time() - head[0] > self._lifetime:
                del self._detections[0]
            else:
                break

    def accept_task(self, task):
        self._detections.append((time.time(), task))
        self._new_tasks.append(task)

    def has_data(self):
        return True

    def collect_data(self):
        dets = [d[1] for d in self._detections]
        return self._localize_from_detections(dets)

    @abstractmethod
    def _localize_from_detections(self, dets: list[LocalizationTask]) -> LocalizationData:
        raise NotImplementedError


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

    def template_match(self, img):
        result = _ImageG8(self._width - img._width, self._height - img._height)
        img_px = img._width * img._height
        for ay in range(self._height - img._height):
            for ax in range(self._width - img._width):
                for by in range(img._height):
                    asi = self._index(ax, ay + by)
                    aei = self._index(ax + img._width, ay + by)
                    ar = self._data[asi:aei]
                    br = img._data[img._index(0, by):img._index(0, by + 1)]
                    # Use ceil so 0 error always means exact match
                    result._data[result._index(ax, ay)] = int(
                        math.ceil(sum([math.ceil(abs(a - b) / 2) for a, b in zip(ar, br)]) / img_px)
                    )
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
        result = _ImageG8(self._width, self._height)
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
    PX_PER_M = 100
    FIELD_OUTLINE_RADIUS_PX = 10
    MAX_DETECTION_DIST_CM = 10
    DETECTION_RADIUS_CM = 5
    FIELD_DRAW_THREADS = 8
    DETECTIONS_DRAW_THREADS = 8

    def __init__(self, field, field_img=None):
        super().__init__(self.DETECTION_LIFETIME)
        self._size_m = field.get_size()
        self._size_px = math.floor(self._size_m * self.PX_PER_M)
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

    def _localize_from_detections(self, dets):
        template = _ImageG8(2 * self.MAX_DETECTION_DIST_CM, self.MAX_DETECTION_DIST_CM)
        points = [
            Vec2(
                det.get_distance() * (1 + math.cos(det.get_angle())),
                det.get_distance() * math.sin(det.get_angle())
            )
            for det in dets if det.get_distance() < self.MAX_DETECTION_DIST_CM
        ]
        template.draw(
            type(self)._draw_detections_kernel,
            num_threads=self.DETECTIONS_DRAW_THREADS,
            userdata=(self, points)
        )
        # match many rotations of template against self._field_img

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
        sum_abs_dist_px = sum([
            (point - Vec2(x * self._size_m.get_x(), y * self._size_m.get_y()) + self._field_tl).len()
            for point in points
        ]) * self.PX_PER_M
        norm_dist = min(self.DETECTION_RADIUS_PX, sub_abs_dist_px) / self.DETECTION_RADIUS_PX
        return (1 - norm_dist) * 255


class EncoderLocalizationSource(LocalizationSource):
    FIN_DIFF_EPSILON = 0.0001
    POSITION_PRECISION = 1
    ROTATION_PRECISION = 1
    ACCURACY = 1

    def __init__(self, encoder_drive_system):
        self._drive = encoder_drive_system
        self._state = None

    def on_start(self, start_tfm):
        self._tfm = start_tfm

    def on_update(self):
        new_state = self._drive.record_state()
        if self._state:
            delta = self._drive.get_state_delta(self._state, new_state)
            self._tfm = self._tfm.mul(delta)
        self._state = new_state

    def has_data(self):
        return self._state != None

    def collect_data(self):
        return SqFalloffLocalizationData(
            self.FIN_DIFF_EPSILON,
            self._tfm,
            self.ACCURACY,
            self.POSITION_PRECISION,
            self.ROTATION_PRECISION
        )


class EncoderDriveSystem(ABC):
    @abstractmethod
    def record_state(self) -> object:
        raise NotImplementedError

    @abstractmethod
    def get_state_delta(self, old_state: object, new_state: object) -> Mat3:
        raise NotImplementedError
