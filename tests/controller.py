from controller import LayerGraph
from controller import RobotController
from layer import Layer
from task import Task
from unittest import TestCase


class TestLayerGraph(TestCase):
    def setUp(self):
        self._g = LayerGraph()

    def test_add_connection(self):
        self._g.add_connection(_Layer_A(), _Layer_B())
        self._assert_verts(2)

    def test_connection_param_types(self):
        with self.assertRaisesRegex(TypeError, 'is not a Layer'):
            self._g.add_connection(None, _TestLayer())
        with self.assertRaisesRegex(TypeError, 'is not a Layer'):
            self._g.add_connection(_TestLayer(), 'foo')
        with self.assertRaisesRegex(TypeError, 'is not a Layer'):
            self._g.add_connection(_TestLayer, _TestLayer)

    def test_connection_compat(self):
        with self.assertRaisesRegex(TypeError, 'compatible'):
            self._g.add_connection(_Layer_B(), _Layer_A())

    def test_connection_cyclic(self):
        a = _TestLayer()
        b = _TestLayer()
        self._g.add_connection(a, b)
        with self.assertRaisesRegex(ValueError, 'Cycle'):
            self._g.add_connection(b, a)

    def test_add_connections(self):
        self._g.add_connections([
            (_Layer_A(), _Layer_B()),
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
                (_Layer_A(),),
                (_Layer_B(),),
            ])

    def test_add_chain(self):
        self._g.add_chain([_Layer_A(), _Layer_B()])
        self._assert_verts(2)

    def _assert_verts(self, verts):
        self.assertEqual(len(self._g.get_verts()), verts)


class TestLayerGraphRelations(TestCase):
    def setUp(self):
        self._g = LayerGraph()
        self._a = _Layer_A()
        self._b = _Layer_B()
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
    pass


class _TestLayer(Layer):
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


class _Layer_A(_TestLayer):
    def get_input_tasks(self):
        return set()


class _Layer_B(_TestLayer):
    def get_output_tasks(self):
        return set()
