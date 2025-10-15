from django import template
import json

register = template.Library()

@register.filter
def map(iterable, attribute):
    """
    Custom filter to map an attribute from objects in an iterable.
    """
    return [getattr(item, attribute, None) for item in iterable]


register = template.Library()

@register.filter
def safejson(value):
    return json.dumps(value)

