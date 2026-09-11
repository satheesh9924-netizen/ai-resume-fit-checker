import os

from openai import OpenAI

ABACUS_ROUTELLM_BASE_URL = "https://routellm.abacus.ai/v1"


def create_client() -> OpenAI:
    api_key = os.environ.get("ABACUS_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ABACUS_API_KEY is not set. Get a RouteLLM API key from abacus.ai and export it.")
    return OpenAI(api_key=api_key, base_url=ABACUS_ROUTELLM_BASE_URL)
