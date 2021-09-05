
import configparser, os

config = configparser.ConfigParser()

for filename in os.listdir('./test_config'):
    if filename.endswith('.ini'):
        config.read(f'./test_config/{filename}', encoding = 'UTF8')


if '803362317978304512' in config['roles'].values():
    print('asdasd')
