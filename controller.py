class LayerGraph:
    def __init__(self):
        self._parents = {}
        self._children = {}

    def add_connection(self, a, b):
        parent_outs = a.get_output_tasks()
        child_ins = b.get_input_tasks()
        if not isinstance(parent_outs, set):
            raise TypeError(f'Output tasks of {a} is not a set')
        if not isinstance(child_ins, set):
            raise TypeError(f'Input tasks of {b} is not a set')
        if not parent_outs.isdisjoint(child_ins):
            raise TypeError(f'Parent {a} and child {b} share no compatible task interface')

        if a not in self._children:
            self._children[a] = {b}
        else:
            self._children[a].add(b)
        if b not in self._parents:
            self._parents[b] = {a}
        else:
            self._parents[b].add(a)

    def add_connections(self, connections):
        try:
            if any(len(c) != 2 for c in connections):
                raise TypeError
        except TypeError:
            raise ValueError('Parameter must be an iterable of two-element iterables')
        self._connections.extend((c[0], c[1]) for c in connections)

    def add_chain(self, chain):
        if len(chain) < 2:
            raise ValueError('Parameter must have at least two elements')
        for connection in zip(chain[:-1], chain[1:]):
            self.add_connection(connection)

    def get_verts(self):
        return {e for l in (self._parents.keys(), *self._parents.values()) for e in l}

    def map_all(self, mapper):
        verts = self.get_verts()
        mapped = {v: mapper(v) for v iv verts}
        new = LayerGraph()
        new._parents = {mapped[k]: {mapped[vi] for vi in v} for k, v in self._parents.items()}
        new._children = {mapped[k]: {mapped[vi] for vi in v} for k, v in self._children.items()}
        return new

    def get_children(self, vertex):
        return self._children.get(vertex, set())

    def get_parents(self, vertex):
        return self._parents.get(vertex, set())

    def get_sources(self):
        return {v in self.get_verts() if v not in self._parents}

    def get_sinks(self):
        return {v in self.get_verts() if v not in self._children}


class RobotController:
    def __init__(self):
        self._layers = None

    def setup(self, robot, localizer, layers, gamepad, keyboard, logger_provider, debug_mode=False):
        self._logger = logger_provider.get_logger("RobotController")
        setup_info = LayerSetupInfo(
            self,
            robot,
            localizer,
            gamepad,
            keyboard,
            logger_provider
        )
        for layer in layers.get_verts():
            layer.setup(setup_info)
        self._layers = layers.map_all(LayerInfo)
        self._debug_mode = debug_mode
        self._update_listeners = []
        self._teardown_listeners = []

    def update():
        self._logger.trace('Begin update')
        for listener in self._update_listeners:
            listener()
        if layers == None:
            return True

        hot = self._layers.get_sinks()

        while hot:
            layer = hot.pop()
            self._logger.trace(f'Now processing {str(layer)}')
            completed_tasks = []
            subtasks = []

            ctx = LayerProcessContext(
                lambda t: subtasks.append(subtask),
                lambda t: completed_tasks.append(t)
            )
            layer.process(ctx)

            for task in completed_tasks:
                for parent in self._layers.get_parents(layer):
                    if any(isinstance(task, cls) for cls in parent.get_output_tasks()):
                        parent.subtask_completed(task)
                        hot.add(parent)

            for task in subtasks:
                for child in self._layers.get_children(layer):
                    if any(isinstance(task, cls) for cls in child.get_input_tasks()):
                        child.accept_task(task)

            if escalate and not self._layers.get_parents(layer):
                for listener in self._teardown_listeners:
                    listener()
                self._update_listeners = []
                self._teardown_listeners = []
                self._layers = None
                return True
        return False
    }

    /**
     * Registers a function to be called on every update.
     * Registers a function to be called on every update of the controller before layer work is
     * performed. Listeners are executed in registration order. After teardown,
     * listeners are unregistered.
     *
     * @param listener - the function to be registered as an update listener.
     */
    public void addUpdateListener(Runnable listener) {
        updateListeners.add(listener);
    }

    /**
     * Registers a function to be called when the layer stack finishes executing.
     * On the first update after the topmost layer runs out of tasks, the
     * listeners are called in registration order, then unregistered.
     *
     * @param listener - the function to be registered as an update listener.
     */
    public void addTeardownListener(Runnable listener) {
        teardownListeners.add(listener);
    }

    /**
     * Thinly wraps a Layer while storing its last accepted task.
     */
    private static class LayerInfo {
        /**
         * The contained Layer.
         */
        private Layer layer;

        /**
         * The last tasks the contained Layer accepted at once.
         */
        private ArrayList<Task> lastTasks;

        /**
         * Whether the previous accepted task satisfied the Layer's need for new tasks.
         */
        private boolean lastTaskSaturated;

        /**
         * Constructs a LayerInfo.
         *
         * @param layer - the Layer to contain.
         */
        LayerInfo(Layer layer) {
            this.layer = layer;
            lastTasks = new ArrayList<>();
            lastTaskSaturated = true;
        }

        /**
         * Returns the implementing class name of the contained Layer.
         *
         * @return the contained Layer's concrete class name.
         */
        public String getName() {
            return layer.getClass().getSimpleName();
        }

        /**
         * Calls {@link Layer#isTaskDone} on the contained Layer.
         *
         * @return whether the contained Layer is finished processing its last accepted task.
         */
        public boolean isTaskDone() {
            return layer.isTaskDone();
        }

        /**
         * Calls {@link Layer#update} on the contained Layer.
         *
         * @param completed - an iterable of the tasks emitted by this Layer that have been
         * completed since the last call to this method.
         * @return an iterator of the tasks for the layer below to accept.
         */
        public Iterator<Task> update(Iterable<Task> completed) {
            return layer.update(completed);
        }

        /**
         * Calls {@link Layer#acceptTask} on the contained Layer.
         * Must not be called if {@link #isTaskDone} returns false.
         *
         * @param task - the task the contained layer should be offered.
         */
        public void acceptTask(Task task) {
            if (lastTaskSaturated) {
                lastTasks.clear();
            }
            lastTasks.add(task);
            layer.acceptTask(task);
            lastTaskSaturated = !layer.isTaskDone();
        }

        /**
         * Returns the layer's last accepted tasks.
         *
         * @return an iterable of the tasks last accepted by the layer.
         * @see #acceptTask
         */
        public Iterable<Task> getLastTasks() {
            return lastTasks;
        }
    }
}

