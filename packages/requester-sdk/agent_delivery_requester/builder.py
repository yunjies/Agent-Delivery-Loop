from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha1


MINIMUM_FIELDS = ["objective", "scope", "success_criteria", "constraints", "budget_or_deadline"]

LIFT_KEYWORDS = {
    "long_running": ["持续", "长期", "每天", "每周", "定期", "跟踪", "后续", "循环", "cron", "loop", "多轮"],
    "interdependent": ["专家", "profile", "workflow", "codex", "飞书", "wiki", "审批", "通知", "分发", "路由"],
    "feedback_driven": ["验收", "确认", "审批", "返工", "先", "再", "计划", "不要直接", "汇报"],
    "traceable": ["证据", "报告", "记录", "状态", "进度", "清单", "归档", "可追踪", "audit"],
}

FIELD_KEYWORDS = {
    "scope": ["wiki", "mind palace", "mind-palace", "飞书", "模型", "workflow", "cron", "目录", "项目", "repo"],
    "success_criteria": ["完成", "输出", "报告", "清单", "计划", "验收", "修复", "通过"],
    "constraints": ["不要", "不能", "只", "先", "禁止", "不允许", "read-only", "只读", "默认"],
    "budget_or_deadline": ["今天", "明天", "本周", "小时", "分钟", "预算", "优先级", "尽快", "deadline"],
}


def create_demand(title, request, requester, success_criteria=None, budget=None, permissions=None):
    demand_id = _stable_id("demand", title, request, requester.get("id", ""))
    return {
        "apiVersion": "agent.delivery.loop/v0",
        "kind": "Demand",
        "metadata": {
            "id": demand_id,
            "title": title,
            "created_at": _now(),
        },
        "spec": {
            "requester": dict(requester),
            "request": request,
            "success_criteria": list(success_criteria or []),
            "budget": dict(budget or {}),
            "permissions": dict(permissions or {}),
        },
    }


def create_goal_from_demand(demand, objective=None):
    title = demand["metadata"]["title"]
    goal_id = _stable_id("goal", demand["metadata"]["id"], title)
    spec = demand["spec"]
    return {
        "apiVersion": "agent.delivery.loop/v0",
        "kind": "Goal",
        "metadata": {
            "id": goal_id,
            "title": title,
            "created_at": _now(),
            "demand_id": demand["metadata"]["id"],
        },
        "spec": {
            "requester": dict(spec["requester"]),
            "objective": objective or spec["request"],
            "success_criteria": list(spec.get("success_criteria") or []),
            "risk_boundary": dict(spec.get("permissions") or {}),
            "budget": dict(spec.get("budget") or {}),
            "state": {
                "status": "active",
                "current_task_ids": [],
                "completed_task_ids": [],
                "blocked_reason": None,
            },
        },
    }


def classify_intake(raw_request, requester, source="direct", preferred_expert=None, extracted=None):
    text = " ".join(str(part or "") for part in [raw_request, preferred_expert]).strip()
    lift = _assess_lift(text)
    minimum_fields = _assess_minimum_fields(text, extracted or {})
    missing_fields = [field for field, present in minimum_fields.items() if not present]
    classification, recommended_path = _classify(lift["score"], missing_fields)
    assessment_id = _stable_id("intake", raw_request, requester.get("id", ""), source)
    title = _title_from_request(raw_request)
    questions = _clarifying_questions(missing_fields)
    return {
        "apiVersion": "agent.delivery.loop/v0",
        "kind": "IntakeAssessment",
        "metadata": {
            "id": assessment_id,
            "title": title,
            "created_at": _now(),
        },
        "spec": {
            "requester": dict(requester),
            "raw_request": raw_request,
            "source": source,
            "classification": classification,
            "lift": lift,
            "minimum_fields": minimum_fields,
            "missing_fields": missing_fields,
            "clarifying_questions": questions,
            "recommended_path": recommended_path,
            "preferred_expert": preferred_expert,
            "extracted": dict(extracted or {}),
        },
    }


def promote_intake_to_demand(assessment, title=None, success_criteria=None, budget=None, permissions=None):
    if assessment["spec"]["classification"] != "loop_candidate":
        raise ValueError(f"intake is not loop_candidate: {assessment['spec']['classification']}")
    extracted = assessment["spec"].get("extracted") or {}
    criteria = success_criteria if success_criteria is not None else extracted.get("success_criteria")
    if isinstance(criteria, str):
        criteria = [criteria]
    return create_demand(
        title=title or assessment["metadata"].get("title") or "Delegated task",
        request=assessment["spec"]["raw_request"],
        requester=assessment["spec"]["requester"],
        success_criteria=criteria or [],
        budget=budget or _budget_from_extracted(extracted),
        permissions=permissions or _permissions_from_intake(assessment),
    )


def _stable_id(prefix, *parts):
    digest = sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _assess_lift(text):
    lowered = text.lower()
    flags = {}
    reasons = []
    for key, keywords in LIFT_KEYWORDS.items():
        matched = [keyword for keyword in keywords if keyword.lower() in lowered]
        flags[key] = bool(matched)
        if matched:
            reasons.append(f"{key}:{matched[0]}")
    score = sum(1 for value in flags.values() if value)
    return {**flags, "score": score, "reasons": reasons}


def _assess_minimum_fields(text, extracted):
    lowered = text.lower()
    fields = {
        "objective": bool(text.strip()) or bool(extracted.get("objective")),
        "scope": bool(extracted.get("scope")) or _contains_any(lowered, FIELD_KEYWORDS["scope"]),
        "success_criteria": bool(extracted.get("success_criteria")) or _contains_any(lowered, FIELD_KEYWORDS["success_criteria"]),
        "constraints": bool(extracted.get("constraints")) or _contains_any(lowered, FIELD_KEYWORDS["constraints"]),
        "budget_or_deadline": bool(extracted.get("budget_or_deadline")) or _contains_any(lowered, FIELD_KEYWORDS["budget_or_deadline"]),
    }
    return fields


def _classify(lift_score, missing_fields):
    if lift_score < 2:
        return "simple_prompt", "normal_prompt"
    if missing_fields:
        return "needs_clarification", "clarify"
    return "loop_candidate", "create_loop"


def _clarifying_questions(missing_fields):
    prompts = {
        "objective": "What outcome should the loop deliver?",
        "scope": "What scope or target should the loop operate on?",
        "success_criteria": "How should the supervisor decide the work is complete?",
        "constraints": "What should the loop avoid or keep read-only?",
        "budget_or_deadline": "What deadline, priority, or budget should constrain the loop?",
    }
    return [prompts[field] for field in missing_fields if field in prompts]


def _title_from_request(raw_request):
    compact = " ".join(raw_request.split())
    return compact[:60] if compact else "Delegated task"


def _contains_any(text, keywords):
    return any(keyword.lower() in text for keyword in keywords)


def _budget_from_extracted(extracted):
    value = extracted.get("budget_or_deadline")
    return {"note": value} if value else {}


def _permissions_from_extracted(extracted):
    constraints = " ".join(str(item) for item in _as_list(extracted.get("constraints"))).lower()
    if any(marker in constraints for marker in ["不要直接写回", "不写回", "只读", "read-only"]):
        return {"docs_write": False}
    return {}


def _permissions_from_intake(assessment):
    extracted = assessment["spec"].get("extracted") or {}
    permissions = _permissions_from_extracted(extracted)
    raw_request = assessment["spec"].get("raw_request", "").lower()
    if any(marker in raw_request for marker in ["不要直接写回", "不写回", "只读", "read-only"]):
        permissions["docs_write"] = False
    return permissions


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
