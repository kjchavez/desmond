from desmond.perception.sensor_reader import SensorReader
from desmond.perception.sensor_spec_pb2 import SensorSpec
from google.protobuf import wrappers_pb2

addr = input("Sensor addr: ")
spec = SensorSpec()
spec.data_source.address = addr
spec.data_source.dtype = "desmond.perception.SensorDatum"

def unwrap_print(datum):
    s = wrappers_pb2.StringValue()
    datum.payload.Unpack(s)
    print(datum.time_usec)
    print(s)

reader = SensorReader(spec, unwrap_print)
reader.run()
