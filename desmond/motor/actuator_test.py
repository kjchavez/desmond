import threading
import time
import pyre
from desmond.motor import actuator
from desmond.motor import MotorService
from desmond import types

def text_printer():
    receiver = actuator.Receiver("Printer", types.Text)
    while True:
        print(receiver.recv())


t = threading.Thread(target=text_printer)
t.daemon = True
t.start()

service = MotorService()

time.sleep(1)

text = types.Text()
text.value = "Hello World!"
# For now... should actually be proto or json
service.actuators[0].send(text.SerializeToString())
