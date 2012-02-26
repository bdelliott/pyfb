import os
os.environ["CURRENT_VERSION_ID"] = "brian.12345"

from django.test import TestCase
from django.test.client import RequestFactory

from pyfb_django import decorators

class DecoratorTest(TestCase):
    
    def testCheckAuth(self):
        rf = RequestFactory()
        #request = rf.get("/foobar")

        #self.assertFalse(decorators.check_auth(request))
        
        

