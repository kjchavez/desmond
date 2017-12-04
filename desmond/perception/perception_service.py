""" Discovers sensors on the network and tracks their data. """
import datetime
import json
import logging
import os
import pyre
import threading
import uuid
import zmq

from desmond.network import message
from desmond.perception import sensor_data_pb2
from desmond.perception import sensor_logger

class ReceivedDatum(object):
    def __init__(self, datum_bytes):
        self.datum = sensor_data_pb2.SensorDatum()
        if not self.datum.ParseFromString(datum_bytes):
            logging.warning("Failed to parse SensorDatum")
        self.type_url = self.datum.payload.type_url

    @property
    def time_usec(self):
        return self.datum.time_usec

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
    def __init__(self, logdb=os.path.join(os.path.expanduser("~"),".desmond/sensorlogs.db")):
        self._shutdown = False
        self.ctx = zmq.Context.instance()
        self.sources = {}
        self.logdb = logdb

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
        sensor_logs = sensor_logger.SensorLogger(db_name=self.logdb)
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
                    sensor_logs.write_datum(datum.datum, self.sources[ready])
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

def cmdline_title(title):
    s = "*"*80 + "\n"
    s += "*" + title.center(78) + "*" + "\n"
    s += "*"*80
    return s

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    service = PerceptionService()
    print(cmdline_title("Perception Service"))
    service.run()
