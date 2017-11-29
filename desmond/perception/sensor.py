import logging
import time
import uuid
import zmq
import pyre

from desmond.perception import sensor_data_pb2
from desmond.network import ipaddr

def time_usec():
    return int(time.time()*1e6)

class Sensor(object):
    def __init__(self, name, transport="tcp"):
        self.name = name
        if transport not in ("inproc", "tcp"):
            raise ValueError("transport must be one of {inproc, tcp}")
        self.transport = transport
        self.socket = None
        self.address = None
        self.node = None
        self._bind()

    def _bind(self):
        context = zmq.Context.instance()
        self.socket = context.socket(zmq.PUB)
        if self.transport == "tcp":
            port_selected = self.socket.bind_to_random_port('tcp://*', min_port=8001, max_port=9000,
                                                            max_tries=100)

            self.address = "tcp://%s:%d" % (ipaddr.get_local_ip_addr(), port_selected)

        elif self.transport == "inproc":
            self.address = "inproc://%s" % (str(uuid.uuid4()),)
            self.socket.bind(self.address)

        # Makes this service discoverable.
        # We don't actually care to discover other nodes on the network
        self.node = pyre.Pyre()
        self.node.set_header("dmd-sensor-addr", self.address)
        # Do I really need this?
        self.node.set_header("dmd-sensor-name", self.name)
        self.node.start()

    def emit(self, proto):
        """Publishes data on bound address."""
        datum = sensor_data_pb2.SensorDatum()
        datum.time_usec = time_usec()
        datum.payload.Pack(proto)
        self.socket.send(datum.SerializeToString())

    def __del__(self):
        if self.socket:
            self.socket.close()
        if self.node:
            self.node.stop()

