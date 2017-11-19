from desmond.perception import sensor

def smoke_test():
    s = sensor.Sensor("foo")
    s.bind()
    print(s.address)
    s2 = sensor.Sensor("bar", protocol="tcp")
    s2.bind()
    print(s2.address)
