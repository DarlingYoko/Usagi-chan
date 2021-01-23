import logging.config

logChannel = 733631069542416387
messageChannel = 734004322177646614
serverID = 733631069542416384
token = 'ODAxMTUzMTk3NTUyMzA0MTI5.YAciDw.Gm9x7NeXHvUrJvLfJ-tmlbD9URs'
thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/801926601481912320/cbf89215894687f9f0e81aa7d125dba1_cupid-bow-arrow-hearts-cupid-heart-with-arrow-png-transparent-_860-.png'
yokoId = 290166276796448768
privateCommands = {
    'valentineCommandAnon': '!валентинка',
    'valentineCommandDeAnon': '!девалентинка',
    'simpleMesageCommand': '!m',
    'deleteValentine': '!удалить'}

def getLogger():
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(name)s] %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "level": "INFO",
            "handlers": [
                "console"
            ]
        }
    })

    return logging.getLogger()
