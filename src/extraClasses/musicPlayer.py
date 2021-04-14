from youtube_dl import YoutubeDL
from gtts import gTTS
from spotdl import __main__ as spotdl
import sys, discord, os, subprocess, random, time
from threading import Thread
from random import randint

class MusicPlayer():
    def __init__(self):
        self.vc = None
        self.repeat = None
        self.pause = None
        self.audioList = []
        self.lastAudio = None
        self.ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '%(title)s.%(ext)s',
                'output_extension': 'mp3',
            }

    def play(self, URL):
        if 'spotify' in URL:
            Thread(target = self.downloadSpoti, args=(URL, )).start()

        else:
            Thread(target = self.downloadYoutube, args=(URL, )).start()

    def pauseAudio(self):
        self.vc.pause()
        self.pause = True

    def resume(self):
        self.vc.resume()
        self.pause = False

    def stop(self):
        self.vc.stop()
        self.repeat = None
        self.audioList = []
        self.lastAudio = None

    def shuffle(self):
        random.shuffle(self.audioList)

    def nowPlay(self):
        answer = 'Ничего не играет'
        if self.lastAudio:
            answer = 'Сейчас играет - {0}'.format(self.lastAudio.split('\\')[2].split('.')[0])
        return answer

    def skip(self):
        if len(self.audioList) > 0:
            if self.vc.is_playing():
                self.vc.stop()
                time.sleep(2)
                os.remove(self.lastAudio)

            self.lastAudio = self.audioList.pop(0)
            self.vc.play(discord.FFmpegPCMAudio(source = self.lastAudio))
            answer = 'Песенка скипнута\nСейчас играет - {0}'.format(self.lastAudio.split('\\')[2].split('.')[0])
        else:
            self.vc.stop()
            self.lastAudio = None
            answer = 'Больше песенок нет('
        return answer

    def query(self):
        audioList = ['{0}. {1}'.format(i+1, self.audioList[i].split('\\')[2].split('.')[0]) for i in range(len(self.audioList))]
        if len(self.audioList) == 0 and not self.lastAudio:
            answer = 'Пусто('
        else:
            answer = 'Сейчас играет - {0}\n{1}'.format(self.lastAudio.split('\\')[2].split('.')[0], '\n'.join(audioList))
        return answer

    def repeat(self, msg):
        if msg.split(command)[1].strip() == 'last':
            self.repeat = 1
            answer = 'Буду повторять песню'
        else:
            self.repeat = None
            answer = 'Больше не повторяю песню'
        return answer

    async def connect(self, client, msg, command):
        channel = await client.fetch_channel(msg.split(command)[1].strip())
        self.vc = await channel.connect()

    def reloadTracks(self):
        for file in os.listdir():
            if file == 'Temp' or file == 'logs.txt':
                continue
            name = '..\\audio\\' + file
            try:
                os.rename(file, name)
            except:
                os.remove(file)
            print(name)
            self.audioList.append(name)

    def downloadSpoti(self, URL):
        subprocess.check_call([sys.executable, spotdl.__file__, URL])
        self.reloadTracks()

    def downloadYoutube(self, URL):
        with YoutubeDL(self.ydl_opts) as ydl:
            ydl.download([URL])
        self.reloadTracks()

    def simpleVoice(self, msg, command):
        file = '..\\audio\\message.mp3'
        language = 'ru'
        speech = gTTS(text = msg.split(command)[1], lang = language, slow = False)
        speech.save(file)
        self.vc.play(discord.FFmpegPCMAudio(source = file), after=lambda e: print(f'music in channel has finished playing.'))

    def checkPlay(self):
        try:
            if not self.vc.is_playing() and self.repeat and self.lastAudio and not self.pause:
                self.vc.play(discord.FFmpegPCMAudio(source = self.lastAudio))

            elif not self.vc.is_playing() and not self.repeat and len(self.audioList) > 0 and not self.pause:
                if self.lastAudio:
                    os.remove(self.lastAudio)
                self.lastAudio = self.audioList.pop(0)
                print('начинаю играть')
                try:
                    self.vc.play(discord.FFmpegPCMAudio(source = self.lastAudio))
                except Exception as e:
                    print(e)


        except Exception as e:
            pass
