# Detects DesmondNodes on the network and displays their headers.
import pyre
import logging
import time
import json
import argparse
from desmond.thought import DesmondNode

parser = argparse.ArgumentParser()
parser.add_argument("--dtype", default=None)
args = parser.parse_args()

node = pyre.Pyre()
node.start()

time.sleep(1.1)
for event in node.recent_events():
    if event.type == 'ENTER':
        if DesmondNode.HEADER_OUTPUT_NAME in event.headers:
            print(json.dumps(event.headers, indent=2, sort_keys=True))

node.stop()

class DebugDescriptor(object):
    def __init__(self, full_name):
        self.full_name = full_name

class DebugType(object):
    DESCRIPTOR = DebugDescriptor(args.dtype)
    def __init__(self):
        self.s = ""

    def ParseFromString(self, s):
        self.s = str(s, 'latin1')

    def __str__(self):
        return self.s

if args.dtype:
    node = DesmondNode("Sniffer", [DebugType], None)
    n = 0
    start = time.time()
    while True:
        node.recv()
        n += 1
        cur = time.time()
        print("Received total %d messages. Avg rate: %0.2f msg/sec" % (n, float(n)/(cur -
            start)))
