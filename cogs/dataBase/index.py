import discord
import psycopg2, datetime, sys
from discord.ext import commands
from bin.functions import print_error

class Database(commands.Cog):
    def __init__(self, bot):

        self.bot = bot

    def connect(self):
        try:
            con = psycopg2.connect(
                                        database = self.bot.config['configDB']['database'],
                                        user = self.bot.config['configDB']['user'],
                                        password = self.bot.config['configDB']['password'],
                                        host = self.bot.config['configDB']['host'],
                                        port = self.bot.config['configDB']['port']
                                        )

            cur = con.cursor()

        except Exception as e:
            print_error()
            return None, None
        return con, cur

    def disconnect(self, cur):
        cur.close()


    def insert(self, tableName, *values):
        try:
            con, cur = self.connect()
            cur.execute("INSERT INTO {0} VALUES {1};".format(tableName, values))
            con.commit()
            self.disconnect(cur)
            return 1
        except Exception as e:
            print_error()
            return 0

    def get_value(self, tableName, argument, selector, value):
        try:
            con, cur = self.connect()
            cur.execute("SELECT {1} from {0} where {2} = \'{3}\';".format(tableName, argument, selector, value))
            con.commit()
            data = cur.fetchall()[0][0]
            self.disconnect(cur)
            return data

        except IndexError:
            return 0
        except Exception as e:
            print_error()
            return 0

    def update(self, tableName, argument, selector, newValue, findValue):
        try:
            con, cur = self.connect()
            cur.execute("UPDATE {0} set {1} = \'{3}\' where {2} = \'{4}\';".format(tableName, argument, selector, newValue, findValue))
            con.commit()
            message = cur.statusmessage
            self.disconnect(cur)
            if message == 'UPDATE 0':
                return 0
            return 1
        except Exception as e:
            print_error()
            return 0

    def remove(self, tableName, selector, value):
        try:
            con, cur = self.connect()
            cur.execute("DELETE from {0} where {1} = \'{2}\';".format(tableName, selector, value))
            con.commit()
            self.disconnect(cur)
            return 1
        except Exception as e:
            print_error()
            return 0

    def get_all(self, tableName):
        try:
            con, cur = self.connect()
            cur.execute("SELECT * from {0};".format(tableName))
            con.commit()
            data = cur.fetchall()
            self.disconnect(cur)
            return data
        except Exception as e:
            print_error()
            return 0

    def custom_command(self, command):
        try:
            con, cur = self.connect()
            cur.execute(command)
            con.commit()
            data = cur.fetchall()
            self.disconnect(cur)
            return data
        except psycopg2.ProgrammingError:
            return 1
        except Exception as e:
            print_error()
            return 0


def setup(bot):
    bot.add_cog(Database(bot))
