import logging
logger = logging.getLogger("pyfb")
import urllib
import urllib2

# App engine is wonky with respect to using urllib2.  Sometimes perfectly valid URLs raise a 404 if urllib2 is used.  So.  Try to detect if we're on app engine and use
# its urlfetch api directly if we are...
#
# <rant>These motherfuckers shouldn't try to replace the implementation of a perfectly working python library if they are going to bollocks it up.</rant>
#
try:
    from google.appengine.api import urlfetch
    app_engine = True
except ImportError:
    # not on app engine.
    app_engine = False
    
    
def app_engine_get(url):
    ''' do a HTTP get using app engine's urlfetch interface directly '''
    
    try:
        response = urlfetch.fetch(url, method="GET", deadline=10) # 10 second deadline
        if not response.status_code == 200:
            logger.debug(response.content)
            raise Exception("Failed to get %s via urlfetch.  HTTP status code was %d" % (url, response.status_code))
            
        return response.content
        
    except:
        logger.error("Failed to GET %s via urlfetch" % url)
        raise
        
def app_engine_post(url, data):
    ''' do a HTTP post using app engine's urlfetch interface directly '''
    
    logger.debug("app_engine_post: " + url)
    try:
        #logger.debug("POST data: ")
        #logger.debug(data)
        
        form_data = urllib.urlencode(data)
        response = urlfetch.fetch(url=url, method="POST", payload=form_data, headers={'Content-Type': 'application/x-www-form-urlencoded'}, deadline=10) # 10 second deadline

        if response.status_code != 200:
            raise Exception("POST to %s failed with status code %d and content='%s" % (url, response.status_code, response.content))

        #logger.debug("POST response code: %s" % response.status_code)
        #logger.debug("POST response content: %s" % response.content)

        return response.content
        
    except:
        logger.error("Failed to POST %s via urlfetch" % url)
        raise
    
def standard_lib_get(url):
    ''' do an HTTP get using python's urllib2 package '''

    try:
        result = urllib2.urlopen(url)
        return result.read()

    except urllib2.URLError, e:
        logger.error("Failed to get %s via urllib2" % url)
        raise

    
def get(url):
    ''' do a simple synchronous get request for this URL '''
    
    logger.debug("GET %s" % url)
    if app_engine:
        return app_engine_get(url)
    else:
        return standard_lib_get(url)
        
def post(url, data):
    ''' synchronost URL POST '''

    logger.debug("POST %s" % url)
    if app_engine:
        return app_engine_post(url, data)
    else:
        raise Exception("Non app-engine POST is not yet implemented")

def delete(url):
    ''' synchronost URL POST '''
    raise Exception("Not yet implemented")
