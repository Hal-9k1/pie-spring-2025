from tests.controller import TestRobotControllerBase
from localization import LocalizationSource
from localization import SqFalloffLocalizationData
from localization import NewtonLocalizer
from matrix import Vec2
from matrix import Mat2
from matrix import Mat3
from layer import Layer
from unittest import TestCase
from task.sensory import LocalizationTask


class TestNewtonLocalizer(TestRobotControllerBase):
    def _test_rc(self, start_tfm, sources, solution):
        l10n = NewtonLocalizer(start_tfm)
        for src in sources:
            l10n.register_source(src)
        recorder = LocalizationRecorder()
        self._lg.add_chain([l10n, recorder])
        super()._test_rc(1, False)
        resolved = recorder.task.get_robot_field_transform()
        delta_len = resolved.get_translation().add(solution.get_translation().mul(-1)).len()
        delta_theta = resolved.get_direction().angle_with(solution.get_direction())
        self.assertLess(abs(delta_len), 0.02)
        self.assertLess(abs(delta_theta), 0.02)

    def test_localize_one_source(self):
        tfm = Mat3.from_transform(
            Mat2.from_angle(2),
            Vec2(2, -2.047)
        )
        self._test_rc(Mat3.identity(), [ConstantLocalizationSource(tfm)], tfm)


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
