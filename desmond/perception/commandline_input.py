from desmond.perception import sensor
from desmond.perception import sensor_spec_pb2
from google.protobuf import wrappers_pb2

class CommandlineInput(object):
    def __init__(self):
        self.sensor = sensor.Sensor("commandline")
        print("Commandline sensor addr:", self.sensor.address)

    def run(self):
        while True:
            text = input(">>> ")
            if not text:
                break
            payload = wrappers_pb2.StringValue()
            payload.value = text
            self.sensor.emit(payload)
