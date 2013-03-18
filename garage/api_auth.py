from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized

from registration.models import Club, User, UserProfile, Event, Car
    

class UserAdminAuthorization(Authorization): 

    def _get_user(self, bundle): 
        if isinstance(bundle.obj, User): 
            try: 
                user = bundle.obj
                user.get_profile() #causes an error for empty users (whatever that means)
            except: 
                "got here"
                if bundle.data: 
                    username = bundle.data['username']
                    user = User.objects.get(username=username)
        else: 
            user = bundle.obj.user

        return user    

    def _read_only(self, bundle):     
        u = self._get_user(bundle)
        if not(bundle.request.user==u or u.has_perm('registration.view_user')): 
            raise Unauthorized()

    def read_list(self, object_list, bundle):
        self._read_only(bundle)
        return object_list

    def read_detail(self, object_list, bundle):
        self._read_only(bundle)
        return True

    def create_list(self, object_list, bundle):
        print "HERE1"

        raise Unauthorized()
        #self._is_self(bundle)
        #return object_list

    def create_detail(self, object_list, bundle):
        u = self._get_user(bundle)

        print "HERE2"
        #raise Unauthorized()
        if bundle.request.user != u:
            raise Unauthorized()
        return True

    def update_list(self, object_list, bundle):
        print "HERE3"
        raise Unauthorized()
        #self._is_self(bundle)
        #return object_list

    def update_detail(self, object_list, bundle):
        print "HERE4"
        u = self._get_user(bundle)
        if bundle.request.user != u:
            raise Unauthorized()
        return True

    def delete_list(self, object_list, bundle):
        print "HERE5"
        raise Unauthorized("Sorry, no deletes.")
        #self._is_user_admin(bundle)
        #return True

    def delete_detail(self, object_list, bundle):
        print "HERE6"
        u = self._get_user(bundle)
        if bundle.request.user != u or isinstance(bundle.obj,User): 
            raise Unauthorized("Sorry, no deletes.")
        #self._is_user_admin(bundle)
        return True


class ClubAdminAuthorization(Authorization): 

    def _is_club_admin(self, bundle): 
        user = bundle.request.user

        if isinstance(bundle.obj, Club): 
            if bundle.data: 
                club = Club.objects.get(pk=bundle.data['safe_name'])
            else: 
                club = bundle.obj
        else: 
            try: 
                club = bundle.obj.club
            except: 
                #print bundle.data
                club_id = bundle.data['club'].split("/")[-2]
                club = Club.objects.get(safe_name=club_id)

        perm = 'registration.%s_admin'%club.safe_name
        if not user.has_perm(perm): 
            raise Unauthorized("Not Allowed to edit this club")

    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        self._is_club_admin(bundle)
        return object_list

    def read_detail(self, object_list, bundle):
        self._is_club_admin(bundle)
        return True

    def create_list(self, object_list, bundle):
        self._is_club_admin(bundle)
        return object_list

    def create_detail(self, object_list, bundle):
        print "************test update_list 2"
        self._is_club_admin(bundle)
        return True

    def update_list(self, object_list, bundle):
        self._is_club_admin(bundle)
        return object_list

    def update_detail(self, object_list, bundle):
        print "************test update_list 3"

        self._is_club_admin(bundle)
        return True

    def delete_list(self, object_list, bundle):
        self._is_club_admin(bundle)
        return object_list

    def delete_detail(self, object_list, bundle):
        #raise Unauthorized("Sorry, no deletes.")
        self._is_club_admin(bundle)
        return True
