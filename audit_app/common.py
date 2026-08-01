from audit_app.models import ActivityLog

def log_activity(user, screen_name, action_type, remark=""):
    ActivityLog.objects.create(
        user=user if user and user.is_authenticated else None,
        screen_name=screen_name,
        action_type=action_type,
        remark=remark
    )
