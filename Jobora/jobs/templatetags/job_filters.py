from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def split(value, separator=','):
    """
    Split a string by the given separator.
    Usage: {{ value|split:"," }}
    """
    if not value:
        return []
    try:
        return [item.strip() for item in value.split(separator) if item.strip()]
    except (AttributeError, TypeError):
        return []

@register.filter
def truncatechars(value, arg):
    """Truncate a string after a certain number of characters"""
    if not value:
        return ''
    try:
        length = int(arg)
        if len(value) > length:
            return value[:length] + '...'
        return value
    except (ValueError, TypeError):
        return value