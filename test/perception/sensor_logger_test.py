import os

from desmond.perception import SensorLogger
from desmond.perception import SensorSpec
from desmond.perception.sensor_data_pb2 import SensorDatum
from desmond.types import Text

TEST_DATABASE = "/tmp/desmond_test/sensorlogs.db"
def clear_test_db():
    if os.path.exists(TEST_DATABASE):
        os.remove(TEST_DATABASE)

def test_create_table():
    clear_test_db()
    logger = SensorLogger(db_name=TEST_DATABASE)
    assert os.path.exists(TEST_DATABASE)

def test_write_datum():
    datum = SensorDatum()
    datum.time_usec = 1000
    text = Text()
    text.value = "Hello World"
    datum.payload.Pack(text)
    spec = SensorSpec(address="tcp://127.0.0.1", name="Foo")
    clear_test_db()
    logger = SensorLogger(db_name=TEST_DATABASE)
    logger.write_datum(datum, spec)

