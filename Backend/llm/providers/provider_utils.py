"""
Adaptive Context Intelligence Engine (ACIE)
Provider Utilities
"""

import os
from pathlib import Path

from dotenv import load_dotenv


# -------------------------------------------------
# Load .env
# -------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILES = (
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "Backend" / ".env",
)

# Support both the repository-level configuration and the Backend/.env file
# used by this project. Existing process variables keep precedence.
for ENV_FILE in ENV_FILES:
    if ENV_FILE.is_file():
        load_dotenv(ENV_FILE)


# -------------------------------------------------
# Get API Key
# -------------------------------------------------

def get_api_key(key_name: str) -> str:

    api_key = os.getenv(key_name)

    if api_key is None:
        raise ValueError(
            f"{key_name} not found in .env"
        )

    api_key = api_key.strip()

    if api_key == "":
        raise ValueError(
            f"{key_name} is empty."
        )

    return api_key


# -------------------------------------------------
# Safe Response Text
# -------------------------------------------------

def get_response_text(response):

    if response is None:
        return ""

    if hasattr(response, "text"):
        return response.text

    return str(response)


# -------------------------------------------------
# Safe Usage Metadata
# -------------------------------------------------

def get_usage(response):

    usage = {}

    metadata = getattr(
        response,
        "usage_metadata",
        None
    )

    if metadata:

        usage = {

            "prompt_tokens":
            getattr(
                metadata,
                "prompt_token_count",
                None
            ),

            "completion_tokens":
            getattr(
                metadata,
                "candidates_token_count",
                None
            ),

            "total_tokens":
            getattr(
                metadata,
                "total_token_count",
                None
            )

        }

    return usage


# -------------------------------------------------
# Pretty Banner
# -------------------------------------------------

def print_provider_banner(provider_name):

    print()
    print("=" * 60)
    print(f"Initializing {provider_name} Provider")
    print("=" * 60)
