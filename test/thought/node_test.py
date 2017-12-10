from desmond.thought.node import DesmondNode
from desmond import types

import time
import logging
import zmq

def text(s):
    t = types.Text()
    t.value = s
    return t

logging.basicConfig(level=logging.INFO)
n1 = DesmondNode("n1", [types.Text], types.Text)
n2 = DesmondNode("n2", [types.Text], types.Text)
n3 = DesmondNode("n3", [types.Text], types.Image)
time.sleep(1)
n1.publish(text("n1 says hi!"))
n2.publish(text("n2 says hi!"))
n3.publish(types.Image())
print("N1 hears:", n1.recv())
print("N2 hears:", n2.recv())
print("N3 hears:", n3.recv())
print("N3 hears:", n3.recv())
print(n1.recv_or_none() is None)
n1.shutdown()
n2.shutdown()
n3.shutdown()
