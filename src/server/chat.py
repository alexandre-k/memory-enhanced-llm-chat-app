import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from .memory import MemoryCategory
from .logger import log


load_dotenv()


LLM_API_URL = os.environ.get("LLM_API_URL", "").strip() or "http://localhost:8000/v1/chat/completions"
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_SYSTEM_PROMPT = os.environ.get("LLM_SYSTEM_PROMPT", "")
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.7"))
LLM_TIMEOUT_S = float(os.environ.get("LLM_TIMEOUT_S", "60"))


class LlmChat:

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=LLM_API_KEY,  # or "sk-xxx"
            base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
            timeout=LLM_TIMEOUT_S,
        )

    def generate_message(self, memories):
        log.debug(f"memories: {memories}")
        if len(memories) > 0:
            user_prompt = f"""You are a helpful assistant with memory of past conversations. Use the settings or context naturally if relevant; don't mention you're using memories.
"""
            settings_block =  "\n".join(f"- {mem['content']}" for mem in memories if mem["category"] == MemoryCategory.SETTING or mem["category"] == MemoryCategory.PREFERENCE)
            user_prompt += f"""
User settings (always apply these):
{settings_block}
"""
            memory_block =  "\n".join(f"- {mem['content']}" for mem in memories if not (mem["category"] == MemoryCategory.SETTING or mem["category"] == MemoryCategory.PREFERENCE))
            user_prompt += f"""Other relevant context:
{memory_block}
"""
        else:
            user_prompt = """You are a helpful assistant.
"""
        user_prompt += """Answer the following message:
{user_message}
"""
        return user_prompt

    async def send_message_stream(self, content: str):
        log.debug(f"Send message: {content}")
        stream = await self.client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": content}],
            stream=True,
        )
        async with stream:          # ensures the HTTP response is closed properly
            async for chunk in stream:
                delta = (
                    chunk.choices[0].delta.content
                    if chunk.choices and chunk.choices[0].delta
                    else None
                )
                if delta is not None:
                    yield delta

    async def send_message(self, content: str) -> str:
        parts = []
        async for chunk in self.send_message_stream(content):
            parts.append(chunk)
        return "".join(parts)

    # @staticmethod
    # def get_message(response):
    #     # Parse SSE chunks as they arrive
    #     for line in response.iter_lines():
    #         print(f"line << {line}")
    #         if not line:
    #             continue

    #         decoded = line.decode('utf-8')

    #         # SSE lines start with "data: "
    #         if decoded.startswith('data: '):
    #             data = decoded[6:]

    #             if data == '[DONE]':
    #                 break  # End of stream

    #             try:
    #                 chunk = json.loads(data)
    #                 output = chunk.get('output', {})
    #                 choices = output.get('choices', [])

    #                 if choices:
    #                     delta = choices[0].get('message', {}).get('content', '')
    #                     print(delta, end='', flush=True)

    #             except json.JSONDecodeError:
    #                 continue

    # def send_message(self, content: str):

    #     base_messages: List[Dict[str, str]] = []
    #     if LLM_SYSTEM_PROMPT:
    #         base_messages.append({"role": "system", "content": LLM_SYSTEM_PROMPT})

    #     messages = base_messages + [{"role": "user", "content": content}]

    #     payload = LlmChat.build_payload(model=LLM_MODEL, messages=messages, temperature=LLM_TEMPERATURE)

    #     headers = {"Content-Type": "application/json"}
    #     if LLM_API_KEY:
    #         headers["Authorization"] = f"Bearer {LLM_API_KEY}"

    #     try:
    #         url = f"{LLM_API_URL}/chat/completions"
    #         print(f"Send payload: {payload}")
    #         r = requests.post(url, headers=headers, json=payload, timeout=LLM_TIMEOUT_S)
    #         r.raise_for_status()
    #         print("R <<< ", r)
    #         message = LlmChat.get_message(r)
    #         print(r.json())
    #     except requests.RequestException as e:
    #         return {"reply": f"[LLM request error] {e}"}

    #     return message
    #     # try:
    #     #     # resp_json = r.json()
    #     #     resp_json = message
    #     # except ValueError:
    #     #     return {"reply": f"[Non-JSON response] {r.text[:1000]}"}

    #     # print(f"Json response: {resp_json}")
    #     # return LlmChat.extract_reply(resp_json)

    # @staticmethod
    # def extract_reply(resp_json: Dict[str, Any]) -> str:
    #     # OpenAI-compatible format:
    #     # { "choices": [ { "message": { "content": "..." } } ] }
    #     try:
    #         choices = resp_json.get("choices") or []
    #         if not choices:
    #             return (
    #                 resp_json.get("output_text")
    #                 or resp_json.get("text")
    #                 or resp_json.get("message")
    #                 or str(resp_json)
    #             )
    #         msg = choices[0].get("message") or {}
    #         content = msg.get("content")
    #         if content is not None:
    #             return content

    #         text = choices[0].get("text")
    #         if text is not None:
    #             return text

    #         return str(resp_json)
    #     except Exception:
    #         return str(resp_json)


    # @staticmethod
    # def build_payload(model: str, messages: List[Dict[str, str]], temperature: float) -> Dict[str, Any]:
    #     return {
    #         "model": model,
    #         "messages": messages,
    #         "temperature": temperature,
    #     }
