import threading
import time
import pyre
import logging

from desmond.motor import actuator
from desmond.motor import MotorService
from desmond import types

def print_once():
    receiver = actuator.Receiver("Printer", types.Text)
    cmd = receiver.recv_cmd()
    receiver.send_ok(cmd.sender)
    receiver.shutdown()

def smoke_test():
    t = threading.Thread(target=print_once)
    t.daemon = True
    t.start()

    service = MotorService()

    # Discovery takes non-negligible time. In practice, we would do something "on discovery".
    time.sleep(0.1)

    text = types.Text()
    text.value = "Hello World!"
    # For now... should actually be proto or json
    remote = service.actuators[0]
    print("Remote CommandProto =", remote.command_type)
    assert remote.command_type.decode('utf8') == types.Text.DESCRIPTOR.full_name
    rep = service.actuators[0].send(text.SerializeToString())
    assert rep.decode('utf8') == "OK"
    service.shutdown()

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    smoke_test()
