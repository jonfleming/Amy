# transcript_tags.py
from django import template
from pytz import FixedOffset

register = template.Library()

@register.simple_tag
def get_hello(str):
    return 'Hello ' + str

@register.simple_tag
def get_day(utc, offset):
    loc = local_time(utc, offset)
    return loc.strftime('%A %b %d, %Y')    

@register.simple_tag
def get_hour(utc, offset):
    loc = local_time(utc, offset)
    return loc.strftime('%I:%M %p')

def local_time(utc, offset):
    return utc.astimezone(FixedOffset(-offset))
    