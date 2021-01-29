import psycopg2, datetime
from src.functions import newLog

class Database():
    def __init__(self):
        try:
            self.con = psycopg2.connect(
                                            database="yoko_bot_test",
                                            user="yoko_bot",
                                            password="yoko_password",
                                            host="62.109.11.88",
                                            port="5432"
                                            )

            newLog('Successfully connected to database at {0}'.format(datetime.datetime.now()), new = 1)
            self.cur = self.con.cursor()

        except Exception as e:
            newLog('Fail to connect to database at {0}'.format(datetime.datetime.now()), new = 1)


    def insert(self, userId, messageId, time = None, user = None):
        try:
            if time:
                self.cur.execute("INSERT INTO emojiData (userId, messageIDs, createTime, author) VALUES (\'{0}\', \'{1}\', \'{2}\', \'{3}\');".format(userId, messageId, time, user))
            else:
                self.cur.execute("INSERT INTO requestsData (userId, messageIDs) VALUES (\'{0}\', \'{1}\');".format(userId, messageId))
            self.con.commit()
            return 1
        except Exception as e:
            newLog('New error in insert db at {1}:\n{0}'.format(e, datetime.datetime.now()))
            return 0

    def get(self, userId, table):
        try:
            self.cur.execute("SELECT messageIDs from {0} where userId = \'{1}\';".format(table, userId))
            return self.cur.fetchall()[0][0]
        except Exception as e:
            newLog('New error in get db at {1}:\n{0}'.format(e, datetime.datetime.now()))
            return 0

    def update(self, userId, messageId, table):
        try:
            self.cur.execute("UPDATE {0} set messageIDs = \'{1}\' where userId = \'{2}\';".format(table, messageId, userId))
            self.con.commit()
            return 1
        except Exception as e:
            newLog('New error in update db at {1}:\n{0}'.format(e, datetime.datetime.now()))
            return 0

    def remove(self, userId, table):
        try:
            self.cur.execute("DELETE from {0} where userId = \'{1}\';".format(table, userId))
            self.con.commit()
            return 1
        except Exception as e:
            newLog('New error in remove db at {1}:\n{0}'.format(e, datetime.datetime.now()))
            return 0

    def getTime(self):
        try:
            self.cur.execute("SELECT userId, createTime, author from emojiData;")
            return self.cur.fetchall()
        except Exception as e:
            newLog('New error in get time db at {1}:\n{0}'.format(e, datetime.datetime.now()))
            return 0
