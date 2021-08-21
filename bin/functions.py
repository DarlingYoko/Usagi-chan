import configparser, os, sys
from datetime import datetime



def get_config():
    config = configparser.ConfigParser()

    for filename in os.listdir('./config'):
        if filename.endswith('.ini'):
            config.read(f'./config/{filename}', encoding = 'UTF8')
    return config


def print_error():
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print('New error:\ntype - {0}, line - {1}, error - {2}, file - {3}\n'.format(exc_type, exc_tb.tb_lineno, exc_obj, fname))
