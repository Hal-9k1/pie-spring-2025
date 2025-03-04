from logging import LoggerBackend
from ioutil import write_flexible_string
from ioutil import write_double
from socket import socket
from queue import Queue

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
        self._packets_in_flight = Queue()
        self._network_thread = None

    def start(self):
        if self._network_thread != None:
            raise RuntimeError("DuskClient already started")
        self._network_thread = process.Process(target=_connect_loop, args=(self,))
        self._stopping = False
        self._network_thread.start()

    def stop(self):
        if self._network_thread == None:
            raise RuntimeError("DuskClient not started")
        self._stopping = True
        self._network_thread.join()
        self._stopping = False

    def process_position(self, logger_label, item_label, position):
        packet = bytearray(_TYPE_POS)
        write_flexible_string(packet, logger_label)
        write_flexible_string(packet, item_label)
        write_double(packet, position.get_x())
        write_double(packet, position.get_y())
        self._packets_in_flight.put(packet)

    def process_vector(self, logger_label, item_label, attach_label, vector):
        packet = bytearray(_TYPE_VEC)
        write_flexible_string(packet, logger_label)
        write_flexible_string(packet, item_label)
        write_flexible_string(packet, attach_label)
        write_double(packet, vector.get_x())
        write_double(packet, vector.get_y())
        self._packets_in_flight.put(packet)

    def process_transform(self, logger_label, item_label, attach_label, transform):
        packet = bytearray(_TYPE_TFM)
        write_flexible_string(packet, logger_label)
        write_flexible_string(packet, item_label)
        write_flexible_string(packet, attach_label)
        write_double(packet, tfm.elem(0, 0))
        write_double(packet, tfm.elem(1, 0))
        write_double(packet, tfm.elem(2, 0))
        write_double(packet, tfm.elem(0, 1))
        write_double(packet, tfm.elem(1, 1))
        write_double(packet, tfm.elem(2, 1))
        self._packets_in_flight.put(packet)

    def process_updatable_object(self, logger_label, item_label, value):
        packet = bytearray(_TYPE_UPD)
        write_flexible_string(packet, logger_label)
        write_flexible_string(packet, item_label)
        write_flexible_string(packet, repr(value))
        self._packets_in_flight.put(packet)

    def process_log(self, log):
        packet = bytearray(_TYPE_LOG)
        log.write_to(packet)
        self._packets_in_flight.put(packet)

    def _connect(self):
        self._socket = socket()
        self._socket.connect((self._hostname, self._port))

    def _connect_loop(self):
        while not self._stopping:
            self._connect()
            self._packet_pump_loop()
            if not self._stopping:
                time.sleep(self._reconnect_timeout)

    def _packet_pump_loop(self):
        while not self._stopping:
            self._socket.sendall(self._packets_in_flight.get())
