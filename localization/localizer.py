from layer import Layer
from localization import RobotLocalizer
from matrix import Mat2
from matrix import Mat3
from matrix import Vec2
from random import random
import math


def _clean_print(s):
    import re
    p = 6
    def r(m):
        return '{0:+.5e}'.format(float(m.group(0)))
    #print(re.sub('(?<![a-zA-Z])[\-\+]?\d+(?:\.\d+)?(?:e[\+\-]\d+)?', r, s), end=' ')


class NewtonHistory:
    def __init__(self, size, weight):
        self._size = size
        self._weight = weight
        self._hist = [None] * size
        self._idx = 0

    def add(self, value):
        self._hist[self._idx] = value
        self._idx = (self._idx + 1) % self._size

    def accumulate(self):
        return sum(
            (
                v if v != None else self._hist[0]
                for v in self._hist
            ), start=Vec2.zero()
        ) * self._weight


class NewtonLocalizer(RobotLocalizer):
    POS_NEWTON_STEPS = 640
    POS_NEWTON_ROOTS = 8
    POS_NEWTON_INITIAL_SPEED = 4
    POS_NEWTON_DISTURBANCE_SIZE = 4
    POS_NEWTON_ROOT_EPSILON = 0.01
    POS_NEWTON_FLAT_THRESHOLD = 10**-9
    POS_NEWTON_SPEED_DAMPING = 0.91
    POS_NEWTON_SPEED_ADJUST_WEIGHT = 0.04
    POS_NEWTON_MIN_SPEED = 0 #10**-1
    POS_NEWTON_MIN_IMPROVEMENT = 0 #10**-3
    POS_NEWTON_HIST_LENGTH = 32
    POS_NEWTON_HIST_WEIGHT = 10**-2
    POS_NEWTON_MIN_GRAD_LEN = 10**-3

    ROT_NEWTON_STEPS = 160
    ROT_NEWTON_ROOTS = 4
    ROT_NEWTON_INITIAL_SPEED = 0.5
    ROT_NEWTON_DISTURBANCE_SIZE = 0.5
    ROT_NEWTON_ROOT_EPSILON = 0.001
    ROT_NEWTON_FLAT_THRESHOLD = 0.001
    ROT_NEWTON_SPEED_DAMPING = 0.5

    def __init__(self, initial_transform):
        super().__init__(initial_transform)
        self.invalidate_cache()
        #print('hello world')

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
                init_speed = self.POS_NEWTON_INITIAL_SPEED
                speed = init_speed
                hist = NewtonHistory(self.POS_NEWTON_HIST_LENGTH, self.POS_NEWTON_HIST_WEIGHT)
                probability = sum(
                    self._get_data(src).get_position_probability(xy)
                    for src in self._sources
                )
                old_probability = probability
                for j in range(self.POS_NEWTON_STEPS + 1):
                    nxy = xy.mul(-1)
                    overlapping_maxima = [
                        maximum for maximum in pos_maxima
                        if maximum.add(nxy).len() < self.POS_NEWTON_ROOT_EPSILON
                    ]
                    for maximum in overlapping_maxima:
                        maxima_hit[maximum] = maxima_hit.get(maximum, 0) + 1
                    nudge_angle = random() * 2 * math.pi
                    size = sum(maxima_hit[maximum] for maximum in overlapping_maxima) * self.POS_NEWTON_DISTURBANCE_SIZE
                    if size:
                        delta = Vec2(
                            math.cos(nudge_angle) * size,
                            math.sin(nudge_angle) * size
                        )
                        probability = 0
                        _clean_print(f'nudge {size}')
                    else:
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
                            hist.add(grad)
                            delta = (
                                grad.unit() * max(self.POS_NEWTON_MIN_GRAD_LEN, grad.len())
                                + hist.accumulate()
                            ) * speed
                            _clean_print(f'grad {grad}[{grad.len()}] hist {hist.accumulate()} delta {delta} speed {speed}')
                            new_probability = sum(
                                self._get_data(src).get_position_probability(xy + delta)
                                for src in self._sources
                            )
                            if new_probability - old_probability < self.POS_NEWTON_MIN_IMPROVEMENT:
                                speed *= self.POS_NEWTON_SPEED_DAMPING
                                if speed < self.POS_NEWTON_MIN_SPEED:
                                    _clean_print(f'terminate slowness on iter {j}\n')
                                    break
                                delta = Vec2.zero()
                                _clean_print('slow')
                            else:
                                probability = new_probability
                                init_speed = ((init_speed * speed ** self.POS_NEWTON_SPEED_ADJUST_WEIGHT)
                                    ** (1 / (1 + self.POS_NEWTON_SPEED_ADJUST_WEIGHT)))
                                speed = init_speed
                                _clean_print('    ')
                            _clean_print(f'({probability} {probability - old_probability})')
                        else:
                            # Terminate this maximum path immediately
                            _clean_print('terminate flatness\n')
                            break
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
            # Find rotation probability maxima
            rot_maxima = []
            for i in range(self.ROT_NEWTON_ROOTS):
                x = 0
                maxima_hit = {}
                speed = self.ROT_NEWTON_INITIAL_SPEED
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
                            delta = slope * speed * self.ROT_NEWTON_INITIAL_SPEED
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
        return self._cached_tfm

    def _get_data(self, source):
        if source not in self._data_cache:
            self._data_cache[source] = source.collect_data()
        return self._data_cache[source]
