


class BeltLayer(Layer):
    def __init__(self, motor_controller):
        self._motor_controller = motor_controller

    def setup(self, setup_info):
        self._motor = Motor(
            setup_info.get_robot(),
            self._motor_controller,
            'a'
        ).set_invert(True)

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
