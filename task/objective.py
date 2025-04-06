from task import Task
from matrix import Mat3


class MoveToFieldTask(Task):
    """
    Instructs the robot to pathfind to a field space transform while avoiding obstacles.
    """

    def __init__(self, transform: Mat3):
        """
        Constructs a MoveToFieldTask.

        :param transform: the goal field space transform.
        """
        self._transform = transform

    def get_goal_transform(self) -> Mat3:
        """
        Returns the goal transform.

        :return: The goal field space transform.
        """
        return self._transform
