import logging.config

logChannel = 733631069542416387
messageChannel = 734004322177646614
serverID = 733631069542416384
token = 'ODAxMTUzMTk3NTUyMzA0MTI5.YAciDw.Gm9x7NeXHvUrJvLfJ-tmlbD9URs'
thumbnail = 'https://cdn.discordapp.com/attachments/801159693404864543/801271549507403826/XUKpfEBhHoc.jpg'

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
