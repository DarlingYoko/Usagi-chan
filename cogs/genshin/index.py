from calendar import c
from cgitb import text
from discord.ext import commands, tasks
from datetime import datetime
from time import mktime
from bin.functions import get_embed, get_member_by_all
from bin.checks import is_transformator_channel
from random import choice
import genshinstats as gs
from genshinstats import errors

instruction = '''
1. Зайти на сайт Хоёлаба <https://www.hoyolab.com/home> и авторизоваться там
2. Нажать Ctrl+Shift+I или ПКМ -> Посмотреть код
3. Выбрать вкладку консоль сверху
4. Выполнить команду document.cookie
5. Скопировать и прислать мне вывод команды, Нья!
'''

class Genshin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        # self.claim_daily_reward.start()
        # self.resin_cup_alert.start()
        

    @commands.command(
        name = 'auth',
        description='Авторизация для использования данных с Хоёлаба',
        help='transformator',
        )
    @commands.check(is_transformator_channel)
    async def genshin_auth(self, ctx):
        dm_channel = ctx.author.dm_channel
        author_id = ctx.author.id
        if dm_channel == None:
            dm_channel = await ctx.author.create_dm()
        
        await dm_channel.send('Шаги авторизации:' + instruction)
        await ctx.reply('Отправила тебе в лс инструкцию.')

        def check(m):
            return m.author.id == author_id and m.channel == dm_channel

        msg = await self.bot.wait_for('message', check=check)
        msg = msg.content.replace('\'', '')
        
        for atr in msg.split('; '):
            if atr.startswith('ltoken'):
                ltoken = atr.split('ltoken=')[1]

            if atr.startswith('ltuid'):
                ltuid = atr.split('ltuid=')[1]

        await dm_channel.send('Супер, а теперь пришли мне UID своего genshin аккаунта, с которого я буду брать информацию.')
        msg = await self.bot.wait_for('message', check=check)
        uid = msg.content

        try:
            gs.set_cookie(ltuid=ltuid, ltoken=ltoken)
            gs.get_notes(uid)
        except errors.NotLoggedIn:
            return await dm_channel.send('Ошибка авторизации, проверь пожалуйста свои данные!')
        except errors.DataNotPublic:
            await dm_channel.send('Я тебя запишу, но ты пожалуйста поставь галочку -> https://discord.com/channels/858053936313008129/873352458443845632/1000726302766137424')

        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]

        if not exists_user:
            response = self.bot.db.insert(
                'genshin_stats', 
                author_id,
                ltuid,
                uid,
                ltoken,
                False,
                False
            )
        else:
            return await dm_channel.send('Ты уже авторизован, бака!')
        if response:
            await dm_channel.send(f'Успешно авторизовала тебя!')
        else:
            await dm_channel.send(f'Не удалось авторизоваться, попробуй позже.')

    @commands.command(
        name = 'resin',
        aliases=['смола'],
        description='Краткая сводка по смоле',
        )
    async def genshin_resin(self, ctx, *, member: str = None):
        if member is not None:
            member = await get_member_by_all(self, member)
            if not member:
                return await ctx.reply('Такого пользователя нет!')
        else:
            member = ctx.author
        data = await self.get_genshin_data(ctx, member)
        if not data: return
        resin_timer = int(mktime(datetime.now().timetuple()) + int(data['until_resin_limit']))
        realm_timer = int(mktime(datetime.now().timetuple()) + int(data['until_realm_currency_limit']))
        fields = []
        fields.append({'name': f'Твоя смола - {data["resin"]} <:resin:1000684701331234857>', 'value': f'160 смолы <t:{resin_timer}:R>', 'inline': False})
        fields.append({'name': f'Монеток в чайнике - {data["realm_currency"]} 🫖', 'value': f'Полная чаша <t:{realm_timer}:R>', 'inline': False})
        cookie = self.bot.db.custom_command(f'select uid from genshin_stats where id = {member.id};')[0]
        embed = get_embed(title = f'Краткая сводка. [{cookie[0]}]', fields = fields)
        msg = await ctx.reply(embed = embed)
        if ctx.guild is not None:
            await ctx.message.delete(delay = 10*60)
            await msg.delete(delay = 10*60)
    
    @commands.command(
        name = 'code',
        aliases=['коды'],
        description='активировать код для геншина',
        )
    async def genshin_code_activate(self, ctx, code_str: str):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            await ctx.reply('Ты не авторизован, бака!')
            return 0
        cookie = self.bot.db.custom_command(f'select ltuid, uid, ltoken from genshin_stats where id = {author_id};')[0]
        ltuid = cookie[0]
        uid = cookie[1]
        ltoken = cookie[2]
        gs.set_cookie(ltuid=ltuid, ltoken=ltoken)
        gs.redeem_code(uid)
        await ctx.reply('Активировала код!')

    @commands.command(
        name = 'notes',
        aliases=['заметки'],
        description='Подробная информация твоего аккаунта',
        help='transformator',
        )
    @commands.check(is_transformator_channel)
    async def genshin_notes(self, ctx):
        data = await self.get_genshin_data(ctx, ctx.author)
        if not data: return
        resin_timer = int(mktime(datetime.now().timetuple()) + int(data['until_resin_limit']))
        realm_timer = int(mktime(datetime.now().timetuple()) + int(data['until_realm_currency_limit']))
        cookie = self.bot.db.custom_command(f'select daily_sub, resin_sub, uid from genshin_stats where id = {ctx.author.id};')[0]
        fields = []
        fields.append({'name': f'Твоя смола - {data["resin"]} <:resin:1000684701331234857>', 'value': f'160 смолы <t:{resin_timer}:R>', 'inline': False})
        fields.append({'name': f'Монеток в чайнике - {data["realm_currency"]} 🫖', 'value': f'Полная чаша <t:{realm_timer}:R>', 'inline': False})
        fields.append({'name': f'Сколько выполнено дейликов - {data["completed_commissions"]}', 'value': f'Забрана ли награда за дейлики - {"Да" if data["claimed_commission_reward"] else "Нет"}', 'inline': False})
        fields.append({'name': f'Подписка на сбор дейли отметок', 'value': f'{"Да" if cookie[0] else "Нет"}', 'inline': False})
        fields.append({'name': f'Подписка на кап смолы', 'value': f'{"Да" if cookie[1] else "Нет"}', 'inline': False})
        fields.append({'name': f'Сколько скидок для боссов осталось', 'value': f'{data["remaining_boss_discounts"]}', 'inline': False})

        embed = get_embed(title = f'Заметки путешественника [{cookie[2]}]', fields = fields)
        await ctx.reply(embed = embed)

    @commands.command(
        name = 'drs',
        help='transformator',
        description='Подписка на сбор дейли отметок',
        )
    @commands.check(is_transformator_channel)
    async def genshin_daily_reward_claim_sub(self, ctx):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            return await ctx.reply('Ты не авторизован, бака!')
        response = self.bot.db.update('genshin_stats', 'daily_sub', 'id', True, author_id)

        if response:
            await ctx.reply('Записала тебя на автоматический сбор дейли отметок.')
        else:
            await ctx.reply('Не получилось записать тебя, попробуй позже.')

    @commands.command(
        name = 'undrs',
        help='transformator',
        description='Отписка от сбора дейли отметок',
        )
    @commands.check(is_transformator_channel)
    async def genshin_daily_reward_claim_unsub(self, ctx):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            return await ctx.reply('Ты не авторизован, бака!')
        response = self.bot.db.update('genshin_stats', 'daily_sub', 'id', False, author_id)

        if response:
            await ctx.reply('Успешно отписала тебя от автоматического сбора дейли отметок.')
        else:
            await ctx.reply('Не получилось отписать тебя, попробуй позже.')

    @commands.command(
        name = 'crs',
        help='transformator',
        description='Подписка на алёрт капа смолы.',
        )
    @commands.check(is_transformator_channel)
    async def genshin_cup_resin_sub(self, ctx):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            return await ctx.reply('Ты не авторизован, бака!')
        response = self.bot.db.update('genshin_stats', 'resin_sub', 'id', True, author_id)

        if response:
            await ctx.reply('Записала тебя на алёрт капа смолы.')
        else:
            await ctx.reply('Не получилось записать тебя, попробуй позже.')

    @commands.command(
        name = 'uncrs',
        help='transformator',
        description='Отписка от алёрта капа смолы.',
        )
    @commands.check(is_transformator_channel)
    async def genshin_cup_resin_unsub(self, ctx):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            return await ctx.reply('Ты не авторизован, бака!')
        response = self.bot.db.update('genshin_stats', 'resin_sub', 'id', False, author_id)

        if response:
            await ctx.reply('Успешно отписала тебя от алёрта капа смолы.')
        else:
            await ctx.reply('Не получилось отписать тебя, попробуй позже.')

    @commands.command(
        name = 'ss',
        aliases=['подписки'],
        description='Статус подписок.',
        )
    async def genshin_sub_status(self, ctx):
        author_id = ctx.author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            return await ctx.reply('Ты не авторизован, бака!')
        cookie = self.bot.db.custom_command(f'select daily_sub, resin_sub from genshin_stats where id = {author_id};')[0]
        if cookie:
            fields = []
            fields.append({'name': f'Сбор дейли отметок', 'value': f'{"Да" if cookie[0] else "Нет"}', 'inline': False})
            fields.append({'name': f'Кап смолы', 'value': f'{"Да" if cookie[1] else "Нет"}', 'inline': False})

            embed = get_embed(title = 'Твои подписки', fields = fields)
            msg = await ctx.reply(embed = embed)
            if ctx.guild is not None:
                await ctx.message.delete(delay = 10*60)
                await msg.delete(delay = 10*60)
        else:
            await ctx.reply('Не получилось прочитать твои подписки, попробуй позже.')

    @tasks.loop(minutes=30)
    async def claim_daily_reward(self):
        if datetime.now().hour in [15,16,17]:
            cookies = self.bot.db.custom_command(f'select ltuid, uid, ltoken from genshin_stats where daily_sub = {True};')
            reward_claimed = False
            for cookie in cookies:
                try:
                    gs.set_cookie(ltuid=cookie[0], ltoken=cookie[2])
                    reward = gs.claim_daily_reward(cookie[1])
                    if reward:
                        reward_claimed = True
                    print(reward)
                except Exception as e:
                    print(f'resin cup error with {cookie[1]}')
                    print(e)
            if reward_claimed:
                channel = await self.bot.fetch_channel(self.config['channel']['main'])
                await channel.send('Собрала ежедневные отметки, Нья!')


    @claim_daily_reward.before_loop
    async def before_claim_daily_reward(self):
        print('waiting claim_daily_reward')
        await self.bot.wait_until_ready()

    @tasks.loop(minutes=30)
    async def resin_cup_alert(self):

        cookies = self.bot.db.custom_command(f'select ltuid, uid, ltoken, resin_alerted, id from genshin_stats where resin_sub = {True};')
        channel = await self.bot.fetch_channel(self.config['channel']['transformator'])
        for cookie in cookies:
            ltuid = cookie[0]
            uid = cookie[1]
            ltoken = cookie[2]
            user_id = cookie[4]
            try:
                gs.set_cookie(ltuid=ltuid, ltoken=ltoken)
                data = gs.get_notes(uid)
                if data['resin'] >= 150 and not cookie[3]:
                    response = self.bot.db.update('genshin_stats', 'resin_alerted', 'id', True, user_id)
                    if response:
                        texts = [
                            f'<@{user_id}>, Вижу у тебя уже {data["resin"]} смолы, время сливать? <:blushDetective:860444156386869288>',
                            f'<@{user_id}>, Вот-вот перекап, уже {data["resin"]} смолы, пойдем сливать? :3',
                            f'<@{user_id}>, АААААААААААААААААААА, СКОРЕЕЕ, УЖЕ {data["resin"]} СМОЛЫ <a:dinkDonk:865127621112102953> <a:dinkDonk:865127621112102953> <a:dinkDonk:865127621112102953>',
                            # f'<@{user_id}>, ',
                            # f'<@{user_id}>, ',
                        ]
                        await channel.send(choice(texts))
                    else:
                        print(f'error {response}, {user_id} resin alert')
                
                if data['resin'] < 150 and cookie[3]:
                    response = self.bot.db.update('genshin_stats', 'resin_alerted', 'id', False, user_id)
                    if not response:
                        print(f'error {response}, {user_id} resin alert')
            except Exception as e:
                print(f'resin cup error with {user_id}')
                print(e)
            
            


    @resin_cup_alert.before_loop
    async def before_resin_cup_alert(self):
        print('waiting resin_cup_alert')
        await self.bot.wait_until_ready()


    async def get_genshin_data(self, ctx, author):
        author_id = author.id
        exists_user = self.bot.db.custom_command(f'select exists(select * from genshin_stats where id = {author_id});')[0][0]
        if not exists_user:
            if author_id != ctx.author.id:
                await ctx.reply('Такого пользователя нет, бака!')
            else:
                await ctx.reply('Ты не авторизован, бака!')
            return 0
        cookie = self.bot.db.custom_command(f'select ltuid, uid, ltoken from genshin_stats where id = {author_id};')[0]
        ltuid = cookie[0]
        uid = cookie[1]
        ltoken = cookie[2]
        gs.set_cookie(ltuid=ltuid, ltoken=ltoken)
        stats = gs.get_notes(uid)
        # gs.genshinstats.session.close()
        return stats

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CheckFailure):
            channel = self.config['channel']['transformator']
            await ctx.send(f'Низя использовать эту команду туть. Тебе сюда <#{channel}>')


    


def setup(bot):
    # pass
    bot.add_cog(Genshin(bot))
