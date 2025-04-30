from layer import Layer
from actuators import DistanceSensor
from task.drive import TankDriveTask
from task import WinTask


class RatStrategy(Layer):
    NOISE_THRESHOLD = 2
    STOP_THRESHOLD = 3
    DRIVE_SPEED = 0.1

    def setup(self, setup_info):
        self._sensor = setup_info.get_device(DistanceSensor, "sensor")
        self._accepted_task = None
        self._emitted_task = None
        self._finished = True

    def get_input_tasks(self):
        return {WinTask}

    def get_output_tasks(self):
        return {TankDriveTask}

    def subtask_completed(self, task):
        if task == self._emitted_task:
            self._emitted_task = None

    def process(self, ctx):
        if self._finished:
            if self._accepted_task:
                ctx.complete_task(self._accepted_task)
                self._accepted_task = None
            ctx.request_task()
            return
        if not self._emitted_task:
            self._finished = self.NOISE_THRESHOLD < self._sensor.get_distance() < self.STOP_THRESHOLD
            speed = 0 if self._finished else self.DRIVE_SPEED
            self._emitted_task = TankDriveTask(speed, speed)
            ctx.emit_subtask(self._emitted_task)

    def accept_task(self, task):
        if isinstance(task, WinTask):
            self._accepted_task = task
            self._finished = False
