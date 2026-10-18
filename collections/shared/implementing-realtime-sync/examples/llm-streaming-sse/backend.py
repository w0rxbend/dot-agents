"""
FastAPI SSE server for streaming LLM responses.

Supports both OpenAI and Anthropic APIs.
"""

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

app = FastAPI(title="LLM Streaming SSE Server")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=False,  # browsers reject credentials with a wildcard origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# Choose LLM provider based on available API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
# Model names change often: set them in .env instead of editing code
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")


def sse(event: str, data) -> str:
    """Format one SSE event. JSON-encoding the payload keeps newlines inside
    tokens from ending the event early (a raw newline would split `data:`)."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"

if OPENAI_API_KEY:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    PROVIDER = "openai"

elif ANTHROPIC_API_KEY:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    PROVIDER = "anthropic"

else:
    # Mock mode for testing without API keys
    client = None
    PROVIDER = "mock"


@app.get("/")
async def root():
    """Serve frontend HTML."""
    with open("frontend.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/chat/stream")
async def stream_chat(
    prompt: str = Query(..., description="User prompt to send to LLM")
):
    """
    Stream LLM response tokens via Server-Sent Events (SSE).

    Returns:
        StreamingResponse with text/event-stream content type

    Events:
        - token: Individual token from LLM
        - done: Streaming complete
        - error: Error occurred
    """

    async def generate():
        try:
            if PROVIDER == "openai":
                # OpenAI streaming
                stream = await client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    stream=True,
                    max_tokens=1024
                )

                async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content

                        yield sse("token", content)

            elif PROVIDER == "anthropic":
                # Anthropic streaming
                async with client.messages.stream(
                    model=ANTHROPIC_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024
                ) as stream:
                    async for text in stream.text_stream:
                        yield sse("token", text)

            else:
                # Mock mode - simulate streaming
                mock_response = f"This is a mock response to: {prompt}. "
                mock_response += "In production, this would stream from OpenAI or Anthropic. "
                mock_response += "Add your API key to .env to test real streaming."

                for token in mock_response.split():
                    yield sse("token", token + " ")
                    await asyncio.sleep(0.05)  # Simulate streaming delay

            # Done signal
            yield sse("done", "[DONE]")

        except Exception as e:
            # Error event
            yield sse("error", str(e))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "provider": PROVIDER,
        "has_api_key": OPENAI_API_KEY is not None or ANTHROPIC_API_KEY is not None
    }


if __name__ == "__main__":
    import uvicorn

    print(f"🚀 Starting SSE server with {PROVIDER.upper()} provider...")
    print(f"📡 Visit http://localhost:8000 to test")

    uvicorn.run(
        app,
        host="127.0.0.1",  # use 0.0.0.0 only when you mean to expose it
        port=8000,
        log_level="info"
    )
