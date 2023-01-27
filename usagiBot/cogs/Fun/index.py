import random
import discord

from usagiBot.cogs.Fun.fun_utils import get_exchange_rate_data
from discord.ext import commands
from usagiBot.db.models import UsagiConfig
from usagiBot.src.UsagiChecks import check_is_already_set_up, check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError


class Fun(commands.Cog):
    def __init__(self, bot):
        pass

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    # Default commands
    @commands.command(
        description="Check Usagi Ping",
        aliases=["пинг"],
        name="ping",
    )
    async def ping_to_usagi(self, ctx) -> None:
        await ctx.reply(f"Pong! {round(ctx.bot.latency * 1000)} ms")

    @commands.command(aliases=["понг"], name="pong")
    async def pong_to_usagi(self, ctx) -> None:
        await ctx.reply(f"Are u sure? Ok, ping. <a:peepoWew:858320256745078834>")

    @commands.command(name="яишенка", aliases=["глазунья"])
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

    @commands.command(name="токсины", aliases=["toxic"])
    async def check_toxic_percent(self, ctx) -> None:
        return await ctx.send(
            f"Уровень токсинов в чате {random.randint(1, 100)}% <:peepoSitStarege:933802101824430201>"
        )

    @commands.command(name="курс")
    async def get_exchange_rate(self, ctx) -> None:
        return_message = "```autohotkey\n" "Сводка курса на данный момент:\n"

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
        await ctx.reply(return_message)

    @commands.command(name="iq")
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

        # key = ""
        for key, value in answers.items():
            if value:
                break

        await ctx.reply(f"Твой iq = {user_iq}\n{key}")

    # Slash commands
    @commands.slash_command(name="resin", description="Get Resin")
    async def test_resin(self, ctx) -> None:
        await ctx.respond(content="It's empty here, come back later", ephemeral=True)

    @commands.slash_command(name="roll", description="Generate random number from to")
    async def roll_random_number(self, ctx, from_: int, to_: int) -> None:
        if to_ < from_:
            from_, to_ = to_, from_
        await ctx.respond(
            content=f"Your random number is **{random.randint(from_, to_)}**",
        )

    # Message commands
    @commands.message_command(name="Get Message ID")
    async def get_message_id(self, ctx, message: discord.Message) -> None:
        await ctx.respond(f"Message ID: `{message.id}`")

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
            content=f"База от {message.author.mention}\n{message.content}",
            files=files,
            embeds=message.embeds,
        )
        await ctx.respond("Добавила базу <:BASEDHM:897821614312394793>")

    # User commandsпочему
    @commands.user_command(name="Get User Info")
    async def get_user_info(self, ctx, user: discord.User) -> None:
        await ctx.respond(f"{user}\n{user.avatar}")


def setup(bot):
    bot.add_cog(Fun(bot))
