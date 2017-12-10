import time

from desmond.perception import sensor_data_pb2
from desmond import thought

def time_usec():
    return int(time.time()*1e6)

class Sensor(object):
    def __init__(self, name, transport="tcp"):
        self.node = thought.DesmondNode(name, [], sensor_data_pb2.SensorDatum,
                                        transport=transport)
        self.name = name

    def emit(self, proto):
        """Publishes data on bound address."""
        datum = sensor_data_pb2.SensorDatum()
        datum.time_usec = time_usec()
        datum.payload.Pack(proto)
        self.node.publish(datum)

    def shutdown(self):
        self.node.shutdown()

