import asyncio
import openai_async

from usagiBot.src.UsagiErrors import OpenAIError


class BaseAI:
    def __init__(self, api_key):
        self._api_key = api_key


class OpenAIHandler(BaseAI):

    def __init__(self, api_key):
        super().__init__(api_key)

        # Default values for gpt model
        self._ai_model = "gpt-3.5-turbo"

    async def get_ai_model(self):
        return self._ai_model

    async def generate_answer(self, question: str, counter: int = 0):
        try:
            response = await openai_async.chat_complete(
                self._api_key,
                timeout=100,
                payload={
                    "model": await self.get_ai_model(),
                    "messages": [{"role": "user", "content": question}],
                },
            )

            if response.status_code == 200:
                json = response.json()
                choices = json.get("choices", None)
                if choices is None:
                    return "Something went wrong, try again."
                return choices[0]["message"]["content"]

            if response.status_code == 500:
                if counter != 10:
                    await asyncio.sleep(2)
                    return await self.generate_answer(question, counter + 1)
                else:
                    return "Something went wrong, try again."
            else:
                raise OpenAIError(response.json().get('error'), response.status_code)

        except OpenAIError as error_answer:
            return error_answer
