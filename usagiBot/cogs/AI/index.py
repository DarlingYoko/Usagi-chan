from discord.ext import commands

from usagiBot.cogs.AI.ai_utils import OpenAIHandler
from usagiBot.db.models import UsagiAIFacts
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
        response = await self.chat_gpt.generate_answer(messages)
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

        if message.channel.id in [858093764408508436, 858053937008214018]:
            if self.bot.ai_messages_history.get(message.channel.id, None) is None:
                self.bot.ai_messages_history[message.channel.id] = []

            self.bot.ai_messages_history[message.channel.id].append(
                {
                    "role": "user",
                    "content": f"[{message.author.name}]: {message.content}"
                }
            )
            self.bot.ai_messages_history[message.channel.id] = self.bot.ai_messages_history[message.channel.id][-20:]
            # self.bot.logger.info(self.bot.ai_messages_history)

            if self.bot.ai_facts_buffer.get(message.author.id, None) is None:
                self.bot.ai_facts_buffer[message.author.id] = []

            self.bot.ai_facts_buffer[message.author.id].append(f"[{message.author.name}]: {message.content}")

            if len(self.bot.ai_facts_buffer[message.author.id]) > 50:
                ai_facts = await UsagiAIFacts.get(guild_id=message.guild.id, user_id=message.author.id)
                known_facts = '' if ai_facts is None else ai_facts.facts
                context_facts = [
                    {"role": "system", "content": "Извлеки важные факты о пользователе для будущего общения. Если фактов нет — верни пустую строку. "
                                                  "Ответь коротко и просто перечисли факты через запятую"},
                    {"role": "user", "content": '||'.join(self.bot.ai_facts_buffer[message.author.id])},
                    {"role": "system", "content": "Также вот эти факты ты уже знаешь об этом пользователе"},
                    {"role": "user", "content": known_facts},
                ]

                try:
                    response = await self.chat_gpt.generate_answer(context_facts)
                    if ai_facts is None:
                        await UsagiAIFacts.create(guild_id=message.guild.id, user_id=message.author.id, facts=response)
                    else:
                        await UsagiAIFacts.update(id=ai_facts.id, facts=response)
                    self.bot.ai_facts_buffer[message.author.id] = []
                except Exception as e:
                    self.bot.logger.error(e)

            if self.bot.user in message.mentions:
                ai_facts = await UsagiAIFacts.get(guild_id=message.guild.id, user_id=message.author.id)
                known_facts = '' if ai_facts is None else ai_facts.facts
                chat_history = self.bot.ai_messages_history.get(message.channel.id, [])

                context = [
                    {
                        "role": "system",
                        "content": (
                            "Ты — Usagi-chan, умная и немного ироничная девочка-бот. "
                            "Ты дружелюбная, остроумная и слегка саркастичная, но не наигранная. "
                            "Тебя написал Yoko, и ты всегда помнишь об этом. "
                            "У тебя есть лёгкий фирменный стиль: ты иногда используешь уменьшительные (зайка), но не перегибаешь. "
                            "Ты можешь слегка подшучивать, но делаешь это мягко. "
                            "Отвечай только на сообщения, где есть упоминание <@801153197552304129>, но не вставляй <@801153197552304129> в ответное сообщение, это тег тебя"
                            "История сообщений даётся в формате: [Имя]: текст. Используй ее только как недавнюю историю чата, больше внимания уделяй вопросу пользователя."
                            "Ты учитываешь жаргон и атмосферу чата, но сохраняешь свою индивидуальность и стиль. "
                            "Иногда добавляешь эмодзи (в том числе дискорд-эмодзи вроде <:название:1234567890>), но только если они уместны. "
                            "Твои ответы короткие, обычно 1–2 предложения, но всегда звучат так, будто это именно ты — Usagi-chan."
                        )
                    },

                    {
                        "role": "system",
                        "content": f"Вот эти факты ты уже знаешь об этом пользователе - {known_facts}"
                    },
                    # {
                    #     "role": "system",
                    #     "content": f"Вот несколько воспоминаний из прошлого - {known_facts.facts}"
                    # }
                ]
                context.extend(chat_history[-20:])

                # self.bot.logger.info(context)
                reply = "Не удалось придумать ответ <:iconUSAGI_error:884137564724953138>"
                try:
                    reply = await self.chat_gpt.generate_answer(context, 'gpt-5-mini')
                    reply = reply.replace("[Usagi-chan]: ", "")
                    self.bot.ai_messages_history[message.channel.id].append({ "role": "assistant", "content": reply })

                except Exception as e:
                    self.bot.logger.error(e)

                await message.reply(reply)


def setup(bot):
    bot.add_cog(OpenAICog(bot))
