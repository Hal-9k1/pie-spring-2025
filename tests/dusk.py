from threading import Event
from threading import Lock
from threading import Thread
from queue import Queue
from unittest import TestCase
from dusk import DuskClient
from log import LoggerProvider
from socket import create_server
from socket import timeout as SocketTimeoutError
from socket import SHUT_RDWR

class TestDusk(TestCase):
    def setUp(self):
        provider = LoggerProvider().timestamp(False)
        self._client = DuskClient("localhost", 22047, 1000)
        provider.add_backend(self._client)
        self._logger = provider.get_logger("Main")
        self._packet_asserts = Queue()
        self._server_process = Thread(target=self._run_server)
        self._server_process.start()
        self._packet_assert_added_event = Event()
        self._packet_assert_added_event_lock = Lock()

    def tearDown(self):
        try:
            self._client.stop()
            proc = self._server_process
            self._server_process = None
            self._packet_assert_added_event.set()
            proc.join()
        except:
            pass

    def _run_server(self):
        try:
            while self._server_process:
                try:
                    self._dummy_server = create_server(("", 22047))
                except OSError:
                    pass
                else:
                    break
            self._dummy_server.settimeout(0.1)
            while self._server_process:
                try:
                    cxn = self._dummy_server.accept()
                    try:
                        self._handle_connection(cxn)
                        print("connection closed")
                    finally:
                        if cxn:
                            while cxn.recv():
                                pass
                            cxn.close()
                except SocketTimeoutError:
                    pass
        finally:
            if hasattr(self, "_dummy_server"):
                self._dummy_server.shutdown(SHUT_RDWR)
                self._dummy_server.close()

    def _handle_connection(self, cxn):
        print("connected")
        while self._server_process:
            try:
                if not self._packet_asserts:
                    print("Waiting for assert")
                    self._packet_assert_added_event.wait()
                    print("Assert added")
                    if not self._server_process:
                        return
                with self._packet_assert_added_event_lock:
                    print("Getting assert (should not block)")
                    packet_assert = self._packet_asserts.get()
                    self._packet_assert_added_event.clear()
                print("recv assert")
                to_recv = packet_assert.get_size()
                buf = bytearray()
                while to_recv and self._server_process:
                    recvd = cxn.recv(to_recv)
                    if not recvd:
                        raise EOFError("Client closed socket!")
                    buf += recvd
                    to_recv -= len(recvd)
                    print(f"received {len(recvd)} bytes over socket")
                if not self._server_process:
                    return
                packet_assert.check_content(buf)
                packet_assert.complete()
            except Exception as e:
                packet_assert.error(e)

    def _queue_packet_assert(self, content):
        assertion = PacketAssert(content, lambda a, b: self.assertEqual(a, b))
        with self._packet_assert_added_event_lock:
            self._packet_asserts.put(assertion)
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
        print("created assert")
        self._size = len(expected_content)
        self._expected_content = expected_content
        self._assert_eq_cb = assert_eq_cb
        self._completed_event = Event()
        self._error = None

    def complete(self):
        print("assert completed")
        import traceback
        traceback.print_stack()
        self._completed_event.set()

    def error(self, error):
        self._error = error
        self.complete()

    def check_content(self, content):
        self._assert_eq_cb(content, self._expected_content)

    def wait_for_completion(self):
        self._completed_event.wait()
        return self._error

    def get_size(self):
        return self._size
