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
    return db.Key(urlsafe=key)
    '''
    n = C_KEY %key
    data = memcache.get(n)
    if data is None:
        data = ndb.Key(urlsafe=key)
        memcache.add(n, data)
    return data
    '''

# idea: use async functions, although i'm not convinced it'd be faster
# fetches all keys; if kind is specified, converts the given key names to keys of that kind
def get_by_keys(keys, kind=None):
    #print("get_by_keys: ", keys)
    if kind:
        keys = [str(ndb.Key.from_path(kind, i)) for i in keys]
    return ndb.get_multi(keys)


def get_areas(user_key):  #return all areas's owned by user.
    data = models.AreaOfInterest.query(models.AreaOfInterest.owner == user_key). \
    order(-models.AreaOfInterest.last_modified). \
    fetch(models.AreaOfInterest.MAX_AREAS)
    return data

def get_area_count(user_key):  #return all areas's owned by user.
    return models.AreaOfInterest.query(models.AreaOfInterest.owner == user_key).count()
    
def get_other_areas(user_key): # returns list of areas user neither created nor follows. User can select an area from this list to follow.
    all_area_keys = models.AreaOfInterest.query(). \
        filter(models.AreaOfInterest.owner != user_key). \
        filter(models.AreaOfInterest.share == models.AreaOfInterest.PUBLIC_AOI ).  \
        fetch(models.AreaOfInterest.MAX_OTHER_AREAS, keys_only=True)
        #order(-models.AreaOfInterest.last_modified). \ # first sort property is last_modified but the inequality filter is on owner

    af = get_following_area_keys(user_key) # a list of area keys.
    other_areas_keys = [x for x in all_area_keys if x not in af] # remove areas user is following from list of all_areas
    otherareas = ndb.get_multi(other_areas_keys)
    data = otherareas
    return data

def get_other_areas_list(user_key): # returns list of areas that user neither created nor follows - stripped just main properties for a list. User can select an area from this list to follow.
    otherareas = get_other_areas(user_key)
    return [x.summary_dictionary() for x in otherareas]


# returns a list of user's area names
def get_areas_list(user_key):
    areas= get_areas(user_key)
    data = [(i.url(), i.name) for i in areas]
    return data

#get_all_areas() returns a list of keys for all areas - inlcuding private and unlisted areas.
def get_all_areas():
    data = models.AreaOfInterest.query().fetch(300) #FIXME limit of 300 will be a problem in future. This is used by CheckNew cron job.
    return data


#get_all_glad_areas() returns a list of keys for all areas - inlcuding private and unlisted areas.
def get_all_glad_areas():
    data = models.AreaOfInterest.query().filter(models.AreaOfInterest.glad_monitored == True).fetch(300)
    #@FIXME limit of 300 will be a problem in future. This is used by CheckNewGlad cron job.
    return data

def get_journals(user_key):
    data = models.Journal.query(ancestor=user_key).fetch(models.Journal.MAX_JOURNALS)
    return data

# returns a list of journal names
def get_journal_list(user_key):
    journals = get_journals(user_key)
    data = [(j.url(), j.key.string_id(), j.journal_type) for j in journals]
    return data

# returns all entry keys sorted by descending date
def get_entries_keys(journal_key):
        # todo: fix limit to 1000 most recent journal entries
    data = models.Entry.query(ancestor = journal_key).order(-models.Entry.date).fetch(300, keys_only=True)
    return data

# returns entry keys of given page
def get_entries_keys_page(journal_key, page):
    entries = get_entries_keys(journal_key)
    data = entries[(page  - 1) * models.Journal.ENTRIES_PER_PAGE:page * models.Journal.ENTRIES_PER_PAGE]
    if not data:
        logging.warning('Page %i requested from %s, but only %i entries, %i pages.', page, journal_key, len(entries), len(entries) / models.Journal.ENTRIES_PER_PAGE + 1)
    return data

# returns entries of given page
def get_entries_page(username, journal_name, page, journal_key):
    if page < 1:
        page = 1

    entries = get_entries_keys_page(journal_key, page)
    data = [unicode(get_entry_render(username, journal_name, i.id())) for i in entries]
    return data

# called when a new entry is posted, and we must clear all the entry and page cache
def clear_entries_cache(journal_key):
    logging.error('clear_entries_cache DISABLED')


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
    task = models.Old_ObservationTask.get_by_id(task_id)
    if not task:
        logging.error('get_obstask(): no task found for %s with id %d', task_name, task_id)
    return task

'''
get a single ObserevationTask by its key name.
@returns: ObsTask or None:
'''
def get_task(task_key_name):

    data = task_key_name.get()
    if data is None:
        logging.error("get_task(): Not an object")
        return None
    else:
        if data.key.kind() != "ObservationTask":
            logging.error("get_task(): Not a task object")
            return None
    return data


def get_obstask_key(entry_id):
    data = ndb.get(ndb.Key('ObservationTask', long(entry_id) ))
    if data:
        data = data.key
    return data

''' 
    get_obstasks_keys() returns all ObservationTask keys sorted by descending date, filtered by username OR areaname but not both.
    @todo: fix limit to 1000 most recent journal obstasks
'''

def get_obstasks_keys(username=None, areaname=None):
    if username is not None:
        user_key = ndb.Key('User', username)
        #data = models.ObservationTask.all(keys_only=True).filter('assigned_owner =', user_key).order('-created_date').fetch(200)
        data = models.Old_ObservationTask.query(models.Old_ObservationTask.assigned_owner == user_key).order(-models.Old_ObservationTask.created_date).fetch(200, keys_only=True)
        logging.debug("get_obstasks_keys for user %s %s", username, user_key)
        if len(data) == 0 :
            logging.info("get_obstasks_keys() user %s has no tasks", username)
    elif areaname is not None:
        area = get_area(areaname)
        area_key = ndb.Key('AreaOfInterest', areaname)
        owner = area.owner.get()
        if (area.share == area.PRIVATE_AOI ) and (owner.name != username):
            logging.debug("get_obstasks_keys PERMISSION ERROR for %s area %s %s", area.shared_str, areaname, area_key)
            data = None
        else:
            #data = models.ObservationTask.all(keys_only=True).filter('aoi =', area_key).order('-created_date').fetch(200)
            data = models.Old_ObservationTask.query(models.Old_ObservationTask.aoi == area_key).order(-models.Old_ObservationTask.created_date).fetch(200, keys_only=True)
            logging.debug("get_obstasks_keys for %s area %s %s", area.shared_str, areaname, area_key)
            if len(data) == 0:
                logging.info("get_obstasks_keys() area %s has no tasks", areaname)
    else:
        data = models.Old_ObservationTask.query(models.Old_ObservationTask.share == models.AreaOfInterest.PUBLIC_AOI).order(-models.Old_ObservationTask.created_date).fetch(200, keys_only=True)
        logging.debug("get_obstasks_keys() loading cache for all tasks")
    return data


''' 
    get_obstasks_keys_page() returns all ObservationTask keys for a given page - sorted by descending date, filtered by username OR areaname but not both.
'''
def get_obstasks_keys_page(page, username=None, areaname=None):
    obstasks = get_obstasks_keys(username, areaname)
    if obstasks != None:
        data = obstasks[(page  - 1) * models.Old_ObservationTask.OBSTASKS_PER_PAGE:page * models.Old_ObservationTask.OBSTASKS_PER_PAGE]
        if not data:
            logging.warning('Page %i requested but only %i obstasks, %i pages.', page, len(obstasks), len(obstasks) / models.Old_ObservationTask.OBSTASKS_PER_PAGE + 1)
        return data
    return None

# returns rendered list of ObservationTasks of given page
def get_obstasks_page(page, username=None, areaname=None):
    if page < 1:
        page = 1

    obstasks = get_obstasks_keys_page(page, username, areaname)
    if obstasks:
        data = [unicode(get_obstask_render(i)) for i in obstasks]
        return data
    return None

'''
    get_obstask_render()

    Renders an ObservationTask into an HTML row.
    Page won't be updated more than once if task already in the cache - unless reload is true.
'''

def get_obstask_render(task_key, reload=False):
    obstask = get_task(task_key)
    obslist = []
    area_name = 'unknown'
    if obstask is not None:
        area = obstask.aoi.get()
        if area != None:
            area_name = area.name.encode('utf-8')
            resultstr = "Observation Task for {0!s} to check area {1!s} <br>".format(obstask.assigned_owner.string_id(), area_name)
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
        else:
            resultstr = 'Observation Task for deleted area! area key: {0:s} <br>'.format(obstask.aoi)
            debugstr = resultstr
            logging.error(resultstr)
            data = utils.render('obstask-render.html', {
                        'obstask': obstask,
                        'obslist': obslist,
                        'resultstr': resultstr,
                        'area' :  'Deleted',
                        'created_date' : obstask.created_date.strftime("%Y-%m-%d"),
                        'obstask_url': obstask.taskurl()
                        } )

    data = utils.render('obstask-render.html', {
        'obstask': obstask,
        'obslist': obslist,
        'resultstr': debugstr,
        'area' :  area_name,
        'created_date' : obstask.created_date.strftime("%Y-%m-%d"),
        'obstask_url': obstask.taskurl()
        } )
    return data


def clear_obstasks_cache(username=None, areaname=None):
    logging.error('clear_obstasks_cache DISABLED')

#def clear_area_cache(user_key, area_key):
#    logging.error('clear_area_cache DISABLED')

def clear_area_followers(area_key):
    logging.error('clear_area_followers DISABLED')

def clear_journal_cache(user_key):
    logging.error('clear_journal_cache DISABLED')

def get_activities(username='', action='', object_key=''):
    data = models.Activity.query()

    if username:
        data = data.filter(models.Activity.user == username)
        logging.debug('activity filter user=%s', username)
    if action:
        data = data.filter(models.Activity.action, action)
    if object_key:
        data = data.filter(models.Activity.object, object_key)

    data = data.order(-models.Activity.date).fetch(models.Activity.RESULTS)
    return data

def get_activities_follower_keys(username):
    ActivityIdx = models.ActivityIndex
    index_keys = ActivityIdx.query(ActivityIdx.receivers == username).order(-ActivityIdx.date).fetch(models.Activity.RESULTS, keys_only=True, )
    data = [str(i.parent()) for i in index_keys]
    return data

def get_activities_follower_data(keys):
    data = ndb.get_multi(keys)
    return data

def get_activities_follower(username):
    keys = get_activities_follower_keys(username)
    # perhaps the keys didn't change, so keep a backup of that data
    data = get_activities_follower_data(keys)
    return data

def get_feed(feed, token):
    data = feeds.feed(feed, token)
    return data


def get_user(username):
    user_key = ndb.Key('User', username)
    return user_key.get()

def get_followers(username):
    followers = models.UserFollowersIndex.get_by_id(username, parent=ndb.Key('User', username))
    if not followers:
        data = []
    else:
        data = followers.users
    return data

def get_following(username):
    following = models.UserFollowingIndex.get_by_id(username, parent=ndb.Key('User', username))
    if not following:
        data = []
    else:
        data = following.users
    return data

def get_area_followers(area_name):
    data= models.AreaFollowersIndex.get_by_id(area_name, parent=ndb.Key('AreaOfInterest', area_name))
    return data

'''
get_following_area_keys()
@param: user key,
@returns: a list of area keys that the user follows.
'''
def get_following_area_keys(user_key):
    following = models.UserFollowingAreasIndex.get_by_username(user_key.id())
    data = []
    if not following:
        logging.debug("get_following_area_keys(): %s not following any areas", user_key.string_id())
    else:
        data = following.area_keys
    return data


'''
get_following_areas()
@param user key:
@returns: a UserFollowingAreasIndex entity that contains a list the names of areas that the user follows.
'''
def get_following_areas(user_key):
    following = models.UserFollowingAreasIndex.get_by_username(user_key.id())
    data = []
    if not following:
        logging.debug("get_following_areas(): %s not following any areas", user_key.string_id())
    else:
        following_areas = following.areas
        allareas = models.AreaOfInterest.query()  #TODO: This is inefficient. Give each user model a list.
        data = [x for x in allareas if x.name in following_areas]
    return data

def get_following_areas_list(user_key):
    areas= get_following_areas(user_key)
    data = [(i.url(), i.name) for i in areas]
    if user_key is not None:
        logging.debug("get_following_areas_list() reloaded user_key: %s", user_key.string_id())
    else:
        logging.error("get_following_areas_list() no user key")
    return data

def get_following_areanames_list(user_key): #as above but returns list of names only without urls for excluding from other_areas
    areas= get_following_areas(user_key)
    if areas:
        data = [i.name for i in areas]
    else:
        logging.debug("get_following_areanames_list()     no following_areas")
        data = []
    return data

def get_area(area_name):
    data = models.AreaOfInterest.get_by_id(area_name)
    if data is None:
        logging.error("get_area() no area found for %s", area_name)
        return None
    return data

def get_area_name_by_cluster_id(cluster_id):
    query1 = models.AreaOfInterest.query(models.AreaOfInterest.glad_monitored == True)
    data = None
    for area in query1:
        if area.get_gladcluster() == cluster_id:
            data = area.name
    if data is None:
        logging.error("get_area() no area found for %s", cluster_id)
        return None
    return data

def get_area_key(username, area_name):
    if username is None:
        data = models.AreaOfInterest.query(models.AreaOfInterest.name == area_name).fetch(keys_only=True)
    else:
        data = models.AreaOfInterest.query(models.AreaOfInterest.owner == username, models.AreaOfInterest.name == area_name.decode('utf-8')).fetch(keys_only=True)
    return data

def get_cell(path, row, area_name):    
    data = models.LandsatCell.get_cell(path, row, area_name)
    if data is None:
        logging.error("cache:get_cell() did not find cell object %d %d for area %s", path, row, area_key)
    return data
  
def get_cells(area_key):
    data = models.LandsatCell.all().filter('area =',  area_key)
    return data

def get_journal_key(username, journal_name):
    user_key = ndb.Key('User', username)
    data = ndb.Key('Journal', journal_name, parent=user_key)
    return data

def get_entry(username, journal_name, entry_id, entry_key=None):
    return models.Entry.get_entry(username, journal_name, entry_id, entry_key)
    
def get_entry_render(username, journal_name, entry_id):
    entry, content, blobs = get_entry(username, journal_name, entry_id)
    data = utils.render('entry-render.html', {
        'blobs': blobs,
        'content': content,
        'entry': entry,
        'entry_url': webapp2.uri_for('view-entry', username=username, journal_name=journal_name, entry_id=entry_id),
    })
    return data

''' EOF '''