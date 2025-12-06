from .models import UserPrivilege, Menu





def check_privilege(user, menu_ids, privilege_fields):
    """
    Check if the logged-in user's role has the given privileges 
    for one or more menus.

    Example:
        check_privilege(user, [1, 2], ["can_read", "can_write"])
    """
    if not user.is_authenticated:
        return False

    # ✅ Superuser always has all privileges
    if getattr(user, "is_superuser", False):
        return True

    role = getattr(user, "user_role", None)
    if not role:
        return False

    # Ensure we always work with lists
    if isinstance(menu_ids, int):
        menu_ids = [menu_ids]
    if isinstance(privilege_fields, str):
        privilege_fields = [privilege_fields]

    # Fetch all privileges for this role and menus in one query
    privileges = UserPrivilege.objects.filter(user_role=role, menu_id__in=menu_ids)

    if not privileges.exists():
        return False

    # Check if ANY privilege matches
    for privilege in privileges:
        for field in privilege_fields:
            if getattr(privilege, field, False):
                return True  # ✅ user has at least one of the privileges

    return False  # ❌ none matched


# from django.http import HttpResponseForbidden
# from functools import wraps
# from .models import Menu, UserPrivilege

# def require_privilege(privilege_field):
#     """
#     Decorator that checks user privilege based on Menu.url matching request.path.
#     ✅ Superusers automatically bypass privilege checks.
#     Example: @require_privilege("can_read")
#     """
#     def decorator(view_func):
#         @wraps(view_func)
#         def wrapper(request, *args, **kwargs):
#             # must be logged in
#             if not request.user.is_authenticated:
#                 return HttpResponseForbidden("🚫 Please log in.")

#             # ✅ superuser bypass
#             if request.user.is_superuser:
#                 return view_func(request, *args, **kwargs)

#             role = getattr(request.user, "user_role", None)
#             if not role:
#                 return HttpResponseForbidden("🚫 No role assigned.")

#             try:
#                 # find menu by url (request.path gives exact matched path)
#                 menu = Menu.objects.get(url=request.path)

#                 # check privilege
#                 privilege = UserPrivilege.objects.get(user_role=role, menu=menu)

#                 if getattr(privilege, privilege_field, False):
#                     return view_func(request, *args, **kwargs)
#                 else:
#                     return HttpResponseForbidden("🚫 You are not authorized.")
#             except (Menu.DoesNotExist, UserPrivilege.DoesNotExist):
#                 return HttpResponseForbidden("🚫 Menu or privilege not found.")

#         return wrapper
#     return decorator