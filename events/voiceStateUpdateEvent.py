import discord, time, os
from gtts import gTTS
from threading import Thread


def playAudio(self, file, timeout):
    time.sleep(timeout)
    try:
        self.musicPlayer.vc.play(discord.FFmpegPCMAudio(source = file), after=lambda e: print(f'music in channel has finished playing.'))
    except Exception as e:
        print(e)

    time.sleep(timeout)
    os.remove(file)


def setVoiceStateUpdateEvent(self):
    @self.client.event
    async def on_voice_state_update(member, before, after):

        try:
            if member.id == self.config['usersIDs'].getint('yokoId'):

                if before.channel and after.channel and before.channel.id != after.channel.id:
                    await discord.utils.get(self.client.voice_clients, channel=before.channel).disconnect()
                    self.musicPlayer.vc = await self.client.get_channel(after.channel.id).connect()

                elif (before.channel and not after.channel and
                        before.channel.id != self.config['data'].getint('kadrovyChannel')):
                    await discord.utils.get(self.client.voice_clients, channel=before.channel).disconnect()
                    self.musicPlayer.vc = None

                elif (after.channel and not before.channel and
                        after.channel.id != self.config['data'].getint('kadrovyChannel')):
                    self.musicPlayer.vc = await self.client.get_channel(after.channel.id).connect()


            if before.channel and before.channel.id == self.config['data'].getint('kadrovyChannel'):
                kadrovyChannel = await self.client.fetch_channel(self.config['data'].getint('kadrovyChannel'))
                if len(kadrovyChannel.members) == 1:
                    await discord.utils.get(self.client.voice_clients, channel=before.channel).disconnect()
                    self.musicPlayer.vc = None


            if after.channel and after.channel.id == self.config['data'].getint('kadrovyChannel'):
                if not self.musicPlayer.vc:
                    self.musicPlayer.vc = await self.client.get_channel(self.config['data'].getint('kadrovyChannel')).connect()
        except:
            pass


        try:
            file = None
            usagiChannel = self.musicPlayer.vc.channel.id
            #print(before.channel and not after.channel and before.channel.id == 788865135724068904 and member.id != self.config['usersIDs'].getint('yokoId') and member.id != self.config['usersIDs'].getint('botId'))
            #print(after.channel, not before.channel, after.channel.id == 733640826256752641, member.id != self.config['usersIDs'].getint('yokoId'), member.id != self.config['usersIDs'].getint('botId'))

            if (before.channel and not after.channel and
                member.id != self.config['usersIDs'].getint('yokoId') and
                member.id != self.config['usersIDs'].getint('botId')):
                if before.channel.id == usagiChannel:
                    file = '../audio/{0}_vishel.mp3'.format(member.id)
                    text = '{0} вышёл'.format(member.display_name)


            elif (after.channel and not before.channel and
                member.id != self.config['usersIDs'].getint('yokoId') and
                member.id != self.config['usersIDs'].getint('botId')):
                if after.channel.id == usagiChannel:
                    file = '../audio/{0}_voshel.mp3'.format(member.id)
                    text = '{0} зашёл'.format(member.display_name)

            if file:
                language = 'ru'
                speech = gTTS(text = text, lang = language, slow = False)
                speech.save(file)
                Thread(target=playAudio, args=(self, file, 5, )).start()

        except Exception as e:
            print(e)
