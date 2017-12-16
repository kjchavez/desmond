# Detects DesmondNodes on the network and displays their headers.
import pyre
import time
import json
from desmond.thought import DesmondNode

node = pyre.Pyre()
node.start()


time.sleep(1.1)
for event in node.recent_events():
    if event.type == 'ENTER':
        if DesmondNode.HEADER_OUTPUT_NAME in event.headers:
            print(json.dumps(event.headers, indent=2, sort_keys=True))

node.stop()
