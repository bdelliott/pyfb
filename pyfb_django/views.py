import logging
logger = logging.getLogger("pyfb")
logger.setLevel(logging.DEBUG)

from django.core.urlresolvers import reverse
from django.http import *
from django.shortcuts import *
from django.template.context import RequestContext

from pyfb import auth
import config

auth_denied_template = config.get("PYFB_AUTH_DENIED_TEMPLATE")
fb_base_url = config.get("PYFB_FB_BASE_URL")      # base url where app is hosted


def auth_redirect(request):
    ''' After logging in user, FB redirects a GET request back to our app.
        It includes a 'code' parameter that is an auth_token that can be exchanged for an
        access_token but it seems like the same parameter appears on every subsequent
        GET to the canvas page, so it seems like it can be just ignored at this point.

        Just log whether the user authorized our app and then redirect back to the canvas
        page.
    '''

    logger.info("auth_redirect")
    context = RequestContext(request)

    if request.method != "GET":
        logger.error("Auth redirect callback with method %s, expected GET" % request.method)
        return HttpResponseNotAllowed(["GET",])        

    if request.GET.has_key("error_reason"):
        # user did not authorize our app
        error_reason = request.GET["error_reason"]
        
        error = error_desc = None
        
        error = request.GET.get("error")
        error_desc = request.GET.get("error_description")

        msg = "User did not authorize the application. "
        msg += "error_reason='%s'," % error_reason
        msg += " error='%s'," % error
        msg += " error_desc=%s" % error_desc
        logger.info(msg)

        return render_to_response(auth_denied_template, context)

    elif request.GET.has_key("code"):
        ''' a auth token was included, means that the app was authorized.  '''
        
        logger.info("A user successfully authorized the application.")
        
        # at this point we have a code that can be traded in for an access token.  no need to do this yet, since we'll get the 
        # same code the next time the canvas page loads, so just redirect.
        return HttpResponseRedirect(fb_base_url)
        
    else:
        # unknown scenario.
        raise Exception("Bad request to auth_rediect:")
