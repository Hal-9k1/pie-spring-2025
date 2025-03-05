from multiprocessing import Event 
from multiprocessing import Process 
from queue import Queue 
from unittest import *
from dusk import DuskClient
from log import LoggerProvider
from socket import create_server

class TestDusk(TestCase):
    def setUp(self):
        provider = logging.LoggerProvider().timestamp(False)
        self._client = dusk.DuskClient(("localhost", 22047), 1000)
        provider.add_backend(self._client)
        self._logger = provider.getLogger("Main")
        self._packet_asserts = Queue()
        self._server_process = Process(target=self._run_server, args=(self,))
        self._packet_assert_added_event = Event()

    def tearDown(self):
        try:
            proc = self._server_process
            self._server_process = None
            self._packet_assert_added_event.set()
            self._client.stop()
            proc.join()
        except:
            pass

    def _run_server(self):
        self._dummy_server = create_server(("", 22047))
        while self._server_process:
            cxn = self._dummy_server.accept()
            with cxn:
                self._handle_connection(cxn)

    def _handle_connection(self, cxn):
        while self._server_process:
            try:
                if not self._packet_asserts:
                    self._packet_assert_added_event.wait()
                    self._packet_assert_added_event.clear()
                    if not self._server_process:
                        return
                packet_assert = self._packet_asserts.get()
                to_recv = packet_assert.get_size()
                buf = bytearray()
                while to_recv and self._server_process:
                    recvd = cxn.recv(to_recv)
                    if not recvd:
                        raise EOFError("Client closed socket!")
                if not self._server_process:
                    return
                packet_assert.check_content(buf)
                packet_assert.complete()
            except Exception as e:
                packet_assert.error(e)

    def _queue_packet_assert(self, content):
        assertion = PacketAssert(content, lambda a, b: self.assertEqual(a, b))
        self._packet_asserts.add(assertion)
        self._packet_assert_added_event.set()
        err = assertion.wait_for_completion()
        if err:
            raise err

    def test_connect(self):
        self._client.start()

    def test_log(self):
        self._client.start()
        self._logger.log("Hello!")
        self._queue_packet_assert(b'\x05\x04INFO\x04Main\x00\x06Hello!')

class PacketAssert:
    def __init__(self, expected_content, assert_eq_cb):
        self._size = len(expected_content)
        self._expected_content = expected_content
        self._assert_eq_cb = assert_eq_cb
        self._completed_event = Event()
        self._error = None

    def complete(self):
        self._completed_event.set()

    def error(self, error):
        self._error = error
        self.resolve()

    def check_content(self, content):
        self._assert_eq_cb(content, self._expected_content)

    def wait_for_completion(self):
        self._completed_event.wait()
        return self._error

    def get_size(self):
        return self._size
