import discord, asyncio
import src.config as config
from src.classMember import Members
from threading import Thread
from src.connectDB import Database


async def checkRequests():
    while True:
        #check requests for over time
        print("CHECK")
        await asyncio.sleep(5)



class UsahiChan:

    def __init__(self):
        intents = discord.Intents.all()
        self.client = discord.Client(intents=intents)
        self.LOGGER = config.getLogger()
        self.members = Members(config.guildId)
        self.db = Database()

    def checkConnection(self):
        @self.client.event
        async def on_ready():
            self.LOGGER.info('Successfully connected')

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

Thread(target=usagi.run).start()
asyncio.run(checkRequests())
