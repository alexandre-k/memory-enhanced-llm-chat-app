import argparse
import os
import readline  # enables readline history on most Unix systems
import sys
from .cli import chat_loop
from .user import get_or_create_user_id
# from os import getenv
from dotenv import load_dotenv


load_dotenv()

def main():
    user_id = get_or_create_user_id()
    parser = argparse.ArgumentParser(description="Simple interactive Memory CLI (POST + wait)")
    parser.add_argument(
        "--url",
        default=os.getenv("APP_API_URL", "").strip() or "http://localhost:8000/v1/api",
        help="LLM endpoint URL (OpenAI-compatible default: /v1/chat/completions).",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("LLM_API_KEY"),
        help="API key (or set env LLM_API_KEY). Omit for no-auth endpoints.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("LLM_MODEL", "gpt-4o-mini"),
        help="Model name to send in the payload.",
    )
    parser.add_argument(
        "--system",
        default=os.getenv("LLM_SYSTEM_PROMPT"),
        help="Optional system prompt.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        help="Sampling temperature.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("LLM_TIMEOUT_S", "60")),
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--no-history",
        action="store_true",
        help="Do not keep conversation history (stateless mode).",
    )

    args = parser.parse_args()

    chat_loop(
        api_url=args.url,
        api_key=args.api_key,
        system_prompt=args.system,
        timeout_s=args.timeout,
        user_id=user_id
    )
