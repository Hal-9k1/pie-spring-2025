from task import Task


class LocalizationTask(Task):
    def __init__(self, transform):
        self._transform = transform

    def get_robot_field_transform(self):
        return self._transform
