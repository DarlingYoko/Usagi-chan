import psycopg2

class Database():
    def __init__(self):
        try:
            self.con = psycopg2.connect(
                                      database="vzztcyjq",
                                      user="vzztcyjq",
                                      password="aMY1iBAoG9SBz6Vxmyl11Dxd2fT5AlTJ",
                                      host="ziggy.db.elephantsql.com",
                                      port="5432"
                                      )

            print('Successfully connected to database')
            self.cur = self.con.cursor()

        except Exception as e:
            print('Fail to connect to database')

#  user TABLE

    def insert(self, userId, messageId):
        try:
            self.cur.execute("INSERT INTO requestsData (userId, messageIDs) VALUES (\'{0}\', \'{1}\');".format(userId, messageId))
            self.con.commit()
            return 1
        except:
            return 0

    def get(self, userId):
        try:
            self.cur.execute("SELECT messageIDs from requestsData where userId = \'{0}\';".format(userId))
            return self.cur.fetchall()[0][0]
        except:
            return 0

    def update(self, userId, messageId):
        try:
            self.cur.execute("UPDATE requestsData set messageIDs = \'{0}\' where userId = \'{1}\';".format(messageId, userId))
            self.con.commit()
            return 1
        except:
            return 0

    def remove(self, userId):
        try:
            self.cur.execute("DELETE from requestsData where userId = \'{0}\';".format(userId))
            self.con.commit()
            return 1
        except:
            return 0

# emoji TABLE

    def insertEmoji(self, userId, messageId, time):
        try:
            self.cur.execute("INSERT INTO emojiData (userId, messageIDs, createTime) VALUES (\'{0}\', \'{1}\', \'{2}\');".format(userId, messageId, time))
            self.con.commit()
            return 1
        except:
            return 0

    def getEmoji(self, userId):
        try:
            self.cur.execute("SELECT messageIDs from emojiData where userId = \'{0}\';".format(userId))
            return self.cur.fetchall()[0][0]
        except:
            return 0

    def getTime(self, userId):
        try:
            self.cur.execute("SELECT createTime from emojiData where userId = \'{0}\';".format(userId))
            return self.cur.fetchall()[0][0]
        except:
            return 0

    def updateEmoji(self, userId, messageId):
        try:
            self.cur.execute("UPDATE emojiData set messageIDs = \'{0}\' where userId = \'{1}\';".format(messageId, userId))
            self.con.commit()
            return 1
        except:
            return 0

    def removeEmoji(self, userId):
        try:
            self.cur.execute("DELETE from emojiData where userId = \'{0}\';".format(userId))
            self.con.commit()
            return 1
        except:
            return 0
