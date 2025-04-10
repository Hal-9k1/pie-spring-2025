from layer import Layer
from layer import LayerSetupInfo
from layer import LayerProcessContext

class LayerGraph:
    def __init__(self):
        self._parents = {}
        self._children = {}

    def add_connection(self, a, b):
        if not isinstance(a, Layer):
            raise TypeError(f'{a} is not a Layer')
        if not isinstance(b, Layer):
            raise TypeError(f'{b} is not a Layer')
        parent_outs = a.get_output_tasks()
        child_ins = b.get_input_tasks()
        if not isinstance(parent_outs, set):
            raise TypeError(f'Output tasks of {a} is not a set')
        if not isinstance(child_ins, set):
            raise TypeError(f'Input tasks of {b} is not a set')
        if parent_outs.isdisjoint(child_ins):
            raise TypeError(f'Parent {a} and child {b} share no compatible task interface')

        if a not in self._children:
            self._children[a] = {b}
        else:
            self._children[a].add(b)

        if b not in self._parents:
            self._parents[b] = {a}
        else:
            self._parents[b].add(a)

        if self._check_cyclic(a):
            raise ValueError(f'Cycle detected')

    def add_connections(self, connections):
        try:
            if any(len(c) != 2 for c in connections):
                raise TypeError
        except TypeError:
            raise ValueError('Parameter must be an iterable of two-element iterables')
        for c in connections:
            self.add_connection(*c)

    def add_chain(self, chain):
        if len(chain) < 2:
            raise ValueError('Parameter must have at least two elements')
        for a, b in zip(chain[:-1], chain[1:]):
            self.add_connection(a, b)

    def get_verts(self):
        return {e for l in (self._parents.keys(), *self._parents.values()) for e in l}

    def get_children(self, vertex):
        return self._children.get(vertex, set())

    def get_parents(self, vertex):
        return self._parents.get(vertex, set())

    def get_sources(self):
        return {v for v in self.get_verts() if v not in self._parents}

    def get_sinks(self):
        return {v for v in self.get_verts() if v not in self._children}

    def _check_cyclic(self, start):
        visited = set()
        stack = [(start, iter(self._children.get(start, [])))]
        while stack:
            child = next(stack[-1][1], None)
            if child:
                if any(e[0] == child for e in stack):
                    return True
                if child in visited:
                    continue
                visited.add(child)
                stack.append([child, iter(self._children.get(child, []))])
            else:
                del stack[-1]
        return False


class RobotController:
    def __init__(self):
        self._layers = None

    def setup(self, robot, localizer, layers, gamepad, keyboard, logger_provider, debug_mode=False):
        self._logger = logger_provider.get_logger("RobotController")
        setup_info = LayerSetupInfo(
            robot,
            self,
            localizer,
            gamepad,
            keyboard,
            logger_provider
        )
        for layer in layers.get_verts():
            layer.setup(setup_info)
        self._layers = layers
        self._debug_mode = debug_mode
        self._update_listeners = []
        self._teardown_listeners = []

    def update(self):
        self._logger.trace('Begin update')
        for listener in self._update_listeners:
            listener()
        if self._layers == None:
            return True

        hot = self._layers.get_sinks()
        all_escalated = True

        while hot:
            layer = hot.pop()
            self._logger.trace(f'Now processing {str(layer)}')
            completed_tasks = []
            subtasks = []
            escalate = False
            parents = self._layers.get_parents(layer)

            def do_escalate():
                nonlocal escalate
                escalate = True

            ctx = LayerProcessContext(
                lambda t: subtasks.append(t),
                lambda t: completed_tasks.append(t),
                do_escalate
            )
            layer.process(ctx)

            for task in completed_tasks:
                for parent in parents:
                    if any(isinstance(task, cls) for cls in parent.get_output_tasks()):
                        parent.subtask_completed(task)
            for task in subtasks:
                for child in self._layers.get_children(layer):
                    if any(isinstance(task, cls) for cls in child.get_input_tasks()):
                        child.accept_task(task)

            if escalate:
                hot.update(parents)
            else:
                all_escalated = False

        if all_escalated:
            for listener in self._teardown_listeners:
                listener()
            self._update_listeners = []
            self._teardown_listeners = []
            self._layers = None
        return all_escalated

    def add_update_listener(self, listener):
        self._update_listeners.append(listener)

    def add_teardown_listener(self, listener):
        self._teardown_listeners.append(listener)

