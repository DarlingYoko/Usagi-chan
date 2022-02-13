from random import choice
import discord
from discord.ext import commands
from asyncio import TimeoutError
from bin.functions import get_embed

# чел присылает Усаги данные для валентинки
# 1. кому 
# 2. как
# 3. текст
# Усаги по имени/нику/айди ищет чела и говорит если не находит никак.

# Дальше Усаги спрашивает правильно ли она нашла пользователя. 

# Создание ембеда и отправка в канал.

class Valentine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    @commands.command(name='валентинка')
    @commands.dm_only()
    # @commands.cooldown(per=30, rate=1)
    async def create_valentine(self, ctx, name: str, from_: str, *, text: str):
        guild = await ctx.bot.fetch_guild(858053936313008129)
        members = await guild.fetch_members(limit=None).flatten()
        name = name.lower()
        channel = ctx.channel
        user = ctx.author.id
        member = discord.utils.find(lambda m: name in m.name.lower() 
                                    or name in m.display_name.lower() , members)
            
        if not member and name.isalnum():
            member = discord.utils.find(lambda m: m.id == int(name), members)

        if not member:
            return await ctx.send('У меня не получилось найти такого пользователя, попробуй по-другому.')

        await ctx.send(f'Пользователь, которого я нашла - {member.mention}, верно? да/нет')

        def check(m):
            return m.channel == channel and m.author.id == user

        try:
            message = await ctx.bot.wait_for('message', check=check)
        except TimeoutError:
            return await ctx.send('Ты ничего не написал, завершаю диалог.')
        
        user_answer = message.content.lower()
        if user_answer not in ['да', 'нет', 'yes', 'no']:
            return await ctx.send('Такого ответа у меня нет, пока пока.')

        if user_answer in ['no', 'нет']:
            return await ctx.send('Штош, попробуй задать полное имя пользователя или используй его ID.')


        # await ctx.send(f'{member}\n{from_}\n{text}')  

        if from_ not in ['анон', 'неанон']:
            return await ctx.send('Такого варианта у меня нет( Попробуй ещё раз. (Варианты - анон/неанон)')

        channel = await guild.fetch_channel(942452515163766805)

        thumbnails = ['https://cdn.discordapp.com/attachments/807349536321175582/942441560291807232/iconUSAGI_heart.png',
                    'https://cdn.discordapp.com/attachments/817507955573915658/942436825744674816/FIN2iATXIAIFzUL.png',
                    'https://images-ext-2.discordapp.net/external/_s4Y4Tmp7YFUdBOCcAYseN6Ra8hFXKUVJeRwgmWmnUE/https/pbs.twimg.com/media/EwbK1CfUYAEa-BI.jpg%3Alarge?width=562&height=468',
                    'https://cdn.discordapp.com/attachments/817507955573915658/942435794734444644/FLRDl97XoAIdaJh.png',
                    'https://cdn.discordapp.com/attachments/817507955573915658/942433205909323776/EuNDRq4XAAQIbx3.png',
                    'https://cdn.discordapp.com/attachments/817507955573915658/942433176058470450/dee5xaj-09754994-d957-4736-83ad-a580f1998760.png',
                    'https://cdn.discordapp.com/attachments/817507955573915658/942432891793702912/genshin_venti_valentine_s__by_n4391_dee6gou-fullview.png',
                    'https://pbs.twimg.com/media/E9kawTiVcAg8YUm.jpg:large',]

        thumbnail = choice(thumbnails)

        if from_ == 'анон':
            from_ = 'Анонимная валентинка'
        elif from_ == 'неанон':
            from_ = f'Валентинка от {ctx.message.author.name}'
        else:
            pass
        image = None
        if ctx.message.attachments:
            for attachment in ctx.message.attachments:
                if 'image' in attachment.content_type:
                    image = attachment.url
                else:
                    print(attachment.content_type)

        embed = get_embed(
                        description=text,
                        author_name=from_,
                        thumbnail=thumbnail,
                        url_image=image)
        
        await channel.send(f'Валентинка для {member.mention}', embed=embed)
        await ctx.send('Отправила твою валентинку!')

    
        
    @create_valentine.error
    async def create_valentine_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f'Ты неправильно указал параметры! Баака')

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Ты не указал необходимые параметры! Баака')

        if isinstance(error, commands.PrivateMessageOnly):
            await ctx.send(f'{ctx.author.mention} Эта команда только для ЛС!')


    @commands.command(name='купидон')
    async def help_valentine(self, ctx):
        text = 'Чтобы создать свою валентинку, надо перейти в лс к Усаги и написать ей команду вида:\n`!валентинка <Имя/Ник/ID пользователя для кого валентинка> анон/неанон текст валентинки.`\nВы также можете прикрепить к своей валентинке картинку или гифку!\nВсе данные вводить без кавычек, скобочек и тд <:ad:858128511209308190>'
        await ctx.send(text)
        



def setup(bot):
    bot.add_cog(Valentine(bot))