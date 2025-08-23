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
            self.bot.logger.info('Got new message')
            response_status, embed_text = await self.chat_gpt.generate_embedding(message.content)
            self.bot.logger.info('Got embed for message')

            if response_status != 200:
                await message.reply("Не удалось придумать ответ <:iconUSAGI_error:884137564724953138>")
                return

            if self.bot.ai_facts_buffer.get(message.author.id, None) is None:
                self.bot.ai_facts_buffer[message.author.id] = []

            self.bot.ai_facts_buffer[message.author.id].append(message.content)

            if len(self.bot.ai_facts_buffer[message.author.id]) > 20:
                self.bot.logger.info('Start uploading facts')
                facts = '||'.join(self.bot.ai_facts_buffer[message.author.id])
                result = await self.chat_gpt.update_fact(message, facts)
                await message.channel.send("Обновила память <:iconUSAGI1:884140804510203944>")
                if result is True:
                    self.bot.ai_facts_buffer[message.author.id] = []


            #return # disable for now, while studying chat history
            self.bot.logger.info('Start typing')
            async with message.channel.typing():
                ai_facts = await UsagiAIFacts.get(guild_id=message.guild.id, user_id=message.author.id)
                known_facts = '' if ai_facts is None else ai_facts.facts
                self.bot.logger.info('Got facts for message')

                chat_history = await UsagiAIMemory.get_last_n(message.channel.id, message.author.id, 10)
                chat_history.reverse()
                chat_context = [
                    {
                        "role": "user",
                        "content": entry.message
                    }
                    for entry in chat_history
                ]
                self.bot.logger.info('Prepared history text')

                chat_memory = await UsagiAIMemory.get_memory(message.author.id, embed_text, 3)
                chat_memory_text = '||'.join([
                    memory.message
                    for memory in chat_memory
                ])
                self.bot.logger.info('Prepared memory text')

                self.bot.logger.info('Chat context')
                self.bot.logger.info(chat_context)
                self.bot.logger.info('Chat memory')
                self.bot.logger.info(chat_memory_text)
                self.bot.logger.info('Chat facts')
                self.bot.logger.info(known_facts)
                context = [
                    {
                        "role": "system",
                        "content": (
                            "Ты — Usagi-chan, умная и немного ироничная девочка-бот. "
                            "Ты дружелюбная, остроумная и слегка саркастичная, но не наигранная. "
                            "Тебя написал Yoko, и ты всегда помнишь об этом. "
                            "У тебя есть лёгкий фирменный стиль: ты иногда используешь уменьшительные слова, но не перегибаешь. "
                            "Ты можешь слегка подшучивать, но делаешь это мягко. "
                            "История сообщений даётся в формате: [Имя]: текст."
                            "Иногда добавляешь эмодзи, но только если они уместны. "
                            "Твои ответы короткие, обычно 1 предложениe, не растягивай сообщения, но всегда звучат так, будто это именно ты — Usagi-chan."
                        )
                    },
                    {
                        "role": "system",
                        "content": f"[User Facts]: {known_facts}"
                    },
                    {
                        "role": "system",
                        "content": f"[Relevant Memory]: {chat_memory_text}"
                    },
                    *chat_context,
                    {
                        "role": "user",
                        "content": f"[User Question]\n{message.content}"
                    }
                ]
                self.bot.logger.info('Final context')
                self.bot.logger.info(context)

                response_status, reply = await self.chat_gpt.generate_answer(context, 'gpt-5-mini')
                self.bot.logger.info('Got the reply')

                if response_status != 200:
                    reply = "Не удалось придумать ответ <:iconUSAGI_error:884137564724953138>"

                await message.reply(reply)

                if response_status == 200:
                    response_status_reply, embed_text_reply = await self.chat_gpt.generate_embedding(reply)
                    self.bot.logger.info('Got embed for reply')


            if response_status_reply == 200:
                await UsagiAIMemory.create(
                    guild_id=message.guild.id,
                    channel_id=message.channel.id,
                    user_id=self.bot.user.id,
                    message=reply,
                    embedding=embed_text_reply
                )
            self.bot.logger.info('Upload reply embed to vector table')

            await UsagiAIMemory.create(
                guild_id=message.guild.id,
                channel_id=message.channel.id,
                user_id=message.author.id,
                message=message.content,
                embedding=embed_text
            )
            self.bot.logger.info('Embed added to vector table')


            # await message.reply(reply.replace("[Usagi-chan]: ", ""))


def setup(bot):
    bot.add_cog(OpenAICog(bot))
