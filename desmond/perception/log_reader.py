import sqlite3

def micros(seconds):
    return int(seconds*1e6)

class SqliteLogReader(object):
    """ For use with SqliteSensorLogger """
    def __init__(self, dbname):
        self.conn = sqlite3.connect(dbname)
        self.conn.row_factory = sqlite3.Row

    def read(self, start, end, datatype=None):
        args = micros(start), micros(end)
        query = ("select *from sensordata "
                 "where time_usec > ? and time_usec < ?")
        if datatype is not None:
            if '/' not in datatype:
                datatype = "type.googleapis.com/"+datatype
            args += (datatype,)
            query += " and type_url = ?"

        query += " order by time_usec desc"
        cur = self.conn.cursor()
        cur.execute(query, args)
        for elem in cur:
            yield elem

    def __del__(self):
        self.conn.close()
