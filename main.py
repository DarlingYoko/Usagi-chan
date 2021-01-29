import discord, asyncio, time, shelve, datetime
import src.config as config
from src.classMember import Members
from threading import Thread
from src.connectDB import Database
from src.guildCommands.autoRemoveRequest import autoRemoveRequest
from src.functions import newLog

async def checkRequests():
    while True:
        time.sleep(10)
        asyncio.run_coroutine_threadsafe(autoRemoveRequest(usagi.db, usagi.client), usagi.loop)

class UsahiChan:

    def __init__(self):
        intents = discord.Intents.all()
        self.client = discord.Client(intents=intents)
        self.LOGGER = config.getLogger()
        self.members = Members(config.guildId)
        self.db = Database()
        self.loop = None

    def checkConnection(self):
        @self.client.event
        async def on_ready():

            self.LOGGER.info('Successfully connected to discord')
            newLog('Successfully connected to discord at {0}'.format(datetime.datetime.now()))
            self.loop = asyncio.get_event_loop()

    def run(self):
        self.client.run(config.token)


    from events.newMessageEvent import setMessageEvent
    from events.voiceStateUpdateEvent import setVoiceStateUpdateEvent
    from events.newReactionEvent import setNewReactionEvent
    from events.removeReactionEvent import setRemoveReactionEvent



usagi = UsahiChan()
usagi.checkConnection()
usagi.setMessageEvent()
usagi.setVoiceStateUpdateEvent()
usagi.setNewReactionEvent()
usagi.setRemoveReactionEvent()



Thread(target=asyncio.run, args=(checkRequests(), )).start()
usagi.run()
