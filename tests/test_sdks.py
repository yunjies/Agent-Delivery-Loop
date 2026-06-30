import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "delivery-core"))
sys.path.insert(0, str(ROOT / "packages" / "requester-sdk"))
sys.path.insert(0, str(ROOT / "packages" / "delivery-supervisor-sdk"))
sys.path.insert(0, str(ROOT / "packages" / "expert-adapter-sdk"))

from agent_delivery_expert import create_attempt
from agent_delivery_loop import validate_object
from agent_delivery_requester import classify_intake, create_demand, create_goal_from_demand, promote_intake_to_demand
from agent_delivery_supervisor import create_loop_decision, create_task, propose_next_task, review_attempt


class SdkTests(unittest.TestCase):
    def test_requester_creates_valid_demand_and_goal(self):
        demand = create_demand(
            title="Maintain wiki health",
            request="Keep the wiki healthy",
            requester={"kind": "human", "id": "requester-example"},
            success_criteria=["lint report succeeds"],
            budget={"token_limit": 1000, "token_used_estimate": 0},
            permissions={"docs_write": False},
        )
        goal = create_goal_from_demand(demand)
        self.assertTrue(validate_object(demand))
        self.assertTrue(validate_object(goal))
        self.assertEqual(goal["metadata"]["demand_id"], demand["metadata"]["id"])

    def test_requester_classifies_simple_prompt_outside_loop(self):
        assessment = classify_intake(
            "查一下今天的天气",
            requester={"kind": "human", "id": "requester-example"},
        )
        self.assertTrue(validate_object(assessment))
        self.assertEqual(assessment["spec"]["classification"], "simple_prompt")
        self.assertEqual(assessment["spec"]["recommended_path"], "normal_prompt")

    def test_requester_clarifies_loop_candidate_with_missing_fields(self):
        assessment = classify_intake(
            "持续跟踪 wiki 状态，后续需要汇报和验收",
            requester={"kind": "human", "id": "requester-example"},
            preferred_expert="mind-palace",
        )
        self.assertTrue(validate_object(assessment))
        self.assertEqual(assessment["spec"]["classification"], "needs_clarification")
        self.assertIn("budget_or_deadline", assessment["spec"]["missing_fields"])
        self.assertGreater(len(assessment["spec"]["clarifying_questions"]), 0)

    def test_requester_promotes_complete_loop_intake_to_demand(self):
        assessment = classify_intake(
            "整理 Mind Palace wiki，先巡检再输出修复计划，不要直接写回，今天完成。",
            requester={"kind": "human", "id": "requester-example"},
            preferred_expert="mind-palace",
        )
        self.assertEqual(assessment["spec"]["classification"], "loop_candidate")
        demand = promote_intake_to_demand(assessment)
        goal = create_goal_from_demand(demand)
        self.assertTrue(validate_object(demand))
        self.assertTrue(validate_object(goal))
        self.assertEqual(demand["spec"]["permissions"]["docs_write"], False)

    def test_requester_promotes_complete_english_loop_intake_to_demand(self):
        assessment = classify_intake(
            "Inspect Mind Palace wiki, produce a fix plan, do not write back, finish today.",
            requester={"kind": "profile", "id": "default"},
            preferred_expert="mind-palace",
        )
        self.assertEqual(assessment["spec"]["classification"], "loop_candidate")
        demand = promote_intake_to_demand(assessment)
        self.assertTrue(validate_object(demand))
        self.assertEqual(demand["spec"]["permissions"]["docs_write"], False)

    def test_expert_creates_valid_attempt(self):
        task = {
            "apiVersion": "agent.delivery.loop/v0",
            "kind": "Task",
            "metadata": {"id": "task-1", "goal_id": "goal-1", "created_at": "2026-06-29T00:00:00+08:00"},
            "spec": {
                "task_type": "script",
                "objective": "Run a report",
                "assignee": {"kind": "script", "id": "report"},
                "permissions": {"docs_write": False},
                "acceptance": {"evidence_required": True},
                "state": {"status": "pending"},
            },
        }
        attempt = create_attempt(
            task,
            executor={"kind": "script", "id": "report"},
            status="succeeded",
            summary="Report completed",
            evidence=[{"kind": "report", "path": "/tmp/report.md"}],
            budget_used={"token_used_estimate": 0},
        )
        self.assertTrue(validate_object(attempt))
        self.assertEqual(attempt["metadata"]["task_id"], "task-1")

    def test_delivery_supervisor_creates_task_and_decision(self):
        demand = create_demand(
            title="Maintain wiki health",
            request="Keep the wiki healthy",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        task = create_task(
            goal,
            task_type="workflow_run",
            objective="Run lint report",
            assignee={"kind": "hermes_workflow", "id": "mind-palace-lint"},
            permissions={"docs_write": False, "external_send": True},
            acceptance={"evidence_required": True},
            required_capabilities=["wiki_lint"],
        )
        decision = create_loop_decision(
            goal,
            action="create_task",
            reason="A lint report is the next low-risk step.",
            next_task={"ref": task["metadata"]["id"]},
            budget_assessment={"within_budget": True},
            risk_assessment={"high_risk": False, "gate_required": False},
        )
        self.assertTrue(validate_object(task))
        self.assertTrue(validate_object(decision))
        self.assertEqual(task["metadata"]["goal_id"], goal["metadata"]["id"])
        self.assertEqual(decision["spec"]["next_task"]["ref"], task["metadata"]["id"])

    def test_delivery_supervisor_requests_approval_for_high_risk_task(self):
        demand = create_demand(
            title="Archive docs",
            request="Archive stale docs",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        expert = {
            "apiVersion": "agent.delivery.loop/v0",
            "kind": "Expert",
            "metadata": {"id": "archiver", "title": "Archiver"},
            "spec": {
                "expert_kind": "script",
                "capabilities": [{"id": "archive", "description": "Archive files", "priority": 100, "default_owner": True}],
                "invocation": {"adapter": "script"},
            },
        }
        task, decision, ranked = propose_next_task(
            goal,
            [expert],
            {
                "task_type": "archive",
                "objective": "Archive stale docs",
                "required_capabilities": ["archive"],
                "permissions": {"delete_move_archive": True},
                "acceptance": {"evidence_required": True},
            },
        )
        self.assertIsNone(task)
        self.assertEqual(decision["spec"]["action"], "request_approval")
        self.assertEqual(ranked[0]["expert_id"], "archiver")

    def test_delivery_supervisor_checks_path_governance_before_task_creation(self):
        demand = create_demand(
            title="Update workflow",
            request="Update workflow spec",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        expert = {
            "apiVersion": "agent.delivery.loop/v0",
            "kind": "Expert",
            "metadata": {"id": "home-media", "title": "Home Media"},
            "spec": {
                "expert_kind": "hermes_profile",
                "capabilities": [{"id": "workflow_edit", "description": "Edit workflow", "priority": 100, "default_owner": True}],
                "invocation": {"adapter": "hermes_workflow", "profile": "home-media"},
            },
        }

        def evaluator(task_spec, selected_expert):
            return {
                "ok": False,
                "actor_profile": task_spec["path_governance"]["actor_profile"],
                "violations": [
                    {
                        "path": "/opt/data/workflows/specs/media.workflow.yaml",
                        "owner_profile": "framework-maintainer",
                        "delegate_profile": "framework-maintainer",
                        "delegate_action": "delegate_task",
                    }
                ],
                "warnings": [],
                "results": [],
            }

        task, decision, ranked = propose_next_task(
            goal,
            [expert],
            {
                "task_type": "workflow_run",
                "objective": "Update workflow spec",
                "required_capabilities": ["workflow_edit"],
                "permissions": {"workflow_mutation": False},
                "path_governance": {
                    "actor_profile": "home-media",
                    "planned_paths": ["/opt/data/workflows/specs/media.workflow.yaml"],
                },
                "acceptance": {"evidence_required": True},
            },
            path_governance_evaluator=evaluator,
        )
        self.assertIsNone(task)
        self.assertEqual(decision["spec"]["action"], "mark_blocked")
        self.assertIsNone(decision["spec"]["required_approval"])
        self.assertIn("reset this goal", decision["spec"]["next_prompt"])
        self.assertIn("delegate_task", decision["spec"]["next_prompt"])
        self.assertIn("framework-maintainer", decision["spec"]["next_prompt"])
        self.assertEqual(decision["spec"]["review_feedback"]["path_governance"]["violations"][0]["owner_profile"], "framework-maintainer")
        self.assertEqual(ranked[0]["expert_id"], "home-media")

    def test_delivery_supervisor_keeps_path_governance_on_created_task(self):
        demand = create_demand(
            title="Update workflow",
            request="Update workflow spec",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        expert = {
            "apiVersion": "agent.delivery.loop/v0",
            "kind": "Expert",
            "metadata": {"id": "framework-maintainer", "title": "Framework Maintainer"},
            "spec": {
                "expert_kind": "hermes_profile",
                "capabilities": [{"id": "workflow_edit", "description": "Edit workflow", "priority": 100, "default_owner": True}],
                "invocation": {"adapter": "hermes_profile", "profile": "framework-maintainer"},
            },
        }

        def evaluator(task_spec, selected_expert):
            return {"ok": True, "actor_profile": "framework-maintainer", "violations": [], "warnings": [], "results": []}

        task, decision, _ = propose_next_task(
            goal,
            [expert],
            {
                "task_type": "workflow_run",
                "objective": "Update workflow spec",
                "required_capabilities": ["workflow_edit"],
                "permissions": {"workflow_mutation": False},
                "path_governance": {
                    "actor_profile": "framework-maintainer",
                    "planned_paths": ["/opt/data/workflows/specs/media.workflow.yaml"],
                },
                "acceptance": {"evidence_required": True},
            },
            path_governance_evaluator=evaluator,
        )
        self.assertIsNotNone(task)
        self.assertEqual(decision["spec"]["action"], "create_task")
        self.assertEqual(task["spec"]["path_governance"]["actor_profile"], "framework-maintainer")

    def test_delivery_supervisor_accepts_successful_attempt_with_evidence(self):
        demand = create_demand(
            title="Maintain wiki health",
            request="Keep the wiki healthy",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        task = create_task(
            goal,
            task_type="workflow_run",
            objective="Run lint report",
            assignee={"kind": "expert", "id": "mind-palace"},
            permissions={"docs_write": False},
            acceptance={"evidence_required": True, "expected_evidence": ["report"]},
            required_capabilities=["wiki_lint"],
        )
        task["spec"]["state"]["status"] = "submitted"
        attempt = create_attempt(
            task,
            executor={"kind": "expert", "id": "mind-palace"},
            status="succeeded",
            summary="Report completed",
            evidence=[{"kind": "report", "path": "/tmp/report.md"}],
            budget_used={"token_used_estimate": 100},
        )
        updated, decision = review_attempt(goal, task, attempt)
        self.assertEqual(updated["spec"]["state"]["status"], "accepted")
        self.assertEqual(decision["spec"]["action"], "mark_complete")
        self.assertEqual(decision["spec"]["review_feedback"]["ok"], True)

    def test_delivery_supervisor_rejects_missing_evidence_and_prompts_rework(self):
        demand = create_demand(
            title="Maintain wiki health",
            request="Keep the wiki healthy",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        task = create_task(
            goal,
            task_type="workflow_run",
            objective="Run lint report",
            assignee={"kind": "expert", "id": "mind-palace"},
            permissions={"docs_write": False},
            acceptance={"evidence_required": True, "expected_evidence": ["report"]},
            required_capabilities=["wiki_lint"],
        )
        task["spec"]["state"]["status"] = "submitted"
        attempt = create_attempt(
            task,
            executor={"kind": "expert", "id": "mind-palace"},
            status="succeeded",
            summary="Report completed without artifact",
            evidence=[],
            budget_used={"token_used_estimate": 100},
        )
        updated, decision = review_attempt(goal, task, attempt)
        self.assertEqual(updated["spec"]["state"]["status"], "rejected")
        self.assertEqual(decision["spec"]["action"], "create_task")
        self.assertIn("next_prompt", decision["spec"])
        self.assertEqual(decision["spec"]["review_feedback"]["ok"], False)

    def test_delivery_supervisor_requests_human_acceptance_when_required(self):
        demand = create_demand(
            title="Review wiki writeback",
            request="Review the proposed writeback",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        task = create_task(
            goal,
            task_type="review",
            objective="Review writeback proposal",
            assignee={"kind": "expert", "id": "mind-palace"},
            permissions={"docs_write": False},
            acceptance={"evidence_required": True, "expected_evidence": ["report"], "human_approval_required": True},
        )
        task["spec"]["state"]["status"] = "submitted"
        attempt = create_attempt(
            task,
            executor={"kind": "expert", "id": "mind-palace"},
            status="succeeded",
            summary="Proposal ready",
            evidence=[{"kind": "report", "path": "/tmp/proposal.md"}],
            budget_used={"token_used_estimate": 100},
        )
        updated, decision = review_attempt(goal, task, attempt)
        self.assertEqual(updated["spec"]["state"]["status"], "submitted")
        self.assertEqual(decision["spec"]["action"], "request_approval")
        self.assertEqual(decision["spec"]["required_approval"]["approval_type"], "human_acceptance")

    def test_delivery_supervisor_marks_blocked_attempt(self):
        demand = create_demand(
            title="Run workflow",
            request="Run a workflow",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        task = create_task(
            goal,
            task_type="workflow_run",
            objective="Run workflow",
            assignee={"kind": "expert", "id": "mind-palace"},
            permissions={"docs_write": False},
            acceptance={"evidence_required": True},
        )
        task["spec"]["state"]["status"] = "submitted"
        attempt = create_attempt(
            task,
            executor={"kind": "expert", "id": "mind-palace"},
            status="blocked",
            summary="Missing runtime permission",
            evidence=[],
            budget_used={"token_used_estimate": 100},
            error="missing permission",
        )
        updated, decision = review_attempt(goal, task, attempt)
        self.assertEqual(updated["spec"]["state"]["status"], "blocked")
        self.assertEqual(decision["spec"]["action"], "mark_blocked")

    def test_delivery_supervisor_stops_review_when_budget_exhausted(self):
        demand = create_demand(
            title="Maintain wiki health",
            request="Keep the wiki healthy",
            requester={"kind": "human", "id": "requester-example"},
            budget={"token_limit": 1000, "token_used_estimate": 950, "stop_when_remaining_below": 100},
        )
        goal = create_goal_from_demand(demand)
        task = create_task(
            goal,
            task_type="workflow_run",
            objective="Run lint report",
            assignee={"kind": "expert", "id": "mind-palace"},
            permissions={"docs_write": False},
            acceptance={"evidence_required": True},
        )
        task["spec"]["state"]["status"] = "submitted"
        attempt = create_attempt(
            task,
            executor={"kind": "expert", "id": "mind-palace"},
            status="succeeded",
            summary="Report completed",
            evidence=[{"kind": "report", "path": "/tmp/report.md"}],
            budget_used={"token_used_estimate": 100},
        )
        updated, decision = review_attempt(goal, task, attempt)
        self.assertEqual(updated["spec"]["state"]["status"], "submitted")
        self.assertEqual(decision["spec"]["action"], "stop_budget")
        self.assertEqual(decision["spec"]["budget_assessment"]["within_budget"], False)

    def test_delivery_supervisor_review_decisions_do_not_collide_between_attempts(self):
        demand = create_demand(
            title="Maintain wiki health",
            request="Keep the wiki healthy",
            requester={"kind": "human", "id": "requester-example"},
        )
        goal = create_goal_from_demand(demand)
        task = create_task(
            goal,
            task_type="workflow_run",
            objective="Run lint report",
            assignee={"kind": "expert", "id": "mind-palace"},
            permissions={"docs_write": False},
            acceptance={"evidence_required": True, "expected_evidence": ["report"]},
        )
        task["spec"]["state"]["status"] = "submitted"
        first = create_attempt(
            task,
            executor={"kind": "expert", "id": "mind-palace"},
            status="succeeded",
            summary="First report completed",
            evidence=[{"kind": "report", "path": "/tmp/first-report.md"}],
            budget_used={"token_used_estimate": 100},
        )
        second = create_attempt(
            task,
            executor={"kind": "expert", "id": "mind-palace"},
            status="succeeded",
            summary="Second report completed",
            evidence=[{"kind": "report", "path": "/tmp/second-report.md"}],
            budget_used={"token_used_estimate": 100},
        )
        _, first_decision = review_attempt(goal, dict(task), first)
        _, second_decision = review_attempt(goal, dict(task), second)
        self.assertNotEqual(first_decision["metadata"]["id"], second_decision["metadata"]["id"])


if __name__ == "__main__":
    unittest.main()
