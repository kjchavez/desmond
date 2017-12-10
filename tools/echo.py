# Simple reactive node to figure out developer experience.
from desmond import types
from desmond.thought import DesmondNode
from desmond.perception import SensorDatum
from desmond.motor import MotorService
import logging

logging.basicConfig(level=logging.INFO)
echo = DesmondNode("Echo", [SensorDatum], types.Text)
motor = MotorService()
while True:
    datum = echo.recv_or_none()
    if not datum:
        continue
    text = types.Text()
    if not datum.payload.Unpack(text):
        continue

    logging.info("Echoing \"%s\"", text.value)
    echo.publish(text)
    motor.actuate("stdout",  text)
