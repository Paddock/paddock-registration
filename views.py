from django.http import HttpResponse

def club(request):
    return HttpResponse("Hello, world. You're at the club index.")