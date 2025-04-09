from controller import LayerGraph
from controller import RobotController
from layer import Layer
from log import LoggerProvider
from task import Task
from unittest import TestCase


class TestLayerGraph(TestCase):
    def setUp(self):
        self._g = LayerGraph()

    def test_add_connection(self):
        self._g.add_connection(OutputOnlyLayer(), InputOnlyLayer())
        self._assert_verts(2)

    def test_connection_param_types(self):
        with self.assertRaisesRegex(TypeError, 'is not a Layer'):
            self._g.add_connection(None, TestLayer())
        with self.assertRaisesRegex(TypeError, 'is not a Layer'):
            self._g.add_connection(TestLayer(), 'foo')
        with self.assertRaisesRegex(TypeError, 'is not a Layer'):
            self._g.add_connection(TestLayer, TestLayer)

    def test_connection_compat(self):
        with self.assertRaisesRegex(TypeError, 'compatible'):
            self._g.add_connection(InputOnlyLayer(), OutputOnlyLayer())

    def test_connection_cyclic(self):
        a = TestLayer()
        b = TestLayer()
        self._g.add_connection(a, b)
        with self.assertRaisesRegex(ValueError, 'Cycle'):
            self._g.add_connection(b, a)

    def test_add_connections(self):
        self._g.add_connections([
            (OutputOnlyLayer(), InputOnlyLayer()),
        ])
        self._assert_verts(2)

    def test_add_connections_empty(self):
        self._g.add_connections([])
        self._assert_verts(0)

    def test_connections_param_types(self):
        with self.assertRaises(ValueError):
            LayerGraph().add_connections(None)

    def test_connections_param_shape(self):
        with self.assertRaises(ValueError):
            LayerGraph().add_connections('humbug')
        with self.assertRaises(ValueError):
            LayerGraph().add_connections([
                (OutputOnlyLayer(),),
                (InputOnlyLayer(),),
            ])

    def test_add_chain(self):
        self._g.add_chain([OutputOnlyLayer(), InputOnlyLayer()])
        self._assert_verts(2)

    def _assert_verts(self, verts):
        self.assertEqual(len(self._g.get_verts()), verts)


class TestLayerGraphRelations(TestCase):
    def setUp(self):
        self._g = LayerGraph()
        self._a = OutputOnlyLayer()
        self._b = InputOnlyLayer()
        self._g.add_connection(self._a, self._b)

    def test_get_children(self):
        self.assertEqual(self._g.get_children(self._a), {self._b})

    def test_get_parents(self):
        self.assertEqual(self._g.get_parents(self._b), {self._a})

    def test_get_sources(self):
        self.assertEqual(self._g.get_sources(), {self._a})

    def test_get_parents(self):
        self.assertEqual(self._g.get_sinks(), {self._b})


class TestRobotController(TestCase):
    def setUp(self):
        self._lg = LayerGraph()

    def _create_rc(self):
        self._rc = RobotController()
        self._rc.setup(None, None, self._lg, None, None, LoggerProvider())

    def test_chain(self):
        c = CollectLayer()
        self._lg.add_chain([
            EmitterLayer([WinTask()]),
            FlatMapLayer({
                WinTask: [GameActionTask(), GameActionTask()],
            }),
            c
        ])
        for _ in range(100):
            if self._rc.update():
                break
        else:
            self.fail('Program did not complete in 100 updates.')
        self.assertEqual([GameActionTask, GameActionTask], [type(t) for t in c.collect()])


class TestLayer(Layer):
    def get_input_tasks(self):
        return {Task}

    def get_output_tasks(self):
        return {Task}

    def subtask_completed(self, task):
        pass

    def process(self, ctx):
        raise NotImplementedError

    def accept_task(self, task):
        raise NotImplementedError


class OutputOnlyLayer(TestLayer):
    def get_input_tasks(self):
        return set()


class InputOnlyLayer(TestLayer):
    def get_output_tasks(self):
        return set()


class CollectLayer(Layer):
    def __init__(self):
        self._tasks = []
        self._task = None

    def get_input_tasks(self):
        return {Task}

    def get_output_tasks(self):
        return set()

    def process(self, ctx):
        if self._task:
            ctx.complete_task(self._task)
            self._task = None
        ctx.request_task()

    def accept_task(self, task):
        self._task = task
        self._tasks.append(task)

    def collect(self):
        return self._task


class FlatMapLayer(Layer):
    def __init__(self, mapping):
        self._mapping = mapping
        self._task = None
        self._subtasks = None
        self._complete = True

    def get_input_tasks(self):
        return set(self._mapping.keys())

    def get_output_tasks(self):
        return {v for l in self._mapping.values() for v in l}

    def subtask_completed(self, task):
        self._complete = True

    def process(self, ctx):
        if self._complete:
            if self._subtasks:
                self._complete = False
                subtask = next(self._subtasks, None)
                if subtask:
                    ctx.emit_subtask(subtask)
                else:
                    self._subtasks = None
            if not self._subtasks:
                if self._task:
                    ctx.complete_task(self._task)
                    self._task = None
                ctx.request_task()
            
    def accept_task(self, task):
        self._task = task
        self._complete = False
        self._subtasks = iter(self._mapping[task])

class EmitterLayer(Layer):
    def __init__(self, tasks):
        self._tasks = iter(tasks)
        self._task_types = {type(t) for t in tasks}

    def get_input_tasks(self):
        return set()

    def get_output_tasks(self):
        return self._task_types

    def subtask_completed(self, task):
        self._complete = True

    def process(self, ctx):
        if self._complete:
            subtask = next(self._tasks, None)
            if subtask:
                self._complete = False
                ctx.emit_subtask(subtask)
            else:
                ctx.request_task()

    def accept_task(self, task):
        raise TypeError

class VisionTask(Task):
    pass

class WinTask(Task):
    pass

class GameActionTask(Task):
    pass

class PathfindTask(Task):
    pass

class RouteTask(Task):
    pass

class DriveTask(Task):
    pass

class PeripheralTask(Task):
    pass
