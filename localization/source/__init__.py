from abc import ABC
from abc import abstractmethod
from layer import Layer
from localization import LocalizationSource
from localization import LocalizationData
from localization.data import SqFalloffLocalizationData
from task.sensory import LocalizationTask
from task.sensory import SensorTurretTask
from matrix import Mat3


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
