class UnsupportedTaskError(ValueError):
    """
    Exception raised by layers when accepting a task type they don't support.
    """

    def __init__(self, layer, task=None, msg=None):
        """
        Constructs an UnsupportedTaskException for a layer that does not support a task.

        :param layer: the Layer throwing the exception.
        :param task: the Task that the layer rejected (optional).
        :param msg: the exception message (optional).
        """
        if task:
            # If task is provided, construct a message based on the layer and task types
            super().__init__(f"Layer '{type(layer).__name__}' does not support task of type '{type(task).__name__}'.")
        elif msg:
            # If a custom message is provided, use it
            super().__init__(msg)
        else:
            # Default message if no task and no custom message are provided
            super().__init__("Unsupported task type.")
