import asyncio
import openai_async

from usagiBot.db.models import UsagiAIFacts, UsagiAIMemory
from usagiBot.src.UsagiErrors import OpenAIError
from pycord18n.extension import _


class OpenAIHandler:

    def __init__(self, api_key, bot):
        self._api_key = api_key
        self.bot = bot

        # Default values for gpt model
        self._ai_model = "gpt-5"

    async def get_ai_model(self):
        return self._ai_model

    async def generate_answer(self, messages, model = None, tools = None, counter: int = 0):
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
                #     return 200, message["content"]
                # elif finish_reason == 'tool_calls':
                #     return 200, message


            retry_codes = [500, 429, 502]
            if response.status_code in retry_codes:
                if counter != 20:
                    await asyncio.sleep(2)
                    return await self.generate_answer(messages, model, tools, counter + 1)
                else:
                    return 400, _("Something went wrong")
            else:
                raise OpenAIError(response.json().get('error'), response.status_code)

        except OpenAIError as error_answer:
            return 401, error_answer

        except Exception as e:
            return 402, str(e)

    async def generate_embedding(self, message_input):
        try:
            response = await openai_async.embeddings(
                self._api_key,
                timeout=200,
                payload={
                    "model": "text-embedding-3-small",
                    "input": message_input
                },
            )

            if response.status_code == 200:
                return 200, response.json()['data'][0]['embedding']

            raise OpenAIError(response.json().get('error'), response.status_code)

        except OpenAIError as error_answer:
            return 401, error_answer

        except Exception as e:
            return 402, str(e)

    async def update_fact(self, message, facts):
        ai_facts = await UsagiAIFacts.get(guild_id=message.guild.id, user_id=message.author.id)
        known_facts = '' if ai_facts is None else ai_facts.facts
        context_facts = [
            {"role": "system",
             "content": "Извлеки важные факты о пользователе для будущего общения. Если фактов нет — верни пустую строку. "
                        "Выдели 3-4 главных факта и только"},
            {"role": "system", "content": f"[New messages]: {facts}"},
            {"role": "system", "content": f"[Old facts]: {known_facts}"},
        ]


        response_status, finish_reason, response = await self.generate_answer(context_facts, 'gpt-5-mini')
        if response_status != 200 and finish_reason != 'stop':
            return None

        if ai_facts is None:
            await UsagiAIFacts.create(guild_id=message.guild.id, user_id=message.author.id, facts=response["content"])
        else:
            await UsagiAIFacts.update(id=ai_facts.id, facts=response["content"])

        self.bot.ai_facts_buffer[message.author.id] = []
        return True

    async def search_memory(self, user_id, query):
        response_status, embed_question = await self.generate_embedding(query)
        self.bot.logger.info('Got embed for message')

        if response_status != 200:
            return None

        chat_memory = await UsagiAIMemory.get_memory(user_id, embed_question, 5)
        return '||'.join([
            memory.message
            for memory in chat_memory
        ])

    async def add_memory(self, user_id, question, answer):
        query = f"Question: {question}\nAnswer: {answer}"
        response_status, embed_qa = await self.generate_embedding(query)
        self.bot.logger.info('Got embed for qa')

        if response_status != 200:
            return

        await UsagiAIMemory.create(
            user_id=user_id,
            message=query,
            embedding=embed_qa
        )


tools = [
    {
        'type': 'function',
        'function': {
            'name': 'set_reminder',
            'description': 'Set timer or reminder to ping user after N seconds.',
            "strict": True,
            'parameters': {
                'type': 'object',
                'properties': {
                    'time': {
                        'type': 'integer',
                        'description': 'Time to wait before ping, there is no limit for this parameter.',
                        "minimum": 60
                    },
                    'text': {
                        'type': 'string',
                        'description': 'Message text to send after timer ends',
                    },
                },
                'required': ['time', 'text'],
                "additionalProperties": False
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'clear_memory',
            'description': 'Clear memory and history for user. User can ask about clearing facts or his history',
            "strict": True,
            'parameters': {
                'type': 'object',
                'properties': {},
                'required': [],
                "additionalProperties": False
            },
        },
    }
]