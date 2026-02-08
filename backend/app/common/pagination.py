def normalize_pagination(skip: int, limit: int, max_limit: int = 100) -> tuple[int, int]:
    safe_skip = max(0, skip)
    safe_limit = max(1, min(limit, max_limit))
    return safe_skip, safe_limit
