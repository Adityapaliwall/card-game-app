import random
from .deck import Card, shuffle_deck
from .deck52 import build_full_deck, card_strength_52

BASE_BID = 7
MAX_BID = 13
LOSING_SCORE = 52  # first team to reach this LOSES

# Fixed partnerships: player "1" and "3" are a team, "2" and "4" are a team
TEAMS = {
    "1": "team_A", "3": "team_A",
    "2": "team_B", "4": "team_B",
}


def deal_all_13(players: list[str]) -> dict[str, list[Card]]:
    """Shuffles a full 52-card deck and deals 13 cards to each of the
    4 players, all at once (unlike 3-2-5's two-stage deal)."""
    deck = shuffle_deck(build_full_deck())
    hands = {}
    for i, player in enumerate(players):
        hands[player] = deck[i * 13: (i + 1) * 13]
    return hands


def team_of(player: str) -> str:
    """Returns which team a player belongs to."""
    return TEAMS[player]


def is_valid_bid(current_highest_bid: int, proposed_bid: int) -> bool:
    """A bid must be higher than the current highest bid, and no more
    than 13 (you can't bid to win more tricks than exist)."""
    return current_highest_bid < proposed_bid <= MAX_BID


def resolve_trick_52(cards_played: list[Card], trump_suit: str, lead_order: list[str]) -> str:
    """Same idea as resolve_trick() in rules_325.py, but uses Chokri's
    52-card ranking (2 lowest, Ace highest) instead of 3-2-5's ranking.
    """
    led_suit = cards_played[0].suit
    trump_cards = [c for c in cards_played if c.suit == trump_suit]

    if trump_cards:
        winning_card = max(trump_cards, key=lambda c: card_strength_52(c))
    else:
        led_suit_cards = [c for c in cards_played if c.suit == led_suit]
        winning_card = max(led_suit_cards, key=lambda c: card_strength_52(c))

    winning_index = cards_played.index(winning_card)
    return lead_order[winning_index]


def calculate_round_score(bidding_team: str, bid: int, tricks_made_by_bidding_team: int) -> dict:
    """Applies your scoring rule:
    - Bidding team MEETS OR BEATS their bid -> the OPPONENT team gets +bid points
    - Bidding team FAILS their bid -> the BIDDING team gets +(2 x bid) points

    Returns which team's score changes and by how much, e.g.:
    {"team": "team_B", "points": 9}
    """
    opponent_team = "team_B" if bidding_team == "team_A" else "team_A"

    if tricks_made_by_bidding_team >= bid:
        return {"team": opponent_team, "points": bid}
    else:
        return {"team": bidding_team, "points": bid * 2}


def check_game_over(team_scores: dict) -> str | None:
    """Checks if any team has reached the losing score.
    Returns the name of the LOSING team, or None if the game continues."""
    for team, score in team_scores.items():
        if score >= LOSING_SCORE:
            return team
    return None