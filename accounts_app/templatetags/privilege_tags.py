from django import template
from accounts_app.common import check_privilege   # adjust import to your actual utils path

register = template.Library()

@register.simple_tag
def has_priv(user, menu_id, privilege_name):
    return check_privilege(user, menu_id, privilege_name)
