""" Discovers sensors on the network and tracks their data. """
import json
import pyre
import threading
import uuid
import zmq

from desmond.network import message


class PerceptionService(object):
    def __init__(self):
        self._shutdown = False
        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()

    def run(self):
        self.node = pyre.Pyre()
        self.node.start()
        context = zmq.Context.instance()
        sock = context.socket(zmq.SUB)
        sock.setsockopt_string(zmq.SUBSCRIBE, "")
        poller = zmq.Poller()
        poller.register(self.node.socket(), zmq.POLLIN)
        poller.register(sock, zmq.POLLIN)
        while not self._shutdown:
            try:
                items = dict(poller.poll(500))
            except KeyboardInterrupt:
                self.shutdown()
                return

            if sock in items:
                print(sock.recv())
            elif self.node.socket() in items:
                msg = message.PyreMessage(self.node.recv())
                if msg.msg_type == message.PyreMessage.ENTER:
                    sock.connect(msg.headers['dmd-sensor-addr'])
                print(msg)

        self.node.stop()

    def shutdown(self):
        self._shutdown = True

if __name__ == "__main__":
    service = PerceptionService()
    input("Exit? ")
    service.shutdown()
