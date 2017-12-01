""" Discovers sensors on the network and tracks their data. """
import datetime
import json
import logging
import pyre
import threading
import uuid
import zmq

from desmond.network import message
from desmond.perception import sensor_data_pb2

class ReceivedDatum(object):
    def __init__(self, datum_bytes):
        self.datum = sensor_data_pb2.SensorDatum()
        if not self.datum.ParseFromString(datum_bytes):
            logging.warning("Failed to parse SensorDatum")
        self.type_url = self.datum.payload.type_url

    @property
    def time_usec(self):
        return self.datum.time_usec

    def deserialize_payload(self):
        raise NotImplementedError

class SensorSpec(object):
    def __init__(self, name, address):
        self.name = name
        self.address = address

    def __str__(self):
        return "{0}@{1}".format(self.name, self.address)

    @staticmethod
    def from_headers(headers):
        return SensorSpec(address=headers["dmd-sensor-addr"],
                          name=headers["dmd-sensor-name"])


class PerceptionService(object):
    def __init__(self):
        self._shutdown = False
        self.ctx = zmq.Context.instance()
        self.sources = {}
        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()

    def _add_new_source(self, spec, poller):
        sock = self.ctx.socket(zmq.SUB)
        sock.setsockopt_string(zmq.SUBSCRIBE, "")
        sock.connect(spec.address)
        poller.register(sock, zmq.POLLIN)
        self.sources[sock] = spec

    def run(self):
        self.node = pyre.Pyre()
        self.node.start()
        context = zmq.Context.instance()

        poller = zmq.Poller()
        poller.register(self.node.socket(), zmq.POLLIN)
        while not self._shutdown:
            try:
                items = dict(poller.poll(500))
            except KeyboardInterrupt:
                self.shutdown()
                return

            for ready in items:
                if ready in self.sources:
                    datum = ReceivedDatum(ready.recv())
                    logging.info("[%s] Recieved %s from %s",
                                 datetime.datetime.fromtimestamp(datum.time_usec/1e6),
                                 datum.type_url, self.sources[ready])

                elif ready == self.node.socket():
                    msg = message.PyreMessage(self.node.recv())
                    print(msg)
                    if msg.msg_type == message.PyreMessage.ENTER:
                        self._add_new_source(SensorSpec.from_headers(msg.headers),
                                             poller)

        self.node.stop()

    def shutdown(self):
        self._shutdown = True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    service = PerceptionService()
    input("Exit? ")
    service.shutdown()
