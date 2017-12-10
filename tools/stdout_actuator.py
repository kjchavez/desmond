from desmond.motor import actuator
from desmond import types
import zmq

receiver = actuator.Receiver("Stdout", types.Text)
print("Stdout Actuator")
print("="*80)
while True:
    cmd = receiver.recv_cmd()
    if not isinstance(cmd.payload, types.Text):
        print("Wrong type?")
        print(cmd.payload)
    else:
        print(">>", cmd.payload.value)
    receiver.send_ok(cmd.sender)
