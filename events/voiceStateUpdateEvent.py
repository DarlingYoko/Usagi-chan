import discord

def setVoiceStateUpdateEvent(self):
    @self.client.event
    async def on_voice_state_update(member, before, after):

        try:
            if member.id == self.config['usersIDs'].getint('botId'):

                if before.channel and after.channel and before.channel.id != after.channel.id:
                    await discord.utils.get(client.voice_clients, channel=before.channel).disconnect()
                    await self.client.get_channel(after.channel.id).connect()

                elif before.channel and not after.channel:
                    await discord.utils.get(self.client.voice_clients, channel=before.channel).disconnect()

                elif after.channel and not before.channel:
                    await self.client.get_channel(after.channel.id).connect()
        except:
            pass
