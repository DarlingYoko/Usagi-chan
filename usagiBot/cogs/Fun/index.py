import asyncio, random, qbittorrentapi
import discord

from discord.ext import commands, tasks
from discord import SlashCommandGroup
from usagiBot.cogs.Fun.fun_utils import get_exchange_rate_data, get_vpn_list
from usagiBot.db.models import UsagiConfig, UsagiTorrent
from usagiBot.src.UsagiChecks import check_is_already_set_up, check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError
from usagiBot.src.UsagiUtils import get_embed

from pycord18n.extension import _
from requests import get
from datetime import datetime


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.check_torrents.start()

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    # Default commands
    @commands.command(
        description="Check Usagi ping",
        aliases=["пинг"],
        name="ping",
    )
    async def ping_to_usagi(self, ctx) -> None:
        ping = round(ctx.bot.latency * 1000)
        await ctx.reply(_("ping pong").format(ping=ping))

    @commands.command(aliases=["понг"], name="pong", description="Check Usagi ping",)
    async def pong_to_usagi(self, ctx) -> None:
        await ctx.reply(_("pong ping"))

    @commands.command(name="link", description="Link to my webs.",)
    async def get_stats_link(self, ctx) -> None:
        await ctx.reply(_("link on my webs"))

    @commands.command(name="яишенка", aliases=["глазунья"], description="Как приготовить яишенку")
    async def how_to_make_fried_eggs(self, ctx) -> None:
        answer = (
            "<a:read:859186021488525323> Ставишь сковороду на небольшую температуру, наливаешь немного масла, "
            "растираешь силиконовой кисточкой или салфеткой равномерно, чтобы не хлюпало, разбиваешь яйцо и "
            "ждёшь\n\n"
            + "<a:read:859186021488525323> Видишь, что нижний слой белка начинает белеть, а сверху вокруг желтка "
            "еще сопелька прозрачная, так вот, бери вилочку и под сопелькой в радиусе разлива яйца разрывай "
            "белок, чтобы слой вокруг желтка тип провалился к сковородке и стал одним целым со всем белком, "
            "посыпаешь приправами на вкус, ждешь, огонь сильно не добавляешь и готово\n\n"
            + "<a:peepoFAT:859363980228427776> Если любишь, чтобы желток внутри приготовился и был не жидкий, "
            "то накрываешь крышкой"
        )
        return await ctx.reply(answer)

    @commands.command(name="arolf", aliases=["арольф", "арофл"])
    async def send_arolf_photo(self, ctx) -> None:
        arolf_file = discord.File("./usagiBot/files/photo/aRolf.png")
        return await ctx.send(file=arolf_file)

    @commands.command(name="toxic", aliases=["токсины"], description="Check toxic lvl")
    async def check_toxic_percent(self, ctx) -> None:
        return await ctx.send(_("toxic lvl").format(toxic=random.randint(1, 100)))

    @commands.command(name="currency", aliases=["курс"], description="Check current exchange rate")
    async def get_exchange_rate(self, ctx) -> None:
        return_message = "```autohotkey\n"

        rates = get_exchange_rate_data()
        required_rates = ["USDRUB", "USDUAH", "USDBYN", "USDKZT"]
        counter = 1
        for rate in required_rates:
            if rate in rates.keys():
                currency = rates[rate]
                value, changes = currency["value"], currency["change"]
                return_message += f"{counter}. {rate} {value} ({changes})\n"
                counter += 1

        return_message += "```"
        await ctx.reply(
            embed=get_embed(
                title=_("currency"),
                description=return_message
            )
        )

    @commands.command(name="iq", description="See your IQ")
    @commands.cooldown(per=60 * 1, rate=1, type=commands.BucketType.user)
    async def get_user_iq(self, ctx) -> None:
        user_iq = random.randint(1, 200)
        answers = {
            "ПЧЕЛ ТЫЫЫ НУЛИНА, соболезную чатерсам": user_iq == 1,
            "Не ну ты чисто очередняря": 110 >= user_iq >= 90,
            "Пчел пытается быть умным aRolf": 200 > user_iq >= 170,
            "А ты хорош, я бы даже сказала МЕГАХАРОШ": user_iq == 200,
            "+ секс": user_iq == 69,
            "Мдааааа, какой же ты тупой": 50 > user_iq > 1,
        }

        answer = next((key for key, value in answers.items() if value), "")

        await ctx.reply(f"Твой iq = {user_iq}\n{answer}")

    @commands.command(aliases=["айпи"], name="ip", description="Check Usagi ip", )
    @commands.cooldown(per=60 * 1, rate=1, type=commands.BucketType.user)
    async def get_ip(self, ctx) -> None:
        cur_ip = get('https://api.ipify.org').content.decode('utf8')
        await ctx.reply(cur_ip)

    # Slash commands
    @commands.slash_command(
        name="roll",
        description="Generate random number from _ to _",
        name_localizations={"ru": "рандом"},
        description_localizations={"ru": "Рандом число от _ до _"},
    )
    @discord.commands.option(
        name="from_",
        name_localizations={"ru": "от"},
    )
    @discord.commands.option(
        name="to_",
        name_localizations={"ru": "до"},
    )
    async def roll_random_number(self, ctx, from_: int, to_: int) -> None:
        if to_ < from_:
            from_, to_ = to_, from_
        number = random.randint(from_, to_)
        await ctx.respond(
            content=_("random number").format(number=number),
        )

    # @commands.slash_command(
    #     name="torrent",
    #     description="Download torrent by url or file to the shared folder.",
    #     name_localizations={"ru": "торрент"},
    #     description_localizations={"ru": "Скачать торрент с помощью ссылки или файла в общую папку."},
    # )
    # @discord.commands.option(
    #     name="URL",
    #     name_localizations={"ru": "Ссылка"},
    #     required=False,
    # )
    # @discord.commands.option(
    #     name="File",
    #     name_localizations={"ru": "Файл"},
    #     required=False,
    # )
    # async def download_torrent_file(self, ctx, url: str = None, file: discord.Attachment = None) -> None:
    #     response = ''
    #     added = False
    #     time = datetime.now().timestamp().__floor__()
    #     tag = f'{ctx.author.id}-{time}'
    #     try:
    #         if file:
    #             bytes_file = await file.read()
    #             self.bot.qbt_client.torrents_add(torrent_files=bytes_file, tags=tag)
    #             response = _('added torrent file').format(filename=file.filename)
    #             added = True
    #         if url:
    #             self.bot.qbt_client.torrents_add(urls=url, tags=tag)
    #             response = _('added torrent url')
    #             added = True
    #     except Exception as e:
    #             response=_('torrent error').format(e=e)

    #     if added:
    #         await UsagiTorrent.create(
    #             guild_id=ctx.guild.id,
    #             channel_id=ctx.channel.id,
    #             user_id=ctx.author.id,
    #             tag=tag
    #         )

    #     await ctx.respond(content=response)

    # @tasks.loop(minutes=1)
    # async def check_torrents(self):
    #     usagi_torrents = await UsagiTorrent.get_all()
    #     usagi_tags = list(map(lambda x: x.tag, usagi_torrents))
    #     finished_torrents = list(filter(
    #         lambda x: x.state == qbittorrentapi.TorrentState.UPLOADING and x.tags in usagi_tags,
    #         self.bot.qbt_client.torrents_info()
    #     ))

    #     for torrent in finished_torrents:
    #         db_record = list(filter(lambda x: x.tag == torrent.tags, usagi_torrents))[0]
    #         guild = self.bot.get_guild(db_record.guild_id)
    #         channel = await guild.fetch_channel(db_record.channel_id)
    #         await channel.send(_('torrent finished').format(user_id=db_record.user_id, torrent_name=torrent.name))

    #         await UsagiTorrent.delete(
    #             guild_id=guild.id,
    #             channel_id=channel.id,
    #             user_id=db_record.user_id,
    #             tag=db_record.tag,
    #         )


    # @check_torrents.before_loop
    # async def before_check_torrents(self):
    #     await self.bot.wait_until_ready()
    #     await asyncio.sleep(5)
    #     self.bot.logger.info("Checking torrents.")

    vpn = SlashCommandGroup(
        name="vpn",
        name_localizations={"ru": "впн"},
        description="Check vpn info.",
        description_localizations={"ru": "Получить информациб о впне."},
    )

    @vpn.command(
        name="top",
        name_localizations={"ru": "топ"},
        description="Top of traffic used users.",
        description_localizations={"ru": "Топ пользователей по потреблению траффика."},
    )
    @commands.cooldown(per=60, rate=1, type=commands.BucketType.channel)
    async def vpn_top(self, ctx: discord.ApplicationContext):
        top_users = get_vpn_list()

        title = _("Top vpn")
        result = list(
            map(
                lambda x: _("Counter vpn users").format(
                    count=x[0] + 1,
                    name=x[1],
                    traffic=top_users[x[1]],
                ),
                enumerate(top_users),
            )
        )

        max_len = max(len(line.split("-")[0]) for line in result)
        formatted_result = []
        for line in result:
            name, traffic = line.split("- ")
            formatted_result.append(f"{name.ljust(max_len)} - {traffic}")

        result_text = "```\n" + "\n".join(formatted_result) + "\n```"
        embed = get_embed(title=title, description=result_text)
        await ctx.respond(embed=embed)

    # Message commands
    @commands.message_command(name="Get Message ID")
    async def get_message_id(self, ctx, message: discord.Message) -> None:
        await ctx.respond(_("message id").format(message_id=message.id))

    @commands.message_command(
        name="Add Based Message", command_tag="based_message_channel"
    )
    @check_is_already_set_up()
    async def add_based_message(self, ctx, message: discord.Message) -> None:
        config = await UsagiConfig.get(
            guild_id=ctx.guild.id, command_tag="based_message_channel"
        )
        based_message_channel_id = config.generic_id
        channel = await ctx.bot.fetch_channel(based_message_channel_id)
        files = []

        if message.attachments:
            for file in message.attachments:
                file = await file.to_file()
                files.append(file)

        await channel.send(
            content=_("based from").format(mention=message.author.mention, message=message.content),
            files=files,
            embeds=message.embeds,
        )
        await ctx.respond(_("base added"))

    # User commands
    @commands.user_command(name="Get User Info")
    async def get_user_info(self, ctx, user: discord.User) -> None:
        embed = get_embed(
            title=user.name,
            url_image=user.avatar
        )
        await ctx.respond(embed=embed)


def setup(bot):
    bot.add_cog(Fun(bot))
