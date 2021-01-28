import psycopg2

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

            print('Successfully connected to database')
            self.cur = self.con.cursor()

        except Exception as e:
            print('Fail to connect to database')


    def insert(self, userId, messageId, table):
        try:
            self.cur.execute("INSERT INTO {0} (userId, messageIDs) VALUES (\'{1}\', \'{2}\');".format(table, userId, messageId))
            self.con.commit()
            return 1
        except:
            return 0

    def get(self, userId, table):
        try:
            self.cur.execute("SELECT messageIDs from {0} where userId = \'{1}\';".format(table, userId))
            return self.cur.fetchall()[0][0]
        except:
            return 0

    def update(self, userId, messageId, table):
        self.cur.execute("UPDATE {0} set messageIDs = \'{1}\' where userId = \'{2}\';".format(table, messageId, userId))
        self.con.commit()
        try:

            return 1
        except:
            return 0

    def remove(self, userId, table):
        try:
            self.cur.execute("DELETE from {0} where userId = \'{1}\';".format(table, userId))
            self.con.commit()
            return 1
        except:
            return 0
