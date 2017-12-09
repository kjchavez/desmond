import logging
import uuid
import zmq
import pyre

from pyre import zhelper
from desmond.network import ipaddr, message

class InputSpec(object):
    def __init__(self, name, addr, dtype):
        self.name = name
        self.addr = bytes(addr, 'latin1')
        self.dtype = bytes(dtype, 'latin1')

class InputManager(object):
    def __init__(self, accepted_types):
        self.accepted_types = []
        for t in accepted_types:
            if isinstance(t, str):
                self.accepted_types.append(t)
            else:
                self.accepted_types.append(t.DESCRIPTOR.full_name)

        # Map of sockets to input specs
        self.inputs = {}

    def add_input(self, headers, ctx, poller):
        """ Creates a new SUB socket for the input described in headers."""
        if DesmondNode.HEADER_OUTPUT_TYPE not in headers or \
           DesmondNode.HEADER_OUTPUT_ADDR not in headers:
            logging.debug("Pyre node is not DesmondNode")
            return False
        name = headers.get(DesmondNode.HEADER_OUTPUT_NAME, "<unknown>")
        addr = headers.get(DesmondNode.HEADER_OUTPUT_ADDR)
        dtype = headers.get(DesmondNode.HEADER_OUTPUT_TYPE)
        if dtype not in self.accepted_types:
            logging.debug("Node %s does not emit desired type", name)
            return False

        sock = ctx.socket(zmq.SUB)
        sock.setsockopt(zmq.SUBSCRIBE, b"")
        sock.connect(addr)
        # TODO(kjchavez): Think about appropriate high water marks.
        poller.register(sock, zmq.POLLIN)
        self.inputs[sock] = InputSpec(name, addr, dtype)
        logging.info("Added node %s to set of inputs", name)
        return True


class DesmondNode(object):
    HEADER_OUTPUT_NAME = "dmd-name"
    HEADER_OUTPUT_TYPE = "dmd-type"
    HEADER_OUTPUT_ADDR = "dmd-addr"
    MSG_SHUTDOWN = b"_$STOP"
    MSG_EMIT = b"_$EMIT"
    def __init__(self, name, inputs, OutputType, transport="tcp"):
        self.name = name
        # These should be actual types.
        self.inputs = inputs
        self.inputs_by_name = {bytes(i.DESCRIPTOR.full_name, 'latin1'): i for i in inputs}
        self.OutputType = OutputType
        context = zmq.Context.instance()
        self.pipe = zhelper.zthread_fork(context, self.run, transport=transport)

    def run(self, context, pipe, transport="tcp"):
        publisher = context.socket(zmq.PUB)
        if transport == "tcp":
            port_selected = publisher.bind_to_random_port('tcp://*', min_port=8001, max_port=9999,
                                                          max_tries=100)

            self.address = "tcp://%s:%d" % (ipaddr.get_local_ip_addr(), port_selected)
        elif transport == "inproc":
            self.address = "inproc://%s" % (str(uuid.uuid4()),)
            publisher.bind(self.address)

        node = pyre.Pyre()
        node.set_header(DesmondNode.HEADER_OUTPUT_NAME, self.name)
        node.set_header(DesmondNode.HEADER_OUTPUT_ADDR, self.address)
        node.set_header(DesmondNode.HEADER_OUTPUT_TYPE, self.OutputType.DESCRIPTOR.full_name)
        node.start()

        poller = zmq.Poller()
        poller.register(node.socket(), zmq.POLLIN)
        poller.register(pipe, zmq.POLLIN)

        input_manager = InputManager(self.inputs)
        while True:
            items = dict(poller.poll(500))
            if pipe in items and items[pipe] == zmq.POLLIN:
                msg = pipe.recv_multipart()
                if not msg:
                    logging.warning("Invalid command")
                    break
                if msg[0] == DesmondNode.MSG_SHUTDOWN:
                    logging.info("Shutting down node")
                    break
                elif msg[0] == DesmondNode.MSG_EMIT:
                    logging.debug("Emitting data.")
                    publisher.send(msg[1])
                else:
                    logging.debug("Unknown internal command")

            elif node.socket() in items:
                pm = message.PyreMessage(node.recv())
                logging.debug("Received message from Pyre node")
                if pm.msg_type == message.PyreMessage.ENTER:
                    logging.info("New node discovered.")
                    input_manager.add_input(pm.headers, context, poller)

            else:
                for sock in input_manager.inputs:
                    if sock in items:
                        msg = sock.recv()
                        spec = input_manager.inputs[sock]
                        logging.debug("Received input from %s", spec.addr)
                        pipe.send_multipart([spec.dtype, spec.addr, msg])

        pipe.close()
        publisher.close()
        node.stop()
        logging.info("Exiting Receiver loop")

    def shutdown(self):
        self.pipe.send_multipart([DesmondNode.MSG_SHUTDOWN])

    def publish(self, data):
        if not isinstance(data, self.OutputType):
            raise ValueError("data must be of type %s" % self.OutputType)
        self.pipe.send_multipart([DesmondNode.MSG_EMIT, data.SerializeToString()])

    def recv(self):
        """Return input of one of the registered input types."""
        while True:
            dtype, addr, payload = self.pipe.recv_multipart()
            proto = self.inputs_by_name[dtype]()
            if proto.ParseFromString(payload):
                return proto
            # Otherwise things are broken...
            logging.warning("Invalid payload received for dtype: %s", dtype)

