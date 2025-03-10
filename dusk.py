from collections import deque
from ioutil import write_double
from ioutil import write_flexible_string
from log import LoggerBackend
from threading import Event
from threading import Lock
from threading import Thread
from socket import socket

class DuskClient(LoggerBackend):
    _TYPE_POS = b"\x01"
    _TYPE_VEC = b"\x02"
    _TYPE_TFM = b"\x03"
    _TYPE_UPD = b"\x04"
    _TYPE_LOG = b"\x05"

    def __init__(self, hostname, port, reconnect_timeout):
        self._hostname = hostname
        self._port = port
        self._reconnect_timeout = reconnect_timeout
        self._packet_queue = deque()
        self._network_thread = None
        self._stop_event = Event()
        self._packet_queued_event = Event()
        self._packet_queued_event_lock = Lock()

    def start(self):
        if self._network_thread != None:
            raise RuntimeError("DuskClient already started")
        self._network_thread = Thread(target=self._connect_loop)
        self._stop_event.clear()
        self._packet_queued_event.clear()
        self._network_thread.start()

    def stop(self):
        if self._network_thread == None:
            raise RuntimeError("DuskClient not started")
        self._stop_event.set()
        self._packet_added_event.set()
        self._network_thread.join()

    def process_position(self, logger_label, item_label, position):
        packet = bytearray(self._TYPE_POS)
        write_flexible_string(packet, logger_label)
        write_flexible_string(packet, item_label)
        write_double(packet, position.get_x())
        write_double(packet, position.get_y())
        self._queue_packet(packet)

    def process_vector(self, logger_label, item_label, attach_label, vector):
        packet = bytearray(self._TYPE_VEC)
        write_flexible_string(packet, logger_label)
        write_flexible_string(packet, item_label)
        write_flexible_string(packet, attach_label)
        write_double(packet, vector.get_x())
        write_double(packet, vector.get_y())
        self._queue_packet(packet)

    def process_transform(self, logger_label, item_label, attach_label, transform):
        packet = bytearray(self._TYPE_TFM)
        write_flexible_string(packet, logger_label)
        write_flexible_string(packet, item_label)
        write_flexible_string(packet, attach_label)
        write_double(packet, tfm.elem(0, 0))
        write_double(packet, tfm.elem(1, 0))
        write_double(packet, tfm.elem(2, 0))
        write_double(packet, tfm.elem(0, 1))
        write_double(packet, tfm.elem(1, 1))
        write_double(packet, tfm.elem(2, 1))
        self._queue_packet(packet)

    def process_updatable_object(self, logger_label, item_label, value):
        packet = bytearray(self._TYPE_UPD)
        write_flexible_string(packet, logger_label)
        write_flexible_string(packet, item_label)
        write_flexible_string(packet, repr(value))
        self._queue_packet(packet)

    def process_log(self, log):
        packet = bytearray(self._TYPE_LOG)
        log.write_to(packet)
        self._queue_packet(packet)

    def _connect(self):
        self._socket = socket()
        try:
            self._socket.connect((self._hostname, self._port))
        except OSError:
            pass

    def _connect_loop(self):
        try:
            while not self._stop_event.is_set():
                self._connect()
                self._packet_pump_loop()
                self._stop_event.wait(self._reconnect_timeout)
        finally:
            self._socket.close()

    def _packet_pump_loop(self):
        while not self._stop_event.is_set():
            if self._packet_queued_event.is_set():
                assert(self._packet_queue)
            if not self._packet_queue:
                self._packet_queued_event.wait()
                assert(self._packet_queue)
                if self._stop_event.is_set():
                    break
            with self._packet_queued_event_lock:
                packet = self._packet_queue.popleft()
                self._packet_queued_event.clear()
            try:
                self._socket.sendall(packet)
            except OSError:
                self._packet_queue.appendleft(packet)

    def _queue_packet(self, packet):
        with self._packet_queued_event_lock:
            self._packet_queue.append(packet)
            self._packet_queued_event.set()
