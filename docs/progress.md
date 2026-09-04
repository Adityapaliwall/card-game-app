# Project Progress Log

## Section 0 — Tool Installation
**Date completed:** [today's date]
**What was done:**
- Installed Python 3.11+, VS Code, Python extension, Git, created GitHub account
- Verified with `python --version` and `git --version`

**Next section:** Section 1

---

## Section 1 — Project Folder & File Structure
**Date completed:** [today's date]
**What was built:**
- Created card-game-app/ with backend/, backend/game/, frontend/, docs/
- Created and activated a Python virtual environment inside backend/venv

**What works:**
- Folder structure matches the target layout
- Terminal shows (venv) when inside backend, confirming the environment is active

**What's NOT done yet:**
- No Python packages installed yet (comes in Section 3)
- backend/game/ and frontend/ are still empty — filled in Sections 2 and 4

**Next section:** Section 2 — Core game logic (deck.py, rules_325.py, state.py)

## Section 2 — Core Game Logic
**Date completed:** [today's date]
**What was built:**
- deck.py: 30-card deck (8-Ace all suits + 7H/7S), Card class, shuffle
- rules_325.py: two-phase dealing (5 then 5 after trump), follow-suit validation, trick resolution, quota checking
- state.py: GameState class managing phase (choosing_trump/playing/hand_complete), turn order, play_card()

**What works:**
- Verified deck.py alone: 30 unique cards, shuffles correctly
- Verified rules_325.py alone: deals 5+5 correctly around trump selection
- Verified all three together via state.py: full trick played, follow-suit enforced correctly, trick winner resolved correctly, leader passes to trick winner

**What's NOT done yet:**
- "Pulling cards" (steal mechanic for players who exceed/miss quota) not implemented
- Only tested for 1 trick, not a full 10-trick hand — worth a longer test later, but core logic is proven
- No networking yet — this is all still local/offline logic

**Next section:** Section 3 — FastAPI + WebSocket backend

## Section 3 — FastAPI + WebSocket Backend
**Date completed:** [today's date]
**What was built:**
- backend/main.py: FastAPI app with a WebSocket endpoint (/ws/{player_name})
- Wraps the Section 2 GameState in a live server: connect, receive state, send actions, broadcast updates
- card_to_dict() / build_state_message() convert Card objects to JSON for the frontend
- requirements.txt added (fastapi, uvicorn[standard], websockets)

**What works:**
- Server runs locally via uvicorn main:app --reload
- test_client.py confirms: connecting receives full initial state, sending choose_trump updates
  the real GameState and broadcasts the new state back correctly

**What's NOT done yet:**
- Only ONE hardcoded shared game right now — no real rooms yet (planned for Section 5)
- play_card action not tested yet over WebSocket (only choose_trump tested so far)
- No error handling sent back to client yet (e.g. illegal move currently just crashes the connection)
- No frontend yet — this was tested purely with a Python script

**Next section:** Section 4 — basic React frontend

- play_card also tested over WebSocket: played a real card from the dealt hand, current_trick updated correctly, hand size dropped from 10 to 9

## Section 4 — Frontend Interactivity (COMPLETE)
**What works:**
- Role picker, live WebSocket connection, clickable trump buttons, clickable hand cards
- Turn indicator (whose_turn from backend) — cards only clickable when it's your turn
- Illegal move (breaking follow-suit) now shows a red error message and keeps the
  connection alive, instead of disconnecting — tested live with a real illegal move

**Next section:** Section 5 — Rooms (code already written, now needs the same
level of real testing this section just got)

