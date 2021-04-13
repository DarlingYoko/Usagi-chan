import psycopg2, datetime, sys
from src.functions import newLog

class Database():
    def __init__(self, usagi):
        try:
            self.con = psycopg2.connect(
                                        database = usagi.config['configDB']['database'],
                                        user = usagi.config['configDB']['user'],
                                        password = usagi.config['configDB']['password'],
                                        host = usagi.config['configDB']['host'],
                                        port = usagi.config['configDB']['port']
                                        )

            self.cur = self.con.cursor()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            newLog(exc_type, exc_obj, exc_tb, e)


    def insert(self, tableName, *values):
        try:
            self.cur.execute("INSERT INTO {0} VALUES {1};".format(tableName, values))
            self.con.commit()
            return 1
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            newLog(exc_type, exc_obj, exc_tb, e)
            return 0

    def getValue(self, tableName, argument, selector, value):
        try:
            self.cur.execute("SELECT {1} from {0} where {2} = \'{3}\';".format(tableName, argument, selector, value))
            return self.cur.fetchall()[0][0]
        except Exception as e:
            return 0

    def update(self, tableName, argument, selector, newValue, findValue):
        try:
            self.cur.execute("UPDATE {0} set {1} = \'{3}\' where {2} = \'{4}\';".format(tableName, argument, selector, newValue, findValue))
            self.con.commit()
            return 1
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            newLog(exc_type, exc_obj, exc_tb, e)
            return 0

    def remove(self, tableName, selector, value):
        try:
            self.cur.execute("DELETE from {0} where {1} = \'{2}\';".format(tableName, selector, value))
            self.con.commit()
            return 1
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            newLog(exc_type, exc_obj, exc_tb, e)
            return 0

    def getAll(self, tableName):
        try:
            self.cur.execute("SELECT * from {0};".format(tableName))
            return self.cur.fetchall()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            newLog(exc_type, exc_obj, exc_tb, e)
            return 0
