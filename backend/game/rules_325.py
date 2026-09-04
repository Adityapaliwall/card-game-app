from .deck import Card, build_deck, shuffle_deck

# Each player's trick quota, based on their position
# (dealer = 2, trump-chooser = 5, third player = 3)
QUOTAS = {
    "dealer": 2,
    "trump_chooser": 5,
    "third_player": 3,
}


def deal_first_batch() -> tuple[list[Card], dict[str, list[Card]]]:
    """Shuffles a fresh deck and deals the FIRST 5 cards to each player.
    Returns (remaining_deck, hands) where hands only has 5 cards each so far.
    The trump_chooser looks at their 5 cards and announces trump before
    anyone gets the rest.
    """
    deck = shuffle_deck(build_deck())

    hands = {
        "dealer": deck[0:5],
        "trump_chooser": deck[5:10],
        "third_player": deck[10:15],
    }

    remaining_deck = deck[15:]  # 15 cards left, not yet dealt
    return remaining_deck, hands


def deal_remaining_batch(remaining_deck: list[Card], hands: dict[str, list[Card]]) -> dict[str, list[Card]]:
    """Deals the last 5 cards to each player, AFTER trump has been chosen.
    Takes the leftover deck and partial hands from deal_first_batch(),
    returns the completed 10-card hands.
    """
    hands["dealer"] += remaining_deck[0:5]
    hands["trump_chooser"] += remaining_deck[5:10]
    hands["third_player"] += remaining_deck[10:15]
    return hands


def is_valid_move(hand: list[Card], card_to_play: Card, trick_so_far: list[Card]) -> bool:
    """Checks if playing `card_to_play` is legal.

    Rule: if this player has any card of the suit that was led, they MUST
    play a card of that suit. If they have none of that suit, they can play
    anything (including a trump).

    `hand` = the player's current cards
    `card_to_play` = the card they're trying to play
    `trick_so_far` = cards already played this trick (empty list if leading)
    """
    # Card must actually be in hand
    if card_to_play not in hand:
        return False

    # If this is the first card of the trick, any card is fine
    if len(trick_so_far) == 0:
        return True

    led_suit = trick_so_far[0].suit

    # Does the player have any card of the suit that was led?
    has_led_suit = any(c.suit == led_suit for c in hand)

    if has_led_suit:
        # Must follow suit
        return card_to_play.suit == led_suit
    else:
        # No card of that suit — any card is legal
        return True


def resolve_trick(cards_played: list[Card], trump_suit: str, lead_order: list[str]) -> str:
    """Decides who wins a trick.

    `cards_played` = list of Cards, in the order they were played
    `trump_suit` = the trump suit for this hand
    `lead_order` = list of player names in the same order as cards_played
                   (so cards_played[i] was played by lead_order[i])

    Returns the name of the winning player.
    """
    led_suit = cards_played[0].suit

    # Find all cards that are trumps
    trump_cards = [c for c in cards_played if c.suit == trump_suit]

    if trump_cards:
        # Highest trump wins
        winning_card = max(trump_cards, key=lambda c: c.strength())
    else:
        # No trumps played — highest card of the suit led wins
        led_suit_cards = [c for c in cards_played if c.suit == led_suit]
        winning_card = max(led_suit_cards, key=lambda c: c.strength())

    winning_index = cards_played.index(winning_card)
    return lead_order[winning_index]


def check_quota(tricks_won: int, position: str) -> bool:
    """Checks if a player met their quota.
    `position` must be one of: 'dealer', 'trump_chooser', 'third_player'
    """
    return tricks_won >= QUOTAS[position]