# Implementation Checklist

## P0 Protocol Baseline

- [x] Define v0 schemas.
- [x] Add fixtures for a minimal loop.
- [x] Add schema validation tests.
- [x] Document Requester, Delivery Supervisor, and Expert roles.
- [x] Document permissions and budget rules.

## P1 Core Library

- [x] Validate protocol objects.
- [x] Create loop state transitions.
- [x] Add budget checks.
- [x] Add permission checks.
- [x] Add routing policy scoring.

## P2 SDKs

- [x] Requester SDK creates Demand and Goal payloads.
- [x] Delivery Supervisor SDK creates Task proposals and LoopDecision records.
- [x] Expert Adapter SDK reports Attempt results and Evidence.

## P3 Adapters

- [x] Filesystem adapter.
- [x] Human approval adapter.
- [x] Hermes profile adapter.
- [x] Hermes workflow adapter.
- [x] Codex thread adapter.
- [x] Claude Code adapter.

## P4 Pilot

- [x] Run a filesystem-only minimal loop.
- [ ] Add Mind Palace as the first Hermes integration pilot.
- [ ] Keep writeback, cron mutation, and archive actions approval-gated.
