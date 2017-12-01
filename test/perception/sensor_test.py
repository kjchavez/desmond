from desmond.perception import sensor

def smoke_test():
    s = sensor.Sensor("foo")
    print(s.address)
    s2 = sensor.Sensor("bar", transport="inproc")
    print(s2.address)
