"""
Adaptive Context Intelligence Engine (ACIE)
Ollama Provider
"""

from typing import Generator, Any
from importlib import import_module

from Backend.llm.providers.base_provider import BaseProvider


class OllamaProvider(BaseProvider):

    def __init__(
        self,
        model_name="llama3.2"
    ):

        super().__init__(model_name)

        print()
        print("=" * 60)
        print("Initializing Ollama Provider")
        print("=" * 60)

        try:
            ollama = import_module("ollama")
            self.client = ollama.Client(
                host="http://localhost:11434"
            )
        except ModuleNotFoundError as error:
            raise RuntimeError(
                "The Ollama Python package is required. Install it with: "
                "pip install ollama"
            ) from error

        print("Host          : http://localhost:11434")
        print("Model         :", self.model_name)
        print("=" * 60)
        print()



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

            response = self.client.chat(

                model=self.model_name,

                messages=[

                    {
                        "role": "user",
                        "content": prompt
                    }

                ],

                options={

                    "temperature": temperature,

                    "num_predict": max_tokens

                }

            )


            return {

                "success": True,

                "provider": "Ollama",

                "model": self.model_name,

                "response":
                    response["message"]["content"],

                "usage": {}

            }


        except Exception as e:

            return {

                "success": False,

                "provider": "Ollama",

                "model": self.model_name,

                "response": "",

                "error": str(e)

            }



    # --------------------------------------------------
    # Streaming Response
    # --------------------------------------------------

    def stream(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048
    ) -> Generator[str, None, None]:

        try:

            stream = self.client.chat(

                model=self.model_name,

                messages=[

                    {
                        "role": "user",
                        "content": prompt
                    }

                ],

                stream=True,

                options={

                    "temperature": temperature,

                    "num_predict": max_tokens

                }

            )


            for chunk in stream:

                if "message" in chunk:

                    yield chunk["message"]["content"]


        except Exception as e:

            yield f"[ERROR] {e}"



    # --------------------------------------------------
    # Health Check
    # --------------------------------------------------

    def health_check(self):

        try:

            response = self.client.chat(

                model=self.model_name,

                messages=[

                    {
                        "role": "user",
                        "content": "Reply with only OK."
                    }

                ]

            )


            text = response["message"]["content"]


            healthy = (

                text is not None

                and text.strip().upper().startswith("OK")

            )


            return {

                "status":
                    "healthy" if healthy else "unhealthy",

                "provider":
                    "Ollama",

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
                    "Ollama",

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
                "Ollama",

            "model":
                self.model_name,

            "streaming":
                True,

            "healthy":
                health["available"]

        }