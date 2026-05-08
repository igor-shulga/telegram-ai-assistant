from collections import defaultdict, deque

# Зберігає останні N повідомлень на user_id
HISTORY_LIMIT = 10
_store: dict[int, deque] = defaultdict(lambda: deque(maxlen=HISTORY_LIMIT))

def add_message(user_id: int, role: str, content: str) -> None:
    _store[user_id].append({"role": role, "content": content})

def get_history(user_id: int) -> list[dict]:
    return list(_store[user_id])

def clear_history(user_id: int) -> None:
    _store[user_id].clear()
