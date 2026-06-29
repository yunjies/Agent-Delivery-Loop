# Feishu Notification Adapter

The Feishu notification adapter creates serializable notification payloads for approved supervision channels.

It does not send messages, store app secrets, create groups, or read chat history. A controlled runtime must inject credentials and send only after policy checks.
