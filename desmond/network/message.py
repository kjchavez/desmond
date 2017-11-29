import uuid
import json

class PyreMessage(object):
    ENTER = b'ENTER'

    def __init__(self, cmds):
        self.msg_type = cmds.pop(0)
        self.source_id = uuid.UUID(bytes=cmds.pop(0))
        self.name = cmds.pop(0)
        self.group = None
        self.headers = {}
        if self.msg_type.decode('utf-8') == "SHOUT":
            self.group = cmds.pop(0)
        elif self.msg_type.decode('utf-8') == "ENTER":
            self.headers = json.loads(cmds.pop(0).decode('utf-8'))

    def __str__(self):
        return ("{0}\nsource={1} || {2}\n"
                "group={3}\nheaders={4}").format(self.msg_type, self.source_id, self.name,
                                                 self.group, str(self.headers))
