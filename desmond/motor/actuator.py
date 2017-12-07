import logging
import pyre
from pyre import zhelper
import uuid
import zmq

from google.protobuf.descriptor_pb2 import DescriptorProto
from google.protobuf import type_pb2
from desmond.network import ipaddr
from desmond import network


# Do we need this??
class ActuatorSpec(object):
    def __init__(self, name, address):
        self.name = name
        self.address = address

    def __str__(self):
        return "{0}@{1}".format(self.name, self.address)

    @staticmethod
    def from_headers(headers):
        return ActuatorSpec(address=headers[Receiver.HEADER_ACTUATOR_ADDR],
                            name=headers[Receiver.HEADER_ACTUATOR_NAME])


class RemoteActuator(object):
    """ Used to send command to remote actuator. """
    MSG_REQUEST_PROTOCOL = b'GPB'
    def __init__(self, spec):
        self.name = spec.name
        self.address = spec.address
        context = zmq.Context.instance()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect(spec.address)
        self.socket.send(RemoteActuator.MSG_REQUEST_PROTOCOL)
        descriptor_bytes = self.socket.recv()
        self.command_def = network.TypeDefinition()
        self.command_def.ParseFromString(descriptor_bytes)
        logging.info("RemoteActuator command def: %s", self.command_def)

    def send(self, command):
        """ Sends data either as proto or json. """
        self.socket.send(command)
        return self.socket.recv()

    def __str__(self):
        return "{0}@{1}#{2}".format(self.name, self.address,
                                    self.command_def.type_name)


class Command(object):
    def __init__(self, sender, payload):
        self.sender = sender
        self.payload = payload


def _get_type_recursive(descriptor, definitions):
    if descriptor.full_name in definitions:
        return
    type_ = type_pb2.Type()
    definitions[descriptor.full_name] = type_
    type_.name = descriptor.full_name
    for field_desc in descriptor.fields:
        field = type_.fields.add()
        field.name = field_desc.name
        field.kind = field_desc.type
        if field_desc.message_type is not None:
            field.type_url = "type.google_apis.com/"+field_desc.message_type.full_name
            _get_type_recursive(field_desc.message_type, definitions)


def _get_type_def(ProtoType):
    type_def = network.TypeDefinition()
    type_def.type_name = ProtoType.DESCRIPTOR.full_name
    definitions = {}
    _get_type_recursive(ProtoType.DESCRIPTOR, definitions)
    for d in definitions.values():
        type_def.types.add().CopyFrom(d)
    return type_def


class Receiver(object):
    """ Actuator implementations should include a receiver to make it
        discoverable in the Desmond network and advertise its command
        protocol.
    """
    HEADER_ACTUATOR_NAME = "dmd-act-name"
    HEADER_ACTUATOR_ADDR = "dmd-act-addr"
    HEADER_ACTUATOR_CMD = "dmd-act-cmd"
    _INTERNAL_STOP = b"$$STOP"
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
        self.command_pipe = zhelper.zthread_fork(context, self.run, transport=transport)

    def run(self, context, pipe, transport="tcp"):
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
        self.node.start()
        logging.info("Started Receiver Pyre node.")

        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)
        poller.register(pipe, zmq.POLLIN)
        while True:
            items = dict(poller.poll(500))
            if pipe in items and items[pipe] == zmq.POLLIN:
                frames = pipe.recv_multipart()
                logging.debug("PIPE command: %s", frames)
                if len(frames) == 1 and frames[0] == Receiver._INTERNAL_STOP:
                    logging.info("Stopping receiver")
                    break
                self.socket.send_multipart(frames)
            elif self.socket in items:
                frames = self.socket.recv_multipart()
                if len(frames) != 3 or frames[1] != b'':
                    logging.error("Invalid multipart message")
                    continue
                if frames[2] == RemoteActuator.MSG_REQUEST_PROTOCOL:
                    # Send this receiver's command protocol.
                    type_def = _get_type_def(self.CommandProto)
                    self.socket.send_multipart([frames[0], b'',
                                                type_def.SerializeToString()])
                else:
                    logging.debug("Forwarding command to command_pipe")
                    pipe.send_multipart(frames)

        pipe.close()
        self.socket.close()
        self.node.stop()
        logging.info("Exiting Receiver loop")

    def recv_cmd(self):
        """ Returns an instance of CommandProto received from Desmond mesh. """
        while True:
            try:
                identity, _, data = self.command_pipe.recv_multipart()
                break
            except zmq.error.Again:
                pass

        # TODO(kjchavez): Parse as CommandProto. Note, we might receive it in JSON format
        # if its a non-standard proto.
        command_proto = self.CommandProto()
        try:
            parsed = command_proto.ParseFromString(data)
        except:
            parsed = False

        return Command(identity, command_proto if parsed else data)

    def send_ok(self, identity):
        self.command_pipe.send_multipart([identity, b'', b'OK'])

    def send_error(self, identity, error):
        self.command_pipe.send_multipart([identity, b'', error])

    def shutdown(self):
        self.command_pipe.send(Receiver._INTERNAL_STOP)
        self.command_pipe.close()

    def __del__(self):
        try:
            self.shutdown()
        except:
            pass
