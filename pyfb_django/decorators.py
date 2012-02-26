''' View decorator to enforce that user is logged into to a valid facebook session '''
import logging
logger = logging.getLogger("pyfb")
import time

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template.context import RequestContext

# On GAE, don't use their login process on a real application server:
try:
    from djangoappengine.utils import on_production_server
    disable_decorator = not on_production_server
except ImportError:
    disable_decorator = False
    
from pyfb import auth
from pyfb_django import config
from pyfb_django import session

app_id = config.get("PYFB_APP_ID")          # facebook app id
app_secret = config.get("PYFB_APP_SECRET")  # facebook app secret
base_url = config.get("PYFB_BASE_URL")      # base url where app is hosted

def epoch():
    return int(time.time())
    
    
def check_auth(request):
    ''' Checking if FB session exists and is unexpired.  Returns True if auth is needed. '''
    
    user_id = session.get_fb_user_id(request, warn=False)
    access_token = session.get_fb_access_token(request, warn=False)
    expires = session.get_fb_expires(request, warn=False)
    
    if not user_id:
        logger.debug("pyfb:check_auth: no user id in session")
        return True
        
    if not access_token:
        logger.debug("pyfb:check_auth: no access token in session")
        return True
        
    if not expires:
        logger.debug("pyfb:check_auth: no expires in session")
        return True
        
    now = epoch()
    try:
        expires = int(expires)
        if now+30 >= expires:
            logger.debug("pyfb:check_auth: token is expired or will within next 30 seconds: expires=%d, epoch=%d" % (expires, now))
            return True
            
    except ValueError:
        logger.error("pyfb:check_auth: expires is not a valid UNIX epoch timestamp: %s" % expires)
        return True
        
    # session still valid!
    secs_left = expires-now
    mins_left = secs_left / 60.0
    logger.debug("pyfb:check_auth: user session is valid until %d (now=%d) (%0.2f mins left)" % (expires, now, mins_left))
    
    
def decode_signed_request(request):
    ''' check if Facebook gave us a signed_request parameter when they loaded our iframe: 
        http://developers.facebook.com/docs/authentication/signed_request/
        
        return True if signed request had valid credentials, otherwise False
    '''
    
    signed_request = request.POST.get("signed_request")
    
    if signed_request:
        logger.debug("pyfb:decode_signed_request: Found signed request")
        
        request_info = auth.handle_signed_request(signed_request, app_id, app_secret)

        if request_info:
            # save signed request info in user session:
            logger.debug("pyfb:decode_signed_request: signed request has credentials. (User %s)" % request_info.user_id)
        
            session.set_fb_access_token(request, request_info.oauth_token)
            session.set_fb_expires(request, request_info.expires)
            session.set_fb_user_id(request, request_info.user_id)
            return True
            
        else:
            logger.debug("pyfb:decode_signed_request: signed request lacks credentials")
            return False

    # no signed req param or signed request didn't have all the user details.
    logger.debug("pyfb:decode_signed_request: No signed request param")
    return False
    
    
def redirect_to_facebook_login(request):
    ''' redirect to facebook auth '''
    
    logger.info("pyfb:redirect_to_facebook_login: Redirecting user to Facebook authorization")

    # user not logged in, needs redirect to auth page:
    redirect_url = base_url + reverse("auth_redirect")

    # get full redirect url to facebook's graph api:
    url = auth.get_redirect_url(redirect_url, app_id, permissions=["publish_stream",])

    # do a crappy javascript redirect, since this is the only kind that works in a canvas app:
    context = RequestContext(request)
    context["url"] = url
    return render_to_response("pyfb_django/redirect.html", context)
    
     
def require_facebook_login(view_func):
    ''' Decorator for making sure user is logging in to facebook '''
    
    def enforce_login(request, *args, **kwargs):
        logger.info("pyfb:require_facebook_login: %s" % request.path)
        
        if disable_decorator:
            # skip decorator
            return view_func(request, *args, **kwargs)
            
        # if a signed_request parameter is present, always do a facebook login.  this is the user hitting our canvas page.
        got_credentials = decode_signed_request(request)
        
        if not got_credentials:
            # signed request didn't have all the goodies, so check out our current session to see if the information is still valid:
            needs_auth = check_auth(request)
            
            if needs_auth:
                # redirect to facebook for auth:
                return redirect_to_facebook_login(request)
            
        # have valid session, pass control to intended view function:
        return view_func(request, *args, **kwargs)

        
    return enforce_login
    