import pyre
import json
import uuid

from desmond.network import ipaddr

def start_publisher():
    ip = ipaddr.get_local_ip_addr()
    port = 12345

def main():
    node = pyre.Pyre()
    node.set_header("d-vision-service", "tcp//127.0.0.1:9829")
    node.start()
    while True:
        try:
            cmds = node.recv()
            msg_type = cmds.pop(0)
            uuid_t = uuid.UUID(bytes=cmds.pop(0))
            name = cmds.pop(0)
            print("NODE_MSG TYPE: %s" % msg_type)
            print("NODE_MSG PEER: %s" % uuid_t)
            print("NODE_MSG NAME: %s" % name)
            if msg_type.decode('utf-8') == "SHOUT":
                print("NODE_MSG GROUP: %s" % cmds.pop(0))
            elif msg_type.decode('utf-8') == "ENTER":
                headers = json.loads(cmds.pop(0).decode('utf-8'))
                print("NODE_MSG HEADERS: %s" % headers)
                for key in headers:
                    print("key = {0}, value = {1}".format(key, headers[key]))

        except KeyboardInterrupt:
            print("interrupted")
            break
    node.stop()

if __name__ == '__main__':
    main()
