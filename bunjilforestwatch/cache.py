# Based on cache.py from Matt Jibson <matt.jibson@gmail.com>, modified by Chris Goodman for Bunjil Forest Watch
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import logging
import models

import counters
import feeds
import utils
import webapp2

from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.datastore import entity_pb

# use underscores since usernames are guaranteed to not have them
# still a problem with journal names?
C_AREA_KEY = 'area_key_%s_%s'
C_AREA= 'area_%s_%s'
C_AREAS = 'areas_%s'
C_OTHER_AREAS = 'other_areas_%s'
C_AREA_LIST = 'areas_list_%s'
C_AREAS_ALL = 'areas'
C_AREA_ALL_LIST = 'areas_list'
C_AREA_FOLLOWERS = 'area_followers_%s'
C_FOLLOWING_AREAS = 'following_areas_%s'
C_FOLLOWING_AREA_KEYS = 'following_area_keys_%s'
C_FOLLOWING_AREAS_LIST = 'following_areas_list_%s'
C_FOLLOWING_AREANAMES_LIST = 'following_areanames_list_%s'

C_ACTIVITIES = 'activities_%s_%s_%s'
C_ACTIVITIES_FOLLOWER = 'activities_follower_%s'
C_ACTIVITIES_FOLLOWER_DATA = 'activities_follower_data_%s'
C_ACTIVITIES_FOLLOWER_KEYS = 'activities_follower_keys_%s'
C_BLOG_COUNT = 'blog_count'
C_BLOG_ENTRIES_KEYS = 'blog_entries_keys'
C_BLOG_ENTRIES_KEYS_PAGE = 'blog_entries_keys_page_%s'
C_BLOG_ENTRIES_PAGE = 'blog_entries_page_%s'
C_BLOG_TOP = 'blog_top'


C_CELL      = 'cell_%s_%s_%s'
C_CELL_KEY = 'cellkey_%s'
C_CELLS     = 'cells_%s'
C_CELLS_ALL     = 'allcells'
C_CELL_NAME = 'cellname_%s_%s'

C_ENTRIES_KEYS = 'entries_keys_%s'
C_ENTRIES_KEYS_PAGE = 'entries_keys_page_%s_%s'
C_ENTRIES_PAGE = 'entries_page_%s_%s_%s'
C_ENTRY = 'entry_%s_%s_%s'
C_ENTRY_KEY = 'entry_key_%s_%s_%s'
C_ENTRY_RENDER = 'entry_render_%s_%s_%s'

C_OBSTASKS_KEYS = 'obstasks_keys_%s'
C_OBSTASKS_KEYS_PAGE = 'obstasks_keys_page_%s_%s'
C_OBSTASKS_PAGE = 'obstasks_page_%s_%s'

C_OBSTASK = 'obstask_%s'
C_OBSTASK_KEY = 'obstask_key_%s'
C_OBSTASK_RENDER = 'obstask_render_%s'


C_FEED = 'feed_%s_%s'
C_FOLLOWERS = 'followers_%s'
C_FOLLOWING = 'following_%s'
C_JOURNAL = 'journal_%s_%s'
C_JOURNALS = 'journals_%s'
C_JOURNAL_KEY = 'journal_key_%s_%s'
C_JOURNAL_LIST = 'journals_list_%s'

C_OBS_TASK = 'obstask_%s'

C_KEY = 'key_%s'
C_STATS = 'stats'

def set(value, c, *args):
    memcache.set(c %args, value)

def set_multi(mapping):
    memcache.set_multi(mapping)

def set_keys(entities):
    memcache.set_multi(dict([(C_KEY %i.key, pack(i)) for i in entities]))

def delete(keys):
    memcache.delete_multi(keys)

def delete_item(key):
    memcache.delete(key)

def flush():
    memcache.flush_all()

def pack(data_models):
    if data_models is None:
        return None
    elif isinstance(data_models, ndb.Model):
    # Just one instance
        return ndb.ModelAdapter().entity_to_pb(data_models).Encode()
    else:
    # A list
        return [ndb.ModelAdapter().entity_to_pb(x).Encode() for x in data_models]

def unpack(data):
    if data is None:
        return None
    elif isinstance(data, str):
    # Just one instance
        return ndb.ModelAdapter().pb_to_entity(entity_pb.EntityProto(data)) 
    else:
        return [ndb.ModelAdapter().pb_to_entity(entity_pb.EntityProto(x)) for x in data]

def get_by_key(key):
    n = C_KEY %key
    data = memcache.get(n)
    if data is None:
        data = ndb.Key(urlsafe=key)
        memcache.add(n, data)
    return data

# idea: use async functions, although i'm not convinced it'd be faster
# fetches all keys; if kind is specified, converts the given key names to keys of that kind
def get_by_keys(keys, kind=None):
    #print("get_by_keys: ", keys)    
    if kind:
        keys = [str(ndb.Key.from_path(kind, i)) for i in keys]
    #print("  get_by_keys as kind: ", keys, kind)
    for i in keys:
        decode_key(i) #debug
    client = memcache.Client()
    values = client.get_multi(keys)
    #print("  get_by_keys values: ", values)    

    data = [values.get(i) for i in keys]
    #print("get_by_keys values, data: ", values, data)    

    if None in data:
        to_fetch = []
        for i in range(len(keys)):
            if data[i] is None:
                to_fetch.append(i)
    
        fetch_keys = [keys[i] for i in to_fetch]
        fetched = ndb.get(fetch_keys)
        set_multi(dict(zip(fetch_keys, fetched)))
        #print("get_by_keys to_fetch : ", to_fetch, fetch_keys, fetched)    

        for i in to_fetch:
            data[i] = fetched.pop(0)

    return data

def decode_key(key):
    #for debugging print the path of the key.
    k = ndb.Key(key)
    _app = k.app()
    path = []
    while k is not None:
        path.append(k.id_or_name())
        path.append(k.kind())
        k = k.parent()
    path.reverse()
    #print 'app=%r, path=%r' % (_app, path)

def get_areas(user_key):  #return all areas's owned by user.
    n = C_AREAS %user_key
    data = memcache.get(n)
    if data is None:
        data = models.AreaOfInterest.query(models.AreaOfInterest.owner == user_key). \
        order(-models.AreaOfInterest.last_modified). \
        fetch(models.AreaOfInterest.MAX_AREAS)
        memcache.add(n, data)

    return data

def get_area_count(user_key):  #return all areas's owned by user.
    return models.AreaOfInterest.query(models.AreaOfInterest.owner == user_key).count()
    
def get_other_areas(user_key): # returns list of areas user neither created nor follows. User can select an area from this list to follow.
    n = C_OTHER_AREAS %user_key
    data = memcache.get(n)
    if data is None:
        all_area_keys = models.AreaOfInterest.query(). \
            filter(models.AreaOfInterest.owner != user_key). \
            filter(models.AreaOfInterest.share == models.AreaOfInterest.PUBLIC_AOI ).  \
            fetch(keys_only=True)
        af = get_following_area_keys(user_key) # a list of area keys.
        other_areas_keys = [x for x in all_area_keys if x not in af] # remove areas user is following from list of all_areas
        otherareas = ndb.get_multi(other_areas_keys)
        data = otherareas
        memcache.add(n, data)

    return data

def get_other_areas_list(user_key): # returns list of areas that user neither created nor follows - stripped just main properties for a list. User can select an area from this list to follow.
    otherareas = get_other_areas(user_key)
    return [x.summary_dictionary() for x in otherareas]


# returns a list of user's area names
def get_areas_list(user_key):
    n = C_AREA_LIST %user_key
    data = memcache.get(n)
    if data is None:
        areas= get_areas(user_key)
        data = [(i.url(), i.name) for i in areas]
        memcache.add(n, data)

    return data

#get_all_areas() returns a list of keys for all areas - inlcuding private and unlisted areas.
def get_all_areas():
    n = C_AREAS_ALL
    data = memcache.get(n)
    if data is None:
        data = models.AreaOfInterest.query().fetch(300) #FIXME limit of 300 will be a problem in future. This is used by CheckNew cron job.
        memcache.add(n, data)

    return data

# returns a list of user's area names
def get_all_areas_list():
    n = C_AREA_ALL_LIST
    data = memcache.get(n)
    if data is None:
        areas= get_areas()
        data = [(i.url(), i.name) for i in areas] #add i.user and i.followers
        memcache.add(n, data)

    return data


def get_journals(user_key):
    n = C_JOURNALS %user_key
    data = memcache.get(n)
    if data is None:
        data = models.Journal.query(ancestor=user_key).fetch(models.Journal.MAX_JOURNALS)
        
        memcache.add(n, data)

    return data

# returns a list of journal names
def get_journal_list(user_key):
    n = C_JOURNAL_LIST %user_key
    data = memcache.get(n)
    if data is None:
        journals = get_journals(user_key)
        data = [(j.url(), j.key.string_id(), j.journal_type) for j in journals]
        memcache.add(n, data)

    return data

# returns all entry keys sorted by descending date
def get_entries_keys(journal_key):
    n = C_ENTRIES_KEYS %journal_key
    data = memcache.get(n)
    if data is None:
        # todo: fix limit to 1000 most recent journal entries
        data = models.Entry.query(ancestor = journal_key).order(-models.Entry.date).fetch(300, keys_only=True)
        memcache.add(n, data)
    return data

# returns entry keys of given page
def get_entries_keys_page(journal_key, page):
    n = C_ENTRIES_KEYS_PAGE %(journal_key, page)
    data = memcache.get(n)
    if data is None:
        entries = get_entries_keys(journal_key)
        data = entries[(page  - 1) * models.Journal.ENTRIES_PER_PAGE:page * models.Journal.ENTRIES_PER_PAGE]
        memcache.add(n, data)

        if not data:
            logging.warning('Page %i requested from %s, but only %i entries, %i pages.', page, journal_key, len(entries), len(entries) / models.Journal.ENTRIES_PER_PAGE + 1)

    return data

# returns entries of given page
def get_entries_page(username, journal_name, page, journal_key):
    n = C_ENTRIES_PAGE %(username, journal_name, page)
    data = memcache.get(n)
    if data is None:
        if page < 1:
            page = 1

        entries = get_entries_keys_page(journal_key, page)
        data = [unicode(get_entry_render(username, journal_name, i.id())) for i in entries]
        memcache.add(n, data)

    return data

# called when a new entry is posted, and we must clear all the entry and page cache
def clear_entries_cache(journal_key):
    journal = journal_key.get()
    keys = [C_ENTRIES_KEYS %journal_key, C_JOURNALS %journal_key.parent()]

    # add one key per page for get_entries_page and get_entries_keys_page
    for p in range(1, journal.entry_count / models.Journal.ENTRIES_PER_PAGE + 2):
        keys.extend([C_ENTRIES_PAGE %(journal.key.parent().string_id(), journal.key.string_id(), p), C_ENTRIES_KEYS_PAGE %(journal_key, p)])
    memcache.delete_multi(keys)



##### OBSTASK LIST #####

def get_obstask(task_name):
    obstask_key = ndb.Key('ObservationTask', task_name)
    task = obstask_key.get()
    if task:
        return task
    
    logging.error('get_obstask(): no task found for %s', task_name)
    #Second attempt
    obstask_key = ndb.Key(urlsafe = task_name) 
    task_id = obstask_key.id()
    task = models.ObservationTask.get_by_id(task_id)
    if not task:
        logging.error('get_obstask(): no task found for %s with id %d', task_name, task_id)
    return task

''' get a single ObserevationTask by its key name.
'''
def get_task(task_key_name):
   
    n = C_OBS_TASK %(task_key_name)
    data = memcache.get(n)
    if data is None:
        #data= get_by_key(task_key_name).get()
        data= task_key_name.get()
        if data is None:
            logging.error("get_task(): Not an object") 
            return None
        else:
            if data.key.kind() != "ObservationTask":
                logging.error("get_task(): Not a task object") 
                return None
        memcache.add(n, data)
    return data


def get_obstask_key(entry_id):
    n = C_OBSTASK_KEY %(entry_id)
    data = memcache.get(n)
    if data is None:
        data = ndb.get(ndb.Key('ObservationTask', long(entry_id) ))
        if data:
            data = data.key
        memcache.add(n, data)
    return data

''' 
    get_obstasks_keys() returns all ObservationTask keys sorted by descending date, filtered by username OR areaname but not both.
'''

def get_obstasks_keys(username=None, areaname=None):
    
    if areaname is not None:
        n = C_OBSTASKS_KEYS%(areaname)
    else:
        n = C_OBSTASKS_KEYS%(username)
    data = memcache.get(n)
    if data is None:
        # todo: fix limit to 1000 most recent journal obstasks
        if username is not None:
            user_key = ndb.Key('User', username)
            #data = models.ObservationTask.all(keys_only=True).filter('assigned_owner =', user_key).order('-created_date').fetch(200)
            data = models.ObservationTask.query(models.ObservationTask.assigned_owner == user_key).order(-models.ObservationTask.created_date).fetch(200, keys_only=True)
            logging.debug("get_obstasks_keys for user %s %s", username, user_key)
            if len(data) == 0 :
                logging.info("get_obstasks_keys() user %s has no tasks", username)
        elif areaname is not None:
            area = get_area(username, areaname) 
            area_key = ndb.Key('AreaOfInterest', areaname)
            
            #print ("area_key ", area_key)
            if (area.share == area.PRIVATE_AOI ) and (area.owner.name != username):
                logging.debug("get_obstasks_keys PERMISSION ERROR for %s area %s %s", area.shared_str, areaname, area_key, )
                data = None
            else:
                #data = models.ObservationTask.all(keys_only=True).filter('aoi =', area_key).order('-created_date').fetch(200)
                data = models.ObservationTask.query(models.ObservationTask.aoi == area_key).order(-models.ObservationTask.created_date).fetch(200, keys_only=True)
                logging.debug("get_obstasks_keys for %s area %s %s", area.shared_str, areaname, area_key)
                if len(data) == 0:
                    logging.info("get_obstasks_keys() area %s has no tasks", areaname)
        else:
            data = models.ObservationTask.query(models.ObservationTask.share == models.AreaOfInterest.PUBLIC_AOI).order(-models.ObservationTask.created_date).fetch(200, keys_only=True)
            logging.debug("get_obstasks_keys() loading cache for all tasks")
        memcache.add(n, data)
    return data


''' 
    get_obstasks_keys_page() returns all ObservationTask keys for a given page - sorted by descending date, filtered by username OR areaname but not both.
'''
def get_obstasks_keys_page(page, username=None, areaname=None):
    if areaname is not None:    
        n = C_OBSTASKS_KEYS_PAGE %(page,areaname)
    elif username is not None:    
        n = C_OBSTASKS_KEYS_PAGE %(page,username)
    else:    
        n = C_OBSTASKS_KEYS_PAGE %(page, None)
        
    data = memcache.get(n)
    if data is None:
        obstasks = get_obstasks_keys(username, areaname)
        if obstasks != None:
            data = obstasks[(page  - 1) * models.ObservationTask.OBSTASKS_PER_PAGE:page * models.ObservationTask.OBSTASKS_PER_PAGE]
            memcache.add(n, data)
            if not data:
                logging.warning('Page %i requested but only %i obstasks, %i pages.', page, len(obstasks), len(obstasks) / models.ObservationTask.OBSTASKS_PER_PAGE + 1)
    return data

# returns rendered list of ObservationTasks of given page
def get_obstasks_page(page, username=None, areaname=None):
    if areaname is not None:    
        n = C_OBSTASKS_PAGE %(page, areaname)
    elif username is not None:    
        n = C_OBSTASKS_PAGE %(page, username)
    else:    
        n = C_OBSTASKS_PAGE %(page, None)
 
    data = memcache.get(n)
    if data is None:
        if page < 1:
            page = 1

        obstasks = get_obstasks_keys_page(page, username, areaname)
        if obstasks:
            data = [unicode(get_obstask_render(i)) for i in obstasks]
            memcache.add(n, data)
    return data

'''
    get_obstask_render()

    Renders an ObservationTask into an HTML row.
    Page won't be updated more than once if task already in the cache - unless reload is true.
'''

def get_obstask_render(task_key, reload=False):
    n = C_OBSTASK_RENDER %(task_key)
    data = memcache.get(n)
    if data is None or reload == True:
        obstask = get_task(task_key)
        obslist = []  
        if obstask is not None:
            area = obstask.aoi.get() 
            resultstr = "Observation Task for {0!s} to check area {1!s} <br>".format(obstask.assigned_owner.string_id(), area.name.encode('utf-8') )
            resultstr += "{0!s} Task assigned to: <i>{1!s}</i><br>".format(obstask.shared_str(), obstask.assigned_owner.string_id())
            resultstr += "Status <em>{0!s}</em>. ".format(obstask.status)
            if obstask.priority != None:
                resultstr += "Priority <em>{0:d}.</em> ".format(obstask.priority)
            
            #debugstr = resultstr + " task: " + str(obstask.key) + " has " + str(len(obstask.observations)) + " observations"
            debugstr = resultstr + "Task has " + str(len(obstask.observations)) + " observations"
            for obs_key in obstask.observations:
                obs = obs_key.get() 
                if obs is not None:
                    obslist.append(obs.Observation2Dictionary()) # includes a list of precomputed overlays
                else:
                    logging.error("Missing Observation from cache")        
        
        data = utils.render('obstask-render.html', {
            'obstask': obstask,
            'obslist': obslist,
            'resultstr': debugstr,
            'area' :  area.name.encode('utf-8'),
            'created_date' : obstask.created_date.strftime("%Y-%m-%d"),
            'obstask_url': obstask.taskurl()
            } )
        memcache.add(n, data)

    return data


def clear_obstasks_cache(username=None, areaname=None):

    obstasks = get_obstasks_keys(username, areaname)
    if obstasks:
        pages = len(obstasks) / models.ObservationTask.OBSTASKS_PER_PAGE + 1    
        for page in pages:
            if areaname is not None:
                memcache.delete_multi([    
                        C_OBSTASKS_KEYS%(areaname),
                        C_OBSTASKS_PAGE %(page, areaname),
                        C_OBSTASKS_KEYS_PAGE %(page,areaname)
            ])
            if username is not None:
                memcache.delete_multi([    
                        C_OBSTASKS_KEYS%(username),
                        C_OBSTASKS_PAGE %(page, username),
                        C_OBSTASKS_KEYS_PAGE %(page,username)
            ])
            if areaname is None and username is None:
                memcache.delete_multi([    
                       C_OBSTASKS_PAGE %(page, None),
                       C_OBSTASKS_KEYS_PAGE %(page, None)
                ])
        logging.debug('cleared %d obstask pages', pages )

###########

def get_stats():
    n = C_STATS
    data = memcache.get(n)
    if data is None:
        data = [(i, counters.get_count(i)) for i in [
            counters.COUNTER_USERS,
            counters.COUNTER_JOURNALS,
            counters.COUNTER_AREAS,
            counters.COUNTER_ENTRIES,
            counters.COUNTER_OBSTASKS,
            counters.COUNTER_CHARS,
            counters.COUNTER_WORDS,
            counters.COUNTER_OBSTASKS,
            counters.COUNTER_SENTENCES,
            counters.COUNTER_SENTENCES,
        ]]

        memcache.add(n, data)

    return data

def clear_area_cache(user_key, area_key):
    #print "clear_area_cache(%s, %s)", user_key, area_key
    tag = "users"
    r = memcache.delete_multi([    C_AREAS_ALL,
                            C_AREA_ALL_LIST,
                            C_AREAS %user_key, 
                            C_AREA_LIST %user_key, 
                            C_OTHER_AREAS %user_key, 
                            C_FOLLOWING_AREAS %user_key,
                            C_FOLLOWING_AREAS_LIST %user_key, 
                            C_FOLLOWING_AREANAMES_LIST %user_key,
                            C_AREA_FOLLOWERS %area_key,
                            C_AREA %(user_key, area_key),
                            C_AREA %(tag, area_key) ])
    logging.debug ('clear_area_cache() returning: %s', r)
    return r


def clear_area_followers(area_key): 
    memcache.delete(C_AREA_FOLLOWERS %area_key)

def clear_journal_cache(user_key):
    memcache.delete_multi([C_JOURNALS %user_key, C_JOURNAL_LIST %user_key])

def get_activities(username='', action='', object_key=''):
    n = C_ACTIVITIES %(username, action, object_key)
    data = memcache.get(n)
    if data is None:
        data = models.Activity.query()

        if username:
            data = data.filter(models.Activity.user == username)
            logging.debug('activity filter user=%s', username)
        if action:
            data = data.filter(models.Activity.action, action)
        if object_key:
            data = data.filter(models.Activity.object, object_key)

        data = data.order(-models.Activity.date).fetch(models.Activity.RESULTS)
        memcache.add(n, data, 60) # cache for 1 minute

    return data

def get_activities_follower_keys(username):
    n = C_ACTIVITIES_FOLLOWER_KEYS %username
    data = memcache.get(n)
    if data is None:
        #index_keys = models.ActivityIndex.all(keys_only=True).filter('receivers', username).order('-date').fetch(50)
        ActivityIdx = models.ActivityIndex
        index_keys = ActivityIdx.query(ActivityIdx.receivers == username).order(-ActivityIdx.date).fetch(models.Activity.RESULTS, keys_only=True, )
        data = [str(i.parent()) for i in index_keys]
        memcache.add(n, data, 300) # cache for 5 minutes

    return data

def get_activities_follower_data(keys):
    n = C_ACTIVITIES_FOLLOWER_DATA %'_'.join(keys)
    data = unpack(memcache.get(n))
    if data is None:
        data = ndb.get_multi(keys)
        memcache.add(n, pack(data)) # no limit on this cache since this data never changes

    return data

def get_activities_follower(username):
    n = C_ACTIVITIES_FOLLOWER %username
    data = unpack(memcache.get(n))
    if data is None:
        keys = get_activities_follower_keys(username)
        # perhaps the keys didn't change, so keep a backup of that data
        data = get_activities_follower_data(keys)
        memcache.add(n, pack(data), 300) # cache for 5 minutes

    return data

def get_feed(feed, token):
    n = C_FEED %(feed, token)
    data = memcache.get(n)
    if data is None:
        data = feeds.feed(feed, token)
        memcache.add(n, data, 600) # cache for 10 minutes

    return data


def get_user(username):
    user_key = ndb.Key('User', username)
    #return get_by_key(user_key)
    return user_key.get()

def get_followers(username):
    n = C_FOLLOWERS %username
    data = memcache.get(n)
    if data is None:
        followers = models.UserFollowersIndex.get_by_id(username, parent=ndb.Key('User', username))
        if not followers:
            data = []
        else:
            data = followers.users

        memcache.add(n, data)

    return data

def get_following(username):
    n = C_FOLLOWING %username
    data = memcache.get(n)
    if data is None:
        following = models.UserFollowingIndex.get_by_id(username, parent=ndb.Key('User', username))
        if not following:
            data = []
        else:
            data = following.users

        memcache.add(n, data)

    return data

def get_area_followers(area_name):
    n = C_AREA_FOLLOWERS %area_name
    data = memcache.get(n)
    if data is None:
        data= models.AreaFollowersIndex.get_by_id(area_name, parent=ndb.Key('AreaOfInterest', area_name))
        memcache.add(n, data)
    return data

'''
get_following_area_keys() given a user key, returns a list of area keys that the user follows.
'''

def get_following_area_keys(user_key): 
    n = C_FOLLOWING_AREA_KEYS %user_key
    data = memcache.get(n)
    if data is None:
        following = models.UserFollowingAreasIndex.get_by_username(user_key.id()) 
        data = []
        if not following:
            logging.debug("get_following_area_keys(): %s not following any areas", user_key.string_id()) 
        else:
            data = following.area_keys
        memcache.add(n, data)
        logging.debug("get_following_area_keys() reloaded: %s ", user_key.string_id())

    return data


'''
get_following_areas() given a user key, returns a UserFollowingAreasIndex entity that contains a list the names of areas that the user follows.

'''

def get_following_areas(user_key): 
    n = C_FOLLOWING_AREAS %user_key
    data = memcache.get(n)
    if data is None:
        following = models.UserFollowingAreasIndex.get_by_username(user_key.id()) 
        data = []
        if not following:
            logging.debug("get_following_areas(): %s not following any areas", user_key.string_id()) 
        else:
            following_areas = following.areas
            allareas = models.AreaOfInterest.query()  #TODO: This is inefficient. Give each user model a list.
            data = [x for x in allareas if x.name in following_areas]
        memcache.add(n, data)
        
        logging.debug("get_following_areas() reloaded: %s ", user_key.string_id())

    return data

def get_following_areas_list(user_key):
    n = C_FOLLOWING_AREAS_LIST %user_key
    data = memcache.get(n)
    if data is None:
        areas= get_following_areas(user_key)
        data = [(i.url(), i.name) for i in areas]
        memcache.add(n, data)
        if user_key is not None:
            logging.debug("get_following_areas_list() reloaded user_key: %s", user_key.string_id())
        else:
            logging.error("get_following_areas_list() no user key")
    return data

def get_following_areanames_list(user_key): #as above but returns list of names only without urls for excluding from other_areas
    n = C_FOLLOWING_AREANAMES_LIST %user_key
    data = memcache.get(n)
    if data is None:
        areas= get_following_areas(user_key)
        if areas:
            data = [i.name for i in areas]
            #data = [get_area(None, i).name for i in areas]
        else:
            logging.debug("get_following_areanames_list()     no following_areas")
            data = []
        memcache.add(n, data)
        #logging.debug("get_following_areanames_list() reloaded: ", user_key)
 
    return data


def get_area(username, area_name):
    n = C_AREA %(username, area_name)
    data = memcache.get(n)
    if data is None:
        data = models.AreaOfInterest.get_by_id(area_name.decode('utf-8'))
        if data is None:
            logging.error("get_area() no area found for %s %s", username, area_name)
            return None
        memcache.add(n, data)
    return data


def get_area_key(username, area_name):
    if username is None:
        n = C_AREA_KEY %("users", area_name)  #users a reserved name so never a username. Fetch areas for all users.
        data = memcache.get(n)
        if data is None:
            #data = models.AreaOfInterest.all(keys_only=True).filter('name', area_name.decode('utf-8')).get()
            data = models.AreaOfInterest.query(models.AreaOfInterest.name == area_name.decode('utf-8')).fetch(keys_only=True)
            memcache.add(n, data)
    else:
        n = C_AREA_KEY %(username, area_name)
        data = memcache.get(n)
        if data is None:
            data = models.AreaOfInterest.query(models.AreaOfInterest.owner == username, models.AreaOfInterest.name == area_name.decode('utf-8')).fetch(keys_only=True)
            memcache.add(n, data)
    return data


def get_cell(path, row, area_name):    
    n = C_CELL %(path, row, area_name)
    data = unpack(memcache.get(n))
    if data is None:  
        data = models.LandsatCell.get_cell(path, row, area_name)
        if data is None:
            logging.error("cache:get_cell() did not find cell object %d %d for area %s", path, row, area_key)
        else:
            memcache.add(n, pack(data))
    return data
  
def get_cells(area_key):
    n = C_CELLS %area_key
    data = unpack(memcache.get(n))
    if data is None:
        data = models.LandsatCell.all().filter('area =',  area_key)
        #print "get_areas()", data
        memcache.add(n, pack(data))
    return data


def get_all_cells(): #FIXME - Doesn't work - too much data returned. 
    n = C_CELLS_ALL
    data = unpack(memcache.get(n))
    if data is None:
        data = models.LandsatCell.all() #TODO This is a big load from ndb.
        memcache.add(n, pack(data))
    return data

def get_journal_key(username, journal_name):
    n = C_JOURNAL_KEY %(username, journal_name)
    data = memcache.get(n)
    if data is None:
        user_key = ndb.Key('User', username)
        data = ndb.Key('Journal', journal_name, parent=user_key)
        memcache.add(n, data)
    return data

def get_entry(username, journal_name, entry_id, entry_key=None):
    return models.Entry.get_entry(username, journal_name, entry_id, entry_key)
    
def get_entry_render(username, journal_name, entry_id):
    n = C_ENTRY_RENDER %(username, journal_name, entry_id)
    data = memcache.get(n)
    if data is None:
        entry, content, blobs = get_entry(username, journal_name, entry_id)
        data = utils.render('entry-render.html', {
            'blobs': blobs,
            'content': content,
            'entry': entry,
            'entry_url': webapp2.uri_for('view-entry', username=username, journal_name=journal_name, entry_id=entry_id),
        })
        memcache.add(n, data)

    return data

