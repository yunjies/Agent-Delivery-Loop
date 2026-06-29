from __future__ import annotations

import argparse
import json
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages" / "delivery-core"))
sys.path.insert(0, str(ROOT / "packages" / "delivery-supervisor-sdk"))
sys.path.insert(0, str(ROOT / "adapters" / "filesystem"))

from agent_delivery_loop import FilesystemStore, KIND_DIRS
from agent_delivery_supervisor import review_attempt
from agent_delivery_filesystem import FilesystemWorkspace


def main(argv=None):
    parser = argparse.ArgumentParser(prog="adl", description="Agent Delivery Loop CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate", help="Validate protocol JSON and fixtures")

    init_parser = sub.add_parser("init-workspace", help="Initialize a filesystem workspace")
    init_parser.add_argument("path")

    status_parser = sub.add_parser("status", help="Summarize a filesystem workspace")
    status_parser.add_argument("workspace")

    list_parser = sub.add_parser("list", help="List objects from a filesystem workspace")
    list_parser.add_argument("workspace")
    list_parser.add_argument("kind", choices=sorted(KIND_DIRS))

    show_parser = sub.add_parser("show", help="Show an object from a filesystem workspace")
    show_parser.add_argument("workspace")
    show_parser.add_argument("kind", choices=sorted(KIND_DIRS))
    show_parser.add_argument("id")

    review_parser = sub.add_parser("review-attempt", help="Review an Attempt and write the supervisor decision")
    review_parser.add_argument("workspace")
    review_parser.add_argument("goal_id")
    review_parser.add_argument("task_id")
    review_parser.add_argument("attempt_id")

    tick_parser = sub.add_parser("supervisor-tick", help="Review submitted tasks with unreviewed attempts")
    tick_parser.add_argument("workspace")
    tick_parser.add_argument("--max-reviews", type=int)

    demo_parser = sub.add_parser("demo", help="Run the minimal filesystem demo")
    demo_parser.add_argument("--reset", action="store_true")
    demo_parser.add_argument("--workspace")

    args = parser.parse_args(argv)
    if args.command == "validate":
        runpy.run_path(str(ROOT / "scripts" / "validate-protocol.py"), run_name="__main__")
        return 0
    if args.command == "init-workspace":
        FilesystemStore(args.path).init()
        print(json.dumps({"ok": True, "workspace": args.path}, ensure_ascii=False))
        return 0
    if args.command == "status":
        print(json.dumps(FilesystemStore(args.workspace).summary(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "list":
        objects = FilesystemStore(args.workspace).list_objects(args.kind)
        print(json.dumps([
            {
                "id": obj.get("metadata", {}).get("id"),
                "title": obj.get("metadata", {}).get("title"),
                "status": obj.get("spec", {}).get("state", {}).get("status"),
            }
            for obj in objects
        ], ensure_ascii=False, indent=2))
        return 0
    if args.command == "show":
        obj = FilesystemStore(args.workspace).load(args.kind, args.id)
        print(json.dumps(obj, ensure_ascii=False, indent=2))
        return 0
    if args.command == "review-attempt":
        store = FilesystemStore(args.workspace).init()
        goal = store.load("Goal", args.goal_id)
        task = store.load("Task", args.task_id)
        attempt = store.load("Attempt", args.attempt_id)
        updated_task, decision = review_attempt(goal, task, attempt)
        store.save(updated_task)
        store.save(decision)
        print(json.dumps({
            "ok": True,
            "task_id": updated_task["metadata"]["id"],
            "task_status": updated_task["spec"]["state"]["status"],
            "decision_id": decision["metadata"]["id"],
            "decision_action": decision["spec"]["action"],
            "next_prompt": decision["spec"].get("next_prompt"),
        }, ensure_ascii=False, indent=2))
        return 0
    if args.command == "supervisor-tick":
        result = FilesystemWorkspace(args.workspace).supervisor_tick(max_reviews=args.max_reviews)
        print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=2))
        return 0
    if args.command == "demo":
        demo_args = []
        if args.workspace:
            demo_args.extend(["--workspace", args.workspace])
        if args.reset:
            demo_args.append("--reset")
        old_argv = sys.argv
        try:
            sys.argv = [str(ROOT / "examples" / "minimal" / "run_minimal_loop.py"), *demo_args]
            runpy.run_path(str(ROOT / "examples" / "minimal" / "run_minimal_loop.py"), run_name="__main__")
        finally:
            sys.argv = old_argv
        return 0
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
