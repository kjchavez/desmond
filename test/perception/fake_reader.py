from desmond.perception.sensor_reader import SensorReader
from desmond.perception.sensor_spec_pb2 import SensorSpec

addr = input("Sensor addr: ")
spec = SensorSpec()
spec.data_source.address = addr
spec.data_source.dtype = "desmond.perception.SensorDatum"

reader = SensorReader(spec, print)
reader.run()
