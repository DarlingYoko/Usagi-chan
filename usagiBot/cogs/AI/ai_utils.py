import time

import openai_async


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

    async def generate_answer(self, question):
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
                answer = response.json()["choices"][0]["message"]["content"]
                return answer

            if response.status_code == 500:
                time.sleep(2)
                return await self.generate_answer(question)
            else:
                raise OpenAIError(response.json().get('error'), response.status_code)

        except OpenAIError as error_answer:
            return error_answer


class OpenAIError(Exception):
    def __init__(self, error, status_code):
        self.status_code = status_code
        self.message = error.get("message")
        self.type = error.get("type")

    def __str__(self):
        return f"""
                Status Code: {self.status_code}
                Error message: {self.message}.
                Error type: {self.type}.
                """
