from hashlib import sha1

from django.contrib.auth.hashers import BasePasswordHasher
from tastypie.authorization import Authorization

class PaddockPasswordHasher(BasePasswordHasher):
    """
    The SHA1 password hashing algorithm (not recommended)
    """
    algorithm = "old_paddock"

    def encode(self, password, salt):
        assert password
        assert salt and '$' not in salt
    
        hash = sha1()
        hash.update(password + salt.hexdigest())
        hashed_password = salt.hexdigest() + hash.hexdigest()

        # Make sure the hased password is an UTF-8 object at the end of the
        # process because SQLAlchemy _wants_ a unicode object for Unicode
        # fields
        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')

        return "%s$%s" % (self.algorithm, hashed_password)
        

    def verify(self, password, encoded):  
        pwd = encoded.split("$")[1]
        hashed_pass = sha1()
        hashed_pass.update(password + pwd[:40])
        return pwd[40:] == hashed_pass.hexdigest()        

    def safe_summary(self, encoded):
        algorithm, salt, hash = encoded.split('$', 2)
        assert algorithm == self.algorithm
        return SortedDict([
            (_('algorithm'), algorithm),
            (_('salt'), mask_hash(salt, show=2)),
            (_('hash'), mask_hash(hash)),
        ])


class IsOwnerAuthorization(Authorization):
    """
    Checks to make sure that the requeted object belongs to the logged in user
    """
    def base_checks(self, bundle):
        klass = self.resource_meta.object_class

        # If it doesn't look like a model, we can't check permissions.
        if not klass or not getattr(klass, '_meta', None):
            return False

        # User must be logged in to check permissions.
        if not hasattr(bundle.request, 'user'):
            return False

        print bundle
        if not bundle.request.user.username == bundle.data['username']: 
            return False    

        return True

    def to_read(self, bundle):
        return self.base_checks(bundle)

    def to_add(self, bundle):
        return self.base_checks(bundle)

    def to_change(self, bundle):
        return self.base_checks(bundle)

    def to_delete(self, bundle):
        return self.base_checks(bundle)

           

         