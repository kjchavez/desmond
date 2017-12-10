""" Discovers sensors on the network and tracks their data. """
import datetime
import time
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
from desmond.thought import DesmondNode

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
        self.logdb = logdb
        self.node = None
        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()
        time.sleep(0.5)

    def run(self):
        self.node = DesmondNode("PerceptionService", [sensor_data_pb2.SensorDatum], None)
        sensor_logs = sensor_logger.SensorLogger(db_name=self.logdb)
        while not self._shutdown:
            datum = self.node.recv_or_none()
            if datum is None:
                continue
            spec = SensorSpec("", "")
            sensor_logs.write_datum(datum, spec)
            logging.info("[%s] Recieved %s from %s",
                         datetime.datetime.fromtimestamp(datum.time_usec/1e6),
                         datum.payload.type_url, spec)

        self.node.shutdown()

    @property
    def sources(self):
        return self.node.sources if self.node else []

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
