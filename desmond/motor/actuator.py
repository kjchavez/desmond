import logging
import pyre
import uuid
import zmq

from desmond.network import ipaddr

class ActuatorSpec(object):
    def __init__(self, name, address, command_proto):
        self.name = name
        self.address = address
        self.command_proto = command_proto

    def __str__(self):
        return "{0}@{1}".format(self.name, self.address)

    @staticmethod
    def from_headers(headers):
        return ActuatorSpec(address=headers[Receiver.HEADER_ACTUATOR_ADDR],
                            name=headers[Receiver.HEADER_ACTUATOR_ADDR],
                            command_proto=headers[Receiver.HEADER_ACTUATOR_CMD])

class RemoteActuator(object):
    """ Used to send command to remote actuator. """
    def __init__(self, spec):
        context = zmq.Context.instance()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(spec.address)

    def send(self, command):
        """ Sends data either as proto or json. """
        self.socket.send(command)
        return self.socket.recv()


class Command(object):
    def __init__(self, sender, payload):
        self.sender = sender
        self.payload = payload

class Receiver(object):
    """ Actuator implementations should include a receiver to make it
        discoverable in the Desmond network and advertise its command
        protocol.
    """
    HEADER_ACTUATOR_NAME = "dmd-act-name"
    HEADER_ACTUATOR_ADDR = "dmd-act-addr"
    HEADER_ACTUATOR_CMD = "dmd-act-cmd"
    def __init__(self, name, CommandProto, transport="tcp"):
        """
        Args:
            name: human-readable name for the actuator
            CommandProto: class of the the command protocol buffer
                          expected by this actuator.
        """


        if transport not in ("inproc", "tcp"):
            raise ValueError("transport must be one of {inproc, tcp}")

        self.name = name
        self.CommandProto = CommandProto
        context = zmq.Context.instance()
        self.socket = context.socket(zmq.ROUTER)
        if transport == "tcp":
            port_selected = self.socket.bind_to_random_port('tcp://*', min_port=8001, max_port=9000,
                                                            max_tries=100)

            self.address = "tcp://%s:%d" % (ipaddr.get_local_ip_addr(), port_selected)
        elif self.transport == "inproc":
            self.address = "inproc://%s" % (str(uuid.uuid4()),)
            self.socket.bind(self.address)

        self.node = pyre.Pyre()
        self.node.set_header(Receiver.HEADER_ACTUATOR_NAME, self.name)
        self.node.set_header(Receiver.HEADER_ACTUATOR_ADDR, self.address)
        self.node.set_header(Receiver.HEADER_ACTUATOR_CMD, self.CommandProto.DESCRIPTOR.full_name)
        self.node.start()

    def recv(self):
        """ Returns an instance of CommandProto received from Desmond mesh. """

        identity = self.socket.recv()
        assert self.socket.recv() == b''
        data = self.socket.recv()
        # TODO(kjchavez): Parse as CommandProto. Note, we might receive it in JSON format
        # if its a non-standard proto.
        return Command(identity, data)

    def send_ok(self, identity):
        self.socket.send_multipart([identity, b'', b'OK'])

    def send_error(self, identity, error):
        self.socket.send_multipart([identity, b'', error])

    def __del__(self):
        self.socket.close()
        self.node.stop()
