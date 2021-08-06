import discord, asyncio, time, shelve, datetime, sys, os
from threading import Thread
from src.functions import newLog, loadConfig, getLogger
from src.extraClasses.classMember import Members
from src.extraClasses.DB import Database
from src.extraClasses.musicPlayer import MusicPlayer
from src.extraClasses.Token import Token
from bin.guildCommands.autoRemoveRequest import autoRemoveRequest
from bin.guildCommands.forum import forum, checkTransform
from bin.guildCommands.news import postNews
from bin.privatCommands.updateShedule import checkNotification
from bin.commandConfig import commands
from events.usersChangedEvents import reportSpam

async def checkRequests():
    while True:
        time.sleep(10)
        asyncio.run_coroutine_threadsafe(autoRemoveRequest(usagi), usagi.loop)


async def checkShedule():
    while True:
        time.sleep(10)
        asyncio.run_coroutine_threadsafe(checkNotification(usagi), usagi.loop)

def checkAudio():
    time.sleep(10)
    while True:
        time.sleep(1)
        usagi.musicPlayer.checkPlay()

async def checkTokens():
    while True:
        time.sleep(10)
        asyncio.run_coroutine_threadsafe(usagi.token.checkTokens(usagi), usagi.loop)

def restartDriver():
    while True:
        time.sleep(10 * 60 * 60)
        usagi.token.restartDriver()

async def checkSpam():
    time.sleep(10)
    while True:
        time.sleep(3)
        asyncio.run_coroutine_threadsafe(reportSpam(usagi), usagi.loop)

async def notificationForum():
    time.sleep(10)
    while True:
        asyncio.run_coroutine_threadsafe(forum(usagi), usagi.loop)
        time.sleep(60 * 30)

async def checkTransformator():
    time.sleep(10)
    while True:
        asyncio.run_coroutine_threadsafe(checkTransform(usagi), usagi.loop)
        time.sleep(60 * 10)

async def checkTime():
    time.sleep(10)
    while True:
        asyncio.run_coroutine_threadsafe(postNews(usagi), usagi.loop)
        time.sleep(60 * 10)



class UsagiChan:

    def __init__(self):
        self.config = loadConfig('src/config')
        self.loop = None
        self.spam = 0
        intents = discord.Intents.all()
        self.client = discord.Client(intents = intents)
        self.LOGGER = getLogger()
        self.members = Members(self.config['data']['guildId'])
        self.db = Database(self)
        #self.token = Token()
        self.lastTimeJoin = datetime.datetime.now()
        self.commnds = commands

    def checkConnection(self):
        @self.client.event
        async def on_ready():

            self.LOGGER.info('Successfully connected to discord')
            await self.client.change_presence(status=discord.Status.online, activity=discord.Game("ver 2.0 | Нья |"))
            self.loop = asyncio.get_event_loop()
            await self.members.fillMembers(self.client)
            self.musicPlayer = MusicPlayer(self.client, self.config)


    def run(self):
        self.client.run(self.config['data']['token'])


    from events.newMessageEvent import setMessageEvent
    from events.voiceStateUpdateEvent import setVoiceStateUpdateEvent
    from events.newReactionEvent import setNewReactionEvent
    from events.removeReactionEvent import setRemoveReactionEvent
    from events.usersChangedEvents import setUsersChangedEvents



usagi = UsagiChan()
usagi.checkConnection()
usagi.setMessageEvent()
usagi.setVoiceStateUpdateEvent()
usagi.setNewReactionEvent()
usagi.setRemoveReactionEvent()
usagi.setUsersChangedEvents()



#newLog('', '', '', '', new = 1)
#Thread(target = asyncio.run, args=(checkRequests(), )).start()
#Thread(target = asyncio.run, args=(checkShedule(), )).start()
#Thread(target = asyncio.run, args=(checkTokens(), )).start()
#Thread(target = asyncio.run, args=(checkSpam(), )).start()
Thread(target = asyncio.run, args=(notificationForum(), )).start()
Thread(target = asyncio.run, args=(checkTransformator(), )).start()
Thread(target = asyncio.run, args=(checkTime(), )).start()
Thread(target = checkAudio).start()
#Thread(target = restartDriver).start()
usagi.run()
