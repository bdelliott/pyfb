''' Code for managing requests to the Facebook Graph API '''

import logging
logger = logging.getLogger()

try:
    import json
except ImportError:
    from django.utils import simplejson as json

import net

FB_GRAPH_BASE_URL = "https://graph.facebook.com"

USER_COLUMNS = [
    "id", 
    "first_name", 
    "last_name",
    "name", # name as it is formatted on FB.
    "religion", 
    "birthday", 
    "gender", 
    "interested_in", # genders user is interested in
    "political", 
    "location", 
    "interests", 
    "music", 
    "picture",
    "television", 
    "movies", 
    "books",
    "relationship_status",
]
USER_COLUMN_CLAUSE = ",".join(USER_COLUMNS)


def authenticate_app(app_id, app_secret, redirect_url, code):
    ''' Authenticate app.  (last step of server-side flow authentication process) '''
    
    url = "%s/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s" % (FB_GRAPH_BASE_URL, app_id, redirect_url, app_secret, code)
    
    logger.info("autenticate_app: code='%s'" % code)    
    logger.info("authenticate_app: url=%s" % url)
    
    s = net.get(url)
    logger.info("authenticate_app: Got '%s'" % s)
    
    # s is a string of the form:
    # 'access_token=AAAENJAf4kUUBAFnyAOxBpLD2O5nJvG5eD4X2ZBKAaZAl23ZA82qExyRZAtO6yILsVgyw963UPvfiOG9wUiHRCiyK5MXOSO5gbZBBdfaPSPu7liNJA9pG7&expires=5242'
    
    # split on & to divide up the 2 useful bits.
    (atok, etok) = s.split("&")
    
    # split each on the equals:
    access_token = atok.split("=")[1]
    expires = etok.split("=")[1]
    
    # expires == number of seconds until token expires.
    return (access_token, expires)


def create_test_user(app_id, app_access_token, installed=True, permissions=[]):
    ''' Create a test user.  The test user cannot interact with real Facebook users.
    
        app_access_token - application access token
        installed - True/False, Specifies whether the user has authorized the app
        permissions - list of extended permissions the app is granted for the user.
    '''
    
    if installed:
        istr = "true"

    else:
        istr = "false"
        # permissions are only valid if installed is true
        permissions = None
        
    permissions = ",".join(permissions)

    url = FB_GRAPH_BASE_URL
    url += "/%s/accounts/test-users?" % app_id
    url += "access_token=%s" % app_access_token
    url += "&installed=%s" % istr
    url += "&permissions=%s" % permissions
        
    s = net.post(url, {})
    
    if s:
        logger.debug("Create test user, response: '%s'" % s)
        return json.loads(s)
    else:
        logger.error("Failed to create test user")
        return None
        

def delete_test_user(uid, access_token):
    ''' Delete the test user '''
    
    url = FB_GRAPH_BASE_URL
    url += "/%s?method=delete&access_token=%s" % (uid, access_token)
    
    s = net.get(url)
    
    if s:
        if s == 'true':
            logger.debug("Deleted test user")
            return True
        else:
            logger.error("Failed to delete test user, response='%s'" % s)
            return None
    else:
        logger.error("Failed to delete test user")
        return False
    
    
def get_application_access_token(app_id, app_secret):
    ''' Get an application access token, as described here:
        http://developers.facebook.com/docs/authentication/#authenticating-as-an-application 
        
        Some graph API calls require one of thse.  
    '''
        
    url = FB_GRAPH_BASE_URL
    url += "/oauth/access_token?"
    url += "client_id=%s" % app_id
    url += "&client_secret=%s" % app_secret
    url += "&grant_type=client_credentials"
    
    s = net.get(url)
    
    if s:
        # in the body of the response will be access_token=
        prefix = "access_token="
        if not s.startswith(prefix):
            logger.error("Got malformed app access token response: '%s'" % s)
        x = len(prefix)
        access_token = s[x:]
        logger.debug("Got application access token: %s" % access_token)
        return access_token
        
    else:
        logger.error("Failed to get application access token")
        return none
            
            
    
def get_friends_list(user_id, access_token, fields=["id"], offset=0, limit=None):
    ''' Get list of the user's friends
    
        fields - list of fields to retrieve. e.g. (name, id)
    '''
    fields = ",".join(fields)
    
    url = "FB_GRAPH_BASE_URL"
    url += "/%s/friends?access_token=%s&fields=%s" % (user_id, access_token, fields)
    if offset:
        url += "&offset=%d" % offset
    if limit:
        url += "&limit=%d" % limit
        
    s = net.get(url)

    if s:
        o = json.loads(s)
        return o["data"]    # data element contains a list of dictionary objects repesenting the friends
    else:
        return None
    


def get_users(user_ids, access_token, fields=None, callback=None):
    ''' Get info about a list of users 
    
        callback - if specific, request will be done asynchronously and a handle to the rpc object will be returned
    '''
    
    user_ids = ",".join(user_ids)
    
    if fields:
        fields = ",".join(fields)
    else:
        fields = USER_COLUMN_CLAUSE
    
    url = "FB_GRAPH_BASE_URL"
    url += "/?ids=%s&access_token=%s&fields=%s" % (user_ids, access_token, fields)

    logger.debug("get_users: url=%s" % url)
    
    def result_callback(result):
        if result:
            o = json.loads(result)
            return callback(o)
        else:
            return callback(None)

    if callback:
        # async
        rpc = net.get_async(url, result_callback)
        return rpc
    else:
        # blocking
        s = net.get(url)
    
        if s:
            o = json.loads(s)
            return o
        else:
            return None
        
        

def get_wall_posts(user_id, access_token):
    ''' requires read_stream to get non-public posts 
    
        Should return a json dictionary containing:
            data - list of posts (maybe up to 50)
            paging - links to get more "pages" of posts
    '''
    
    url = "FB_GRAPH_BASE_URL"
    url += "/%s/feed?access_token=%s" % (user_id, access_token)
    s = net.get(url)
    logger.info("Got user's posts: %s" % s)
    if s:
        o = json.loads(s)
        return o
    else:
        return None
        
def list_test_users(app_id, app_access_token):
    ''' List test users associated with this application '''
    
    url = "FB_GRAPH_BASE_URL"
    url += "/%s/accounts/test-users" % app_id
    url += "?access_token=%s" % app_access_token
        
    s = net.get(url)
    
    if s:
        logger.debug("List test users, response: '%s'" % s)
        o = json.loads(s)
        users = o["data"]
        return users
        
    else:
        logger.error("Failed to list test users")
        return None


def make_test_friends(uid1, user1_access_token, uid2, user2_access_token):
    ''' Make two test users friends. '''
    
    # create friend request from u1 to u2
    url = "FB_GRAPH_BASE_URL"
    url += "/%s/friends/%s" % (uid1, uid2)
    url += "?access_token=%s" % user1_access_token
    
    s = net.post(url)

    if s:
        logger.debug("make_test_friends: created friend request from u1->2:, response: '%s'" % s)
    else:
        logger.error("make_test_friends: Failed to create friend request from u1->u2")
        return False
    
    
    # confirm friend request to u2
    url = "FB_GRAPH_BASE_URL"
    url += "/%s/friends/%s" % (uid2, uid1)
    url += "?access_token=%s" % user2_access_token
    
    s = net.post(url)

    if s:
        logger.debug("make_test_friends: created friend request from u1->2:, response: '%s'" % s)
        return True
    else:
        logger.error("make_test_friends: Failed to create friend request from u1->u2")
        return False
    
def post_to_wall(access_token, user_id, message, link=None, name=None, description=None, caption=None, picture=None, 
                                                 source=None, wall_filtering=True, allowed_ids=[]):
    ''' Post a message to the user's wall. 
    
        message - message to post
        link - Link attached ot the post
        name - Name of the link
        description - Description of the link
        caption - link caption
        picture - link to the picture included with the post
        source - URL to Flash movie or video file used within the post.
        wall_filtering - flag to avoid making test posts on other people's walls
        
    '''
    
    # first check filtering settings.  for spam filtering, we do not post to user's walls for any sort of test messages.
    if wall_filtering:
        
        if user_id == "me":
            # special user id referring to user whose access token we're throwing about.  always ok, this is only going to be seen in dev
            # code.
            pass
            
        elif user_id not in allowed_ids:
            logger.warn("User '%s' is NOT on the approved list for wall posting.  Skipping" % user_id)
            return
            
        
    url = FB_GRAPH_BASE_URL + "/%s/feed?access_token=%s" % (user_id, access_token)

    #if not caption:
    #    caption = "Spark matcher caption"
        
    data = {
        "message" : message,
    }
    if caption is not None:
        data["caption"] = caption
    if link:
        data["link"] = link
    if name:
        data["name"] = name
    if description:
        data["description"] = description
    if picture:
        data["picture"] = picture
    if source:
        data["source"] = source
            
    
    
    s = net.post(url, data)
    
    # returns info about the post
    if s:
        o = json.loads(s)
        
        # object is a dictionary with just "id" in it, probably meaning the post id.
        logger.error("POST returned: " + s)
        
        return o
    else:
        logger.error("post_to_wall: failed to post to url: %s" % url)
        return None
