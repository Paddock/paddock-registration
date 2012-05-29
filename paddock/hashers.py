from django.contrib.auth.hashers import BasePasswordHasher

from hashlib import sha1

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
        print pwd
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