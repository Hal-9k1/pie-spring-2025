from task import Task


class LocalizationTask(Task):
    def __init__(self, transform):
        self._transform = transform

    def get_robot_field_transform(self):
        return self._transform


class SensorTurretTask(Task):
    def __init__(self, angle, distance):
        self._angle = angle
        self._distance = distance

    def get_angle(self):
        return self._angle

    def get_distance(self):
        return self._distance
