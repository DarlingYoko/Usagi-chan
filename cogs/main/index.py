import discord, requests
from discord.ext import commands, tasks
from twitchAPI.twitch import Twitch
from easy_pil import Editor, Canvas
from PIL import Image, ImageFont, ImageOps
from discord import File


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.check_twitch_online.start()


    @commands.command()
    @commands.is_owner()
    async def purge(self, ctx, limit: int):
        await ctx.channel.purge(limit = limit + 1)
        await ctx.send('Успешно удалила', delete_after = 10)

    @commands.command()
    @commands.is_owner()
    async def send(self, ctx, channel_id: int, *, message: str):
        try:
            channel = await ctx.bot.fetch_channel(channel_id)
        except:
            guild = await ctx.bot.fetch_guild(self.config['data']['guild_id'])
            channel = guild.get_thread(channel_id)
        await channel.send(message)

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('Nothing to see here comrade.')
        else:
            print(error)

    @commands.command()
    @commands.is_owner()
    async def connect(self, ctx, channel_id: int):
        channel = await ctx.bot.fetch_channel(channel_id)
        await channel.connect()
        await ctx.send('Успешно подключилась')

    @connect.error
    async def connect_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send('Nothing to see here comrade.')
        else:
            print(error)


    @commands.command(name = 'помощь', aliases = ['хелп', 'хлеп'])
    async def help(self, ctx, *, args = None):
        if args:
            await ctx.send_help(args)
        else:
            await ctx.send_help()

    @commands.command(name = 'redirect')
    @commands.is_owner()
    async def redirect(self, ctx, switch: str):
        if switch == 'on':
            self.bot.redirect = True
            answer = 'Включила переадресацию'
        elif switch == 'off':
            self.bot.redirect = False
            answer = 'Выключила переадресацию'
        await ctx.send(answer)

    @tasks.loop(minutes=1)
    async def check_twitch_online(self):
        client_id = 'ytl8amzfrreo3hf413ywaua8jd7of8'
        client_secret = 'keiz535fdh87qb5a0h2to0vjz7ndi9'
        twitch = Twitch(client_id, client_secret)
        status = twitch.get_streams(user_login=[])#'yoko_o0', 'tunnelkin', 'stepustk', 'hyver', 'uselessmouth', 'kegebe88'])

        if 'data' in status.keys() and status['data']:
            channel = await self.bot.fetch_channel(858053937008214018)

            for user in status['data']:

                name = user['user_name']
                # print(name)
                game = user['game_name']
                link = f'<https://www.twitch.tv/{user["user_login"]}>'
                text = f'**{name}** start stream!\n{link}'
                posted = False
                async for message in channel.history(limit=1000):
                    if text in message.content:
                        posted = True
                        break

                if posted:
                    continue


                stream_name = user['title'].split(' ')
                title = []
                string = []
                for word in stream_name:
                    if len(' '.join(string) + word) < 40:
                        string.append(word)
                    else:
                        title.append(' '.join(string))
                        string = [word]
                title.append(' '.join(string))

                viewer_count = str(user['viewer_count'])

                user_info = twitch.get_users(logins=[name])
                url = user_info['data'][0]['profile_image_url']

                blank = Image.open('./files/photo/stream.png')
                mask = Image.open('./files/photo/mask2.png').convert('L')
                image = Image.open(requests.get(url, stream=True).raw)

                background = Editor(Image.new('RGBA', (1050, 301), (255, 0, 0, 0)))

                font_bold = ImageFont.truetype(font = './files/fonts/Inter-Bold.ttf', size = 30)
                font_bold_big = ImageFont.truetype(font = './files/fonts/Inter-Bold.ttf', size = 40)
                font_light = ImageFont.truetype(font = './files/fonts/Inter-Light.ttf', size = 38)
                font_regular = ImageFont.truetype(font = './files/fonts/Inter-Regular.ttf', size = 38)



                output = ImageOps.fit(image, mask.size, centering=(0.5, 0.5))
                output.putalpha(mask)

                background.paste(blank, ((0, 0)))
                background.paste(output.resize((160, 160)), (42, 55))

                background.text((245, 60), name, font = font_bold_big, color = "white")
                for i in range(len(title)):
                    background.text((245, 120 + i * 40), title[i], font = font_bold, color = "white")
                background.text((245, 170 + i * 40), game, font = font_regular, color = "#bf94ff")
                background.text((90, 255), viewer_count, font = font_bold_big, color = "#ff8280")


                file = File(fp = background.image_bytes, filename = "background.png")
                await channel.send(text, file = file)









def setup(bot):
    bot.add_cog(Main(bot))
