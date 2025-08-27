import json
from typing import List, Dict
from datetime import datetime, timedelta, UTC

import discord
from discord.ext import commands, tasks

from usagiBot.cogs.AI.ai_utils import OpenAIHandler, tools
from usagiBot.db.models import UsagiAIFacts, UsagiAIMemory, UsagiAIReminder
from usagiBot.src.UsagiChecks import check_cog_whitelist
from usagiBot.src.UsagiErrors import UsagiModuleDisabledError
from usagiBot.src.UsagiUtils import get_embed
from usagiBot.env import OPENAI_API_KEY

from pycord18n.extension import _


class OpenAICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chat_gpt = OpenAIHandler(OPENAI_API_KEY, bot)
        self.ACTIONS = {
            'set_reminder': self._set_reminder,
            'clear_memory': self._clear_memory,
        }
        self.check_reminders.start()

    def cog_check(self, ctx):
        if check_cog_whitelist(self, ctx):
            return True
        raise UsagiModuleDisabledError()

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        reminders = await UsagiAIReminder.get_all()
        date_now = datetime.now()

        for reminder in reminders:
            if reminder.date > date_now:
                continue

            guild = await self.bot.fetch_guild(reminder.guild_id)
            channel = await guild.fetch_channel(reminder.channel_id)

            await channel.send(f'<@{reminder.user_id}>, <a:dinkDonk:865127621112102953> {reminder.text}')
            await UsagiAIReminder.delete(id=reminder.id)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()
        self.bot.logger.info("Update check reminders.")


    @commands.slash_command(
        name='ask',
        name_localizations={'ru': 'спросить'},
        description='Ask any question to AI!',
        description_localizations={'ru': 'Задай любой вопрос AI.'},
    )
    async def ask_gpt(self, ctx, *, question: str):
        await ctx.defer()

        messages = [{'role': 'user', 'content': question}]
        response_status, finish_reason, response = await self.chat_gpt.generate_answer(messages)
        if finish_reason == 'stop':
            response = str(response['content'])[:4000]
            embed = get_embed(description=response)

            message = await ctx.followup.send(embed=embed)
            await message.add_reaction('❌')
            self.bot.ai_questions[message.id] = ctx.author.id
        else:
            await ctx.followup.send('Не удалось придумать ответ <:iconUSAGI_error:884137564724953138>')

    @commands.slash_command(
        name='current_model',
        name_localizations={'ru': 'текущая_модель'},
        description='Show the current ChatGPT model.',
        description_localizations={'ru': 'Узнать текущую модель ЧатГПТ'},
    )
    async def current_gpt_stats(self, ctx):
        cur_model = await self.chat_gpt.get_ai_model()

        embed = get_embed(title=_('GPT info'))
        embed.add_field(name=_('Model').format(cur_model=cur_model), value='', inline=False)

        await ctx.respond(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Get only messages addresed to Usagi."""
        if self._should_ignore_message(message):
            return

        self.bot.logger.info('Got new message')

        user_id = message.author.id
        content = self._clean_message_content(message)

        # Generate user question with reply
        user_question = await self._format_user_question(message, content)
        self.bot.logger.info(user_question)

        self.bot.logger.info('Start typing')
        async with message.channel.typing():
            known_facts = await self._get_user_facts(message.guild.id, user_id)
            chat_context = await self._get_chat_context(user_id)
            chat_memory_text = await self.chat_gpt.search_memory(user_id, content)

            if chat_memory_text is None:
                await message.reply('Не удалось придумать ответ <:iconUSAGI_error:884137564724953138>')
                return

            context = self._build_context(
                known_facts=known_facts,
                chat_memory_text=chat_memory_text,
                chat_context=chat_context,
                user_question=user_question
            )
            self.bot.logger.info('Final context')
            self.bot.logger.info(context)

            response_status, finish_reason, reply = await self.chat_gpt.generate_answer(
                context, 'gpt-5-mini', tools
            )
            self.bot.logger.info('Got the reply')

            if response_status != 200 or finish_reason not in ['tool_calls', 'stop']:
                reply = 'Не удалось придумать ответ <:iconUSAGI_error:884137564724953138>'
                await message.reply(reply)
                return

            # Extra GPT call for function calling
            if finish_reason == 'tool_calls':
                # await message.reply("Выполняю команду!")
                response_status, reply = await self._call_ai_function(message, context, reply)

            if response_status != 200:
                reply = 'Не удалось придумать ответ <:iconUSAGI_error:884137564724953138>'
                await message.reply(reply)
                return

            reply_content = reply['content']

            await self.chat_gpt.add_memory(user_id, content, reply_content)
            self.bot.logger.info('Embed added to vector table')

        # Fix for 2000 symbols limit
        for i in range(0, len(reply_content), 2000):
            await message.reply(reply_content[i:i + 2000])

    def _should_ignore_message(self, message: discord.Message) -> bool:
        """Check do we need to ignore message."""
        # if message.author.id != 290166276796448768:
        #     return True
        if message.author == self.bot.user or message.author.bot:
            return True
        if not (self.bot.user in message.mentions or message.content.lower().startswith('усаги,')):
            return True
        return False

    def _clean_message_content(self, message: discord.Message) -> str:
        """Clean message content."""
        return (
            message.content.lower()
            .replace(f'<@{self.bot.user.id}>', '')
            .replace('усаги,', '')
            .strip()
        )

    async def _format_user_question(self, message: discord.Message, content: str) -> str:
        """Format user question with reply"""
        user_question = f'[User Question]: {content}'
        if message.type == discord.MessageType.reply and message.reference:
            prev_message = await message.channel.fetch_message(message.reference.message_id)
            prev_answer = prev_message.content
            user_question = f'[Previous answer]: {prev_answer}\n{user_question}'
        return user_question

    async def _get_user_facts(self, guild_id: int, user_id: int) -> str:
        """Get user facts"""
        ai_facts = await UsagiAIFacts.get(guild_id=guild_id, user_id=user_id)
        self.bot.logger.info('Got facts for message')
        return '' if ai_facts is None else ai_facts.facts

    async def _get_chat_context(self, user_id: int) -> str:
        """Get chat last N messages in chat."""
        chat_history = await UsagiAIMemory.get_last_n(user_id)
        chat_history.reverse()
        chat_context = '\n'.join(entry.message for entry in chat_history)
        self.bot.logger.info('Prepared history text')
        return chat_context

    def _build_context(
            self, known_facts: str, chat_memory_text: str, chat_context: str, user_question: str
    ) -> list[dict]:
        """Build chat context."""
        return [
            {
                'role': 'system',
                'content': (
                    'Ты — Usagi-chan, девочка-бот. '
                    'Тебя написал Yoko, и ты всегда помнишь об этом. '
                    'История сообщений даётся в формате: Вопрос: текст, Ответ: текст. '
                    'Твои ответы короткие, обычно 1 предложениe, не растягивай сообщения.'
                ),
            },
            {'role': 'system', 'content': f'[User facts]: {known_facts}'},
            {'role': 'system', 'content': f'[Relevant chat memory]: {chat_memory_text}'},
            {'role': 'system', 'content': f'[Last 10 messages in chat]: {chat_context}'},
            {'role': 'system', 'content': user_question},
        ]

    async def _call_ai_function(self, ctx, context: List, reply: Dict) -> tuple[int, list[str]] | None:
        """Call AI function."""

        # Parse all values
        context += [reply]
        function_call = reply['tool_calls'][0]
        function_call_name = function_call['function']['name']
        function_call_id = function_call['id']
        function_call_arguments = json.loads(function_call['function']['arguments'])

        # Get function to call
        function = self.ACTIONS.get(function_call_name, None)
        if function is None:
            return 400, []

        result = {function_call_name: await function(ctx, **function_call_arguments)}

        # Provide function call results to the model
        context.append({
            'role': 'tool',
            'tool_call_id': function_call_id,
            'content': json.dumps(result),
        })

        context = [
            {
                'role': 'system',
                'content': 'Ответ из tools - это технический ответ, не цитируй его полностью, а интерпретируй его смысл в стиле обычного ответа. Но добавь в конце <:iconUSAGI1:884140804510203944>'
            },
            *context
        ]
        response_status, _, reply = await self.chat_gpt.generate_answer(
            context, 'gpt-5-mini', tools
        )

        return response_status, reply

    async def _set_reminder(self, message: discord.Message, time: int, text: str) -> str:
        """Create new remind for user"""
        now = datetime.now( )
        date = now + timedelta(seconds=time)
        await UsagiAIReminder.create(
            guild_id=message.guild.id,
            channel_id=message.channel.id,
            user_id=message.author.id,
            text=text,
            date=date
        )
        self.bot.logger.info(f'Set reminder to {date} for {time} seconds')
        return f'Поставила таймер на {time} сек.'

    async def _clear_memory(self, message: discord.Message) -> str:
        """Clear history and facts for user"""
        await UsagiAIFacts.delete(guild_id=message.guild.id, user_id=message.author.id)

        memory_list = await UsagiAIMemory.get_all_by(user_id=message.author.id)
        memory_ids = [memory.id for memory in memory_list]
        await UsagiAIMemory.delete_all(memory_ids)

        self.bot.logger.info(f'Clear memory for {message.author.name}')
        return f'Очистила память о тебе.'


def setup(bot):
    bot.add_cog(OpenAICog(bot))
