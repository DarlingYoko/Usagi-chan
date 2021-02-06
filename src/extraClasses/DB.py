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


    def insert(self, userId, messageId, time = None, user = None):
        try:
            if time:
                self.cur.execute("INSERT INTO emojiData (userId, messageIDs, createTime, author) VALUES (\'{0}\', \'{1}\', \'{2}\', \'{3}\');".format(userId, messageId, time, user))
            else:
                self.cur.execute("INSERT INTO requestsData (userId, messageIDs) VALUES (\'{0}\', \'{1}\');".format(userId, messageId))
            self.con.commit()
            return 1
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            newLog(exc_type, exc_obj, exc_tb, e)
            return 0

    def get(self, userId, table):
        try:
            self.cur.execute("SELECT messageIDs from {0} where userId = \'{1}\';".format(table, userId))
            return self.cur.fetchall()[0][0]
        except Exception as e:
            return 0

    def update(self, userId, messageId, table):
        try:
            self.cur.execute("UPDATE {0} set messageIDs = \'{1}\' where userId = \'{2}\';".format(table, messageId, userId))
            self.con.commit()
            return 1
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            newLog(exc_type, exc_obj, exc_tb, e)
            return 0

    def remove(self, userId, table):
        try:
            self.cur.execute("DELETE from {0} where userId = \'{1}\';".format(table, userId))
            self.con.commit()
            return 1
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            newLog(exc_type, exc_obj, exc_tb, e)
            return 0

    def getTime(self):
        try:
            self.cur.execute("SELECT userId, createTime, author from emojiData;")
            return self.cur.fetchall()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            newLog(exc_type, exc_obj, exc_tb, e)
            return 0
