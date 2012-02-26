''' Wrapper around session access.  Keep track of session madness as the app grows. '''

import logging
logger = logging.getLogger("pyfb")

FB_ACCESS_TOKEN = "fb_access_token"
FB_EXPIRES = "fb_expires"
FB_USER_ID = "fb_user_id"

def get_fb_access_token(request, warn=True):
    token = request.session.get(FB_ACCESS_TOKEN)
    if not token and warn:
        logger.warn("pyfb: No access token found in session")
    return token
    
    
def get_fb_expires(request, warn=True):
    expires = request.session.get(FB_EXPIRES)
    if not expires and warn:
        logger.warn("pyfb: No 'expires' found in session")
    return expires
    
def get_fb_user_id(request, warn=True):
    user_id = request.session.get(FB_USER_ID)
    if not user_id and warn:
        logger.warn("pyfb: No user_id found in session")
    return user_id
    
def set_fb_access_token(request, access_token):
    request.session[FB_ACCESS_TOKEN] = access_token

def set_fb_expires(request, expires):
    request.session[FB_EXPIRES] = expires
    
def set_fb_user_id(request, user_id):
    request.session[FB_USER_ID] = user_id

