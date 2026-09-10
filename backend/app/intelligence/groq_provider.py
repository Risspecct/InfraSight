import json
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class GroqProvider:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured"
            )

        self.client = Groq(api_key=api_key)

        self.model = os.getenv(
            "GROQ_MODEL",
            "openai/gpt-oss-20b",
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict,
    ) -> dict:

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "infrasight_intelligence",
                    "strict": True,
                    "schema": response_schema,
                },
            },
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError(
                "Groq returned an empty response"
            )

        return json.loads(content)