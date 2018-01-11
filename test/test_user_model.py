import unittest
import time
from ..app import create_app, db
from ..app.models import User, AnonymousUser, Role, Permission

class UserModelTestCase(unittest):
    def test_password_setter(self):
        u=User(password='cat')
        self.assertTrue=(u.password_hash is not None)

    def test_no_password_getter(self):
        u=User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verfication(self):
        u=User(password = 'cat')
        self.assertTrue=(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u=User(password='cat')
        u2=User(password='cat')
        self.assertTrue(u.password_hash !=u2.password_hash)

    def test_roles_and_permissions(self):
        Role.insert_roles()
        u=User(email='zhuo@example.com',password='cat')
        self.aassertTrue(u.can(Permission.ADMINSTER))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

    def test_anonymous_user(self):
        u=AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))


