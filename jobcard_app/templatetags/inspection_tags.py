from django import template

register = template.Library()


@register.filter
def get_result(dictionary, key):
    """
    Returns dictionary[key] if it exists.
    """
    if dictionary is None:
        return None

    return dictionary.get(key)

@register.filter
def get_result(obj, field_name):
    """
    Returns obj.<field_name>
    """

    if obj is None:
        return None

    return getattr(obj, field_name, None)