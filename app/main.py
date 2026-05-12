from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import os
from app.engine import analyze_vulnerabilities, generate_immunefi_markdown

app = FastAPI(title="RainSoul258Studios Infinity 02")
app.mount("/assets", StaticFiles(directory="public"), name="assets")

log_queue: asyncio.Queue[str] = asyncio.Queue()
redis_client = None
REDIS_URL = os.environ.get("REDIS_URL")

try:
    import redis.asyncio as aioredis
    if REDIS_URL:
        redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
except ImportError:
    redis_client = None


async def broadcast(message: str) -> None:
    await log_queue.put(message)
    if redis_client:
        try:
            await redis_client.lpush("rain_soul_logs", message)
        except Exception:
            pass


@app.get("/radar")
async def radar():
    await broadcast("Radar ping: loading bug bounty programs")
    return {
        "programs": [
            {
                "name": "Immunefi Ultra",
                "reward_range": "5k-500k USD",
                "scope": "Ethereum & Layer 2 smart contracts",
            },
            {
                "name": "RainSoul Audit Grid",
                "reward_range": "2k-150k USD",
                "scope": "DeFi protocol core functions",
            },
            {
                "name": "Neon Fortify",
                "reward_range": "1k-100k USD",
                "scope": "Access control and token bridges",
            },
        ]
    }


@app.post("/audit")
async def audit(payload: dict):
    code = payload.get("code", "")
    if not code.strip():
        await broadcast("Audit failed: no Solidity source code received.")
        return JSONResponse({"error": "Solidity source code is required."}, status_code=400)

    await broadcast("Audit started: parsing Solidity payload")
    report = analyze_vulnerabilities(code)
    markdown = generate_immunefi_markdown(report)
    await broadcast("Audit complete: report generated")

    if redis_client:
        try:
            await redis_client.set("rain_soul_latest_report", markdown)
        except Exception:
            pass

    return {
        "report": report,
        "report_markdown": markdown,
    }


@app.get("/logs")
async def logs():
    async def event_generator():
        while True:
            message = await log_queue.get()
            yield f"data: {message}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/")
async def home():
    index_path = Path("public/index.html")
    if index_path.exists():
        return FileResponse(index_path)
    return {"status": "frontend missing"}
