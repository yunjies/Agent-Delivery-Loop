from __future__ import annotations


COST_SCORE = {
    "free": 20,
    "low": 15,
    "medium": 8,
    "high": 2,
}

RELIABILITY_SCORE = {
    "high": 20,
    "medium": 10,
    "low": 3,
}


def score_expert(task, expert):
    required = set(task.get("spec", {}).get("required_capabilities", []))
    objective = str(task.get("spec", {}).get("objective", "")).lower()
    capabilities = expert.get("spec", {}).get("capabilities", [])
    best = 0
    reasons = []
    for cap in capabilities:
        cap_id = str(cap.get("id", ""))
        description = str(cap.get("description", "")).lower()
        score = int(cap.get("priority") or 0)
        if required and cap_id in required:
            score += 50
            reasons.append(f"required:{cap_id}")
        if cap_id and cap_id.replace("_", " ") in objective:
            score += 15
        if description and any(word in objective for word in description.split()):
            score += 5
        score += COST_SCORE.get(cap.get("cost_class"), 0)
        score += RELIABILITY_SCORE.get(cap.get("reliability"), 0)
        if cap.get("default_owner"):
            score += 10
        best = max(best, score)
    return {"expert_id": expert.get("metadata", {}).get("id"), "score": best, "reasons": reasons}


def rank_experts(task, experts):
    scored = [score_expert(task, expert) for expert in experts]
    return sorted(scored, key=lambda item: (-item["score"], item["expert_id"] or ""))
