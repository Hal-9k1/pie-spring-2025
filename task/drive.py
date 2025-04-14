from task import Task


class AxialMovementTask(Task):
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


class TurnTask(Task):
    """
    Turns the robot in place.
    """

    def __init__(self, angle: float):
        """
        Constructs a TurnTask.

        :param angle: the angle in radians to turn the robot counterclockwise.
        """
        self._angle = angle

    def get_angle(self) -> float:
        """
        Returns the angle in radians to turn the robot counterclockwise.

        :return: the angle in radians to turn the robot counterclockwise. Negative values indicate
                 clockwise turns.
        """
        return self._angle


class LinearMovementTask(Task):
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
        self._axial = axial
        self._lateral = lateral

    def get_axial(self) -> float:
        """
        Returns the distance in meters to move in the forward direction.
        Negative values indicate backward movement.
        """
        return self._axial

    def get_lateral(self) -> float:
        """
        Returns the distance in meters to move in the robot's rightward direction.
        Negative values indicate leftward movement.
        """
        return self._lateral


class HolonomicDriveTask(Task):
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
        self._axial = axial
        self._lateral = lateral
        self._yaw = yaw

    def get_axial(self) -> float:
        """
        Returns the relative acceleration to apply in the direction the robot is facing.
        """
        return self._axial

    def get_lateral(self) -> float:
        """
        Returns the relative acceleration to apply in the perpendicular direction
        to the one the robot is facing.
        """
        return self._lateral

    def get_yaw(self) -> float:
        """
        Returns the relative acceleration to use to turn the robot.
        """
        return self._yaw


class TankDriveTask(Task):
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
        self._left = left
        self._right = right

    def get_left(self) -> float:
        """
        Returns the relative acceleration to apply to the left side of the robot.

        :return: the relative acceleration to apply to the left side of the robot. Positive values
                 indicate forward movement and negative values indicate backward.
        """
        return self._left

    def get_right(self) -> float:
        """
        Returns the relative acceleration to apply to the right side of the robot.

        :return: the relative acceleration to apply to the right side of the robot. Positive values
                 indicate forward movement and negative values indicate backward.
        """
        return self._right
