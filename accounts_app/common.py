from .models import UserPrivilege, Menu
from django.contrib.auth import authenticate
from django.http import JsonResponse



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

# def check_admin_override(request):
#     """
#     Checks admin username & password sent in POST
#     """
#     admin_username = request.POST.get("admin_username")
#     admin_password = request.POST.get("admin_password")

#     if not admin_username or not admin_password:
#         return False, "Admin credentials required"

#     admin_user = authenticate(
#         request,
#         username=admin_username,
#         password=admin_password
#     )

#     if not admin_user:
#         return False, "Invalid admin credentials"

#     if not getattr(admin_user.user_role, "is_admin", False):
#         return False, "User is not an admin"

#     return True, admin_user




def check_admin_override(request):
    """
    Allows override by:
    - Django superuser
    - Custom admin role (user_role.is_admin)
    """

    admin_username = request.POST.get("admin_username")
    admin_password = request.POST.get("admin_password")

    if not admin_username or not admin_password:
        return False, "Admin credentials required"

    admin_user = authenticate(
        request,
        username=admin_username,
        password=admin_password
    )

    if not admin_user:
        return False, "Invalid admin credentials"

    # ✅ ALLOW DJANGO SUPERUSER
    if admin_user.is_superuser:
        return True, admin_user

    # ✅ ALLOW CUSTOM ADMIN ROLE
    if getattr(admin_user.user_role, "is_admin", False):
        return True, admin_user

    return False, "User is not authorized as admin"