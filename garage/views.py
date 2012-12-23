from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core import serializers
from django.views.generic.create_update import create_object, update_object
from django.views.decorators.http import require_http_methods

from django.contrib.auth.models import User
from django.contrib.auth.views import login as django_login,logout
from django.contrib.auth.decorators import login_required

from django.forms import ModelChoiceField, HiddenInput

from registration.models import Club, Event, Car, UserProfile

from registration.forms import UserCreationForm, ActivationForm,\
     RegForm, CarAvatarForm, form_is_for_self, AuthenticationForm

from django.views.decorators.csrf import csrf_exempt


@require_http_methods(['GET'])
def admin_user(request, username): 
    context = {}
    
    return render_to_response('garage/base.html',
                              context,
                              context_instance=RequestContext(request))


@require_http_methods(['GET'])
def admin_club(request, user_id): 
    return HttpResponse()

@csrf_exempt  #TODO: Remove this major security bug, just for testing
@require_http_methods(['PUT', 'POST'])
def car_avatar(request, car_id):
    """Handles a POST or PUT to a car for an avatar file upload, returns JSON"""

    form = CarAvatarForm(request.POST, request.FILES)
    if form.is_valid(): 
        #print "TESTING"
        data = {'avatar_url': '/test', 'thumb_url': '/test', 'error': None}
        return HttpResponse(json.dumps(data), mimetype='application/json')
    #print form.errors
    data = {'error': 'Invalid Image File'}
    return HttpResponse(json.dumps(data), mimetype='application/json')    

