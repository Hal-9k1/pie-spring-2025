class TurnTask(Task):
    """
    Turns the robot in place.
    """

    def __init__(self, angle: float):
        """
        Constructs a TurnTask.

        :param angle: the angle in radians to turn the robot counterclockwise.
        """
        self.angle = angle

    def get_angle(self) -> float:
        """
        Returns the angle in radians to turn the robot counterclockwise.

        :return: the angle in radians to turn the robot counterclockwise. Negative values indicate
                 clockwise turns.
        """
        return self.angle
