from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
from uuid import uuid4
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, dict] = {}


class CreateSessionResponse(BaseModel):
    session_id: str


class JoinRequest(BaseModel):
    name: str
    is_bot: bool = False


class ChatRequest(BaseModel):
    player_id: str
    message: str


@app.get("/ping")
def ping():
    return {"message": "alive and well!"}


@app.post("/sessions", response_model=CreateSessionResponse)
def create_session():
    session_id = str(uuid4())
    sessions[session_id] = {
        "players": [],
        "messages": [],
        "votes": {}
    }
    return {"session_id": session_id}


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
    return player


@app.post("/sessions/{session_id}/chat")
def send_chat(session_id: str, body: ChatRequest):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

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
    return msg
class VoteRequest(BaseModel):
    voter_id: str
    suspect_id: str

@app.post("/sessions/{session_id}/vote")
def submit_vote(session_id: str, body: VoteRequest):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    players=sessions[session_id]["players"]
    player_ids={p["player_id"] for p in players}
    if body.voter_id not in player_ids:
        raise HTTPException(status_code=404, detail="Voter not found")
    if body.suspect_id not in player_ids:
        raise HTTPException(status_code=404, detail="Suspect not found")
    
    sessions[session_id]["votes"][body.voter_id] = body.suspect_id
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

    tally = {}
    for suspect_id in votes.values():
        tally[suspect_id] = tally.get(suspect_id, 0) + 1
    most_voted_id = max(tally, key=tally.get) if tally else None

    return {
        "human_player": human_player,
        "vote_tally": tally,
        "most_voted_id": most_voted_id,
        "all_messages": data["messages"]
    }
    