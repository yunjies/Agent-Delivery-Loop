# Implementation Checklist

## P0 Protocol Baseline

- [ ] Define v0 schemas.
- [ ] Add fixtures for a minimal loop.
- [ ] Add schema validation tests.
- [ ] Document Requester, Delivery Supervisor, and Expert roles.
- [ ] Document permissions and budget rules.

## P1 Core Library

- [ ] Validate protocol objects.
- [ ] Create loop state transitions.
- [ ] Add budget checks.
- [ ] Add permission checks.
- [ ] Add routing policy scoring.

## P2 SDKs

- [ ] Requester SDK creates Demand and Goal payloads.
- [ ] Delivery Supervisor SDK creates Task proposals and LoopDecision records.
- [ ] Expert Adapter SDK reports Attempt results and Evidence.

## P3 Adapters

- [ ] Filesystem adapter.
- [ ] Human approval adapter.
- [ ] Hermes profile adapter.
- [ ] Hermes workflow adapter.
- [ ] Codex thread adapter.
- [ ] Claude Code adapter.

## P4 Pilot

- [ ] Run a filesystem-only minimal loop.
- [ ] Add Mind Palace as the first Hermes integration pilot.
- [ ] Keep writeback, cron mutation, and archive actions approval-gated.

