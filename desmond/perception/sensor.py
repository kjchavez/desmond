import uuid
import logging
import zmq

from desmond.network import ipaddr

class Sensor(object):
    def __init__(self, name, protocol="inproc"):
        self.name = name
        if protocol not in ("inproc", "tcp"):
            raise ValueError("protocol must be one of {inproc, tcp}")
        self.protocol = protocol
        self.socket = None
        self.address = None

    def bind(self):
        context = zmq.Context.instance()
        self.socket = context.socket(zmq.PUB)
        if self.protocol == "tcp":
            port_selected = self.socket.bind_to_random_port('tcp://*', min_port=8001, max_port=9000,
                                                            max_tries=100)

            self.address = "tcp://%s:%d" % (ipaddr.get_local_ip_addr(), port_selected)

        elif self.protocol == "inproc":
            self.address = "inproc://%s" % (str(uuid.uuid4()),)
            self.socket.bind(self.address)

    def __del__(self):
        if self.socket is not None:
            self.socket.close()

