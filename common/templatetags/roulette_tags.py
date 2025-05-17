from django import template

register = template.Library()

@register.filter
def times(value, arg):
    """Ikki sonni ko‘paytiradi."""
    try:
        return int(value) * int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def filter_by_user(queryset, user):
    return queryset.filter(user=user)