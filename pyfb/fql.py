''' Code for managing requests to the Facebook FQL API '''

# GAE allows you to use the standard Python API to retrieve URLs, or their URL fetch service.  Behind the scenes, they are translating
# everything to the URL fetch service.  It would be 100% portable to stick to the urllib2 library, although the URL Fetch service looks a lot nicer.

import logging
logger = logging.getLogger("pyfb")

try:
    import json
except ImportError:
    # app engine is on python 2.5
    from django.utils import simplejson as json
    
    
import time
import urllib

import net

class InvalidOAuthException(Exception):
    pass

# fql api base url
FQL_BASE_URL = "https://api.facebook.com/method/fql.query?format=json"

def get_fql(url):
    ''' Generic helper to execute an FQL request and handle error codes.  '''
    
    # record time to get FQL data.
    t1 = time.time()
    
    s = net.get(url)
    
    if not s:
        raise NetException("Failed to execute FQL request, url=%s" % url)
        
    
    # should have json.  check for error or success now.
    o = json.loads(s)
    
    #logger.info("****FQL:")
    #logger.info(o)
    #logger.info("*************")
    
    # type checking is ghetto, but FQL will return a JSON dictionary on error and a potentially a list otherwise.  If it's not a dictionary,
    # skip further error checking.
    
    if isinstance(o, type({})):
        try:

            error_code = o["error_code"]
        
            try:
                error_msg = o["error_msg"]
            except KeyError:
                error_msg = ""
            
            if error_code == 190: # Invalid OAuth 2.0 token
                raise InvalidOAuthException("Invalid auth: error_msg='%s', url=%s" % (error_msg, url))
        
            else:
                raise Exception("FQL error code: %d, error_msg='%s', url=%s" % (error_code, error_msg, url))
                
        except KeyError:
            # no error.  should have successfully retrieved friends json.
            pass
        
    # success

    t2 = time.time()
    x = t2 - t1
    logger.info("get_fql: took %0.2f seconds" % x)

    return o



USER_COLUMNS = [
    "uid", 
    "first_name", 
    "middle_name",
    "last_name",
    "name", # name as it is formatted on FB.
    "pic_square", 
    "religion", 
    "birthday_date", 
    "sex", 
    "meeting_sex", 
    "political", 
    "current_location", 
    "activities",
    "interests", 
    "music", 
    "tv", 
    "movies", 
    "books",
    "relationship_status",
    "is_app_user",
]
USER_COLUMN_CLAUSE = ", ".join(USER_COLUMNS)

def get_user(access_token, uid="me()"):
    ''' Get top level user information.  Return user's info. '''
    
    query = urllib.quote("SELECT %s FROM user WHERE uid = %s" % (USER_COLUMN_CLAUSE, uid))
    
    url = FQL_BASE_URL
    url += "&access_token=%s" % access_token
    url += "&query=%s" % query
    
    logger.debug("get_user fql url = %s" % query)
    
    o = get_fql(url)
    
    # user json comes back as a list of length 1 containing the user's info
    if len(o) != 1:
        raise FQLException("Weird user response: %s" % o)
        
    user = o[0]
    
    return user

def get_friend_app_user_list(access_token, uid="me()"):
    ''' Get list of user's friends who have installed the current application '''
    
    friend_query = "SELECT uid1 FROM friend WHERE uid2 = %s" % str(uid)
    get_app_user_query = "SELECT uid from user where is_app_user=1 and uid in (%s)" % (friend_query)
    get_app_user_query = urllib.quote(get_app_user_query)
    
    url = FQL_BASE_URL
    url += "&access_token=%s" % access_token
    url += "&query=%s" % get_app_user_query
    o = get_fql(url)

    # list of dictionary objects containly only 'uid1' as a key for each uid
    logger.debug(o)
    uids = [ d["uid"] for d in o]
    logger.debug(uids)
    return uids

def get_friend_uid_list(access_token, uid="me()"):
    ''' Get list of users friends with just uids. '''
    
    get_list_query = "SELECT uid1 from friend where uid2 = %s" % str(uid)
    get_list_query = urllib.quote(get_list_query)
    
    url = FQL_BASE_URL
    url += "&access_token=%s" % access_token
    url += "&query=%s" % get_list_query
    o = get_fql(url)
    
    # list of dictionary objects containly only 'uid1' as a key for each uid
    logger.debug(o)
    uids = [ d["uid1"] for d in o]
    logger.debug(uids)
    return uids
        
def get_friends(access_token):
    ''' Get info about all of the user's friends. 
    
        This method can be really expensive so break it down into multiple requests.
        
     '''

    get_friends_query = "SELECT uid1 FROM friend WHERE uid2 = me()" # get all of current users's friends
    
    query = "SELECT %s from user" % USER_COLUMN_CLAUSE
    query += " where uid in (%s)" % get_friends_query
    
    # filter people who are married or in a relationship
    query += " and relationship_status != 'In a relationship'"
    query += " and relationship_status != 'Married'"
    
    query = urllib.quote(query)

    url = FQL_BASE_URL
    url += "&access_token=%s" % access_token
    url += "&query=%s" % query
    
    o = get_fql(url)

    logger.debug("Got friends: %s" % o)
    return o
    
def find_friends_by_name(access_token, name_query):
    ''' search friends to find those who match the given name substring '''
    
    get_friends_query = "SELECT uid1 FROM friend WHERE uid2 = me()" # get all of current users's friends

    query = "SELECT uid, first_name, last_name, name, pic_square, pic_small, pic, pic_big FROM user WHERE uid in (%s) and strpos(lower(name), \"%s\") >= 0" % (get_friends_query, name_query)
    
    query = urllib.quote(query)
    
    url = FQL_BASE_URL
    url += "&access_token=%s" % access_token
    url += "&query=%s" % query
    
    o = get_fql(url)

    logger.debug("Found matching friends: %s" % o)
    return o
    
    