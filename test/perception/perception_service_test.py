from desmond.perception import perception_service
from desmond.perception import sensor
from desmond import types
import logging

def smoke_test():
    s = sensor.Sensor("test")
    service = perception_service.PerceptionService()
    assert len(service.sources) == 1, "sensor not found"
    t = types.Text()
    t.value = "Hello World!"
    s.emit(t)
    s.shutdown()
    service.shutdown()
