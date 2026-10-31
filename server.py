import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pywebpush import WebPushException, webpush

load_dotenv()

USERNAME = os.getenv("TIKTOK_USERNAME", "dope2000").lstrip("@")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIMS_SUB = os.getenv("VAPID_CLAIMS_SUB", "mailto:admin@example.com")
SUBSCRIPTIONS_FILE = Path(os.getenv("SUBSCRIPTIONS_FILE", "subscriptions.json"))

app = FastAPI(title="DOPE2000 WATCH")
app.mount("/static", StaticFiles(directory="static"), name="static")

state: dict[str, Any] = {
    "username": USERNAME,
    "is_live": False,
    "monitor_ok": False,
    "last_check": None,
    "last_error": "起動待ち",
    "privacy_status": "unknown",
}


def load_subscriptions() -> list[dict]:
    try:
        return json.loads(SUBSCRIPTIONS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_subscriptions(items: list[dict]) -> None:
    SUBSCRIPTIONS_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def send_one(subscription: dict, title: str, body: str, url: str) -> bool:
    if not VAPID_PUBLIC_KEY or not VAPID_PRIVATE_KEY:
        return True
    try:
        webpush(
            subscription_info=subscription,
            data=json.dumps({"title": title, "body": body, "url": url}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CLAIMS_SUB},
        )
        return True
    except WebPushException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in (404, 410):
            return False
        print(f"Push delivery error: {exc}")
        return True


async def push_all(title: str, body: str) -> None:
    url = f"https://www.tiktok.com/@{USERNAME}/live"
    old = load_subscriptions()
    kept = []
    for subscription in old:
        ok = await asyncio.to_thread(send_one, subscription, title, body, url)
        if ok:
            kept.append(subscription)
    save_subscriptions(kept)


async def monitor():
    try:
        from TikTokLive import TikTokLiveClient
        from TikTokLive.events import ConnectEvent, DisconnectEvent
    except Exception as exc:
        state["last_error"] = f"TikTokLiveを読み込めません: {exc}"
        return

    client = TikTokLiveClient(unique_id=f"@{USERNAME}")
    was_live = False

    @client.on(ConnectEvent)
    async def on_connect(event):
        nonlocal was_live
        state.update(is_live=True, monitor_ok=True, last_error=None)
        if not was_live:
            await push_all(
                f"🔴 @{USERNAME} がLIVEを開始した可能性があります",
                "TikTokで配信を確認してください。",
            )
        was_live = True

    @client.on(DisconnectEvent)
    async def on_disconnect(event):
        nonlocal was_live
        state["is_live"] = False
        was_live = False

    while True:
        try:
            state["last_check"] = asyncio.get_running_loop().time()
            if not client.connected:
                await client.start()
            await asyncio.sleep(8)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            state.update(
                is_live=False,
                monitor_ok=False,
                last_error=f"TikTok側の応答を確認できません: {str(exc)[:180]}",
                privacy_status="unknown",
            )
            await asyncio.sleep(30)


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(monitor())


@app.get("/")
async def index():
    return FileResponse("static/index.html")


@app.get("/api/config")
async def config():
    return {"username": USERNAME, "vapidPublicKey": VAPID_PUBLIC_KEY}


@app.get("/api/status")
async def status():
    return {
        "username": USERNAME,
        "is_live": state["is_live"],
        "monitor_ok": state["monitor_ok"],
        "last_error": state["last_error"],
        "privacy_status": "unknown",
        "subscriber_count": len(load_subscriptions()),
        "push_configured": bool(VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY),
    }


@app.post("/api/subscribe")
async def subscribe(request: Request):
    body = await request.json()
    sub = body.get("subscription")
    if not isinstance(sub, dict) or not sub.get("endpoint"):
        raise HTTPException(status_code=400, detail="Invalid subscription")
    items = load_subscriptions()
    if not any(x.get("endpoint") == sub["endpoint"] for x in items):
        items.append(sub)
        save_subscriptions(items)
    return {"ok": True}


@app.post("/api/unsubscribe")
async def unsubscribe(request: Request):
    body = await request.json()
    endpoint = body.get("endpoint", "")
    save_subscriptions([s for s in load_subscriptions() if s.get("endpoint") != endpoint])
    return {"ok": True}


@app.get("/api/health")
async def health():
    return {"ok": True}
