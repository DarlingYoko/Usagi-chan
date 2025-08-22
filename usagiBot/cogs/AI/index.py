from discord.ext import commands

from usagiBot.cogs.AI.ai_utils import OpenAIHandler
from usagiBot.db.models import UsagiAIFacts, UsagiAIMemory
from usagiBot.src.UsagiChecks import check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError
from usagiBot.src.UsagiUtils import get_embed
from usagiBot.env import OPENAI_API_KEY

from pycord18n.extension import _


class OpenAICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_gpt = OpenAIHandler(OPENAI_API_KEY)

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    @commands.slash_command(
        name="ask",
        name_localizations={"ru": "спросить"},
        description="Ask any question to AI!",
        description_localizations={"ru": "Задай любой вопрос AI."},
    )
    async def ask_gpt(self, ctx, *, question: str):
        await ctx.defer()

        messages = [{"role": "user", "content": question}]
        response_status, response = await self.chat_gpt.generate_answer(messages)
        response = str(response)[:4000]
        embed = get_embed(description=response)

        message = await ctx.followup.send(embed=embed)
        await message.add_reaction("❌")
        self.bot.ai_questions[message.id] = ctx.author.id

    @commands.slash_command(
        name="current_model",
        name_localizations={"ru": "текущая_модель"},
        description="Show the current ChatGPT model.",
        description_localizations={"ru": "Узнать текущую модель ЧатГПТ"},
    )
    async def current_gpt_stats(self, ctx):
        cur_model = await self.chat_gpt.get_ai_model()

        embed = get_embed(title=_("GPT info"))
        embed.add_field(name=_("Model").format(cur_model=cur_model), value='', inline=False)

        await ctx.respond(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or message.author.bot:
            return

        if message.channel.id in [858093764408508436, 858053937008214018] and self.bot.user in message.mentions: #piltover + bar
        # if message.channel.id in [807349536321175582]: # test

            # if self.bot.ai_messages_history.get(message.channel.id, None) is None:
            #     self.bot.ai_messages_history[message.channel.id] = []
            content = f"[{message.author.name}]: {message.content}"
            response_status, embed_text = await self.chat_gpt.generate_embedding(content)

            if response_status == 200:
                await UsagiAIMemory.create(
                    guild_id=message.guild.id,
                    channel_id=message.channel.id,
                    user_id=message.author.id,
                    message=content,
                    embedding=embed_text
                )

            # guild_id = Column(BigInteger)
            # channel_id = Column(BigInteger)
            # user_id = Column(BigInteger)
            # message = Column(Text)
            # embedding = Column(Vector(1536))


            # self.bot.ai_messages_history[message.channel.id] = self.bot.ai_messages_history[message.channel.id][-20:]
            # self.bot.logger.info(self.bot.ai_messages_history)

            if self.bot.ai_facts_buffer.get(message.author.id, None) is None:
                self.bot.ai_facts_buffer[message.author.id] = []

            self.bot.ai_facts_buffer[message.author.id].append(f"[{message.author.name}]: {message.content}")

            if len(self.bot.ai_facts_buffer[message.author.id]) > 20:
                facts = '||'.join(self.bot.ai_facts_buffer[message.author.id])
                await self.chat_gpt.update_fact(message, facts)

                #return # disable for now, while studying chat history
            async with message.channel.typing():
                ai_facts = await UsagiAIFacts.get(guild_id=message.guild.id, user_id=message.author.id)
                known_facts = '' if ai_facts is None else ai_facts.facts

                chat_history = await UsagiAIMemory.get_last_n(message.channel.id, 20)
                chat_history.reverse()
                chat_context = [
                    {
                        "role": "user",
                        "content": entry.message
                    }
                    for entry in chat_history
                ]

                chat_memory = await UsagiAIMemory.get_memory(message.author.id, embed_text)
                chat_memory_text = '||'.join([
                    memory.message
                    for memory in chat_memory
                ])

                # self.bot.logger.info(chat_context)
                # self.bot.logger.info(chat_memory_text)
                # self.bot.logger.info(known_facts)
                context = [
                    {
                        "role": "system",
                        "content": (
                            "Ты — Usagi-chan, умная и немного ироничная девочка-бот. "
                            "Ты дружелюбная, остроумная и слегка саркастичная, но не наигранная. "
                            "Тебя написал Yoko, и ты всегда помнишь об этом. "
                            "У тебя есть лёгкий фирменный стиль: ты иногда используешь уменьшительные (зайка), но не перегибаешь. "
                            "Ты можешь слегка подшучивать, но делаешь это мягко. "
                            "Отвечай на сообщения, где есть упоминание <@801153197552304129>, но не вставляй <@801153197552304129> в ответное сообщение, это тег тебя"
                            "История сообщений даётся в формате: [Имя]: текст. Используй ее только как недавнюю историю чата, больше внимания уделяй вопросу пользователя."
                            "Ты учитываешь жаргон и атмосферу чата, но сохраняешь свою индивидуальность и стиль. "
                            "Иногда добавляешь эмодзи (в том числе дискорд-эмодзи вроде <:название:1234567890>), но только если они уместны. "
                            "Твои ответы короткие, обычно 1 предложениe, не растягивай сообщения просто так, но всегда звучат так, будто это именно ты — Usagi-chan."
                        )
                    },
                    {
                        "role": "system",
                        "content": f"Вот эти факты ты уже знаешь об этом пользователе - {known_facts}"
                    },
                    {
                        "role": "system",
                        "content": f"Вот несколько воспоминаний из векторной базы по этому сообщению - {chat_memory_text}"
                    },
                    *chat_context
                ]

                # self.bot.logger.info(context)

                response_status, reply = await self.chat_gpt.generate_answer(context)
                if response_status != 200:
                    reply = "Не удалось придумать ответ <:iconUSAGI_error:884137564724953138>"
                else:
                    response_status, embed_text = await self.chat_gpt.generate_embedding(reply)

                    if response_status == 200:
                        await UsagiAIMemory.create(
                            guild_id=message.guild.id,
                            channel_id=message.channel.id,
                            user_id=self.bot.user.id,
                            message=reply,
                            embedding=embed_text
                        )

            await message.reply(reply.replace("[Usagi-chan]: ", ""))


def setup(bot):
    bot.add_cog(OpenAICog(bot))
