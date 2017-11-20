from desmond.perception import sensor
from desmond.perception import sensor_spec_pb2
from google.protobuf import wrappers_pb2

class CommandlineInput(object):
    def __init__(self):
        self.sensor = sensor.Sensor("commandline", protocol="tcp")
        print("Commandline sensor addr:", self.sensor.address)

    def run(self):
        while True:
            text = input(">>> ")
            if not text:
                break
            datum = sensor_spec_pb2.SensorDatum()
            payload = wrappers_pb2.StringValue()
            payload.value = text
            datum.payload.Pack(payload)
            self.sensor.emit_proto(datum)
