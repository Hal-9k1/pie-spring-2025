from layer import Layer
from devices import DistanceSensor
from devices import Motor
from devices import Servo
from mechanisms import ServoTurret
from task import WinTask
from task.manipulator import DriveBeltTask
from task.manipulator import DriveButtonPusherTask
from task.manipulator import DriveWheelBeltTask
from task.sensory import SensorTurretTask


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
    HIGH_POSITION = 1
    LOW_POSITION = -1

    def setup(self, setup_info):
        self._servo = setup_info.get_device(Servo, 'button_pusher_servo')
        self._task = None
        self._init = True

    def get_input_tasks(self):
        return {DriveButtonPusherTask}

    def get_output_tasks(self):
        return set()

    def process(self, ctx):
        if self._init:
            self._init = False
            self._servo.set_position(self.HIGH_POSITION)
        if self._task:
            ctx.complete_task(self._task)
            self._task = None
        ctx.request_task()

    def accept_task(self, task):
        self._task = task
        if task.should_change():
            self._servo.set_position(
                self.HIGH_POSITION if task.is_high()
                else self.LOW_POSITION
            )


class SensorTurretLayer(Layer):
    FULL_RANGE_TIME = 0.75
    SAFE_RANGE = (-1, 0.6)

    def setup(self, setup_info):
        self._turret = ServoTurret(
            setup_info.get_device(Servo, 'sensor_turret_servo'),
            self.FULL_RANGE_TIME,
            self.SAFE_RANGE
        )
        self._sensor = setup_info.get_device(DistanceSensor, 'turret_sensor')
        self._running = False
        self._subtask = None
        self._should_emit = True

    def get_input_tasks(self):
        return {WinTask}

    def get_output_tasks(self):
        return {SensorTurretTask}

    def subtask_completed(self, task):
        if task == self._subtask:
            self._subtask = None
            self._should_emit = True

    def process(self, ctx):
        if self._running:
            self._turret.move()
            if self._should_emit and self._sensor.can_read():
                self._should_emit = False
                ctx.emit_subtask(SensorTurretTask(
                    self._turret.get_angle(),
                    self._sensor.get_distance(),
                ))
                print('emit')
        else:
            ctx.request_task()

    def accept_task(self, task):
        if isinstance(task, WinTask):
            self._running = True
