from task import Task


class DistanceSensorTask(Task):
    def __init__(self, distance, robot_space_transform):
        self._distance = distance
        self._transform = robot_space_transform

    def get_distance(self):
        return self._distance

    def get_robot_space_transform(self):
        return self._transform
