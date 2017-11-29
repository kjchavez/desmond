import logging
import time
import uuid
import zmq
import pyre

from desmond.perception import sensor_spec_pb2
from desmond.network import ipaddr

def time_usec():
    return int(time.time()*1e6)

class Sensor(object):
    # The topic should
    DEFAULT_TOPIC = b"data"
    def __init__(self, name, protocol="inproc"):
        self.name = name
        if protocol not in ("inproc", "tcp"):
            raise ValueError("protocol must be one of {inproc, tcp}")
        self.protocol = protocol
        self.socket = None
        self.address = None
        self._bind()

    def _bind(self):
        context = zmq.Context.instance()
        self.socket = context.socket(zmq.PUB)
        if self.protocol == "tcp":
            port_selected = self.socket.bind_to_random_port('tcp://*', min_port=8001, max_port=9000,
                                                            max_tries=100)

            self.address = "tcp://%s:%d" % (ipaddr.get_local_ip_addr(), port_selected)

        elif self.protocol == "inproc":
            self.address = "inproc://%s" % (str(uuid.uuid4()),)
            self.socket.bind(self.address)

        # Make this service discoverable.
        # We don't actually care to discover other nodes on the network
        node = pyre.Pyre()
        node.set_header("des-sensor", self.address)
        node.start()


    def emit(self, proto, topic=None):
        """Publishes data on bound address."""
        datum = sensor_spec_pb2.SensorDatum()
        datum.time_usec = time_usec()
        datum.payload.Pack(proto)
        self.socket.send(b"%s %s" % (topic or Sensor.DEFAULT_TOPIC, datum.SerializeToString()))

    def __del__(self):
        if self.socket is not None:
            self.socket.close()

