import random
import string
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from game.state import GameState
from game.deck import Card
from game.rules_325 import is_valid_move, QUOTAS
from game.chokri_state import ChokriGameState
from game.chokri_rules import team_of

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://card-game-app-gamma.vercel.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

ROLE_ORDER = ["dealer", "trump_chooser", "third_player"]
CHOKRI_ROLE_ORDER = ["1", "2", "3", "4"]


class Room:
    """One game session. Supports either game_type: '325' or 'chokri'."""

    def __init__(self, code: str, game_type: str = "325"):
        self.code = code
        self.game_type = game_type

        if game_type == "chokri":
            self.role_order = CHOKRI_ROLE_ORDER
            self.game = None  # created once the 4th player joins
        else:
            self.role_order = ROLE_ORDER
            self.game = GameState()

        self.connections: dict[str, WebSocket] = {}
        self.player_names: dict[str, str] = {}

    def next_available_role(self):
        for role in self.role_order:
            if role not in self.connections:
                return role
        return None

    def is_full(self):
        return len(self.connections) == len(self.role_order)


rooms: dict[str, Room] = {}


def generate_room_code() -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase, k=4))
        if code not in rooms:
            return code


def card_to_dict(card: Card) -> dict:
    return {"suit": card.suit, "rank": card.rank}


def build_state_message_325(room: Room) -> dict:
    game = room.game
    message = {
        "type": "state_update",
        "game_type": "325",
        "phase": game.phase,
        "trump_suit": game.trump_suit,
        "hands": {
            role: [card_to_dict(c) for c in cards]
            for role, cards in game.hands.items()
        },
        "current_trick": [card_to_dict(c) for c in game.current_trick],
        "current_leader": game.current_leader,
        "tricks_won": game.tricks_won,
        "quotas": QUOTAS,
        "whose_turn": game.whose_turn() if game.phase == "playing" else None,
        "players": room.player_names,
    }
    if game.phase == "hand_complete":
        message["quota_results"] = game.quota_results()
    return message


def build_state_message_chokri(room: Room) -> dict:
    game = room.game

    if game is None:
        # Not all 4 players have joined yet
        return {
            "type": "state_update",
            "game_type": "chokri",
            "phase": "waiting_for_players",
            "players": room.player_names,
            "seats_filled": len(room.connections),
        }

    message = {
        "type": "state_update",
        "game_type": "chokri",
        "phase": game.phase,
        "dealer": game.dealer,
        "trump_suit": game.trump_suit,
        "hands": {
            seat: [card_to_dict(c) for c in cards]
            for seat, cards in game.hands.items()
        },
        "current_trick": [card_to_dict(c) for c in game.current_trick],
        "current_leader": game.current_leader,
        "tricks_won": game.tricks_won,
        "team_scores": game.team_scores,
        "current_bid": game.current_bid,
        "highest_bidder": game.highest_bidder,
        "whose_bid_turn": game.whose_bid_turn() if game.phase == "bidding" else None,
        "whose_turn": game.whose_turn() if game.phase == "playing" else None,
        "players": room.player_names,
    }

    if game.phase in ("hand_complete", "game_over"):
        message["last_round_result"] = getattr(game, "last_round_result", None)

    if game.phase == "game_over":
        message["losing_team"] = game.losing_team

    return message


def build_state_message(room: Room) -> dict:
    if room.game_type == "chokri":
        return build_state_message_chokri(room)
    return build_state_message_325(room)


async def broadcast_state(room: Room):
    message = build_state_message(room)
    for websocket in room.connections.values():
        await websocket.send_json(message)


@app.post("/create_room")
def create_room(game_type: str = "325"):
    code = generate_room_code()
    rooms[code] = Room(code, game_type)
    return {"room_code": code, "game_type": game_type}


@app.websocket("/ws/{room_code}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, room_code: str, player_name: str):
    room_code = room_code.upper()

    if room_code not in rooms:
        await websocket.close(code=4404)
        return

    room = rooms[room_code]
    role = room.next_available_role()

    if role is None:
        await websocket.close(code=4403)
        return

    await websocket.accept()
    room.connections[role] = websocket
    room.player_names[role] = player_name
    print(f"{player_name} joined room {room_code} as {role}")

    await websocket.send_json({"type": "role_assigned", "role": role})

    # For Chokri: once the 4th player joins, actually start the game
    if room.game_type == "chokri" and room.game is None and room.is_full():
        room.game = ChokriGameState(dealer="1")
        print(f"Chokri game started in room {room_code}")

    await broadcast_state(room)

    try:
        while True:
            data = await websocket.receive_json()

            try:
                if room.game_type == "chokri":
                    await handle_chokri_action(room, role, data)
                else:
                    await handle_325_action(room, role, data)

            except ValueError as e:
                await websocket.send_json({"type": "error", "message": str(e)})

    except WebSocketDisconnect:
        print(f"{player_name} disconnected from room {room_code}")
        del room.connections[role]
        del room.player_names[role]


async def handle_325_action(room: Room, role: str, data: dict):
    if data["type"] == "choose_trump":
        room.game.choose_trump(data["suit"])
        await broadcast_state(room)

    elif data["type"] == "play_card":
        card = Card(data["card"]["suit"], data["card"]["rank"])
        room.game.play_card(role, card)
        await broadcast_state(room)

        if room.game.is_trick_full():
            await asyncio.sleep(1.5)
            room.game.resolve_current_trick()
            await broadcast_state(room)


async def handle_chokri_action(room: Room, role: str, data: dict):
    game = room.game
    if game is None:
        raise ValueError("Game hasn't started yet — waiting for all 4 players.")

    if data["type"] == "submit_bid":
        if data.get("pass_turn"):
            game.submit_bid(role, pass_turn=True)
        else:
            game.submit_bid(role, bid=data["bid"])
        await broadcast_state(room)

    elif data["type"] == "choose_trump":
        game.choose_trump(role, data["suit"])
        await broadcast_state(room)

    elif data["type"] == "play_card":
        card = Card(data["card"]["suit"], data["card"]["rank"])
        game.play_card(role, card)
        await broadcast_state(room)

        if game.is_trick_full():
            await asyncio.sleep(1.5)
            game.resolve_current_trick()
            await broadcast_state(room)

    elif data["type"] == "start_next_hand":
        game.start_next_hand()
        await broadcast_state(room)