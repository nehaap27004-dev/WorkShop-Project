from functools import wraps
from audit_app.common import log_activity

def log_action(screen_name, action_type, remark=None, remark_field=None):
    """
    screen_name   -> Human readable screen/module name
    action_type   -> CREATE / UPDATE / DELETE / etc
    remark        -> Static remark (optional)
    remark_field  -> Model field name to build remark dynamically (optional)
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            response = view_func(request, *args, **kwargs)

            try:
                # If remark_field is provided, try to extract object from kwargs
                obj = kwargs.get('pk') or kwargs.get('id')
                dynamic_remark = remark

                if remark_field and hasattr(request, 'logged_object'):
                    field_value = getattr(request.logged_object, remark_field, '')
                    dynamic_remark = f"{screen_name} '{field_value}' {action_type.lower()}"

                log_activity(
                    user=request.user,
                    screen_name=screen_name,
                    action_type=action_type,
                    remark=dynamic_remark or ""
                )

            except Exception:
                # Logging must NEVER break business logic
                pass

            return response

        return wrapper
    return decorator
