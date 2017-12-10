import logging
import uuid
import zmq
import pyre
from google.protobuf import empty_pb2

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
    """Core processing node in Desmond network.

    A single node aggregates any number of inputs from the network and
    publishes a single output type. A DesmondNode registers on datatypes
    that it wishes to process, not specific sources of that datatype.

    Example:

        node = DesmondNode("MyNode", [types.Foo, types.Bar], types.Baz)

    Such a node will receive all Foos and Bars that are published on the
    Desmond network and may publish Baz to the network.

    Nit. Prefer to use CamelCase node names to mirror class naming convention
    in this project.
    """

    # Headers that are broadcast by this node for others to discover.
    # Example: "Echo"
    HEADER_OUTPUT_NAME = "dmd-name"
    # Example: "desmond.types.Text"
    HEADER_OUTPUT_TYPE = "dmd-type"
    # Example: "tcp://192.68.1.14:5555"
    HEADER_OUTPUT_ADDR = "dmd-addr"

    # Messages send via an inproc pipe from application code to DesmondNode main loop.
    MSG_SHUTDOWN = b"_$STOP"
    MSG_EMIT = b"_$EMIT"
    def __init__(self, name, inputs, OutputType, transport="tcp"):
        for i in inputs:
            if not hasattr(i, 'ParseFromString'):
                raise ValueError("All input types must implement 'ParseFromString' (e.g. protocol"
                                 " buffer)")
        if OutputType is None:
            OutputType = empty_pb2.Empty

        if not hasattr(OutputType, "SerializeToString"):
            raise ValueError("OutputType must implement 'SerializeToString' (e.g. protocol buffer)")

        self.name = name
        self.inputs = inputs
        self.inputs_by_name = {bytes(i.DESCRIPTOR.full_name, 'latin1'): i for i in inputs}
        self.OutputType = OutputType

        # List of InputSpecs that are being used by this DesmondNode
        # TODO(kjchavez): Make this thread safe! Important when many nodes are joining/leaving the
        # network frequently.
        self._sources = []

        context = zmq.Context.instance()
        self.pipe = zhelper.zthread_fork(context, self.run, transport=transport)

    @property
    def sources(self):
        return self._sources

    def run(self, context, pipe, transport="tcp"):
        """Maintains pyre node and other zmq sockets used to receive inputs and publish output.

        This should be called via zhelper.zthread_fork where the application code owns the other end
        of the |pipe|.
        """
        publisher = context.socket(zmq.PUB)
        if transport == "tcp":
            port_selected = publisher.bind_to_random_port('tcp://*', min_port=8001, max_port=9999,
                                                          max_tries=100)

            self.address = "tcp://%s:%d" % (ipaddr.get_local_ip_addr(), port_selected)
        elif transport == "inproc":
            self.address = "inproc://%s" % (str(uuid.uuid4()),)
            publisher.bind(self.address)

        logging.info("Starting DesmondNode: %s", self.name)
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
                    logging.warning("Received empty message from pipe")
                    break
                if msg[0] == DesmondNode.MSG_SHUTDOWN:
                    logging.info("Shutting down node")
                    break
                elif msg[0] == DesmondNode.MSG_EMIT:
                    logging.debug("Emitting data.")
                    publisher.send(msg[1])
                else:
                    logging.info("Unknown internal command ignored")

            elif node.socket() in items:
                pm = message.PyreMessage(node.recv())
                logging.debug("Received message from Pyre node")
                if pm.msg_type == message.PyreMessage.ENTER:
                    logging.info("New node discovered.")
                    input_manager.add_input(pm.headers, context, poller)
                    self._sources = input_manager.inputs.values()

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
        """Terminates the discovery/handling loop of the node."""
        self.pipe.send_multipart([DesmondNode.MSG_SHUTDOWN])

    def publish(self, data):
        """Emits instance of self.OutputType to Desmond network.

        Arguments:
            data: instance of self.OutputType.
        """

        if not isinstance(data, self.OutputType):
            raise ValueError("data must be of type %s" % self.OutputType)
        self.pipe.send_multipart([DesmondNode.MSG_EMIT, data.SerializeToString()])

    def recv(self):
        """Return input of one of the registered input types.

        Returns:
            instance of one of the self.input datatypes

        Raises:
            zmq.error.Again if no data is available
        """
        while True:
            dtype, addr, payload = self.pipe.recv_multipart()
            proto = self.inputs_by_name[dtype]()
            if proto.ParseFromString(payload):
                return proto
            # Otherwise things are broken...
            logging.warning("Invalid payload received for dtype: %s", dtype)

    def recv_or_none(self):
        """Similar to DesmondNode.recv, except returns None rather than raising zmq.error.Again

        Returns:
            instance of one of self.input dtypes or None
        """
        try:
            return self.recv()
        except zmq.error.Again:
            return None
