class AxialMovementTask:
    """
    Moves the robot forwards or backwards by a distance.
    """

    def __init__(self, distance: float):
        """
        Constructs an AxialMovementTask.

        :param distance: The distance in meters to move the robot forward.
                         Negative values indicate backward movement.
        """
        self._distance = distance

    def get_distance(self) -> float:
        """
        Returns the distance to move the robot forward.

        :return: The distance in meters to move the robot forward.
                 Negative values indicate backward movement.
        """
        return self._distance
