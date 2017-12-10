from desmond.perception import sensor

def smoke_test():
    s = sensor.Sensor("foo")
    print(s.node.name)
    s2 = sensor.Sensor("bar", transport="inproc")
    print(s2.node.name)
    s.shutdown()
    s2.shutdown()
