from audit_app.services import log_audit_event


def log_activity(user, screen_name, action_type, remark=""):
    """
    Backward-compatible entry point for logging screen-level actions.
    Enriched with client IP, device, browser, and user role.
    """
    return log_audit_event(
        action=action_type,
        module='GENERAL',
        screen_name=screen_name,
        description=remark,
        user=user,
    )

