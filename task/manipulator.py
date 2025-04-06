from task import Task

class LiftTask(Task):
    """
    Extends or retracts the lift.
    """

    def __init__(self, swing: float, full_extend: bool, full_retract: bool, raise_lift: bool, lower_lift: bool):
        """
        Constructs a LiftTask.

        :param swing: The rotation of the arm in radians.
        :param full_extend: Whether the lift should be fully extended.
        :param full_retract: Whether the lift should be fully retracted.
        :param raise_lift: Whether the lift should be fully raised in an arc.
        :param lower_lift: Whether the lift should be fully lowered in an arc.
        """
        if full_extend and full_retract:
            raise ValueError("Cannot simultaneously fully extend and fully retract the lift.")
        if raise_lift and lower_lift:
            raise ValueError("Cannot simultaneously fully raise and lower the lift in an arc.")

        self.swing = swing
        self.full_extend = full_extend
        self.full_retract = full_retract
        self.raise_lift = raise_lift
        self.lower_lift = lower_lift


class LiftTeleopTask(Task):
    """
    Extends, retracts, or swings a lift using absolute powers.
    """

    def __init__(self, swing: float, extension: float):
        """
        LiftTeleopTask constructor.

        :param swing: The direction and speed the lift should swing with. Must be in the range [-1, 1].
        :param extension: The direction and speed the lift should extend with.
                          Must be in the range [-1, 1]. Negative values indicate retraction.
        """
        self.swing = swing
        self.extension = extension


class TowerForearmTask(Task):
    """
    Unfolds the tower's forearm.
    Should be issued before any other tower tasks to initialize the tower.
    """

    def __init__(self):
        """
        Constructs a TowerForearmTask.
        """
        passclass TowerTask(Task):
    """
    Raises or lowers the arm in an arc.
    """

    def __init__(self, full_raise: bool, full_lower: bool):
        """
        Constructs a TowerTask.

        :param full_raise: Whether the tower should be fully raised in an arc.
        :param full_lower: Whether the tower should be fully lowered in an arc.
        """
        if full_raise and full_lower:
            raise ValueError("The arm can't be both fully raised and fully lowered")

        self.full_raise = full_raise
        self.full_lower = full_lower

    def get_full_raise(self) -> bool:
        """
        Returns whether the tower should be fully raised in an arc.

        :return: whether the tower should be fully raised in an arc.
        """
        return self.full_raise

    def get_full_lower(self) -> bool:
        """
        Returns whether the tower should be fully lowered in an arc.

        :return: whether the tower should be fully lowered in an arc.
        """
        return self.full_lower


class TowerTeleopTask(Task):
    """
    Controls the tower in teleop.
    """

    def __init__(self, tower_swing_power: float, forearm_swing_power: float):
        """
        Constructs a TowerTeleopTask.

        :param tower_swing_power: the direction and speed to swing the tower in.
        :param forearm_swing_power: the direction and speed to swing the forearm in.
        """
        self.tower_swing_power = tower_swing_power
        self.forearm_swing_power = forearm_swing_power

    def get_tower_swing_power(self) -> float:
        """
        Returns the direction and speed to swing the tower in.

        :return: the direction and speed to swing the tower in. Negative values lower the tower
                 (towards the front of the robot).
        """
        return self.tower_swing_power

    def get_forearm_swing_power(self) -> float:
        """
        Returns the direction and speed to swing the forearm in.

        :return: the direction and speed to swing the forearm in. Negative values lower the forearm
                 (towards the front of the robot if the tower is fully lowered).
        """
        return self.forearm_swing_power
