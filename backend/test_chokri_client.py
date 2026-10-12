import asyncio
import websockets
import json
import urllib.request

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000"


def create_chokri_room():
    """Plain HTTP POST to /create_room, asking for a Chokri room."""
    req = urllib.request.Request(f"{BASE_URL}/create_room?game_type=chokri", method="POST")
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())
    return data["room_code"]


def pick_legal_card(hand, trick_so_far):
    """Follows suit if possible, otherwise plays the first card in hand."""
    if not trick_so_far:
        return hand[0]
    led_suit = trick_so_far[0]["suit"]
    for card in hand:
        if card["suit"] == led_suit:
            return card
    return hand[0]


async def player_task(name, room_code, results):
    """One simulated player: connects, then automatically bids, chooses
    trump, and plays cards whenever it's their turn."""
    uri = f"{WS_URL}/ws/{room_code}/{name}"
    async with websockets.connect(uri) as ws:
        my_seat = None

        while True:
            message = await ws.recv()
            data = json.loads(message)

            if data["type"] == "role_assigned":
                my_seat = data["role"]
                print(f"{name} assigned seat {my_seat}")
                continue

            if data["type"] == "error":
                print(f"{name} got ERROR: {data['message']}")
                continue

            phase = data.get("phase")

            if phase == "waiting_for_players":
                continue

            elif phase == "bidding":
                if data.get("whose_bid_turn") == my_seat:
                    if data["current_bid"] == 0:
                        await ws.send(json.dumps({"type": "submit_bid", "bid": 8}))
                        print(f"{name} (seat {my_seat}) bids 8")
                    else:
                        await ws.send(json.dumps({"type": "submit_bid", "pass_turn": True}))
                        print(f"{name} (seat {my_seat}) passes")

            elif phase == "choosing_trump":
                if data.get("highest_bidder") == my_seat:
                    await ws.send(json.dumps({"type": "choose_trump", "suit": "Spades"}))
                    print(f"{name} (seat {my_seat}) chooses trump: Spades")

            elif phase == "playing":
                if data.get("whose_turn") == my_seat:
                    hand = data["hands"][my_seat]
                    card = pick_legal_card(hand, data["current_trick"])
                    print(f"{name} (seat {my_seat}) plays {card['rank']} of {card['suit']}")
                    await ws.send(json.dumps({"type": "play_card", "card": card}))

            elif phase in ("hand_complete", "game_over"):
                results["final_state"] = data
                print(f"{name} sees phase: {phase}")
                return


async def main():
    room_code = create_chokri_room()
    print(f"Created Chokri room: {room_code}\n")

    results = {}
    names = ["Aditya", "Bhavik", "Akshay", "Rahul"]
    tasks = [player_task(name, room_code, results) for name in names]

    await asyncio.wait_for(asyncio.gather(*tasks), timeout=90)

    final = results.get("final_state")
    if final:
        print("\n--- FINAL STATE ---")
        print("Phase:", final["phase"])
        print("Dealer:", final["dealer"])
        print("Trump:", final["trump_suit"])
        print("Tricks won:", final["tricks_won"])
        print("Team scores:", final["team_scores"])
        print("Last round result:", final.get("last_round_result"))


asyncio.run(main())