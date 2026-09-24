import logging
from decimal import Decimal
from datetime import date, datetime
from audit_app.models import ActivityLog
from audit_app.context import get_audit_context

logger = logging.getLogger(__name__)


def serialize_val(val):
    """Converts non-JSON serializable objects into clean JSON-serializable primitives."""
    if val is None:
        return None
    if isinstance(val, (Decimal, float)):
        return float(val)
    if isinstance(val, (date, datetime)):
        return val.isoformat()
    if isinstance(val, (int, str, bool)):
        return val
    if hasattr(val, 'pk'):
        # If it's a Django model instance
        return str(val)
    return str(val)


def compute_model_diff(old_instance, new_data, monitored_fields=None):
    """
    Compares an existing model instance against updated values.
    Args:
        old_instance: Existing Django model instance before saving.
        new_data: Dict of new values or updated model instance.
        monitored_fields: Optional list of field names to inspect. If None, checks all model fields.
    Returns:
        diff (dict): {'field': {'old': ..., 'new': ...}}
        descriptions (list of str): Human-readable change sentences.
    """
    diff = {}
    descriptions = []

    if old_instance is None:
        return diff, descriptions

    fields_to_check = monitored_fields
    if not fields_to_check:
        fields_to_check = [f.name for f in old_instance._meta.fields if not f.primary_key]

    for field in fields_to_check:
        if isinstance(new_data, dict):
            if field not in new_data:
                continue
            new_val = new_data[field]
        elif hasattr(new_data, field):
            new_val = getattr(new_data, field)
        else:
            continue

        old_val = getattr(old_instance, field, None)

        old_norm = serialize_val(old_val)
        new_norm = serialize_val(new_val)

        # Normalize string comparisons (e.g. None vs empty string)
        if str(old_norm or '').strip() != str(new_norm or '').strip():
            # Get human friendly field name
            label = field
            try:
                label = old_instance._meta.get_field(field).verbose_name.title()
            except Exception:
                label = field.replace('_', ' ').title()

            diff[field] = {
                'old': old_norm,
                'new': new_norm,
            }
            descriptions.append(f"{label} changed from '{old_norm}' to '{new_norm}'")

    return diff, descriptions


def log_audit_event(
    action,
    module,
    entity_type='',
    entity_id='',
    entity_reference='',
    description='',
    changes_diff=None,
    user=None,
    request=None,
    screen_name=''
):
    """
    Primary API to record transactional audit log entries.
    Gracefully pulls context (IP, user, browser, OS, trace ID) from ambient request context.
    Never raises an uncaught exception into business logic.
    """
    try:
        ctx = get_audit_context() or {}

        # 1. Resolve User
        acting_user = user or (request.user if request and getattr(request, 'user', None) and request.user.is_authenticated else None) or ctx.get('user')
        username = "System"
        role = ""

        if acting_user and acting_user.is_authenticated:
            username = acting_user.username
            if acting_user.is_superuser:
                role = "SuperAdmin"
            elif acting_user.groups.exists():
                role = acting_user.groups.first().name
            elif acting_user.is_staff:
                role = "Staff"
            else:
                role = "User"

        # 2. Extract Client Network / Device details
        ip_address = ctx.get('ip_address')
        correlation_id = ctx.get('correlation_id', '')
        device_type = ctx.get('device_type', 'Unknown')
        browser = ctx.get('browser', 'Unknown')
        operating_system = ctx.get('os', 'Unknown')
        user_agent = ctx.get('user_agent', '')

        # Fallback if request is explicitly passed and contextvars was empty
        if request and not ip_address:
            from audit_app.context import extract_client_ip, parse_device_info
            ip_address = extract_client_ip(request)
            dev_info = parse_device_info(request.META.get('HTTP_USER_AGENT', ''))
            device_type = dev_info['device_type']
            browser = dev_info['browser']
            operating_system = dev_info['os']
            user_agent = dev_info['user_agent']

        # 3. Create ActivityLog entry
        log_entry = ActivityLog.objects.create(
            user=acting_user if acting_user and acting_user.is_authenticated else None,
            user_username=username,
            user_role=role,
            action_type=action,
            module=module,
            screen_name=screen_name or module,
            entity_type=entity_type,
            entity_id=str(entity_id),
            entity_reference=str(entity_reference or entity_id),
            description=description,
            changes_diff=changes_diff or {},
            remark=description,
            ip_address=ip_address,
            device_type=device_type,
            browser=browser,
            operating_system=operating_system,
            user_agent=user_agent,
            correlation_id=correlation_id,
        )
        return log_entry

    except Exception as exc:
        # Audit logging should NEVER crash business logic
        logger.error(f"Failed to record audit log event: {exc}", exc_info=True)
        return None
