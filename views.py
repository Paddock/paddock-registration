from django.http import HttpResponse

from paddock.models import Club

def clubs(request):

    clubs = Club.objects.all()
    
    
    return HttpResponse("Hello World. There are %d clubs in the database: %s"%(len(clubs),
                                                                               ", ".join([c.name for c in clubs])))