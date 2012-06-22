import os
import re
from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


register = template.Library()

@register.filter(needs_autoescape=True)
def spacify(value, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x
    return mark_safe(re.sub('\s', '&'+'nbsp;', esc(value)))

@register.inclusion_tag('paddock/events_table.html')
def events_table(events): 
    return {'events': events}


@register.inclusion_tag('paddock/direction_bubble.html')
def directions_bubble(lat,long,name): 
    return {'lat': lat,
            'long': long,
            'name': name}

@register.inclusion_tag('paddock/reg_list.html')
def reg_table(regs,table_id=None,table_class=None):
    return {'table_id':table_id,
            'table_class':table_class,
            'regs':regs}

@register.inclusion_tag('paddock/result_list.html')
def result_table(regs,table_id=None,table_class=None):
    return {'table_id':table_id,
            'table_class':table_class,
            'regs':regs}
    