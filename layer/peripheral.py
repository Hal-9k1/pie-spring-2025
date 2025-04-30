from layer import Layer
from devices import Motor


class BeltLayer(Layer):
    def setup(self, setup_info):
        self._motor = setup_info.get_device(Motor, 'belt_motor')

    def get_input_tasks(self):
        return {DriveBeltTask}

    def get_output_tasks(self):
        return set()

    def process(self, ctx):
        if self._task:
            ctx.complete_task(self._task)
            self._task = None
        ctx.request_task()

    def accept_task(self, task):
        self._task = task
        self._motor.set_velocity(task.get_power())
