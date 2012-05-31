from django import template

register = template.Library()

@register.inclusion_tag('paddock/events_table.html')
def events_table(events): 
    return {'events': events}
    