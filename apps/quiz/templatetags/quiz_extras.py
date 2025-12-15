from django import template

register = template.Library()


@register.filter(name='chr')
def chr_filter(value):
    """Convert an integer (65->'A') for template usage."""
    try:
        return chr(int(value))
    except (TypeError, ValueError, OverflowError):
        return ''


@register.filter(name='get_item')
def get_item(obj, key):
    """Safe dict access in templates: {{ mydict|get_item:mykey }}"""
    try:
        return obj.get(key)
    except Exception:
        try:
            return obj[key]
        except Exception:
            return None
