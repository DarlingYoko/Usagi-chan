import psycopg2, datetime, sys
from src.functions import printError

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
            printError()


    def insert(self, tableName, *values):
        try:
            self.cur.execute("INSERT INTO {0} VALUES {1};".format(tableName, values))
            self.con.commit()
            return 1
        except Exception as e:
            printError()
            return 0

    def getValue(self, tableName, argument, selector, value):
        try:
            self.cur.execute("SELECT {1} from {0} where {2} = \'{3}\';".format(tableName, argument, selector, value))
            self.con.commit()
            return self.cur.fetchall()[0][0]

        except IndexError:
            return 0
        except Exception as e:
            printError()
            return 0

    def update(self, tableName, argument, selector, newValue, findValue):
        try:
            self.cur.execute("UPDATE {0} set {1} = \'{3}\' where {2} = \'{4}\';".format(tableName, argument, selector, newValue, findValue))
            self.con.commit()
            return 1
        except Exception as e:
            printError()
            return 0

    def remove(self, tableName, selector, value):
        try:
            self.cur.execute("DELETE from {0} where {1} = \'{2}\';".format(tableName, selector, value))
            self.con.commit()
            return 1
        except Exception as e:
            printError()
            return 0

    def getAll(self, tableName):
        try:
            self.cur.execute("SELECT * from {0};".format(tableName))
            self.con.commit()
            return self.cur.fetchall()
        except Exception as e:
            printError()
            return 0

    def command(self, command):
        try:
            self.cur.execute(command)
            self.con.commit()
            return self.cur.fetchall()
        except Exception as e:
            printError()
            return 0
