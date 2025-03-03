class TopLayerSequence(Layer):
    def __init__(self, layers):
        self.layers = layers
        self.layersIter = iter(layers)
        self.layer = None
        self.logger = None

    def isTaskDone(self):
        # not sure how to get hasNext() for iterator.
        return layer.isTaskDone()

    def setup(self, setupInfo):
        #placeholder
        pass