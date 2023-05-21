# transcript_tags.py
from django import template

register = template.Library()

@register.filter(name="date")
def date_bar(value, date):
    if value == date:
        return ""
    else:
        value = date
        return value
    
