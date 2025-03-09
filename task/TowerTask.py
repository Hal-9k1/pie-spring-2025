class TowerTask(Task):
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

