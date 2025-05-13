from abc import ABC
from abc import abstractmethod
from layer import Layer
from matrix import Mat2
from matrix import Mat3
from matrix import Vec2
from random import random
from task.sensory import LocalizationTask
import math


def _clean_print(s):
    import re
    p = 6
    def r(m):
        return str(round(float(m.group(0)) * 10**p) / 10**p).ljust(p + 2, '0') if '.' in m.group(0) else m.group(0)
    print(re.sub('(?<![a-zA-Z])[\d\.]+', r, s), end=' ')


class LocalizationData(ABC):
    @abstractmethod
    def get_position_probability(self, pos):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dx(self, pos):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dy(self, pos):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dx_gradient(self, pos):
        raise NotImplementedError

    @abstractmethod
    def get_position_probability_dy_gradient(self, pos):
        raise NotImplementedError

    @abstractmethod
    def get_rotation_probability(self, rot):
        raise NotImplementedError

    @abstractmethod
    def get_rotation_probability_dx(self, rot):
        raise NotImplementedError

    @abstractmethod
    def get_rotation_probability_dx2(self, rot):
        raise NotImplementedError


class AbstractFinDiffLocalizationData(LocalizationData):
    def __init__(self, epsilon):
        self._epsilon = epsilon

    def get_position_probability_dx(self, pos):
        return ((self.get_position_probability(pos.add(Vec2(self._epsilon, 0)))
            - self.get_position_probability(pos))
            / self._epsilon)

    def get_position_probability_dy(self, pos):
        return ((self.get_position_probability(pos.add(Vec2(0, self._epsilon)))
            - self.get_position_probability(pos))
            / self._epsilon)

    def get_position_probability_dx_gradient(self, pos):
        z = self.get_position_probability_dx(pos)
        wrtX = (self.get_position_probability_dx(pos.add(Vec2(self._epsilon, 0))) - z) / self._epsilon
        wrtY = (self.get_position_probability_dx(pos.add(Vec2(0, self._epsilon))) - z) / self._epsilon
        return Vec2(wrtX, wrtY)

    def get_position_probability_dy_gradient(self, pos):
        z = self.get_position_probability_dy(pos)
        wrtX = (self.get_position_probability_dy(pos.add(Vec2(self._epsilon, 0))) - z) / self._epsilon
        wrtY = (self.get_position_probability_dy(pos.add(Vec2(0, self._epsilon))) - z) / self._epsilon
        return Vec2(wrtX, wrtY)

    def get_rotation_probability_dx(self, rot):
        return ((self.get_rotation_probability(rot + self._epsilon)
            - self.get_rotation_probability(rot))
            / self._epsilon)

    def get_rotation_probability_dx2(self, rot):
        return (self.get_rotation_probability_dx(rot + self._epsilon)
            - self.get_rotation_probability_dx(rot)) / self._epsilon


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
    POS_NEWTON_STEPS = 1280
    POS_NEWTON_ROOTS = 4
    POS_NEWTON_STEP_SIZE = 1
    POS_NEWTON_DISTURBANCE_SIZE = 4
    POS_NEWTON_ROOT_EPSILON = 0.01
    POS_NEWTON_FLAT_THRESHOLD = 0.001
    POS_NEWTON_SPEED_DAMPING = 0.9
    POS_NEWTON_MIN_SPEED = 0.1
    POS_NEWTON_MIN_IMPROVEMENT = 0.00001

    ROT_NEWTON_STEPS = 160
    ROT_NEWTON_ROOTS = 4
    ROT_NEWTON_STEP_SIZE = 0.5
    ROT_NEWTON_DISTURBANCE_SIZE = 0.5
    ROT_NEWTON_ROOT_EPSILON = 0.001
    ROT_NEWTON_FLAT_THRESHOLD = 0.001
    ROT_NEWTON_SPEED_DAMPING = 0.5

    def __init__(self, initial_transform):
        super().__init__(initial_transform)
        self.invalidate_cache()
        print('hello world')

    def invalidate_cache(self):
        self._cached_tfm = None
        self._data_cache = {}

    def resolve_transform(self):
        if not self._cached_tfm:
            # Find position probability maxima
            pos_maxima = []
            for i in range(self.POS_NEWTON_ROOTS):
                xy = Vec2.zero()
                maxima_hit = {}
                speed = 1
                probability = sum(
                    self._get_data(src).get_position_probability(xy)
                    for src in self._sources
                )
                for j in range(self.POS_NEWTON_STEPS + 1):
                    if j < self.POS_NEWTON_STEPS:
                        grad = sum(
                            (
                                Vec2(
                                    self._get_data(src).get_position_probability_dx(xy),
                                    self._get_data(src).get_position_probability_dy(xy)
                                )
                                for src in self._sources
                            ),
                            start=Vec2.zero()
                        )
                        old_probability = probability
                        if grad.len() > self.POS_NEWTON_FLAT_THRESHOLD:
                            _clean_print(f'diff {grad * speed * self.POS_NEWTON_STEP_SIZE} speed {speed}')
                            delta = grad * speed * self.POS_NEWTON_STEP_SIZE
                            probability = sum(
                                self._get_data(src).get_position_probability(xy + delta)
                                for src in self._sources
                            )
                            if probability - old_probability < self.POS_NEWTON_MIN_IMPROVEMENT:
                                speed *= self.POS_NEWTON_SPEED_DAMPING
                                if speed < self.POS_NEWTON_MIN_SPEED:
                                    _clean_print('terminate slowness\n')
                                    break
                                delta = Vec2.zero()
                                _clean_print('slow')
                            _clean_print(f'{probability - old_probability}')
                        else:
                            nxy = xy.mul(-1)
                            overlapping_maxima = [
                                maximum for maximum in pos_maxima
                                if maximum.add(nxy).len() < self.POS_NEWTON_ROOT_EPSILON
                            ]
                            if not overlapping_maxima:
                                # Terminate this maximum path immediately
                                _clean_print('terminate flatness\n')
                                break
                            for maximum in overlapping_maxima:
                                maxima_hit[maximum] = maxima_hit.get(maximum, 0) + 1
                            nudge_angle = random() * 2 * math.pi
                            size = sum(maxima_hit[maximum] for maximum in overlapping_maxima) * self.POS_NEWTON_DISTURBANCE_SIZE
                            delta = Vec2(
                                math.cos(nudge_angle) * size,
                                math.sin(nudge_angle) * size
                            )
                            _clean_print(f'nudge {size}')
                        _clean_print(f'{xy} -> {delta + xy} \n')
                        xy = delta + xy
                else:
                    _clean_print('terminate iters\n')
                pos_maxima.append(xy)
            # Pick absolute maximum
            for m in pos_maxima:
                _clean_print(f'{m}: {sum(self._get_data(src).get_position_probability(m) for src in self._sources)}\n')
            pos = max(
                ((maximum, sum(
                    self._get_data(src).get_position_probability(maximum)
                    for src in self._sources
                )) for maximum in pos_maxima),
                key=lambda x: x[1]
            )[0]
            _clean_print(f'absolute answer: {pos}\n\n\n')
            # Find rotation probability maxima
            rot_maxima = []
            for i in range(self.ROT_NEWTON_ROOTS):
                x = 0
                maxima_hit = {}
                speed = 1
                probability = sum(
                    self._get_data(src).get_rotation_probability(x)
                    for src in self._sources
                )
                for j in range(self.ROT_NEWTON_STEPS + 1):
                    if j < self.ROT_NEWTON_STEPS:
                        slope = sum(
                            self._get_data(src).get_rotation_probability_dx(x)
                            for src in self._sources
                        )
                        old_probability = probability
                        if abs(slope) > self.ROT_NEWTON_FLAT_THRESHOLD:
                            delta = slope * speed * self.ROT_NEWTON_STEP_SIZE
                            probability = sum(
                                self._get_data(src).get_rotation_probability(x)
                                for src in self._sources
                            )
                            if probability < old_probability:
                                speed *= self.ROT_NEWTON_SPEED_DAMPING
                                delta = 0
                        else:
                            overlapping_maxima = [
                                maximum for maximum in rot_maxima
                                if abs(maximum - x) < self.ROT_NEWTON_ROOT_EPSILON
                            ]
                            if not overlapping_maxima:
                                break
                            for maximum in overlapping_maxima:
                                maxima_hit[maximum] = maxima_hit.get(maximum, 0) + 1
                            size = sum(
                                maxima_hit[maximum]
                                for maximum in overlapping_maxima
                            ) * self.ROT_NEWTON_DISTURBANCE_SIZE
                            delta = math.copysign(size, random() - 1 / 2)
                        x += delta
                rot_maxima.append(x)
            # Pick absolute maximum probability
            rot = max(
                ((maximum, sum(
                    self._get_data(src).get_rotation_probability(maximum)
                    for src in self._sources
                )) for maximum in rot_maxima),
                key=lambda x: x[1]
            )[0]
            # Combine most probable position and rotation into transform
            self._cached_tfm = Mat3.from_transform(
                Mat2.from_angle(rot),
                pos
            )
            _clean_print(f'Final pos: {self._cached_tfm.get_translation()}\n')
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
