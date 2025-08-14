from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import hmac
import hashlib
import time
import json
import os
import requests
from typing import Optional
from .generator import Generator

import sys
import logging

logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

# 로그 파일 설정
file_handler = logging.FileHandler("app.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class SlackBot:
    def __init__(self, env: dict):
        self.signing_secret = env["SLACK_SIGNING_SECRET"]
        self.bot_token = env["SLACK_BOT_TOKEN"]
        self.generator = Generator(env)

    def verify_request(self, timestamp: str, signature: str, body: bytes) -> bool:
        try:
            # 타임스탬프 검증 (너무 오래된 요청 차단)
            if abs(time.time() - int(timestamp)) > 60 * 5:
                print("⚠️ Request timestamp too old. Ignoring request.")
                return False

            sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
            my_signature = "v0=" + hmac.new(
                self.signing_secret.encode(),
                sig_basestring.encode(),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(my_signature, signature):
                print(f"⚠️ Signature mismatch! Expected: {my_signature}, Received: {signature}")
                return False

            print("✅ Signature verified successfully.")
            return True
        except Exception as e:
            print(f"❌ Error verifying request: {str(e)}")
            return False

    async def send_message(self, channel_id: str, message: str, thread_ts: Optional[str] = None):
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "channel": channel_id,
            "text": message,
            "thread_ts": thread_ts
        }



        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to send message: {str(e)}")
            return None

    async def handle_message(self, event: dict):
        """Handle incoming message events"""
        # Ignore bot messages to prevent loops
        if event.get("bot_id"):
            return

        channel_id = event["channel"]
        thread_ts = event.get("thread_ts", event.get("ts"))
        question = event["text"]

        # Get answer using Generator
        try:
            answer = self.generator.get_answer(question)
            await self.send_message(channel_id, answer, thread_ts)
        except Exception as e:
            error_msg = f"Error processing your request: {str(e)}"
            await self.send_message(channel_id, error_msg, thread_ts)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
slack_bot: Optional[SlackBot] = None

@app.on_event("startup")
async def startup_event():
    """Initialize SlackBot on startup"""
    from main import load_env  # Reference to main.py lines 9-27
    global slack_bot
    env = load_env()
    slack_bot = SlackBot(env)

@app.post("/slack/events")
async def slack_events(request: Request):
    body = await request.body()
    data = json.loads(body)

    if data.get("type") == "url_verification":
        return JSONResponse(content={"challenge": data["challenge"]})
    elif "challenge" in data:
        return JSONResponse(content={"challenge": data["challenge"]})

    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")
    retry_num = request.headers.get("X-Slack-Retry-Num", "0")

    print(f"🔄 Received Slack request. Retry Num: {retry_num}")

    # 요청 검증
    if not slack_bot.verify_request(timestamp, signature, body):
        print("❌ Invalid request. Ignoring...")
        raise HTTPException(status_code=403, detail="Invalid request")

    # Slack의 재시도 요청 방지 (첫 번째 요청만 처리)
    if retry_num != "0":
        print("🔄 Slack retry request detected. Ignoring...")
        return JSONResponse(content={"status": "ignored"}, status_code=200)

    # 이벤트 비동기 처리
    if data.get("type") == "event_callback":
        event = data.get("event", {})
        if event.get("type") == "message":
            asyncio.create_task(slack_bot.handle_message(event))

    return JSONResponse(content={"status": "ok"}, status_code=200)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Slack Bot"}

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}


@app.post("/")
async def root_post(request: Request):
    return {"message": "POST request received"}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"📩 Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"📤 Response status: {response.status_code}")
    return response