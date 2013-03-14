import json
import StringIO
import os
import zipfile
import datetime

from PIL import Image 

from django.http import HttpResponseRedirect, HttpResponse,  HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.core import serializers
from django.core.files.uploadedfile import UploadedFile
from django.core.files.base import ContentFile,File
from django.core.files.temp import NamedTemporaryFile
from django.core.mail import send_mail
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.db import transaction

from django.contrib.auth.models import User
from django.contrib.auth.views import login as django_login,logout
from django.contrib.auth.decorators import login_required

from django.forms import ModelChoiceField, HiddenInput

from registration.models import Club, Event, Car, UserProfile, User, find_user, \
    Membership, Session

from django.views.decorators.csrf import csrf_exempt

from garage.api import MembershipResource
from garage.utils import reg_txt, reg_dat, parse_axtime


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
               'user': request.user}

    return render_to_response('garage/base.html',
                              context,
                              context_instance=RequestContext(request))


@login_required
@require_http_methods(['GET'])
def admin_event(request, event_id): 

    event = Event.objects.get(pk=event_id)
    context = {'js_target': 'events',
               'club': event.club,
               'user': request.user,
               'event': event}

    return render_to_response('garage/base.html',
                              context,
                              context_instance=RequestContext(request))           


@login_required
@require_http_methods(['POST'])
def email_regd_drivers(request, event_id):
    e = Event.objects.get(pk=event_id)
    emails = e.regs.filter(user_profile__isnull=False).\
        select_related('user_profile__user').\
        values_list('user_profile__user__email', flat=True).\
        all()
    
    subject = request.POST['subject']
    body = request.POST['body']
    
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, emails)
    
    return HttpResponse(status=200)


@login_required
@require_http_methods(['GET'])
def reg_data_files(request, event_id): 

    e = Event.objects.select_related().get(pk=event_id)
    
    out_file = StringIO.StringIO()
    z = zipfile.ZipFile(out_file, 'w')

    dat = reg_dat(e.regs.all())
    txt = reg_txt(e.regs.all())

    z.writestr('pre_reg.dat', dat)
    z.writestr('pre_reg.txt', txt)

    z.close()
    out_file.seek(0)
    response = HttpResponse(status=200, mimetype="application/x-zip-compressed",
        content=out_file)
    response['Content-Disposition'] = 'filename="pre_reg.zip"'
    return response


@login_required
@require_http_methods(['POST'])
def upload_results(request, event_id): 
    validate_error = dict()

    event = Event.objects.get(pk=event_id)

    with transaction.atomic():
        name = request.params.get('name') 
        if not name: 
            validate_error['name'] = "you must name the session"
            raise ValueError

        session = Session()
        s.club = event.club

        f = StringIO.StringIO(request.FILES['results_file'].read())

        results = parse_axtime(event,session,f)

        if isintance(results,dict): #some kind of error happened
            validate_error = results
            raise ValueError

        return HttpResponse(mimetype="application/json",status=200)
        
    except Exception: 
        return HttpResponse(content=json.dumps({'msg': validate_error}),
                                mimetype="application/json",
                                status=400)

@login_required
@require_http_methods(['POST'])
def car_avatar(request, car_id):
    """Handles a POST or PUT to a car for an avatar file upload, returns JSON"""

    car = Car.objects.get(pk=car_id)

    if request.FILES == None:
            msg = "No Files uploaded!"
            return HttpResponse(content=json.dumps({'msg': msg}),
                                mimetype="application/json",
                                status=415)

    #getting file data for farther manipulations
    uploaded = request.FILES['file']

    avatar_img = Image.open(uploaded)

    avatar_img.thumbnail((400, 400), Image.ANTIALIAS)
    avatar_file = NamedTemporaryFile()
    avatar_img.save(avatar_file, 'JPEG')
    name = '%d_avatar.jpg'%car.pk
    if os.path.exists(name): 
        os.remove(name)
    car.avatar.save(name, File(avatar_file))
    avatar_file.close()

    uploaded.seek(0)
    thumb_img = Image.open(uploaded)
    thumb_img.thumbnail((100, 100), Image.ANTIALIAS)
    thumb_file = NamedTemporaryFile()
    thumb_img.save(thumb_file, 'JPEG')
    name = '%d_thumb.jpg'%car.pk
    if os.path.exists(name): 
        os.remove(name)
    car.thumb.save(name, File(thumb_file))
    thumb_file.close()

    uploaded.close()
    car.save()
    data = {}
    data["msg"] = "Upload successful"
    data['avatar'] = car.avatar.url
    data['thumb'] = car.thumb.url
    return HttpResponse(json.dumps(data), mimetype='application/json')


@login_required
def search_users(request, query): 
    """Query against user database and returns possible matches"""

    results = [{'first_name':u.first_name, 'last_name': u.last_name, 'username': u.username} for u in find_user(query)]

    return HttpResponse(json.dumps(results), mimetype='application/json')


@login_required
@require_http_methods(['POST'])
def new_membership(request, clubname): 
    """create a new membership for the given user and club"""

    username = request.POST['username']

    u = User.objects.get(username=username)
    up = u.get_profile()
    c = Club.objects.get(safe_name=clubname)

    try: 
        m = Membership.objects.get(club=c, user_prof=up)
    except Membership.DoesNotExist: 
        m = Membership()
        m.club = c
        m.user_prof = up
        m.start = datetime.date.today()
        m.valid_thru = m.start + datetime.timedelta(days=365.2425)
        m.save()

    mr = MembershipResource()
    mr_bundle = mr.build_bundle(obj=m, request=request)
    return HttpResponse(mr.serialize(None, mr.full_dehydrate(mr_bundle),'application/json'), mimetype='application/json')

