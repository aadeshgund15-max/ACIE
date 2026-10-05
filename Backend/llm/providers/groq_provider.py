"""
Adaptive Context Intelligence Engine (ACIE)
Groq Provider
"""

from importlib import import_module
from typing import Any


from Backend.llm.providers.base_provider import BaseProvider
from Backend.llm.providers.provider_utils import (
    get_api_key,
    print_provider_banner
)


class GroqProvider(BaseProvider):

    def __init__(
        self,
        model_name="llama-3.3-70b-versatile"
    ):

        super().__init__(model_name)

        print_provider_banner("Groq")

        api_key = get_api_key("GROQ_API_KEY")

        print("API Key Found :", True)
        print("Key Prefix    :", api_key[:10] + "...")
        print("=" * 60)
        print()

        groq_module = import_module("groq")
        self.client = groq_module.Groq(
            api_key=api_key
        )

        self.last_response = None
        

    # --------------------------------------------------
    # Generate Response
    # --------------------------------------------------

    

    def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048
    ) -> dict[str, Any]:

        try:

            response = self.client.chat.completions.create(

                model=self.model_name,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=temperature,

                max_tokens=max_tokens

            )

            usage = {}

            if response.usage:

                usage = {

                    "prompt_tokens":
                        response.usage.prompt_tokens,

                    "completion_tokens":
                        response.usage.completion_tokens,

                    "total_tokens":
                        response.usage.total_tokens

                }

            self.last_response = {

                "success": True,

                "provider": "Groq",

                "model": self.model_name,

                "response":
                    response.choices[0].message.content,

                "usage": usage

            }


        except Exception as e:

            self.last_response = {

                "success": False,

                "provider": "Groq",

                "model": self.model_name,

                "response": "",

                "error": str(e)

            }

        return self.last_response

    # --------------------------------------------------
    # Streaming Response
    # --------------------------------------------------

    def stream(  # type: ignore[override]

        self,

        prompt: str,

        temperature: float = 0.3,

        max_tokens: int = 2048

    ):

        try:

            stream = self.client.chat.completions.create(

                model=self.model_name,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=temperature,

                max_tokens=max_tokens,

                stream=True

            )

            for chunk in stream:

                if (
                    chunk.choices
                    and chunk.choices[0].delta.content
                ):

                    yield chunk.choices[0].delta.content

        except Exception as e:

            yield f"[ERROR] {e}"

   # --------------------------------------------------
# Health Check
# --------------------------------------------------

def health_check(self):

    try:

        response = self.client.chat.completions.create(

            model=self.model_name,

            messages=[
                {
                    "role": "user",
                    "content": "Reply with only the word OK."
                }
            ],

            temperature=0,

            max_tokens=5

        )


        text = response.choices[0].message.content


        healthy = (

            text is not None

            and text.strip().upper().startswith("OK")

        )


        return {

            "status":
                "healthy" if healthy else "unhealthy",

            "provider":
                "Groq",

            "model":
                self.model_name,

            "available":
                healthy

        }


    except Exception as e:


        return {

            "status":
                "unhealthy",

            "provider":
                "Groq",

            "model":
                self.model_name,

            "available":
                False,

            "error":
                str(e)

        }

    # --------------------------------------------------
# Provider Information
# --------------------------------------------------

def info(self):

    health = self.health_check()


    return {

        "provider":
            "Groq",

        "model":
            self.model_name,

        "streaming":
            True,

        "healthy":
            health["available"]

    }