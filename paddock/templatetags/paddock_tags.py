import os
from django import template

register = template.Library()

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
    