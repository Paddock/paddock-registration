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

@register.inclusion_tag('registration/events_table.html')
def events_table(events): 
    return {'events': events}


@register.inclusion_tag('registration/direction_bubble.html')
def directions_bubble(lat,long,name): 
    return {'lat': lat,
            'long': long,
            'name': name}

@register.inclusion_tag('registration/reg_list.html')
def reg_table(regs,table_id=None,table_class=None):
    return {'table_id':table_id,
            'table_class':table_class,
            'regs':regs}

@register.inclusion_tag('registration/result_list.html')
def result_table(regs,table_id=None,table_class=None,pax=False):
    return {'table_id':table_id,
            'table_class':table_class,
            'regs':regs,
            'pax':pax}

@register.inclusion_tag('registration/points_list.html')
def points_table(points,table_id=None,table_class=None,pax=False): 
    return {'table_id':table_id,
            'table_class':table_class,
            'points':points,
            'pax':pax} 



class VerbatimNode(template.Node):

    def __init__(self, text):
        self.text = text
    
    def render(self, context):
        return self.text
    
@register.tag
def verbatim(parser, token):
    text = []
    while 1:
        token = parser.tokens.pop(0)
        if token.contents == 'endverbatim':
            break
        if token.token_type == template.TOKEN_VAR:
            text.append('{{')
        elif token.token_type == template.TOKEN_BLOCK:
            text.append('{%')
        text.append(token.contents)
        if token.token_type == template.TOKEN_VAR:
            text.append('}}')
        elif token.token_type == template.TOKEN_BLOCK:
            text.append('%}')
    return VerbatimNode(''.join(text))
    