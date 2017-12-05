import threading
import time
import pyre
import logging

from desmond.motor import actuator
from desmond.motor import MotorService
from desmond import types

def print_once():
    receiver = actuator.Receiver("Printer", types.Text)
    cmd = receiver.recv()
    print(cmd.payload)
    receiver.send_ok(cmd.sender)

def smoke_test():
    t = threading.Thread(target=print_once)
    t.daemon = True
    t.start()

    service = MotorService()

    # Discovery takes non-negligible time. In practice, we would do something "on discovery".
    time.sleep(.1)

    text = types.Text()
    text.value = "Hello World!"
    # For now... should actually be proto or json
    service.actuators[0].send(text.SerializeToString())
    service.shutdown()

