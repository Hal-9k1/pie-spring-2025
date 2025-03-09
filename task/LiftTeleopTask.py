class LiftTeleopTask:
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
