import random
import string
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from game.state import GameState
from game.deck import Card

app = FastAPI()

# Allows your React frontend (running on port 5173) to talk to this
# backend (running on port 8000) — browsers block this by default
# unless the server explicitly allows it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ROLE_ORDER = ["dealer", "trump_chooser", "third_player"]


class Room:
    """One game session: its own GameState, plus who's connected and
    which role (dealer/trump_chooser/third_player) each person has."""

    def __init__(self, code: str):
        self.code = code
        self.game = GameState()
        self.connections: dict[str, WebSocket] = {}   # role -> websocket
        self.player_names: dict[str, str] = {}          # role -> display name

    def next_available_role(self):
        """Returns the next open role, or None if all 3 seats are taken."""
        for role in ROLE_ORDER:
            if role not in self.connections:
                return role
        return None


rooms: dict[str, Room] = {}


def generate_room_code() -> str:
    """Makes a random 4-letter code, e.g. 'QXRT', avoiding any code
    already in use."""
    while True:
        code = "".join(random.choices(string.ascii_uppercase, k=4))
        if code not in rooms:
            return code


def card_to_dict(card: Card) -> dict:
    return {"suit": card.suit, "rank": card.rank}


def build_state_message(room: Room) -> dict:
    game = room.game
    return {
        "type": "state_update",
        "phase": game.phase,
        "trump_suit": game.trump_suit,
        "hands": {
            role: [card_to_dict(c) for c in cards]
            for role, cards in game.hands.items()
        },
        "current_trick": [card_to_dict(c) for c in game.current_trick],
        "current_leader": game.current_leader,
        "tricks_won": game.tricks_won,
        "whose_turn": game.whose_turn() if game.phase == "playing" else None,
        "players": room.player_names,  # e.g. {"dealer": "Aditya", "trump_chooser": "Rahul"}
    }


async def broadcast_state(room: Room):
    message = build_state_message(room)
    for websocket in room.connections.values():
        await websocket.send_json(message)


@app.post("/create_room")
def create_room():
    """A normal (non-WebSocket) endpoint. Makes a new empty room and
    returns its code so the frontend can share it with friends."""
    code = generate_room_code()
    rooms[code] = Room(code)
    return {"room_code": code}


@app.websocket("/ws/{room_code}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, player_name: str):
    room_code = room_code.upper()

    if room_code not in rooms:
        await websocket.close(code=4404)  # custom code we invented: "room not found"
        return

    room = rooms[room_code]
    role = room.next_available_role()

    if role is None:
        await websocket.close(code=4403)  # custom code we invented: "room full"
        return

    await websocket.accept()
    room.connections[role] = websocket
    room.player_names[role] = player_name
    print(f"{player_name} joined room {room_code} as {role}")

    # Tell this player which role they were assigned
    await websocket.send_json({"type": "role_assigned", "role": role})

    await broadcast_state(room)

    try:
        while True:
            data = await websocket.receive_json()

            try:
                if data["type"] == "choose_trump":
                    room.game.choose_trump(data["suit"])
                    await broadcast_state(room)

                elif data["type"] == "play_card":
                    card = Card(data["card"]["suit"], data["card"]["rank"])
                    room.game.play_card(role, card)
                    await broadcast_state(room)

            except ValueError as e:
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        print(f"{player_name} disconnected from room {room_code}")
        del room.connections[role]
        del room.player_names[role]