import discord
from discord.ext import commands


class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_message(self, message):
        if str(message.type) == 'MessageType.pins_add':
                return await message.delete()

        if message.author == self.bot.user:
            return

        emojis = {858655225412845568: 877301189102927892, 858727806401904660: 858179418371784714}
        if message.channel.id in emojis.keys() and message.attachments:
            emoji = self.bot.get_emoji(emojis[message.channel.id])
            return await message.add_reaction(emoji)




    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        message_id = payload.message_id
        user_id = payload.user_id
        emoji = payload.emoji
        channel_id = payload.channel_id

        if str(emoji.id) in self.bot.config['roles']:
            if message_id in [881687828482912286, 881687833922916363]:
                return await self.give_role_to_user(user_id, self.bot.config['roles'].getint(f'{emoji.id}'))

        # сейчас только два действия требуется отслеживать
        # 1. Выбор роли по цвету
        # 2. Получение КАРЫТА
        # Потом сделать автоматические реакт роль сообщения

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        message_id = payload.message_id
        user_id = payload.user_id
        emoji = payload.emoji
        channel_id = payload.channel_id

        if str(emoji.id) in self.bot.config['roles']:
            if message_id in [881687828482912286, 881687833922916363]:
                return await self.remove_role_from_user(user_id, self.bot.config['roles'].getint(f'{emoji.id}'))

    @commands.Cog.listener()
    async def on_member_join():
        pass

    @commands.Cog.listener()
    async def on_member_remove():
        pass

    @commands.Cog.listener()
    async def on_voice_state_update():
        pass


    async def give_role_to_user(self, user_id, role_id):
        guild = await self.bot.fetch_guild(self.bot.config['data']['guild_id'])
        role = guild.get_role(role_id)
        user = await guild.fetch_member(user_id)
        return await user.add_roles(role)

    async def remove_role_from_user(self, user_id, role_id):
        guild = await self.bot.fetch_guild(self.bot.self.bot.config['data']['guild_id'])
        role = guild.get_role(role_id)
        user = await guild.fetch_member(user_id)
        return await user.remove_roles(role)

def setup(bot):
    bot.add_cog(Events(bot))
