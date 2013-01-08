import json
import StringIO
import os

from PIL import Image 

from django.http import HttpResponseRedirect, HttpResponse,  HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core import serializers
from django.core.files.uploadedfile import UploadedFile
from django.core.files.base import ContentFile,File
from django.core.files.temp import NamedTemporaryFile
from django.views.decorators.http import require_http_methods

from django.contrib.auth.models import User
from django.contrib.auth.views import login as django_login,logout
from django.contrib.auth.decorators import login_required

from django.forms import ModelChoiceField, HiddenInput

from registration.models import Club, Event, Car, UserProfile, User

from django.views.decorators.csrf import csrf_exempt


@login_required
@require_http_methods(['GET'])
def admin_user(request, username): 
    user = User.objects.get(username=username)

    context = {'js_target':'users',
               'user': user}

    return render_to_response('garage/base.html',
                              context,
                              context_instance=RequestContext(request))

#TODO Permissions for user to access this? 
@login_required
@require_http_methods(['GET'])
def admin_club(request, clubname): 

    #club = Club.objects.get(safe_name=clubname)
    club = Club.objects.get(safe_name="noraascc")
    context = {'js_target': 'clubs',
               'club': club,
               'user': request.user }

    return render_to_response('garage/base.html',
                              context,
                              context_instance=RequestContext(request))


@require_http_methods(['POST'])
def car_avatar(request, car_id):
    """Handles a POST or PUT to a car for an avatar file upload, returns JSON"""

    car = Car.objects.get(pk=car_id)


    if request.FILES == None:
            msg = "No Files uploaded!"
            return HttpResponse(content=json.dumps({'msg':msg}), 
                                mimetype="application/json",
                                status=415)

    #getting file data for farther manipulations
    uploaded = request.FILES['file']

    avatar_img = Image.open(uploaded)

    avatar_img.thumbnail((400,400),Image.ANTIALIAS)
    avatar_file = NamedTemporaryFile()
    avatar_img.save(avatar_file,'JPEG')
    name = '%d_avatar.jpg'%car.pk
    if os.path.exists(name): 
      os.remove(name)
    car.avatar.save(name,File(avatar_file))
    avatar_file.close()

    uploaded.seek(0)
    thumb_img = Image.open(uploaded)
    thumb_img.thumbnail((100,100),Image.ANTIALIAS)
    thumb_file = NamedTemporaryFile()
    thumb_img.save(thumb_file,'JPEG')
    name = '%d_thumb.jpg'%car.pk
    if os.path.exists(name): 
      os.remove(name)
    car.thumb.save(name,File(thumb_file))
    thumb_file.close()

    uploaded.close()
    car.save()
    data = {}
    data["msg"] = "Upload successful"
    data['avatar'] = car.avatar.url
    data['thumb'] = car.thumb.url
    return HttpResponse(json.dumps(data), mimetype='application/json')

