"""
Adaptive Context Intelligence Engine (ACIE)
Model Registry
"""


class ModelRegistry:

    def __init__(self):

        self.models = {

            # ==========================================
            # Google
            # ==========================================

            "gemini": {

                "provider": "Google",

                "model_name": "gemini-3.5-flash-lite",

                "capabilities": [

                    "chat",

                    "reasoning",

                    "vision",

                    "coding",

                    "multimodal"

                ],

                "available": True

            },

            # ==========================================
            # OpenAI
            # ==========================================

            "gpt": {

                "provider": "OpenAI",

                "model_name": "gpt-5",

                "capabilities": [

                    "chat",

                    "reasoning",

                    "coding",

                    "tools"

                ],

                "available": False

            },

            # ==========================================
            # Anthropic
            # ==========================================

            "claude": {

                "provider": "Anthropic",

                "model_name": "claude-sonnet-4",

                "capabilities": [

                    "research",

                    "reasoning",

                    "long_context"

                ],

                "available": False

            },

            # ==========================================
            # Groq
            # ==========================================

            "groq": {

                "provider": "Groq",

                "model_name": "llama-3.3-70b-versatile",

                "capabilities": [

                    "fast",

                    "chat"

                ],

                "available": True

            },

            # ==========================================
            # Ollama
            # ==========================================

            "ollama": {

                "provider": "Ollama",

                "model_name": "llama3.2",

                "capabilities": [

                    "offline",

                    "chat"

                ],

                "available": True

            },

            # ==========================================
            # DeepSeek
            # ==========================================

            "deepseek": {

                "provider": "DeepSeek",

                "model_name": "deepseek-r1",

                "capabilities": [

                    "math",

                    "reasoning",

                    "coding"

                ],

                "available": False

            }

        }

    # -------------------------------------------------
    # Get Model
    # -------------------------------------------------

    def get_model(

        self,

        name

    ):

        return self.models.get(

            name.lower()

        )

    # -------------------------------------------------
    # Register Model
    # -------------------------------------------------

    def register_model(

        self,

        key,

        provider,

        model_name,

        capabilities,

        available=False

    ):

        self.models[key.lower()] = {

            "provider": provider,

            "model_name": model_name,

            "capabilities": capabilities,

            "available": available

        }

    # -------------------------------------------------
    # Available Models
    # -------------------------------------------------

    def available_models(self):

        return [

            key

            for key, value in self.models.items()

            if value["available"]

        ]

    # -------------------------------------------------
    # All Models
    # -------------------------------------------------

    def all_models(self):

        return self.models


if __name__ == "__main__":

    registry = ModelRegistry()

    print()

    print("Available Models")

    print("----------------")

    print(

        registry.available_models()

    )

    print()

    print("Gemini")

    print("-------")

    print(

        registry.get_model(

            "gemini"

        )

    )

    print()

    print("All Registered Models")

    print("---------------------")

    print(

        registry.all_models()

    )
