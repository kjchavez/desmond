import os
import sqlite3

class SensorLogger(object):
    def __init__(self, db_name="sensorlogs.db"):
        dirname = os.path.dirname(db_name)
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname)

        self.conn = sqlite3.connect(db_name)
        self.conn.execute("CREATE TABLE IF NOT EXISTS sensordata"
                          "(time_usec INT, type_url TEXT, payload BLOB, sensor_address TEXT,"
                          "sensor_name TEXT)")

    def write_datum(self, datum, sensor_spec):
        entry = (datum.time_usec, datum.payload.type_url, datum.payload.value,
                 sensor_spec.address, sensor_spec.name)
        self.conn.execute("insert into sensordata values (?, ?, ?, ?, ?)", entry)
        self.conn.commit()

    def write_data(self, sensor_data, sensor_spec):
        entries = [(datum.time_usec, dataum.payload.type_url, datum.payload.value,
                    sensor_spec.address, sensor_spec.name) for datum in sensor_data]
        self.conn.executemany("insert into sensordata values (?, ?, ?, ?, ?)", entries)

    def __del__(self):
        self.conn.close()
