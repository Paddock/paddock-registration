from django import template

register = template.Library()

@register.inclusion_tag('paddock/club_event_table.html')
def club_event_table(events): 
    return {'events': events}
    