from layer import Layer
from task.sensor import DistanceSensorTask


class DistanceSensorLayer(Layer):
    def __init__(self, controller_id, robot_space_transform):
        self._controller_id = controller_id
        self._robot_space_transform

    def setup(self, setup_info):
        self._robot = setup_info.get_robot()

    def get_input_tasks(self):
        return set()

    def get_output_tasks(self):
        return {DistanceSensorTask}

    def subtask_completed(self, task):
        if self._emitted == task:
            self._should_emit = True
    
    def process(self, ctx):
        if self._should_emit:
            self._should_emit = False
            task = DistanceSensorTask(self._robot.get_value(self._controller_id, 'distance'), self._robot_space_transform)
            self._emitted = task
            ctx.emit_subtask(task)
        # Prevent this layer from keeping the program alive
        ctx.request_task()

    def accept_task(self, task):
        raise TypeError
