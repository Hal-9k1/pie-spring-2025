from matrix import Mat3  # assuming Mat3 is imported from a module

class MoveToFieldTask:
    """
    Instructs the robot to pathfind to a field space transform while avoiding obstacles.
    """

    def __init__(self, transform: Mat3):
        """
        Constructs a MoveToFieldTask.

        :param transform: the goal field space transform.
        """
        self.transform = transform

    def get_goal_transform(self) -> Mat3:
        """
        Returns the goal transform.

        :return: The goal field space transform.
        """
        return self.transform

