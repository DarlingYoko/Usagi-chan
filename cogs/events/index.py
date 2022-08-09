import discord, telebot, re
from discord.ext import commands
from bin.functions import *
from time import mktime
from datetime import datetime



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
        # return
        user_id = message.author.id
        channel_id = message.channel.id
        if user_id in self.bot.messages_dump.keys():
            if channel_id not in self.bot.messages_dump[user_id].keys():
                self.bot.messages_dump[user_id][channel_id] = {'message': 1, 'image': 0, 'gif': 0, 'emoji': 0, 'sticker': 0}
            else:
                self.bot.messages_dump[user_id][channel_id]['message'] += 1
        else:
            self.bot.messages_dump[user_id] = {channel_id: {'message': 1, 'image': 0, 'gif': 0, 'emoji': 0, 'sticker': 0}}

        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type in ['image/png', 'image/jpeg', 'image/jpg']:
                    self.bot.messages_dump[user_id][channel_id]['image'] += 1
                if attachment.content_type in ['image/gif']:
                    self.bot.messages_dump[user_id][channel_id]['gif'] += 1
        if '.gif' in message.content:
            self.bot.messages_dump[user_id][channel_id]['gif'] += 1
        if re.search('<*:*:*>', message.content):
            self.bot.messages_dump[user_id][channel_id]['emoji'] += 1
        if message.stickers:
            self.bot.messages_dump[user_id][channel_id]['sticker'] += len(message.stickers)

        # print(self.bot.messages_dump)
        lenght = 0
        for user in self.bot.messages_dump.keys():
            lenght += len(self.bot.messages_dump[user])
        # print(lenght)
        if lenght > 3:
            await self.manual_dump()

        # print(message.content)

        # if 'dababy' in message.content.lower():
            
        #     values = self.bot.db.custom_command(f'SELECT money, spend, notify from pivo where user_id = {message.author.id};')
        #     if not values:
        #         await message.channel.send(f'{message.author.mention}, У тебя не хватает <:dababy:949712395385843782> на счету для использования!')
        #         await message.delete()
        #     else:
        #         values = values[0]
        #         money, spend, notify = values[0], values[1], values[2]
                
        #         if money < 1 and not notify:
        #             await message.channel.send(f'{message.author.mention}, У тебя не хватает <:dababy:949712395385843782> на счету для использования!')
        #             await message.delete()
        #             notify = True
        #         elif money < 1 and notify:
        #             await message.delete()
        #         else:
        #             money -= 1
        #             spend += 1
        #             notify = False
        #         self.bot.db.custom_command(f'UPDATE pivo set money = {money}, spend = {spend}, notify = {notify} where user_id = {message.author.id};')



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

        # if 'dababy' in emoji.name.lower():
        #     guild = await self.bot.fetch_guild(guild_id)
        #     channel = await self.bot.fetch_channel(channel_id)
        #     message = await channel.fetch_message(message_id)
        #     member = await guild.fetch_member(user_id)
        #     values = self.bot.db.custom_command(f'SELECT money, spend, notify from pivo where user_id = {user_id};')
        #     if not values:
        #         await channel.send(f'{member.mention}, У тебя не хватает <:dababy:949712395385843782> на счету для использования!')
        #         await message.remove_reaction(emoji, member)
        #     else:
        #         values = values[0]
        #         money, spend, notify = values[0], values[1], values[2]
        #         if money < 1 and not notify:
        #             await message.channel.send(f'{member.mention}, У тебя не хватает <:dababy:949712395385843782> на счету для использования!')
        #             await message.remove_reaction(emoji, member)
        #             notify = True
        #         elif money < 1 and notify:
        #             await message.remove_reaction(emoji, member)
        #         else:
        #             money -= 1
        #             spend += 1
        #             notify = False
        #         self.bot.db.custom_command(f'UPDATE pivo set money = {money}, spend = {spend}, notify = {notify} where user_id = {user_id};')




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
        request = f"SELECT EXISTS(SELECT * from web_stat_user_data where uid = {member.id});"
        user_in_db = self.bot.db.custom_command(request)[0][0]
        if user_in_db:
            request = f'update web_stat_user_data set active = {True} where uid = {member.id};\n'
        else:
            request = f'insert into web_stat_user_data values (nextval(\'web_stat_user_data_id_seq\'), {member.id}, \'{member.name}\', \'{member.display_name}\', \'{member.avatar}\', {True});\n'
        result = self.bot.db.custom_command(request)
        print('Set active True for user in database - ', result, member.id)
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
        request = f"SELECT EXISTS(SELECT * from web_stat_user_data where uid = {member.id});"
        user_in_db = self.bot.db.custom_command(request)[0][0]
        if user_in_db:
            request = f'update web_stat_user_data set active = {False} where uid = {member.id};\n'
            sql = f'update discordlogin_discorduser set has_link = {False} where id = {member.id};\n'
            result = self.bot.db.custom_command(request)
            self.bot.db.custom_command(sql)
            print('Set active false to user in database - ', result, member.id)
        else:
            print('Wrong user, isn\'t in database')
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
        user_id = member.id
        voice_channel = self.config['channel'].getint('mp_voice')
        vc = get_vc(self)

        if before.channel and before.channel.id == voice_channel:
            mp_voice = await self.bot.fetch_channel(voice_channel)
            if len(mp_voice.members) == 1:
                await vc.disconnect()

        if after.channel and after.channel.id == voice_channel and not vc:
            await after.channel.connect()
        # return
        # user connect voice
        if after.channel and not before.channel:
            self.bot.voice_users[user_id] = {'state': 'connect', 'time': mktime(datetime.now().timetuple())}
        
        # user disconnect voice 
        if not after.channel and before.channel:
            if user_id not in self.bot.voice_users.keys():
                return
            if self.bot.voice_users[user_id]['state'] == 'disconnect':
                return
            channel_id = before.channel.id
            exists_user = self.bot.db.custom_command(f'select exists(select * from web_stat_all_stats where user_id = {user_id} and channel_id = {channel_id});')[0][0]
            cur_time = mktime(datetime.now().timetuple())
            time = (cur_time - self.bot.voice_users[user_id]['time'])
            if exists_user:
                sql = f'update web_stat_all_stats set voice = voice + {time} where user_id = {user_id} and channel_id = {channel_id};'
            else:
                sql = f'insert into web_stat_all_stats values (nextval(\'web_stat_all_stats_id_seq\'), {user_id}, {channel_id}, 0, 0, 0, 0, 0, {time});\n'
            self.bot.db.custom_command(sql)
            self.bot.voice_users[user_id]['state'] = 'disconnect'
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        request = f"SELECT EXISTS(SELECT * from web_stat_user_data where uid = {after.id});"
        user_in_db = self.bot.db.custom_command(request)[0][0]
        if user_in_db:
            request = f'update web_stat_user_data set display_name = \'{after.display_name}\' where uid = {after.id};\n'
        else:
            request = f'insert into web_stat_user_data values (nextval(\'web_stat_user_data_id_seq\'), {after.id}, \'{after.name}\', \'{after.display_name}\', \'{after.avatar}\', {True});\n'
        result = self.bot.db.custom_command(request)
        print('Update display name for user in database - ', result, after.display_name)
    
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        request = f'insert into web_stat_user_data values (nextval(\'web_stat_user_data_id_seq\'), {channel.id}, \'{channel.name}\', \'\', \'\', {True});\n'
        result = self.bot.db.custom_command(request)
        print('Create channel in database - ', result, channel.name)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if after.id == 863159302213337179:
            return
        request = f'update web_stat_user_data set name = \'{after.name}\' where uid = {after.id};\n'
        result = self.bot.db.custom_command(request)
        print('Update channel in database - ', result, after.name)


    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        request = f"SELECT EXISTS(SELECT * from web_stat_user_data where uid = {after.id});"
        user_in_db = self.bot.db.custom_command(request)[0][0]
        if user_in_db:
            request = f'update web_stat_user_data set name = \'{after.name}\', icon_url = \'{after.avatar}\' where uid = {after.id};\n'
        else:
            request = f'insert into web_stat_user_data values (nextval(\'web_stat_user_data_id_seq\'), {after.id}, \'{after.name}\', \'{after.display_name}\', \'{after.avatar}\', {True});\n'
        result = self.bot.db.custom_command(request)
        print('Update display name for user in database - ', result, after.name)

    @commands.is_owner()
    @commands.command()
    async def dump_messages(self, ctx):
        await self.manual_dump()
        await ctx.reply('Done')


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

    async def manual_dump(self):
        sql = ''
        sql_exists = ''
        for user_id in self.bot.messages_dump.keys():
            for channel_id in self.bot.messages_dump[user_id].keys():
                if not sql_exists:
                    sql_exists = f'select * from web_stat_all_stats where (user_id = {user_id} and channel_id = {channel_id})'
                else:
                    sql_exists += f' or (user_id = {user_id} and channel_id = {channel_id})'

        sql_exists += ';'
        exists_user = self.bot.db.custom_command(sql_exists)
        sql = ''
        # print(sql_exists)
        # print(exists_user)
        user_id = 0
        channel_id = 0
        for user in exists_user:
            if user_id == user[1] and channel_id == user[2]:
                self.bot.db.custom_command(f'delete from web_stat_all_stats where id = {user[0]}')
                continue
            user_id = user[1]
            channel_id = user[2]
            # print(user_id, channel_id)
            # print(exists_user)
            sql += f'update web_stat_all_stats set message = message + {self.bot.messages_dump[user_id][channel_id]["message"]}, emoji = emoji + {self.bot.messages_dump[user_id][channel_id]["emoji"]}, sticker = sticker + {self.bot.messages_dump[user_id][channel_id]["sticker"]}, image = image + {self.bot.messages_dump[user_id][channel_id]["image"]}, gif = gif + {self.bot.messages_dump[user_id][channel_id]["gif"]} where user_id = {user_id} and channel_id = {channel_id};'
            del self.bot.messages_dump[user_id][channel_id]
            if len(self.bot.messages_dump[user_id]) == 0:
                del self.bot.messages_dump[user_id]

        for user_id in self.bot.messages_dump.keys():
            for channel_id in self.bot.messages_dump[user_id].keys():
                sql += f'insert into web_stat_all_stats values (nextval(\'web_stat_all_stats_id_seq\'), {user_id}, {channel_id}, {self.bot.messages_dump[user_id][channel_id]["message"]}, {self.bot.messages_dump[user_id][channel_id]["emoji"]}, {self.bot.messages_dump[user_id][channel_id]["sticker"]}, {self.bot.messages_dump[user_id][channel_id]["image"]}, {self.bot.messages_dump[user_id][channel_id]["gif"]}, 0);\n'
        # print(sql)
        # print(self.bot.messages_dump)
        self.bot.messages_dump = {}
        self.bot.db.custom_command(sql)

def setup(bot):
    bot.add_cog(Events(bot))
