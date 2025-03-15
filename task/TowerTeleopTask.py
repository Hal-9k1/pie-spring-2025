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
