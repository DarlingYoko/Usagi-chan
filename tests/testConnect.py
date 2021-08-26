from datetime import datetime
from time import mktime
import configparser
import psycopg2, datetime, sys


config = configparser.ConfigParser()
config.read('{0}.ini'.format('src/config'), encoding = 'UTF8')

con = psycopg2.connect(
                            database = config['configDB']['database'],
                            user = config['configDB']['user'],
                            password = config['configDB']['password'],
                            host = config['configDB']['host'],
                            port = config['configDB']['port']
                            )

cur = con.cursor()

#cur.execute('''DROP TABLE emojidata;''')
cur.execute('''CREATE TABLE tokens
     (id SERIAL,
     token TEXT,
     trend TEXT,
     price TEXT,
     name TEXT);''')
print("Table created successfully")

#print(cur.execute('''SELECT userId, data, users from SHEDULE;'''))
con.commit()
