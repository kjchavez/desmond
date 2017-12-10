# Simple reactive node to figure out developer experience.
from desmond import types
from desmond.thought import DesmondNode
import logging

logging.basicConfig(level=logging.INFO)
echo = DesmondNode("Echo", [types.Text], types.Text)
while True:
    text = echo.recv_or_none()
    if text:
        logging.info("Echoing \"%s\"", text.value)
        echo.publish(text)
