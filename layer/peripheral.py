from layer import Layer
from devices import Motor
from devices import Servo
from task.manipulator import DriveBeltTask
from task.manipulator import DriveButtonPusherTask
from task.manipulator import DriveWheelBeltTask


class BeltLayer(Layer):
    def setup(self, setup_info):
        self._motor = setup_info.get_device(Motor, 'belt_motor_left')
        self._motor_alt = setup_info.get_device(Motor, 'belt_motor_right')
        self._task = None

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
        self._motor_alt.set_velocity(task.get_power())


class WheelBeltLayer(Layer):
    def setup(self, setup_info):
        self._motor = setup_info.get_device(Motor, 'front_belt_motor')
        self._task = None

    def get_input_tasks(self):
        return {DriveWheelBeltTask}

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


class ButtonPusherLayer(Layer):
    HIGH_POSITION = 180
    LOW_POSITION = 0

    def setup(self, setup_info):
        self._servo = setup_info.get_device(Servo, 'button_pusher_servo')
        self._task = None

    def get_input_tasks(self):
        return {DriveButtonPusherTask}

    def get_output_tasks(self):
        return set()

    def process(self, ctx):
        if self._task:
            ctx.complete_task(self._task)
            self._task = None
        ctx.request_task()

    def accept_task(self, task):
        self._task = task
        if task.should_change():
            self._servo.set_position(self.HIGH_POSITION
                if task.is_high()
                else self.LOW_POSITION
            )
