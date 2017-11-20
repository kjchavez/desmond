import logging
import threading
import zmq
from desmond.perception import sensor_spec_pb2

class SensorReader(object):
    def __init__(self, sensor_spec, callback):
        self.spec = sensor_spec
        self.callback = callback
        self.stop_requested = False

    def run(self):
        instance = zmq.Context.instance()
        sock = instance.socket(zmq.SUB)
        sock.setsockopt_string(zmq.SUBSCRIBE, "")
        address = self.spec.data_source.address
        logging.info("Connecting to %s", address)
        sock.connect(address)
        while not self.stop_requested:
            # TODO(kjchavez): Set a timeout based on the spec!
            logging.debug("Waiting for sensor input on %s", address)
            topic, datum_bytes = sock.recv().split(b" ", 1)
            print(topic, datum_bytes)
            datum = sensor_spec_pb2.SensorDatum()
            datum.ParseFromString(datum_bytes)
            self.callback(datum)

    def start(self):
        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()

    def stop(self):
        self.stop_requested = True

