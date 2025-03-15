class HolonomicDriveTask:
    """
    Specifies relative accelerations for the axial, lateral, and yaw component
    of a holonomic drive (a drive train that can strafe without turning).
    """

    def __init__(self, axial: float, lateral: float, yaw: float):
        """
        Constructs a HolonomicDriveTask.

        :param axial: The relative acceleration to apply in the direction the robot is facing.
                      Positive values indicate forward movement, and negative values indicate backward.
        :param lateral: The relative acceleration to apply in the direction perpendicular
                        to the one the robot is facing. Positive values indicate rightward
                        movement, and negative values indicate leftward.
        :param yaw: The relative acceleration to use to turn the robot.
                    Positive values indicate counterclockwise turning, and negative values indicate clockwise.
        """
        self.axial = axial
        self.lateral = lateral
        self.yaw = yaw

    def get_axial(self) -> float:
        """
        Returns the relative acceleration to apply in the direction the robot is facing.
        """
        return self.axial

    def get_lateral(self) -> float:
        """
        Returns the relative acceleration to apply in the perpendicular direction
        to the one the robot is facing.
        """
        return self.lateral

    def get_yaw(self) -> float:
        """
        Returns the relative acceleration to use to turn the robot.
        """
        return self.yaw
