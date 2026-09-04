import asyncio
import websockets
import json

async def test_connection():
    uri = "ws://127.0.0.1:8000/ws/trump_chooser"
    async with websockets.connect(uri) as websocket:
        print("Connected as trump_chooser!")

        message = await websocket.recv()
        data = json.loads(message)
        print("\nInitial state received. Phase:", data["phase"])

        print("\nSending choose_trump: Hearts...")
        await websocket.send(json.dumps({
            "type": "choose_trump",
            "suit": "Hearts"
        }))

        updated_message = await websocket.recv()
        updated_data = json.loads(updated_message)
        print("Phase:", updated_data["phase"])
        print("Trump suit:", updated_data["trump_suit"])

        # Grab trump_chooser's first card to play (they lead first)
        first_card = updated_data["hands"]["trump_chooser"][0]
        print(f"\nSending play_card: {first_card}")
        await websocket.send(json.dumps({
            "type": "play_card",
            "card": first_card
        }))

        played_message = await websocket.recv()
        played_data = json.loads(played_message)
        print("\nState after playing a card:")
        print("Current trick:", played_data["current_trick"])
        print("Trump_chooser's hand size:", len(played_data["hands"]["trump_chooser"]))

asyncio.run(test_connection())