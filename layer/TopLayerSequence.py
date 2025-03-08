class TopLayerSequence(Layer):
    def __init__(self, layers):
        # Is a list
        self.layers = layers

        # is a iterator
        self.layerIter = None

        # Top level layer being operated on.
        self.layer = None

        self.logger = None

    def isTaskDone(self):
        if hasNext(layerIter) and layer.isTaskDone():
            return True
        else:
            return False

    def setup(self, setupInfo):
        name = []

        for elem in layers:
            name.append(elem.__class__)
            elem.setup(setupInfo)
        
        logger = setupInfo.getLogger(f'TopLayerSequence[{name.join(", ")}]')

        self.layerIter = iter(layers)
        layer = next(self.layerIter)

    def update(self, completed):
        subtasks = layer.update(iter(completed))
        if(layer.isTaskDone() and hasNext(layerIter):
            layer = layerIter.next()

        return subtasks


    def hasNext(layerIter):
        if layerIter.next() == None:
            return False
        else:
            return True
