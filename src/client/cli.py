import json
from typing import List, Dict, Any, Optional

import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.spinner import Spinner

def build_payload(
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
) -> Dict[str, Any]:
    # OpenAI-compatible payload shape
    return {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }


def extract_reply(resp_json: Dict[str, Any]) -> str:
    # OpenAI-compatible reply extraction:
    # resp_json["choices"][0]["message"]["content"]
    try:
        choices = resp_json.get("choices") or []
        if not choices:
            # Some APIs might return different keys; try common fallbacks
            return (
                resp_json.get("output_text")
                or resp_json.get("text")
                or resp_json.get("message")
                or json.dumps(resp_json, ensure_ascii=False)
            )
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        if content is not None:
            return content
        # fallback if the provider uses "text"
        text = choices[0].get("text")
        if text is not None:
            return text
        return json.dumps(resp_json, ensure_ascii=False)
    except Exception:
        return json.dumps(resp_json, ensure_ascii=False)


def chat_loop(
    api_url: str,
    api_key: Optional[str],
    system_prompt: Optional[str],
    timeout_s: float,
    user_id: str
):
    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    base_messages: List[Dict[str, str]] = []
    if system_prompt:
        base_messages.append({"role": "system", "content": system_prompt})

    prompt_counter = 0
    console = Console()
    print("LLM CLI ready. Type '/quit' or press Ctrl-D to exit.")
    while True:
        try:
            user_text = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_text:
            continue
        if user_text.lower() in {"/quit", "/exit"}:
            print("Exiting.")
            break

        prompt_counter += 1

        reply_so_far = ""

        spinner = Spinner("dots", text="Thinking...")  # or Spinner("line", ...)
        try:
            with Live(spinner, refresh_per_second=12, console=console) as live:
                r = requests.post(
                    f"{api_url}/chat",
                    headers=headers,
                    json={"content": user_text, "user_id": user_id},
                    timeout=timeout_s,
                    stream=True,
                )
                r.raise_for_status()
                # 3) Parse SSE: each line looks like "data: <chunk>"
                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue  # blank line between SSE events

                    if line.startswith("data: "):
                        chunk = line[6:]

                        # End-of-stream marker sent by the server
                        if chunk == "[DONE]":
                            break

                        reply_so_far += chunk

                        # 4) Replace spinner with accumulating Markdown
                        live.update(Markdown(reply_so_far))

        except requests.RequestException as e:
            # spinner stops automatically when leaving the with-block
            print(f"[HTTP error] {e}")
            continue
        except KeyboardInterrupt:
            print("\nInterrupted.")
            continue

        # reply = extract_reply(resp_json)

        # Print the full object nicely
        # console.print_json(json.dumps(resp_json))
        print()  # newline before next prompt
