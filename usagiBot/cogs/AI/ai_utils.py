import asyncio
import openai_async
import time

from usagiBot.db.models import UsagiAIFacts, UsagiAIMemory
from usagiBot.src.UsagiErrors import OpenAIError
from pycord18n.extension import _
from collections import deque


class OpenAIHandler:
    def __init__(self, api_key, bot):
        self._api_key = api_key
        self.bot = bot
        self.logger = bot.logger

        # Default values for gpt model
        self._ai_model = "gpt-5"

    async def get_ai_model(self):
        return self._ai_model

    async def generate_answer(self, messages, model=None, tools=None, counter: int = 0):
        if tools is None:
            tools = []
        if model is None:
            model = await self.get_ai_model()
        try:
            response = await openai_async.chat_complete(
                self._api_key,
                timeout=200,
                payload={
                    "model": model,
                    "messages": messages,
                    "tools": tools,
                },
            )

            if response.status_code == 200:
                response = response.json()["choices"][0]
                finish_reason = response["finish_reason"]
                message = response["message"]
                return 200, finish_reason, message

                # if finish_reason == 'stop':
                #     return 200, message['content']
                # elif finish_reason == 'tool_calls':
                #     return 200, message

            retry_codes = [500, 429, 502]
            if response.status_code in retry_codes:
                if counter != 20:
                    await asyncio.sleep(2)
                    return await self.generate_answer(
                        messages, model, tools, counter + 1
                    )
                else:
                    return 400, _("Something went wrong")
            else:
                raise OpenAIError(response.json().get("error"), response.status_code)

        except OpenAIError as error_answer:
            return 401, error_answer

        except Exception as e:
            return 402, str(e)

    async def generate_embedding(self, message_input):
        try:
            response = await openai_async.embeddings(
                self._api_key,
                timeout=200,
                payload={"model": "text-embedding-3-small", "input": message_input},
            )

            if response.status_code == 200:
                return 200, response.json()["data"][0]["embedding"]

            raise OpenAIError(response.json().get("error"), response.status_code)

        except OpenAIError as error_answer:
            return 401, error_answer

        except Exception as e:
            return 402, str(e)

    async def update_fact(self, message, facts):
        ai_facts = await UsagiAIFacts.get(
            guild_id=message.guild.id, user_id=message.author.id
        )
        known_facts = "" if ai_facts is None else ai_facts.facts
        context_facts = [
            {
                "role": "system",
                "content": "Извлеки важные факты о пользователе для будущего общения. Если фактов нет — верни пустую строку. "
                "Выдели 3-4 главных факта и только",
            },
            {"role": "system", "content": f"[New messages]: {facts}"},
            {"role": "system", "content": f"[Old facts]: {known_facts}"},
        ]

        response_status, finish_reason, response = await self.generate_answer(
            context_facts, "gpt-5-mini"
        )
        if response_status != 200 and finish_reason != "stop":
            return None

        if ai_facts is None:
            await UsagiAIFacts.create(
                guild_id=message.guild.id,
                user_id=message.author.id,
                facts=response["content"],
            )
        else:
            await UsagiAIFacts.update(id=ai_facts.id, facts=response["content"])

        self.bot.ai_facts_buffer[message.author.id] = []
        return True

    async def search_memory(self, guild_id, user_id, query):
        response_status, embed_question = await self.generate_embedding(query)
        self.logger.info("Got embed for message")

        if response_status != 200:
            return None

        chat_memory = await UsagiAIMemory.get_embedding(
            query_vec=embed_question, limit=5, guild_id=guild_id, user_id=user_id
        )
        return "||".join([memory.message for memory in chat_memory])

    async def add_memory(self, message, question, answer, thread_id):
        query = f"[Question][{message.author.name}]: {question}\n[Answer][Usagi-chan]: {answer}"
        response_status, embed_qa = await self.generate_embedding(query)
        self.logger.info("Got embed for qa")

        if response_status != 200:
            return

        await UsagiAIMemory.create(
            guild_id=message.guild.id,
            user_id=message.author.id,
            message=query,
            thread_id=thread_id,
            embedding=embed_qa,
        )


class RateLimiter:
    def __init__(
        self,
        min_interval: float = 10.0,  # minimum interval between messages
        window_size: float = 120.0,  # windows size (sec)
        max_messages: int = 5,  # max messages count in window
        abuse_cooldown: float = 180.0,  # time-out
    ):
        self.min_interval = min_interval
        self.window_size = window_size
        self.max_messages = max_messages
        self.abuse_cooldown = abuse_cooldown

        # save user's history
        self.user_messages: dict[int, deque] = {}
        self.user_last_time: dict[int, float] = {}
        self.user_cooldowns: dict[int, float] = {}

    def check(self, user_id: int) -> tuple[bool, str | None]:
        """Can user send new message
        Return: allowed, reason"""

        now = time.time()

        # Check global time-out
        if user_id in self.user_cooldowns:
            if now < self.user_cooldowns[user_id]:
                remaining = int(self.user_cooldowns[user_id] - now)
                return False, f"⏳ Подожди {remaining} сек. (тайм-аут за спам)"
            else:
                del self.user_cooldowns[user_id]

        # Check minimum interval
        last_time = self.user_last_time.get(user_id, 0)
        if now - last_time < self.min_interval:
            wait = int(self.min_interval - (now - last_time))
            return (
                False,
                f"⌛ Сообщения можно отправлять не чаще, чем раз в {int(self.min_interval)} сек. Подожди {wait} сек.",
            )

        # Check window
        if user_id not in self.user_messages:
            self.user_messages[user_id] = deque()

        # Remove old messages
        while (
            self.user_messages[user_id]
            and now - self.user_messages[user_id][0] > self.window_size
        ):
            self.user_messages[user_id].popleft()

        if len(self.user_messages[user_id]) >= self.max_messages:
            self.user_cooldowns[user_id] = now + self.abuse_cooldown
            return (
                False,
                f"🚫 Слишком много сообщений. Ты получил тайм-аут на {int(self.abuse_cooldown)} сек.",
            )

        # State update
        self.user_messages[user_id].append(now)
        self.user_last_time[user_id] = now

        return True, None


tools = [
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Set timer or reminder to ping user after N seconds.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "time": {
                        "type": "integer",
                        "description": "Time to wait before ping, there is no limit for this parameter.",
                        "minimum": 60,
                    },
                    "text": {
                        "type": "string",
                        "description": "Message text to send after timer ends",
                    },
                },
                "required": ["time", "text"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clear_memory",
            "description": "Clear memory and history for user. User can ask about clearing facts or his history",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_fact",
            "description": "Add new fact about user, if user ask",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "new_fact": {
                        "type": "string",
                        "description": "Text with new fact about user.",
                    },
                },
                "required": ["new_fact"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_prompt",
            "description": "If user ask about setting new prompt for him.",
            "strict": True,
            "parameters": {
                "type": "object",
                "properties": {
                    "new_prompt": {
                        "type": "string",
                        "description": "New prompt for user.",
                    },
                },
                "required": ["new_prompt"],
                "additionalProperties": False,
            },
        },
    },
]
