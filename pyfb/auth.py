''' Facebook API authentication related code. '''

import hmac

import logging
logger = logging.getLogger("pyfb")

from django.core.urlresolvers import reverse
from django.http import HttpResponseServerError
from django.shortcuts import render_to_response

try:
    import json
except ImportError:
    # google app engine is old on python2.5, try to pick up simplejson from django
    from django.utils import simplejson as json
    

from base64 import urlsafe_b64decode
from hashlib import sha256

class SignedRequestInfo(object):
    def __init__(self, redirect_url=None, user_id=None, oauth_token=None, expires=None):
        self.redirect_url = redirect_url
        self.user_id = user_id
        self.oauth_token = oauth_token
        self.expires = expires

########################################################
def handle_signed_request(signed_request, app_id, app_secret):
    ''' Parse signed request and logic for the authorization handshake 
    
        Params:
            signed_request - encoded parameter from facebook containing info to do authorization on behalf of the user
            app_secret - facebook app id (found on developer site)
            app_secret - facebook app secret (found on developer site)
            
        Response
            signed_request_info - user and oauth information, or None if user needs to be logged in.
        
    '''
    
    logger.debug("app_id = %s" % app_id)
    logger.debug("app_secret = %s" % app_secret)

    if not app_id:
        raise Exception("Facebook app id is missing")
    if not app_secret:
        raise Exception("Facebook app secret is missing")
        
    try:
        data = parse_signed_request(signed_request, app_secret)
        logger.info(data)
    except:
        logger.exception("Error parsing signed request")
        raise

    # if the JSON object does not contain a user_id parameter, user needs to be logged
    # in in order to access their profile info.

    # signed request will have a user object containing only locale, age info and country. (no identity)
    issued_at = data.get("issued_at", "")
    
    locale = country = min_age = max_age = ""

    user = data.get("user")
    if user:
        locale = user.get("locale", "")
        country = user.get("country", "")
        
        age = user.get("age")
        if age:
            min_age = age.get("min", "")
            max_age = age.get("max", "")

    user_id = data.get("user_id", "")   # facebook user id, only available after user authorizes the app.
            
    if not user_id:
        # user needs to be logged in.
        return None

    # ok at this point we know we have an authorized user.  we should have an 'oauth_token' parameter that will allow us to make 
    # API calls.
    logger.info("Auth: user is %s" % user_id)
    
    if not data.has_key("oauth_token"):
        raise Exception("Bad request.  User id (%s) was present, but no oauth_token" % user_id)
    
    oauth_token = data["oauth_token"]

    if not data.has_key("expires"):
        raise Exception("Bad request.  Access token (%s) was present, but no expires" % access_token)

    expires = data["expires"]
    
    request_info = SignedRequestInfo(user_id=user_id, oauth_token=oauth_token, expires=expires)
    return request_info
    

def parse_signed_request(signed_request, app_secret):
    ''' Parse the signed_request POST parameter handed to convas page 
   
        See: http://developers.facebook.com/docs/authentication/canvas

        This parameter is irritatingly signed and JSON encoded, but requires some padding
        magic because the Python implementation doesn't agree on base 64 url encoding rules.

        Padding/signing code is a modified version of the one at:
        https://gist.github.com/670637/d129a1c4b4a1eec8cd6480186da38c3d2223eb35
    '''

    (sig, payload) = signed_request.split('.')

    # decode data
    sig = base64_url_decode(sig)
    data = json.loads(base64_url_decode(payload))

    if data['algorithm'].upper() != 'HMAC-SHA256':
        raise Exception('Unknown algorithm. Expected HMAC-SHA256')

    # check sig
    expected_sig = hmac.new(app_secret, payload, sha256).digest()
    if sig != expected_sig:
        raise Exception('Bad Signed JSON signature!')

    return data

def base64_url_decode(input):
    ''' Do base 64 URL decoding.  Enforce that the input string is padding to a multiple
        of 4 characters. '''
    input += '=' * (4 - (len(input) % 4))

    return urlsafe_b64decode(input.encode('utf-8'))


def get_redirect_url(redirect_url, app_id, permissions=[], dev_env=False):
    ''' redirect user to facebook's authorization process '''

    url = "https://graph.facebook.com/oauth/authorize"
    url += "?client_id=%s" % app_id
    url += "&redirect_uri=%s" % redirect_url

    if dev_env:
        # authorization requests from a standalone application require this parameter.  (as opposed to originating from a canvas page)
        url += "&type=user_agent"
    
    # Facebook extended permissions
    if permissions:
        perm_str = ",".join(permissions)
        logger.info(perm_str)
    
        url += "&scope=%s" % perm_str

    logger.debug(url)

    return url
    
    
