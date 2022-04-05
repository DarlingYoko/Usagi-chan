from xmlrpc.client import Boolean
import discord, telebot
from discord.ext import commands
from bin.functions import *



class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.tg_bot = telebot.TeleBot('5080341472:AAGRRMfyO68ys333warKu97C5iepRH7IC3Q')


    @commands.Cog.listener()
    async def on_message(self, message):
        if str(message.type) == 'MessageType.pins_add':
                return await message.delete()

        if message.channel.id == 942169382124134410:
            emoji = self.bot.get_emoji(897821614312394793)
            return await message.add_reaction(emoji)

        if message.author == self.bot.user or message.author.bot:
            return

        # print(message.content)

        if 'dababy' in message.content.lower():
            
            values = self.bot.db.custom_command(f'SELECT money, spend, notify from pivo where user_id = {message.author.id};')
            if not values:
                await message.channel.send(f'{message.author.mention}, У тебя не хватает <:dababy:949712395385843782> на счету для использования!')
                await message.delete()
            else:
                values = values[0]
                money, spend, notify = values[0], values[1], values[2]
                
                if money < 1 and not notify:
                    await message.channel.send(f'{message.author.mention}, У тебя не хватает <:dababy:949712395385843782> на счету для использования!')
                    await message.delete()
                    notify = True
                elif money < 1 and notify:
                    await message.delete()
                else:
                    money -= 1
                    spend += 1
                    notify = False
                self.bot.db.custom_command(f'UPDATE pivo set money = {money}, spend = {spend}, notify = {notify} where user_id = {message.author.id};')



        emojis = self.config['reacts']
        if str(message.channel.id) in emojis.keys() and message.attachments:
            emoji = self.bot.get_emoji(emojis.getint(str(message.channel.id)))
            return await message.add_reaction(emoji)

        

        # if message.channel.id in [930076834350133288] and self.bot.redirect:
        #     answer = f'{message.author.name} send:\n{message.content}'
        #     ls = 317513731
        #     chat = -712264970

        #     if message.attachments:
        #         for attachment in message.attachments:
        #             if 'image' in attachment.content_type:
        #             # print(attachment.url)
        #                 self.tg_bot.send_photo(chat, attachment.url, caption = answer)
        #                 return

            # self.tg_bot.send_message(chat, answer)


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        message_id = payload.message_id
        user_id = payload.user_id
        emoji = payload.emoji
        channel_id = payload.channel_id
        guild_id = payload.guild_id

        if str(emoji.id) in self.config['roles'].keys():
            if message_id in [858131920729931796, 877665594307125268, 933409260874903602, 951943709900017694]:
                return await self.give_role_to_user(user_id, self.config['roles'].getint(f'{emoji.id}'), guild_id)

        if 'dababy' in emoji.name.lower():
            guild = await self.bot.fetch_guild(guild_id)
            channel = await self.bot.fetch_channel(channel_id)
            message = await channel.fetch_message(message_id)
            member = await guild.fetch_member(user_id)
            values = self.bot.db.custom_command(f'SELECT money, spend, notify from pivo where user_id = {user_id};')
            if not values:
                await channel.send(f'{member.mention}, У тебя не хватает <:dababy:949712395385843782> на счету для использования!')
                await message.remove_reaction(emoji, member)
            else:
                values = values[0]
                money, spend, notify = values[0], values[1], values[2]
                if money < 1 and not notify:
                    await message.channel.send(f'{member.mention}, У тебя не хватает <:dababy:949712395385843782> на счету для использования!')
                    await message.remove_reaction(emoji, member)
                    notify = True
                elif money < 1 and notify:
                    await message.remove_reaction(emoji, member)
                else:
                    money -= 1
                    spend += 1
                    notify = False
                self.bot.db.custom_command(f'UPDATE pivo set money = {money}, spend = {spend}, notify = {notify} where user_id = {user_id};')




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
        guild_id = payload.guild_id

        if str(emoji.id) in self.config['roles'].keys():
            if message_id in [858131920729931796, 877665594307125268, 933409260874903602, 951943709900017694]:
                return await self.remove_role_from_user(user_id, self.config['roles'].getint(f'{emoji.id}'), guild_id)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # проверить, есть ли пользователь в бд, и если да, то выдать его роли
        request = f"SELECT EXISTS(SELECT * from user_stats where user_id = {member.id});"
        user_in_db = self.bot.db.custom_command(request)[0][0]
        if user_in_db:
            response = self.bot.db.get_value('user_stats', 'roles', 'user_id', member.id)
            if response:
                guild = await self.bot.fetch_guild(self.config['data']['guild_id'])
                for role_id in eval(response):
                    if role_id not in [self.config['roles_id'].getint('everyone'), self.config['roles_id'].getint('server_buster')]:
                        role = guild.get_role(role_id)
                        await member.add_roles(role)
                answer = f'{member.mention}, Вернула тебе твои роли, бааака!'
            else:
                answer = f'{member.mention}, Не получилось достать твои роли'
        else:
            answer = f'Новый пользователь\n Пивет пивет на нашем сервере {member.mention} <:HmmFlower:861241411805642782>'

        channel = await self.bot.fetch_channel(self.config['channel']['main'])
        await channel.send(answer)


    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # сохранить все роли у юзера при выходе с серва
        request = f"SELECT EXISTS(SELECT * from user_stats where user_id = {member.id});"
        user_in_db = self.bot.db.custom_command(request)[0][0]
        roles = str([i.id for i in member.roles])
        if user_in_db:
            response = self.bot.db.update('user_stats', 'roles', 'user_id', roles, member.id)
        else:
            response = self.bot.db.insert('user_stats', member.id, roles)

        if response:
            answer = f'Сохранила роли этого дэбила {member.mention}, нья!'
        else:
            answer = f'Не получилось засейвить этого долбаёба {member.mention}, бб аРольф!'

        channel = await self.bot.fetch_channel(self.config['channel']['main'])
        await channel.send(answer)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_channel = self.config['channel'].getint('mp_voice')
        channel = before.channel or after.channel
        vc = get_vc(self)

        if before.channel and before.channel.id == voice_channel:
            mp_voice = await self.bot.fetch_channel(voice_channel)
            if len(mp_voice.members) == 1:
                await vc.disconnect()

        if after.channel and after.channel.id == voice_channel and not vc:
            await after.channel.connect()
    
    # @commands.Cog.listener()
    # async def on_member_update(self, before, after):
    #     user_id = before.id
    #     huis = {686586463357370449: 'Хуй 1', 864765911663116288: 'Хуй 2', 289361805279494145: 'Хуй 3', 674650795525799994: 'Хуй 4'}
    #     if user_id in huis.keys():
    #         if 'хуй' not in after.display_name.lower():
    #             await after.edit(nick=huis[user_id])


    async def give_role_to_user(self, user_id, role_id, guild_id):
        guild = await self.bot.fetch_guild(guild_id)
        role = guild.get_role(role_id)
        user = await guild.fetch_member(user_id)
        return await user.add_roles(role)

    async def remove_role_from_user(self, user_id, role_id, guild_id):
        guild = await self.bot.fetch_guild(guild_id)
        role = guild.get_role(role_id)
        user = await guild.fetch_member(user_id)
        return await user.remove_roles(role)

def setup(bot):
    bot.add_cog(Events(bot))
