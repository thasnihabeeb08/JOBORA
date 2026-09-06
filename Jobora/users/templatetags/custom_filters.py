from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter and return list WITH TRIMMED ITEMS"""
    if value:
        # Split AND trim each item
        return [item.strip() for item in value.split(delimiter) if item.strip()]
    return []

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary"""
    return dictionary.get(key)

@register.filter
def intcomma(value):
    """Format number with commas (like humanize.intcomma)"""
    try:
        return f"{int(value):,}"
    except:
        return value

@register.filter
def truncate_words(value, num_words):
    """Truncate text to specified number of words"""
    if value:
        words = value.split()
        if len(words) > num_words:
            return ' '.join(words[:num_words]) + '...'
        return value
    return ''

# ADD THIS FILTER since your template uses |trim
@register.filter
def trim(value):
    """Trim whitespace from string"""
    if value:
        return str(value).strip()
    return value

# ADD THIS TAG - This is what you're missing!
@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.
    """
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()