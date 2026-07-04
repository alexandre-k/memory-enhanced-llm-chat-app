import asyncio
import uuid
import json
from contextlib import asynccontextmanager
from json.decoder import JSONDecodeError
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from .chat import LlmChat
from .environment import supabase_key, supabase_url
from .memory import Memory
from .logger import log

app = FastAPI()

templates = Jinja2Templates(directory="templates")


def get_or_create_session_id(request: Request, response: Response) -> str:
    session_id = request.cookies.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        # simple cookie; in production set secure/httpOnly/samesite properly
        response.set_cookie("session_id", session_id, max_age=3600 * 24)
    return session_id


# @app.get("/", response_class=HTMLResponse)
# async def index(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.memory = Memory()          # init once
    app.state.memory_lock = asyncio.Lock()  # optional: protects shared Memory if needed
    yield
    # optional cleanup here

app = FastAPI(lifespan=lifespan)

@app.get("/v1/api/health")
def check_health():
    log.info("It works!")
    return JSONResponse(
        status_code=200,
        content={"status": "ok"},
        media_type="application/json"
    )

@app.post("/v1/api/chat")
async def chat(request: Request, response: Response):
    """
    Body:
      { "content": "..." }
    Returns:
      { "reply": "..." }
    """
    try:
        data = await request.json()
        content = (data.get("content") or "").strip()
        user_id = data.get("user_id")
        log.debug(f"Request from client: {request.client}")
        metadata = {
            "host": request.client.host,
            "port": request.client.port,
            "user-agent": request.headers["user-agent"]
        }
        log.debug(f"metadata: {metadata}")
    except JSONDecodeError:
        content = None
        user_id = None
        metadata = {}
    if not content:
        return {"reply": "Please ask something as content to process."}

    llm = LlmChat()
    memory = app.state.memory
    memories = await memory.recall(user_id, content)
    # Schedule and DO NOT await
    log.info("Start memory pipeline")
    asyncio.create_task(memory_pipeline(content, user_id, metadata))
    log.debug(f"Send message: {content}")
    # print("Replace sleep to simulate expensive work.")
    # print(f"Send message: {content}")
    # await asyncio.sleep(1)  # <-- was blocking sleep(1)

    prompt = llm.generate_message(memories)
    prompt_with_memories = prompt.format(user_message=content)
    # reply = llm.send_message(prompt_with_memories)
    # print(f"Respond with reply: {reply}")
    # return {"reply": reply}

    async def sse_generator():
        # Stream each token from Qwen as a Server-Sent Event
        async for chunk in llm.send_message_stream(prompt_with_memories):
            yield f"data: {chunk}\n\n"
        # Optional: send a close marker so the client knows the stream ended
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
    )


async def memory_pipeline(content, user_id, metadata):
    memory = app.state.memory
    try:
        llm = LlmChat()
        response = await llm.send_message(Memory.EXTRACTION_PROMPT.format(text=content))
        extracted_memories = await asyncio.to_thread(
            memory.extract_memories, response
        )
        if extracted_memories:
            # DB work (also sync) -> thread
            try:
                assert supabase_url
                assert supabase_key
                log.info(f"Extracted memories: {extracted_memories}")
                await memory.save_memories(user_id, extracted_memories, metadata)
            except (EnvironmentError, AssertionError) as err:
                log.error(f"Missing database URL/API key: {err}")
                raise

    except Exception as e:
        # Important: never crash the request due to memory pipeline
        log.error("Memory pipeline failed:", repr(e))