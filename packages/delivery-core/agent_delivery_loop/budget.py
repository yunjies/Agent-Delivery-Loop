def remaining_tokens(budget):
    limit = int(budget.get("token_limit") or 0)
    used = int(budget.get("token_used_estimate") or 0)
    return max(0, limit - used)


def should_stop_for_budget(budget):
    threshold = int(budget.get("stop_when_remaining_below") or 0)
    return remaining_tokens(budget) < threshold
