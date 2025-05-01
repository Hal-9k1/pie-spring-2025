from controller import LayerGraph
from controller import RobotController
from layer import Layer
from log import LoggerProvider
from log import StdioBackend
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
        self._rc.setup(None, None, self._lg, LoggerProvider())

    def _test_rc(self):
        self._create_rc()
        for _ in range(100):
            if self._rc.update():
                break
        else:
            self.fail('Program did not complete in 100 updates.')

    def _check_collector(self, c, types):
        self.assertEqual(types, [type(t) for t in c.collect()])

    def _check_collector_unordered(self, c, types):
        unique = {t for t in types}
        collected = [type(t) for t in c.collect()]
        for t in unique:
            self.assertEqual(collected.count(t), types.count(t))

    def test_direct(self):
        c = CollectLayer()
        self._lg.add_chain([
            EmitterLayer([WinTask()]),
            c
        ])
        self._test_rc()
        self._check_collector(c, [WinTask])

    def test_short_chain(self):
        c = CollectLayer()
        self._lg.add_chain([
            EmitterLayer([WinTask()]),
            FlatMapLayer({
                WinTask: [GameActionTask(), GameActionTask()],
            }),
            c
        ])
        self._test_rc()
        self._check_collector(c, [GameActionTask] * 2)

    def test_chain(self):
        c = CollectLayer()
        self._lg.add_chain([
            EmitterLayer([WinTask()]),
            FlatMapLayer({
                WinTask: [GameActionTask(), GameActionTask()],
            }),
            FlatMapLayer({
                GameActionTask: [PeripheralTask(), PathfindTask()],
            }),
            c
        ])
        self._test_rc()
        self._check_collector(c, [PeripheralTask, PathfindTask] * 2)

    def test_split(self):
        peripheral_layer = CollectLayer(input_tasks={PeripheralTask})
        drive_layer = CollectLayer(input_tasks={DriveTask})
        snooper_layer = CollectLayer()

        game_action_layer = FlatMapLayer({
            GameActionTask: [PeripheralTask(), DriveTask()],
        })
        self._lg.add_chain([
            EmitterLayer([WinTask()]),
            FlatMapLayer({
                WinTask: [GameActionTask(), GameActionTask()],
            }),
            game_action_layer,
            snooper_layer,
        ])
        self._lg.add_connection(game_action_layer, peripheral_layer)
        self._lg.add_connection(game_action_layer, drive_layer)
        self._test_rc()
        self._check_collector(peripheral_layer, [PeripheralTask] * 2)
        self._check_collector(drive_layer, [DriveTask] * 2)
        self._check_collector_unordered(snooper_layer, [PeripheralTask, DriveTask] * 2)


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
    def __init__(self, input_tasks=None):
        self._tasks = []
        self._task = None
        self._input_tasks = input_tasks or {Task}

    def setup(self, setup_info):
        self._logger = setup_info.get_logger('CollectLayer')

    def get_input_tasks(self):
        return self._input_tasks

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
        return self._tasks


class FlatMapLayer(Layer):
    def __init__(self, mapping):
        self._mapping = mapping
        self._task = None
        self._subtasks = None
        self._complete = True
        self._emitted = None

    def setup(self, setup_info):
        self._logger = setup_info.get_logger('FlatMapLayer')

    def get_input_tasks(self):
        return set(self._mapping.keys())

    def get_output_tasks(self):
        return {type(v) for l in self._mapping.values() for v in l}

    def subtask_completed(self, task):
        if task == self._emitted:
            self._complete = True

    def process(self, ctx):
        if self._complete:
            if self._subtasks:
                subtask = next(self._subtasks, None)
                if subtask:
                    self._complete = False
                    ctx.emit_subtask(subtask)
                    self._emitted = subtask
                else:
                    self._subtasks = None
            if not self._subtasks:
                if self._task:
                    ctx.complete_task(self._task)
                    self._task = None
                ctx.request_task()

    def accept_task(self, task):
        self._task = task
        self._subtasks = iter(self._mapping[type(task)])

class EmitterLayer(Layer):
    def __init__(self, tasks):
        self._tasks = iter(tasks)
        self._task_types = {type(t) for t in tasks}
        self._complete = True

    def setup(self, setup_info):
        self._logger = setup_info.get_logger('EmitterLayer')

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

class ConcurrentEmitterLayer(Layer):
    def __init__(self, groups):
        self._groups = iter(groups)
        self._task_types = {type(t) for g in groups for t in g}
        self._task = None
        self._should_emit = True

    def get_input_tasks(self):
        return set()

    def get_output_tasks(self):
        return self._task_types

    def subtask_completed(self, task):
        if task in self._pending:
            self._pending.remove(task)

    def process(self, ctx):
        if not self._pending:
            self._pending = next(self._groups, None)
            if not self._pending:
                if self._task:
                    ctx.complete_task(self._task)
                    self._task = None
                ctx.request_task()
        if self._should_emit:
            self._should_emit = False
            for t in self._pending:
                ctx.emit_subtask(t)

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
