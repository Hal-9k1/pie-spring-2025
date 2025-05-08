from controller import LayerGraph
from controller import RobotController
from layer import Layer
from localization import LocalizationSource
from localization import NewtonLocalizer
from localization import SqFalloffLocalizationData
from log import LoggerProvider
from matrix import Mat2
from matrix import Mat3
from matrix import Vec2
from multiprocessing import Pool
from random import seed
from task.sensory import LocalizationTask
from tests.controller import TestRobotControllerBase
from unittest import TestCase
import math

class TestNewtonLocalizer(TestRobotControllerBase):
    def _test_rc(start_tfm, sources, lg=None):
        lg = lg or LayerGraph()
        l10n = NewtonLocalizer(start_tfm)
        for src in sources:
            l10n.register_source(src)
        recorder = LocalizationRecorder()
        lg.add_chain([l10n, recorder])
        rc = RobotController()
        rc.setup(None, None, lg, LoggerProvider())
        rc.update()
        return recorder.task.get_robot_field_transform()

    def _test_localize_one_source(tfm):
        try:
            seed(0)
            return TestNewtonLocalizer._test_rc(Mat3.identity(), [ConstantLocalizationSource(tfm)])
        except Exception as e:
            return e

    def _check_tfm(self, resolved, solution):
        delta_len = resolved.get_translation().add(solution.get_translation().mul(-1)).len()
        delta_theta = resolved.get_direction().angle_with(solution.get_direction())
        self.assertLess(abs(delta_len), 0.01)
        self.assertLess(abs(delta_theta), 0.001)

    def test_localize_one_source_many(self):
        resolution = 2
        minimum = int(-5.5 / resolution)
        maximum = int(5.5 / resolution)
        runs = []
        for x in (i * resolution for i in range(minimum, maximum)):
            for y in (i * resolution for i in range(minimum, maximum)):
                for t in (i * resolution * 2 * math.pi for i in range(0, resolution)):
                    runs.append((x, y, t))
        tfms = [Mat3.from_transform(
            Mat2.from_angle(t),
            Vec2(x, y)
        ) for x, y, t in runs]
        with Pool() as p:
            results = p.map(TestNewtonLocalizer._test_localize_one_source, tfms)
        for run, tfm, result in zip(runs, tfms, results):
            with self.subTest(x=run[0], y=run[1], theta=run[2]):
                if isinstance(tfm, Mat3):
                    self._check_tfm(result, tfm)
                else:
                    raise tfm

    def test_localize_one_source_single(self):
        tfm = Mat3.from_transform(
            Mat2.from_angle(2),
            Vec2(2, -2.047)
        )
        self._check_tfm(
            TestNewtonLocalizer._test_rc(Mat3.identity(), [ConstantLocalizationSource(tfm)]),
            tfm
        )


class ConstantLocalizationSource(LocalizationSource):
    def __init__(self, tfm):
        self._tfm = tfm

    def has_data(self):
        return True

    def collect_data(self):
        return SqFalloffLocalizationData(0.001, self._tfm, 1, 1, 1)


class LocalizationRecorder(Layer):
    def get_input_tasks(self):
        return {LocalizationTask}

    def get_output_tasks(self):
        return set()

    def process(self, ctx):
        ctx.request_task()

    def accept_task(self, task):
        self.task = task
