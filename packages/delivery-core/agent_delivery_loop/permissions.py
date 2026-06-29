PERMISSION_KEYS = {
    "docs_write",
    "delete_move_archive",
    "cron_mutation",
    "workflow_mutation",
    "profile_mutation",
    "external_send",
    "code_write",
    "shell_exec",
}


def is_allowed(permissions, key):
    if key not in PERMISSION_KEYS:
        raise ValueError(f"unknown permission: {key}")
    return bool((permissions or {}).get(key, False))


def assert_allowed(permissions, key):
    if not is_allowed(permissions, key):
        raise PermissionError(f"permission denied: {key}")
    return True
