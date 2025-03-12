from layer import Layer

class TopLayerSequence(Layer):
    def __init__(self, layers):
        # Is a list
        self._layers = layers

        # is a iterator
        self._layer_iter = None

        # Top level layer being operated on.
        self._layer = None

        self._logger = None

    def is_task_done(self):
        if has_next(self._layer_iter) and self._layer.is_task_done():
            return True
        else:
            return False

    def setup(self, setup_info):
        name = []

        for elem in self._layers:
            name.append(elem.__class__)
            elem.setup(setupInfo)
        
        self._logger = setup_info.get_logger(f'TopLayerSequence[{name.join(", ")}]')

        self._layer_iter = iter(self._layers)
        layer = next(self._layer_iter)

    def update(self, completed):
        subtasks = self._layer.update(iter(completed))
        if(self._layer.is_task_done() and has_next(self._layer_iter)):
            self._layer = self._layer_iter.next()

        return subtasks


    def has_next(self, layerIter):
        if layerIter.next() == None:
            return False
        else:
            return True
