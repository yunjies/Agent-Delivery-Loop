# Filesystem Adapter

The filesystem adapter persists Agent Delivery Loop objects as JSON files and appends JSONL events through the core `FilesystemStore`.

It is intended for local demos, NAS-backed pilots, and offline verification. It does not run a daemon, consume queues, call LLMs, or contact external services.

## Minimal Usage

```python
from agent_delivery_filesystem import FilesystemWorkspace

workspace = FilesystemWorkspace(".adl-workspace")
```
