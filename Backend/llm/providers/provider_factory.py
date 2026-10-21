"""
Adaptive Context Intelligence Engine (ACIE)

Provider Factory
"""

from Backend.llm.providers.gemini_provider import GeminiProvider
from Backend.llm.providers.groq_provider import GroqProvider
from Backend.llm.providers.ollama_provider import OllamaProvider


class ProviderFactory:

    @staticmethod
    def create(model="gemini"):

        model = model.lower().strip()


        # ---------------------------------
        # Gemini Models
        # ---------------------------------

        gemini_models = [

            "gemini",

            "gemini-flash-latest",

            "gemini-2.5-flash",

            "gemini-2.5-flash-lite",

            "gemini-pro"

        ]


        if model in gemini_models:

            return GeminiProvider(
                model_name="gemini-3.5-flash-lite"
            )



        # ---------------------------------
        # Groq Models
        # ---------------------------------

        groq_models = [

            "groq",

            "llama-3.3-70b-versatile",

            "llama-3.1-8b-instant",

            "mixtral-8x7b-32768"

        ]


        if model in groq_models:

            return GroqProvider(
                model_name="llama-3.3-70b-versatile"
            )



        # ---------------------------------
        # Ollama Models
        # ---------------------------------

        ollama_models = [

            "ollama",

            "llama3",

            "llama3:latest",

            "llama3.2",

            "mistral",

            "phi3",

            "gemma"

        ]


        if model in ollama_models:

            return OllamaProvider(
                model_name="llama3.2"
            )



        # ---------------------------------
        # Unsupported Model
        # ---------------------------------

        raise ValueError(
            f"Unsupported model : {model}"
        )
