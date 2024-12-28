import random

QUOTES: list[str] = [
    '"hello bro" - anonymous',
    '"isdifsjdfo" - osidjo',
    '"u bum" - lebron'
]


def get_quote(*args) -> str:
    return random.choice(QUOTES)
