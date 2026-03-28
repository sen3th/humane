from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
from typing import List
import time
import random
import sqlite3
import json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://humane-the-game.netlify.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def save_session(session_id: str):
    conn =  sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO sessions (session_id, data) VALUES (?, ?)",
        (session_id, json.dumps(sessions[session_id])),
    )
    conn.commit()
    conn.close()

def load_all_sessions():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT session_id, data FROM sessions")
    rows = cur.fetchall()
    conn.close()
    for session_id, data_json in rows:
        sessions[session_id] = json.loads(data_json)

sessions: Dict[str, dict] = {}

DB_PATH = "humane.db"
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE IF NOT EXISTS sessions(
                session_id TEXT PRIMARY KEY,
                data TEXT NOT NULL
                )
                """)
    conn.commit()
    conn.close()
init_db()
load_all_sessions()

class CreateSessionRequest(BaseModel):
    human_name: str
    bot_count: int = 3
    chat_duration_seconds: int = 60

class CreateSessionResponse(BaseModel):
    session_id: str
    players: list
    phase: str
    chat_seconds_left: int


class JoinRequest(BaseModel):
    name: str
    is_bot: bool = False


class ChatRequest(BaseModel):
    player_id: str
    message: str

class BotTestRequest(BaseModel):
    message: str

class BotTickResponse(BaseModel):
    ok: bool
    message: dict | None = None

def refresh_session_phase(session_id: str) -> None:
    session = sessions[session_id]
    if session["phase"] == "chat" and time.time() >= session.get("chat_ends_at", 0):
        session["phase"] = "voting"
        cast_bot_votes(session)
        save_session(session_id)
def chat_seconds_left(session:dict)->int:
    return max(0, int(session.get("chat_ends_at", 0) - time.time()))
def cast_bot_votes(session:dict) -> None:
    players = session["players"]
    votes = session["votes"]
    bots = [p for p in players if p["is_bot"]]
    all_player_ids = [p["player_id"] for p in players]
    for bot in bots:
        bot_id = bot["player_id"]
        if bot_id in votes:
            continue
        options = [pid for pid in all_player_ids if pid!= bot_id]
        if not options:
            continue
        votes[bot_id] = random.choice(options)
async def get_bot_reply(user_text: str, bot_name: str, bot_style: str = "neutral") -> str:
    api_key = os.getenv("HACKCLUB_API_KEY")
    if not api_key:
        return "bot is missing api key"
    
    url="https://ai.hackclub.com/proxy/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    style_hints = {
        "cautious": "Speak carefully, hedge claims, ask for more proof.",
        "bold": "Make confident accusations and push quick votes.",
        "logical": "Focus on contradictions and evidence.",
        "quiet": "Use brief, minimal words and fewer claims.",
        "aggressive": "Pressure others and demand immediate action.",
    }
    style_hint = style_hints.get(bot_style, "Speak neutral and concise.")

    payload = {
        "model": "qwen/qwen3-32b",
        "messages": [
            {"role": "system", "content": f"You are {bot_name}, a {bot_style} bot in a social deduction game chat. {style_hint} Your only goal is to help bot teammates identify the one human player. Stay inside this game only. Do not mention parasites, sci-fi lore, special roles, or outside stories. Reply in plain text with exactly one sentence, maximum 10 words. Keep it casual, suspicious, and focused on who seems human."},
            {"role":"user","content": user_text},
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            res = await client.post(url, headers=headers, json=payload)
            data= res.json()
            if not res.is_success:
                return "bot errr api"
            return data["choices"][0]["message"]["content"]
    except Exception:
        return "bot error"

@app.post("/bot-test") 
async def bot_test(body: BotTestRequest):
    reply = await get_bot_reply(body.message, bot_name="TestBot", bot_style="neutral")
    return {"reply": reply}

@app.get("/ping")
def ping():
    return {"message": "alive and well!"}

@app.post("/sessions/{session_id}/bot-tick", response_model=BotTickResponse)
async def bot_tick(session_id: str): 
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    refresh_session_phase(session_id)
    if session.get("phase") != "chat":
        return {"ok": False, "message": None}
    
    players=sessions[session_id]["players"]
    bots = [p for p in players if p["is_bot"]]
    if not bots:
        return {"ok":False, "message": None}
    
    idx = sessions[session_id].get("next_bot_index", 0) % len(bots)
    bot = bots[idx]
    sessions[session_id]["next_bot_index"] = (idx + 1) % len(bots)

    latest = sessions[session_id]["messages"][-1]["message"] if sessions[session_id]["messages"] else "Type a message first"
    bot_reply = await get_bot_reply(
        latest,
        bot_name=bot["name"],
        bot_style=bot.get("style", "neutral"),
    )

    bot_msg = {
        "player_id": bot["player_id"],
        "name": bot["name"],
        "message": bot_reply,
    }
    sessions[session_id]["messages"].append(bot_msg)
    save_session(session_id)
    return {"ok": True, "message": bot_msg}

@app.post("/sessions", response_model=CreateSessionResponse)
def create_session(body: CreateSessionRequest):
    session_id = str(uuid4())
    players = []
    duration = max(15, min(body.chat_duration_seconds, 600))

    human_player = {
        "player_id": str(uuid4()),
        "name": body.human_name,
        "is_bot": False
    }
    players.append(human_player)

    bot_names = ["Tom", "Lily", "James", "Emma", "Teddy"]
    bot_styles = ["cautious", "bold", "logical", "quiet", "aggressive"]
    count = max(1, min(body.bot_count, 5))
    for i in range (count):
        players.append({
            "player_id": str(uuid4()),
            "name": bot_names[i % len(bot_names)],
            "is_bot": True,
            "style": bot_styles[i % len(bot_styles)],
        })
    sessions[session_id] = {
            "next_bot_index": 0,
            "players": players,
            "messages": [],
            "votes": {},
            "phase":"chat",
            "chat_ends_at": time.time()+duration
        }
    save_session(session_id)
    return{
            "session_id": session_id,
            "players": players,
            "phase": "chat",
            "chat_seconds_left": duration
        }

@app.post("/sessions/{session_id}/join")
def join_session(session_id: str, body: JoinRequest):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    player_id = str(uuid4())
    player = {
        "player_id": player_id,
        "name": body.name,
        "is_bot": body.is_bot,
    }
    sessions[session_id]["players"].append(player)
    save_session(session_id)
    return player


@app.post("/sessions/{session_id}/chat")
async def send_chat(session_id: str, body: ChatRequest):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session=sessions[session_id]
    refresh_session_phase(session_id)
    if session.get("phase") != "chat":
        raise HTTPException(status_code= 400, detail="voting in progress, chat closed")

    players = sessions[session_id]["players"]
    sender = next((p for p in players if p["player_id"] == body.player_id), None)
    if sender is None:
        raise HTTPException(status_code=404, detail="Player not found")

    msg = {
        "player_id": body.player_id,
        "name": sender["name"],
        "message": body.message,
    }
    sessions[session_id]["messages"].append(msg)
    save_session(session_id)
    return msg
class VoteRequest(BaseModel):
    voter_id: str
    suspect_id: str

@app.post("/sessions/{session_id}/vote")
def submit_vote(session_id: str, body: VoteRequest):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = sessions[session_id]
    refresh_session_phase(session_id)
    if session.get("phase") != "voting":
        raise HTTPException(status_code=400, detail="Voting hasn't started yet")

    players=sessions[session_id]["players"]
    player_ids={p["player_id"] for p in players}
    if body.voter_id not in player_ids:
        raise HTTPException(status_code=404, detail="Voter not found")
    if body.suspect_id not in player_ids:
        raise HTTPException(status_code=404, detail="Suspect not found") 
    
    sessions[session_id]["votes"][body.voter_id] = body.suspect_id
    save_session(session_id)
    return{"ok": True}

@app.get("/sessions/{session_id}/reveal")
def reveal(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    data = sessions[session_id]
    players = data["players"]
    votes = data["votes"]
    humans = [p for p in players if not p["is_bot"]]
    human_player=humans[0] if humans else None
    human_id = human_player["player_id"] if human_player else None

    tally = {}
    for suspect_id in votes.values():
        tally[suspect_id] = tally.get(suspect_id, 0) + 1
    most_voted_id = max(tally, key=tally.get) if tally else None

    if most_voted_id is None:
        playerOutcome = "unknown"
    elif human_id is not None and most_voted_id == human_id:
        playerOutcome= "lose"
    else:
        playerOutcome = "win"

    return {
        "human_player": human_player,
        "vote_tally": tally,
        "most_voted_id": most_voted_id,
        "playerOutcome": playerOutcome,
        "all_messages": data["messages"]
    }
    
@app.get("/sessions/{session_id}/state")
def session_state(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code = 404, detail="Session not found")
    session = sessions[session_id]
    refresh_session_phase(session_id)
    return {
        "phase": session["phase"],
        "chat_seconds_left": chat_seconds_left(session),
    }