from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized

from registration.models import Club, User, UserProfile
    

class UserAdminAuthorization(Authorization): 

    def _get_user(self, bundle): 
        user = bundle.request.user
        if isinstance(bundle.obj, UserProfile): 
            user = bundle.obj.user
        else: 
            cls = type(bundle.obj)
            id = bundle.data['id'] #this is shitty... but the bundle.obj does not seem to be valid yet
            obj = cls.objects.get(pk=id)
            user = obj.user

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
        raise Unauthorized()
        #self._is_self(bundle)
        #return object_list

    def create_detail(self, object_list, bundle):
        raise Unauthorized()
        return True

    def update_list(self, object_list, bundle):
        raise Unauthorized()
        #self._is_self(bundle)
        #return object_list

    def update_detail(self, object_list, bundle):
        u = self._get_user(bundle)
        return bundle.request.user == u

    def delete_list(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes.")
        #self._is_user_admin(bundle)
        #return True

    def delete_detail(self, object_list, bundle):
        raise Unauthorized("Sorry, no deletes.")
        #self._is_user_admin(bundle)
        #return True


class ClubAdminAuthorization(Authorization): 

    def _is_club_admin(self, bundle): 
        user = bundle.request.user

        if isinstance(bundle.obj, Club): 
            if bundle.data: 
                club = Club.objects.get(pk=bundle.data['safe_name'])
            else: 
                club = bundle.obj
        else: 
            cls = type(bundle.obj)
            id = bundle.data['id'] #this is shitty... but the bundle.obj does not seem to be valid yet
            obj = cls.objects.get(pk=id)
            club = obj.club

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
        self._is_club_admin(bundle)
        return True

    def update_list(self, object_list, bundle):
        self._is_club_admin(bundle)
        return object_list

    def update_detail(self, object_list, bundle):
        self._is_club_admin(bundle)
        return True

    def delete_list(self, object_list, bundle):
        self._is_club_admin(bundle)
        return object_list

    def delete_detail(self, object_list, bundle):
        #raise Unauthorized("Sorry, no deletes.")
        self._is_club_admin(bundle)
        return True