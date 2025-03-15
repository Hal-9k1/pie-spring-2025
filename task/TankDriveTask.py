class TankDriveTask:
    """
    Specifies relative accelerations for left and right side of the robot.
    Despite the name, not necessarily produced by tank drive controls.
    """

    def __init__(self, left: float, right: float):
        """
        Constructs a TankDriveTask.

        :param left: the relative acceleration to apply to the left side of the robot.
        :param right: the relative acceleration to apply to the right side of the robot.
        """
        self.left = left
        self.right = right

    def get_left(self) -> float:
        """
        Returns the relative acceleration to apply to the left side of the robot.

        :return: the relative acceleration to apply to the left side of the robot. Positive values
                 indicate forward movement and negative values indicate backward.
        """
        return self.left

    def get_right(self) -> float:
        """
        Returns the relative acceleration to apply to the right side of the robot.

        :return: the relative acceleration to apply to the right side of the robot. Positive values
                 indicate forward movement and negative values indicate backward.
        """
        return self.right
