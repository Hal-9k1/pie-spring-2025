from abc import ABC
from abc import abstractmethod
from array import array
from layer import Layer
from localization import LocalizationSource
from localization import LocalizationData
from localization.data import SqFalloffLocalizationData
from task.sensory import LocalizationTask
from task.sensory import SensorTurretTask
from matrix import Mat3
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
        self._localize_from_detections(dets)

    @abstractmethod
    def _localize_from_detections(self, dets: list[LocalizationTask]) -> LocalizationData:
        raise NotImplementedError


class _Image:
    def __init__(self, width, height, data=None):
        self._width = width
        self._height = height
        self._data = array('B', data or [0] * width * height)

    def get_norm(self, x, y):
        x_norm = max(0, min(self._width, x * self._width))
        y_norm = max(0, min(self._height, y * self._height))
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

    def draw(self, draw_func):
        for i in len(self._data):
            self._data[i] = draw_func(
                (i % self._width) / self._width,
                (i // self._width) / self._height
            )

    def template_match(self, img):
        result = _Image(self._width - img._width, self._height - img._height)
        for ay in range(self._height - img._height):
            for ax in range(self._width - img._width):
                for by in range(img._height):
                    asi = self._index(ax, ay + by)
                    aei = self._index(ax + img._width, ay + by)
                    ar = self._data[asi:aei]
                    br = img._data[img._index(0, by):img._index(0, by + 1)]
                    # Use ceil so 0 error always means exact match
                    result._data[result._index(ax, ay)] = int(
                        sum([math.ceil(abs(a - b) / 2) for a, b in zip(ar, br)])
                    )
        return result

    def convolve(self, img):
        raise NotImplementedError('Broken, kernel is anchored at top left instead of floor center')
        result = _Image(self._width, self._height)
        for ay in range(self._height):
            for ax in range(self._width):
                for by in range(img._height):
                    asi = self._index(ax, min(ay + by, self._height - 1))
                    aei = self._index(min(ax, self._width - 1), min(ay + by, self._height - 1))
                    ar = self._data[asi:aei]
                    br = img._data[img._index(0, by):img._index(0, by + 1)]
                    len_diff = len(ar) - len(br)
                    if len_diff > 0:
                        ar += [ar[-1]] * len_diff
                    result._data[result._index(ax, ay)] = int(
                        sum([int(a * b / 255**2) for a, b in zip(ar, br)])
                    )
        return result

    def _index(self, x, y):
        return self._width * y + x



class TemplateMatchingLocalizationSource(AbstractStaticObstacleLocalizationSource):
    DETECTION_LIFETIME = 1
    PX_PER_M = 100
    FIELD_OUTLINE_RADIUS_PX = 20
    MAX_DETECTION_DIST_CM = 10
    DETECTION_RADIUS_CM = 5

    def __init__(self, field):
        super().__init__(self.DETECTION_LIFETIME)
        size = field.get_size() * self.PX_PER_M
        self._field_img = _Image(size.get_x(), size.get_y())
        self._field_img.draw(lambda x, y: self._draw_field_kernel(x, y, field))

    def _localize_from_detections(self, dets):
        template = _Image(2 * self.MAX_DETECTION_DIST_CM, self.MAX_DETECTION_DIST_CM)
        points = [
            Vec2(
                det.get_distance() * (1 + math.cos(det.get_angle())),
                det.get_distance() * math.sin(det.get_angle())
            )
            for det in dets if det.get_distance() < self.MAX_DETECTION_DIST_CM
        ]
        template.draw(lambda x, y: self._draw_detections_kernel(x, y, points))
        # match many rotations of template against self._field_img

    def _draw_field_kernel(self, x, y, field):
        sum_abs_dist_px = sum([
            abs(o.get_distance_to(x / self.PX_PER_M, y / self.PX_PER_M))
            for o in self._field.get_pathfinding_obstacles()
        ]) * self.PX_PER_M
        norm_dist = min(self.FIELD_OUTLINE_RADIUS_PX, sub_abs_dist_px) / self.FIELD_OUTLINE_RADIUS_PX
        return (1 - norm_dist) * 255

    def _draw_detections_kernel(self, x, y, points):
        sum_abs_dist_px = sum([
            point.add(Vec2(x / self.PX_PER_M, y / self.PX_PER_M) * -1).len()
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
