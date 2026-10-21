"""
Adaptive Context Intelligence Engine (ACIE)
Gemini Provider
"""

import os
import importlib
from pathlib import Path
from typing import Any

# Load dotenv dynamically so environments without the optional package can
# still import this provider.
try:
    load_dotenv = importlib.import_module("dotenv").load_dotenv
except ImportError:
    def load_dotenv(*args: Any, **kwargs: Any) -> None:
        return None

# Import dynamically so static analyzers do not fail when the optional SDK
# is installed in a different environment or exposes ``google.genai`` as a
# namespace package.
genai = importlib.import_module("google.genai")

from Backend.llm.providers.base_provider import BaseProvider


# --------------------------------------------------
# Load .env from project root
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]
for env_file in (ROOT / ".env", ROOT / "Backend" / ".env"):
    if env_file.is_file():
        load_dotenv(env_file)


class GeminiProvider(BaseProvider):

    def __init__(self, model_name="gemini-3.5-flash-lite"):

        super().__init__(model_name)

        api_key = os.getenv("GEMINI_API_KEY")

        print("\n" + "=" * 60)
        print("Initializing Gemini Provider")
        print("=" * 60)
        print("API Key Found:", bool(api_key and api_key.strip()))

        print("=" * 60 + "\n")

        if api_key is None:
            raise ValueError("GEMINI_API_KEY is None")

        if api_key.strip() == "":
            raise ValueError("GEMINI_API_KEY is empty")

        self.client = genai.Client(
            api_key=api_key
        )

    # --------------------------------------------------
    # Generate Response
    # --------------------------------------------------

    def generate(
        self,
        prompt,
        temperature=0.3,
        max_tokens=2048
    ) -> Any:

        # Use Flash-Lite by default. If it is temporarily unavailable, retry
        # once on Google's current Flash alias.
        models_to_try = [self.model_name]
        if self.model_name == "gemini-3.5-flash-lite":
            models_to_try.append("gemini-flash-latest")

        last_error = None
        for model_name in models_to_try:
            try:
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens
                    }
                )

                metadata = getattr(response, "usage_metadata", None)
                usage = {
                    "prompt_tokens": getattr(metadata, "prompt_token_count", None),
                    "completion_tokens": getattr(metadata, "candidates_token_count", None),
                    "total_tokens": getattr(metadata, "total_token_count", None)
                } if metadata else {}

                return {
                    "success": True,
                    "provider": "Gemini",
                    "model": model_name,
                    "response": response.text,
                    "usage": usage
                }

            except Exception as exc:
                last_error = exc
                error_text = str(exc).upper()
                transient = any(
                    marker in error_text
                    for marker in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED")
                )
                if not transient:
                    break

        return {
            "success": False,
            "provider": "Gemini",
            "model": self.model_name,
            "response": "",
            "error": str(last_error) if last_error else "Gemini request failed"
        }

    # --------------------------------------------------
    # Streaming
    # --------------------------------------------------

    def stream(
        self,
        prompt,
        temperature=0.3,
        max_tokens=2048
    ) -> Any:

        try:

            stream = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens
                }
            )

            for chunk in stream:

                if hasattr(chunk, "text"):
                    yield chunk.text

        except Exception as e:

            yield f"[ERROR] {e}"

    # --------------------------------------------------
# Health Check
# --------------------------------------------------

def health_check(self):

    try:

        response = self.client.models.generate_content(

            model=self.model_name,

            contents="Reply only with OK."

        )

        text = getattr(response, "text", "")

        healthy = (

            text is not None

            and text.strip().upper().startswith("OK")

        )

        return {

            "status": "healthy" if healthy else "unhealthy",

            "provider": "Gemini",

            "model": self.model_name,

            "available": healthy

        }


    except Exception as e:

        return {

            "status": "unhealthy",

            "provider": "Gemini",

            "model": self.model_name,

            "available": False,

            "error": str(e)

        }
