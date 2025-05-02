from abc import ABC
from abc import abstractmethod
from layer import Layer
from matrix import Mat3
from matrix import Vec2
from random import random
from task.sensory import LocalizationTask
import math


class LocalizationData(ABC):
    @abstractmethod
    def get_position_probability(self, pos):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dx(self, pos, ignore_roots):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dy(self, pos, ignore_roots):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dx_gradient(self, pos, ignore_roots):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dy_gradient(self, pos, ignore_roots):
        raise NotImplementedError

    @abstractmethod
    def get_rotation_probability(self, rot):
        raise NotImplementedError

    @abstractmethod
    def get_rotation_probability_dx(self, rot, ignore_roots):
        raise NotImplementedError

    @abstractmethod
    def get_rotation_probability_dx2(self, rot, ignore_roots):
        raise NotImplementedError


class AbstractFinDiffLocalizationData(LocalizationData):
    def __init__(self, epsilon):
        self._epsilon = epsilon

    def get_position_probability_dx(self, pos, ignore_roots):
        return ((self.get_position_probability(pos.add(Vec2(self._epsilon, 0)))
            - self.get_position_probability(pos))
            / self._epsilon
            * self._calculate_ignore_root_factor_2d(pos, ignore_roots))

    def get_position_probability_dy(self, pos, ignore_roots):
        return ((self.get_position_probability(pos.add(Vec2(0, self._epsilon)))
            - self.get_position_probability(pos))
            / self._epsilon
            * self._calculate_ignore_root_factor_2d(pos, ignore_roots))

    def get_position_probability_dx_gradient(self, pos, ignore_roots):
        z = self.get_position_probability_dx(pos, ignore_roots)
        wrtX = (self.get_position_probability_dx(pos.add(Vec2(self._epsilon, 0)), ignore_roots) - z) / self._epsilon
        wrtY = (self.get_position_probability_dx(pos.add(Vec2(0, self._epsilon)), ignore_roots) - z) / self._epsilon
        return Vec2(wrtX, wrtY)

    def get_position_probability_dy_gradient(self, pos, ignore_roots):
        z = self.get_position_probability_dy(pos, ignore_roots)
        wrtX = (self.get_position_probability_dy(pos.add(Vec2(self._epsilon, 0)), ignore_roots) - z)
        wrtY = (self.get_position_probability_dy(pos.add(Vec2(0, self._epsilon)), ignore_roots) - z)
        return Vec2(wrtX, wrtY)

    def get_rotation_probability_dx(self, rot, ignore_roots):
        return ((self.get_rotation_probability(rot + self._epsilon)
            - self.get_rotation_probability(rot))
            / self._epsilon
            * ignore_root_factor)

    def get_rotation_probability_dx2(self, rot, ignore_roots):
        return (self.get_rotation_probability_dx(rot + self._epsilon, ignore_roots)
            - self._get_rotation_probability_dx(rot, ignore_roots)) / self._epsilon

    def _calculate_ignore_root_factor_2d(self, pos, ignore_roots):
        ignore_root_factor = 1
        for root in ignore_roots:
            product = math.inf
            negative_center = pos.mul(-1)
            epsilon_vec = Vec2(self._epsilon, self._epsilon)
            while True:
                if not math.isfinite(product):
                    diff = negative_center.add(root)
                    factor = 1 / (diff.dot(diff) + 1) - 1
                    product = 1 / factor
                    negative_center = negative_center.add(epsilon_vec)
                else:
                    ignore_root_factor *= product
                    break
        return ignore_root_factor

    def _calculate_ignore_root_factor_1d(self, pos, ignore_roots):
        ignore_root_factor = 1
        for root in ignore_roots:
            x = rot
            while True:
                if not math.isfinite(product):
                    product = a / (x - b)
                    x = x + self._epsilon
                else:
                    ignore_root_factor *= product
                    break
        return ignore_root_factor


class LocalizationSource(ABC):
    def on_start(self, start_pos: Mat3):
        pass

    def on_update(self):
        pass

    @abstractmethod
    def has_data(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def collect_data() -> LocalizationData:
        raise NotImplementedError


class SqFalloffLocalizationData(AbstractFinDiffLocalizationData):
    def __init__(self, epsilon, transform, accuracy, position_precision, rotation_precision):
        super().__init__(epsilon)
        self._transform = transform
        self._accuracy = accuracy
        self._position_precision = position_precision
        self._rotation_precision = rotation_precision

    def get_position_probability(self, pos):
        diff = self._transform.get_translation().mul(-1).add(pos)
        return self._accuracy / ((diff.dot(diff) * self._position_precision) + 1)

    def get_rotation_probability(self, rot):
        diff = rot - self._transform.get_direction().get_angle()
        return self._accuracy / (diff * diff * self._rotation_precision + 1)


class RobotLocalizer(Layer):
    def __init__(self, initial_transform):
        self._init = True
        self._should_emit = True
        self._sources = []
        self._init_tfm = initial_transform

    def setup(self, setup_info):
        setup_info.add_update_listener(lambda: self._on_update())

    def get_input_tasks(self):
        return set()

    def get_output_tasks(self):
        return {LocalizationTask}

    def complete_task(self, task):
        if task == self._emitted_task:
            self._should_emit = True

    def process(self, ctx):
        if self._init:
            self._init = False
            for source in self._sources:
                source.on_start(self._init_tfm)
        if self._should_emit:
            ctx.emit_subtask(LocalizationTask(self.resolve_transform()))

    def accept_task(self):
        raise TypeError

    def register_source(self, source):
        self._sources.append(source)

    def _on_update(self):
        self.invalidate_cache()
        for source in self._sources:
            source.on_update()

    def _get_sources(self):
        return self._sources

    @abstractmethod
    def resolve_transform(self):
        raise NotImplementedError

    @abstractmethod
    def invalidate_cache(self):
        raise NotImplementedError


class NewtonLocalizer(RobotLocalizer):
    MAX_NEWTON_STEPS = 40
    MAX_NEWTON_ROOTS = 10
    NEWTON_DISTURBANCE_SIZE = 1

    def __init__(self, initial_transform):
        super().__init__(initial_transform)
        self.invalidate_cache()

    def invalidate_cache(self):
        self._cached_tfm = None
        self._data_cache = {}

    def resolve_transform(self):
        if not self._cached_tfm:
            # Find roots of position derivative
            pos_roots = []
            for i in range(self.MAX_NEWTON_ROOTS):
                xy = Vec2.zero()
                xy_min_err = xy
                min_err = math.inf
                for j in range(self.MAX_NEWTON_STEPS + 1):
                    err = sum((
                        self._get_data(src).get_position_probability_dx(xy, pos_roots)
                        + self._get_data(src).get_position_probability_dy(xy, pos_roots)
                    ) for src in self._sources)
                    if err < min_err:
                        xy_min_err = xy
                        min_err = err
                    if j < self.MAX_NEWTON_STEPS:
                        grad = sum(
                            ((
                                self._get_data(src).get_position_probability_dx_gradient(xy, pos_roots)
                                + self._get_data(src).get_position_probability_dy_gradient(xy, pos_roots)
                            ) for src in self._sources),
                            start=Vec2.zero()
                        )
                        delta = grad * (-err / grad.len())
                        if not delta.is_finite():
                            nudge_angle = random() * 2 * math.pi
                            delta = Vec2(
                                math.cos(nudge_angle) * self.NEWTON_DISTURBANCE_SIZE,
                                math.sin(nudge_angle) * self.NEWTON_DISTURBANCE_SIZE
                            )
                        xy += delta
                pos_roots.append(xy_min_err)
            # Pick absolute maximum probability from roots
            pos = max(
                ((root, sum(
                    self._get_data(src).get_position_probability(root)
                    for src in self._sources
                )) for root in pos_roots),
                key=lambda x: x[1]
            )[0]
            # Find roots of rotation derivative
            rot_roots = []
            for i in range(self.MAX_NEWTON_ROOTS):
                x = 0
                x_min_err = x
                min_err = math.inf
                for j in range(self.MAX_NEWTON_STEPS + 1):
                    err = sum(
                        self._get_data(src).get_rotation_probability_dx(x, roots)
                        for src in self._sources
                    )
                    if err < min_err:
                        x_min_err = x
                        min_err = err
                    if j < MAX_NEWTON_STEPS:
                        slope = sum(
                            self._get_data(src).get_rotation_probability_dx2(x, roots)
                            for src in self._sources
                        )
                        delta = -err / slope
                        if not math.isfinite(delta):
                            delta = math.copysign(self.NEWTON_DISTURBANCE_SIZE, random() - 1 / 2)
                        x += delta
                rot_roots.append(x_min_err)
            # Pick absolute maximum probability from roots
            rot = max(
                ((root, sum(
                    self._get_data(src).get_rotation_probability(root)
                    for src in self._sources
                )) for root in pos_roots),
                key=lambda x: x[1]
            )[0]
            # Combine most probable position and rotation into transform
            self._cached_tfm = Mat3.from_transform(
                Mat2.from_angle(rot),
                pos
            )
        return self._cached_tfm

    def _get_data(self, source):
        if source not in self._data_cache:
            self._data_cache[source] = source.collect_data()
        return self._data_cache[source]


class PersistenceLocalizationSource(Layer, LocalizationSource):
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


class StaticObstacleLocalizationSource(Layer, LocalizationSource):
    def __init__(self):
        raise NotImplementedError

    def get_input_tasks(self):
        return {LocalizationTask}

    def get_output_tasks(self):
        return set()

    def process(self, ctx):
        raise NotImplementedError

    def accept_task(self, task):
        raise NotImplementedError

    def has_data(self):
        return True

    def collect_data(self):
        raise NotImplementedError


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
