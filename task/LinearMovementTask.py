class LinearMovementTask:
    """
    Tells a robot supporting holonomic drive to move in a straight line without turning.
    """

    def __init__(self, axial: float, lateral: float):
        """
        Constructs a LinearMovementTask.

        :param axial: The distance to move in the forward direction (meters).
                      Negative values indicate backward movement.
        :param lateral: The distance to move in the rightward direction (meters).
                        Negative values indicate leftward movement.
        """
        self.axial = axial
        self.lateral = lateral

    def get_axial(self) -> float:
        """
        Returns the distance in meters to move in the forward direction.
        Negative values indicate backward movement.
        """
        return self.axial

    def get_lateral(self) -> float:
        """
        Returns the distance in meters to move in the robot's rightward direction.
        Negative values indicate leftward movement.
        """
        return self.lateral
