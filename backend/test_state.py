from game.state import GameState
from game.rules_325 import is_valid_move

def pick_legal_card(hand, trick_so_far):
    """Finds the first card in hand that's actually a legal move."""
    for card in hand:
        if is_valid_move(hand, card, trick_so_far):
            return card
    raise ValueError("No legal card found — this shouldn't happen.")


game = GameState()

print("Phase:", game.phase)
print("First 5 cards each:")
for player, cards in game.hands.items():
    print(f"  {player}: {cards}")

game.choose_trump("Hearts")
print("\nTrump chosen: Hearts")
print("Phase:", game.phase)
print("Full hands after dealing the rest:")
for player, cards in game.hands.items():
    print(f"  {player}: {cards} (total: {len(cards)})")

print("\n--- Playing one trick ---")
for _ in range(3):
    current_player = game.whose_turn()
    hand = game.hands[current_player]
    card_to_play = pick_legal_card(hand, game.current_trick)
    print(f"{current_player} plays {card_to_play}")
    game.play_card(current_player, card_to_play)

print("\nTricks won so far:", game.tricks_won)
print("Next leader:", game.current_leader)