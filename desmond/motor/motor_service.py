import pyre
import logging
import threading
import time
import zmq

from desmond.network.message import PyreMessage
from desmond.motor.actuator import RemoteActuator, ActuatorSpec

class MotorService(object):
    """Provides simple access to actuators on the Desmond network."""
    def __init__(self):
        self.actuators = []
        self.stop_requested = False  # should use zmq pipe?
        t = threading.Thread(target=self.discover)
        t.daemon = True
        t.start()
        # Give the service a little time to discover nodes with live
        # heartbeats.
        time.sleep(0.5)

    def _add_actuator(self, remote):
        self.actuators.append(remote)

    def discover(self):
        node = pyre.Pyre()
        node.start()
        poller = zmq.Poller()
        poller.register(node.socket(), zmq.POLLIN)
        while not self.stop_requested:
            items = dict(poller.poll(500))
            if node.socket() not in items:
                continue
            msg = PyreMessage(node.recv())
            logging.info(msg)
            if msg.msg_type == PyreMessage.ENTER:
                spec = ActuatorSpec.from_headers(msg.headers)
                if spec:
                    self._add_actuator(RemoteActuator(spec))
                    logging.info("Found new actuator!")

        node.stop()

    def get(self, name):
        actuators = [a for a in self.actuators if a.name == name]
        if not actuators:
            return None

        return actuators[0]

    def actuate(self, name, payload):
        actuators = [a for a in self.actuators if a.name == name]
        results = [a.send(payload.SerializeToString()) for a in actuators]
        return results

    def shutdown(self):
        self.stop_requested = True
