import discord, asyncio, time, shelve, datetime, sys
from src.extraClasses.classMember import Members
from threading import Thread
from src.extraClasses.DB import Database
from src.guildCommands.autoRemoveRequest import autoRemoveRequest
from src.functions import newLog, loadConfig, getLogger

async def checkRequests():
    while True:
        time.sleep(10)
        asyncio.run_coroutine_threadsafe(autoRemoveRequest(usagi), usagi.loop)

class UsahiChan:

    def __init__(self):
        self.config = loadConfig('src/config')
        intents = discord.Intents.all()
        self.client = discord.Client(intents=intents)
        self.LOGGER = getLogger()
        self.members = Members(self.config['data']['guildId'])
        self.db = Database(self)
        self.loop = None
        self.vc = None


    def checkConnection(self):
        @self.client.event
        async def on_ready():

            self.LOGGER.info('Successfully connected to discord')
            await self.client.change_presence(status=discord.Status.online, activity=discord.Game("ver 1.0.0.0.4 | Учится работать |"))
            self.loop = asyncio.get_event_loop()
            await self.members.fillMembers(self.client)

    def run(self):
        self.client.run(self.config['data']['token'])


    from events.newMessageEvent import setMessageEvent
    from events.voiceStateUpdateEvent import setVoiceStateUpdateEvent
    from events.newReactionEvent import setNewReactionEvent
    from events.removeReactionEvent import setRemoveReactionEvent
    from events.usersChangedEvents import setUsersChangedEvents



usagi = UsahiChan()
usagi.checkConnection()
usagi.setMessageEvent()
usagi.setVoiceStateUpdateEvent()
usagi.setNewReactionEvent()
usagi.setRemoveReactionEvent()
usagi.setUsersChangedEvents()



newLog('', '', '', '', new = 1)
Thread(target=asyncio.run, args=(checkRequests(), )).start()
usagi.run()
