class LiftTask:
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
