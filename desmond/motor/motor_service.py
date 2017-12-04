import pyre
import logging
import threading

from desmond.network.message import PyreMessage
from desmond.motor.actuator import RemoteActuator, ActuatorSpec

class MotorService(object):
    """Provides simple access to actuators on the Desmond network."""
    def __init__(self):
        self.actuators = []
        t = threading.Thread(target=self.discover)
        t.daemon = True
        t.start()

    def _add_actuator(self, remote):
        self.actuators.append(remote)

    def discover(self):
        node = pyre.Pyre()
        node.start()
        while True:
            msg = PyreMessage(node.recv())
            logging.info(msg)
            if msg.msg_type == PyreMessage.ENTER:
                self._add_actuator(RemoteActuator(ActuatorSpec.from_headers(msg.headers)))
                logging.info("Found new actuator!")

        node.stop()
