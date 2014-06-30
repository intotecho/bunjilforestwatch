# Based on cache.py from Copyright (c) 2011 Matt Jibson <matt.jibson@gmail.com>
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

from google.appengine.api import memcache
from google.appengine.datastore import entity_pb
from google.appengine.ext import db

import counters
import feeds
import models
import utils
import webapp2

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

C_CELL      = 'cell_%s_%s'
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
    memcache.set_multi(dict([(C_KEY %i.key(), pack(i)) for i in entities]))

def delete(keys):
    memcache.delete_multi(keys)

def delete_item(key):
    memcache.delete(key)

def flush():
    memcache.flush_all()

def pack(models):
    if models is None:
        return None
    elif isinstance(models, db.Model):
    # Just one instance
        return db.model_to_protobuf(models).Encode()
    else:
    # A list
        return [db.model_to_protobuf(x).Encode() for x in models]

def unpack(data):
    if data is None:
        return None
    elif isinstance(data, str):
    # Just one instance
        return db.model_from_protobuf(entity_pb.EntityProto(data))
    else:
        return [db.model_from_protobuf(entity_pb.EntityProto(x)) for x in data]

def get_by_key(key):
    n = C_KEY %key
    data = unpack(memcache.get(n))
    if data is None:
        data = db.get(key)
        memcache.add(n, pack(data))

    return data

# idea: use async functions, although i'm not convinced it'd be faster
# fetches all keys; if kind is specified, converts the given key names to keys of that kind
def get_by_keys(keys, kind=None):
    #print("get_by_keys: ", keys)    
    if kind:
        keys = [str(db.Key.from_path(kind, i)) for i in keys]
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
        fetched = db.get(fetch_keys)
        set_multi(dict(zip(fetch_keys, fetched)))
        #print("get_by_keys to_fetch : ", to_fetch, fetch_keys, fetched)    

        for i in to_fetch:
            data[i] = fetched.pop(0)

    return data

def decode_key(key):
    #for debugging print the path of the key.
    k = db.Key(key)
    _app = k.app()
    path = []
    while k is not None:
        path.append(k.id_or_name())
        path.append(k.kind())
        k = k.parent()
    path.reverse()
    #print 'app=%r, path=%r' % (_app, path)

def get_areas(user_key):
    n = C_AREAS %user_key
    data = unpack(memcache.get(n))
    if data is None:
        #data = models.AreaOfInterest.all().ancestor(user_key).fetch(models.AreaOfInterest.MAX_AREAS)
        #q = db.Query(models.AreaOfInterest)
        #data = q.filter('owner =',  user_key)
        data = models.AreaOfInterest.all().filter('owner =',  user_key).fetch(models.AreaOfInterest.MAX_AREAS)
        #print "get_areas()", data
        memcache.add(n, pack(data))

    return data

def get_other_areas(username, user_key): # returns list of areas I created but includes areas I follow
    #user_key = db.Key.from_path('User', username)
    #print ("get_other_areas() ", username, user_key)

    n = C_OTHER_AREAS %user_key
    data = unpack(memcache.get(n))
    if data is None:
        allareas = models.AreaOfInterest.all()
        af =  get_following_areanames_list(username)
        #for y in af:
        #    print ("get_other_areas following:",  y)

        #data = models.AreaOfInterest.all().ancestor(user_key).fetch(models.AreaOfInterest.MAX_AREAS)
        #q = db.Query(models.AreaOfInterest)
        #udata = q.filter('owner !=',  user_key) # excludes areas I created but includes areas I follow
        #print ("get_other_areas: ", udata, af)
        otherareas = [x for x in allareas if x.name not in af and  x.owner.name != username ] # remove areas user created and elements in af that user follows
        data = otherareas #[(x.url(), x.name, x.owner.name) for x in otherareas]
        for y in data:
            print "get_other_areas() returns: ",  y
        print "get_other_areas() reloaded: ", username, user_key
        memcache.add(n, pack(data))
        #memcache.add(n, data)

    return data

# returns a list of user's area names
def get_areas_list(user_key):
    n = C_AREA_LIST %user_key
    data = memcache.get(n)
    if data is None:
        areas= get_areas(user_key)
        data = [(i.url(), i.name) for i in areas]
        memcache.add(n, data)

    return data

#returns a list of keys for all areas.
def get_all_areas():
    n = C_AREAS_ALL
    data = unpack(memcache.get(n))
    if data is None:
        data = models.AreaOfInterest.all().fetch(180) #FIXME limit of 180 will be a problem in future. This is used by CheckNew cron job.
        memcache.add(n, pack(data))

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
    data = unpack(memcache.get(n))
    if data is None:
        data = models.Journal.all().ancestor(user_key).fetch(models.Journal.MAX_JOURNALS)
        memcache.add(n, pack(data))

    return data

# returns a list of journal names
def get_journal_list(user_key):
    n = C_JOURNAL_LIST %user_key
    data = memcache.get(n)
    if data is None:
        journals = get_journals(user_key)
        data = [(i.url(), i.name, i.journal_type) for i in journals]
        memcache.add(n, data)

    return data

# returns all entry keys sorted by descending date
def get_entries_keys(journal_key):
    n = C_ENTRIES_KEYS %journal_key
    data = memcache.get(n)
    if data is None:
        # todo: fix limit to 1000 most recent journal entries
        data = models.Entry.all(keys_only=True).ancestor(journal_key).order('-date').fetch(1000)
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

def get_entry_key(username, journal_name, entry_id):
    n = C_ENTRY_KEY %(username, journal_name, entry_id)
    data = memcache.get(n)
    if data is None:
        data = db.get(db.Key.from_path('Entry', long(entry_id), parent=get_journal_key(username, journal_name)))

        if data:
            data = data.key()

        memcache.add(n, data)

    return data

# called when a new entry is posted, and we must clear all the entry and page cache
def clear_entries_cache(journal_key):
    journal = get_by_key(journal_key)
    keys = [C_ENTRIES_KEYS %journal_key, C_JOURNALS %journal_key.parent()]

    # add one key per page for get_entries_page and get_entries_keys_page
    for p in range(1, journal.entry_count / models.Journal.ENTRIES_PER_PAGE + 2):
        keys.extend([C_ENTRIES_PAGE %(journal.key().parent().name(), journal.name, p), C_ENTRIES_KEYS_PAGE %(journal_key, p)])

    memcache.delete_multi(keys)

def get_stats():
    n = C_STATS
    data = memcache.get(n)
    if data is None:
        data = [(i, counters.get_count(i)) for i in [
            counters.COUNTER_USERS,
            counters.COUNTER_JOURNALS,
            counters.COUNTER_AREAS,
            counters.COUNTER_ENTRIES,
            counters.COUNTER_CHARS,
            counters.COUNTER_WORDS,
            counters.COUNTER_SENTENCES,
        ]]

        memcache.add(n, data)

    return data

def clear_area_cache(user_key, area_key):
    print "clear_area_cache(%s, %s)", user_key, area_key
    tag = "users"
    memcache.delete_multi([    C_AREAS_ALL,
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


def clear_area_followers(area_key): #not used
    memcache.delete(C_AREA_FOLLOWERS %area_key)



def clear_journal_cache(user_key):
    memcache.delete_multi([C_JOURNALS %user_key, C_JOURNAL_LIST %user_key])

def get_activities(username='', action='', object_key=''):
    n = C_ACTIVITIES %(username, action, object_key)
    data = unpack(memcache.get(n))
    if data is None:
        data = models.Activity.all()

        if username:
            data = data.filter('user', username)
        if action:
            data = data.filter('action', action)
        if object_key:
            data = data.filter('object', object_key)

        data = data.order('-date').fetch(models.Activity.RESULTS)
        memcache.add(n, pack(data), 60) # cache for 1 minute

    return data

def get_activities_follower_keys(username):
    n = C_ACTIVITIES_FOLLOWER_KEYS %username
    data = memcache.get(n)
    if data is None:
        index_keys = models.ActivityIndex.all(keys_only=True).filter('receivers', username).order('-date').fetch(50)
        data = [str(i.parent()) for i in index_keys]
        memcache.add(n, data, 300) # cache for 5 minutes

    return data

def get_activities_follower_data(keys):
    n = C_ACTIVITIES_FOLLOWER_DATA %'_'.join(keys)
    data = unpack(memcache.get(n))
    if data is None:
        data = db.get(keys)
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
    user_key = db.Key.from_path('User', username)
    return get_by_key(user_key)

def get_followers(username):
    n = C_FOLLOWERS %username
    data = memcache.get(n)
    if data is None:
        followers = models.UserFollowersIndex.get_by_key_name(username, parent=db.Key.from_path('User', username))
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
        following = models.UserFollowingIndex.get_by_key_name(username, parent=db.Key.from_path('User', username))
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
        followers = models.AreaFollowersIndex.get_by_key_name(area_name) 
        #, parent=db.Key.from_path('AreaOfInterest', area_name))
        if followers is not None:
            data = [(i.url(), i.name, i.id()) for i in followers]
        else: 
            data = []    
        memcache.add(n, data)
    #print "get_area_followers"
    return data

def get_following_areas(user_key): 
    n = C_FOLLOWING_AREAS %user_key
    data = memcache.get(n)
    if data is None:
        following_key = db.Key.from_path('User', user_key, 'UserFollowingAreasIndex', user_key)
        #following = models.UserFollowingAreasIndex.from_path(kind, id_or_name, parent=None, namespace=None)
        #following_key = db.Key.from_path('User', thisuser, 'UserFollowingAreasIndex', thisuser)
        #following = models.UserFollowingAreasIndex.get_by_key_name(user_key, None)
        following = models.UserFollowingAreasIndex.get(following_key)
        data = []
        #following = models.UserFollowingAreasIndex.get_by_key_name(username, None)
        if not following:
            logging.debug("  get_following_areas - [no followers] %s", user_key)
        else:
            #print ("get_following_areas: areas", following.areas)
            #data = following.areas
            following_areas = following.areas
            #print "get_following_areas(): ", following_areas, type(following_areas) 
            
            #data = [get_area(None, af) for af in following_areas]
            allareas = models.AreaOfInterest.all()  #inefficient
            data = [x for x in allareas if x.name in following_areas]
            
            #print ("get_following_areas", following.areas)
            #data = [(get_area(None, i).url(), get_area(None, i).name) for i in following.areas]
        #memcache.add(n, pack(data))
        memcache.add(n, data)
        #for y in data:
            #print ("  get_following_areas af:",  y)
        #logging.debug("get_following_areas() reloaded: %s ", user_key)
        #print ("get_following_areas: ", data)
    return data

def get_following_areas_list(user_key):
    n = C_FOLLOWING_AREAS_LIST %user_key
    data = memcache.get(n)
    if data is None:
        areas= get_following_areas(user_key)
        data = [(i.url(), i.name) for i in areas]
        #data = [(get_area(None, i).url(), get_area(None, i).name) for i in areas]
        memcache.add(n, data)
        #print ("get_following_areas_list() reloaded: ", user_key)
        
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
    data = unpack(memcache.get(n))
    if data is None:
        area_key = get_area_key(username, area_name)
        if area_key is None:
            logging.error("get_area() no key for %s %s", username, area_name)
            return None
        data = db.get(area_key)
        if data is None:
            logging.error("get_area() ERROR!!!! %s %s %s", username, area_name, area_key )
        memcache.add(n, pack(data))
    logging.debug("get_area() returns: %s", data )
    return data


def get_area_key(username, area_name):
    if username is None:
        n = C_AREA_KEY %("users", area_name)  #users a reserved name so never a username. Fetch areas for all users.
        data = memcache.get(n)
        if data is None:
            data = models.AreaOfInterest.all(keys_only=True).filter('name', area_name).get()
            memcache.add(n, data)
    else:
        n = C_AREA_KEY %(username, area_name)
        data = memcache.get(n)
        if data is None:
            #user_key = db.Key.from_path('User', username)
            data = models.AreaOfInterest.all(keys_only=True).filter('owner =', username).filter('name', area_name.decode('utf-8')).get() #FIXME - Is why is there an '='  in owner =' but not for other string matches?
            #print ("get_area_userkey for user: ", username, data, )
            memcache.add(n, data)
    return data


def get_cell(path, row):
    n = C_CELL %(path, row)
    #print "get_cell() ", n
    data = unpack(memcache.get(n))
    if data is None:
        data = models.LandsatCell.all().filter('path =', int(path)).filter('row =', int(row)).get()
        if data is None:
            logging.error("get_cell() Cache did not find cell object %d %d", path, row)
        else:
            memcache.add(n, pack(data))
    return data

def get_cell_from_keyname(cell_name, area): #TODO - Does not really add anything different to the generic cache.get_by_key()
     
    n = C_CELL_NAME %(cell_name, area)
    #print "get_cell_from_key() ", n
    data = unpack(memcache.get(n))
    if data is None:
        #data = models.LandsatCell.get()
        data = models.LandsatCell.get_by_key_name( u'key_name', cell_name)
        if data is None:
            logging.error("get_cell_from_key() Missing Cell Object %s", cell_name)
        else:
            memcache.add(n, pack(data))
    return data
    
       
def get_cell_from_key(cell_key): #TODO - Does not really add anything different to the generic cache.get_by_key()
     
    n = C_CELL_KEY %(cell_key)
    #print "get_cell_from_key() ",
    data = unpack(memcache.get(n))
    if data is None:
        #data = models.LandsatCell.get()
        data = models.LandsatCell.get(cell_key)
        if data is None:
            logging.error("get_cell_from_key() Missing Cell Object")
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
        data = models.LandsatCell.all() #TODO This is a big load from DB.
        memcache.add(n, pack(data))
    return data

#following_key = db.Key.from_path('User', user_key, 'UserFollowingAreasIndex', user_key)
        #following = models.UserFollowingAreasIndex.from_path(kind, id_or_name, parent=None, namespace=None)
        #following_key = db.Key.from_path('User', thisuser, 'UserFollowingAreasIndex', thisuser)
        #following = models.UserFollowingAreasIndex.get_by_key_name(user_key, None)
#        following = models.UserFollowingAreasIndex.get(following_key)

def get_task(task_key_name):
   
    n = C_OBS_TASK %(task_key_name)
    data = unpack(memcache.get(n))
    if data is None:
        data= get_by_key(task_key_name)
        if data is None:
            logging.error("get_task(): Not an object") 
            return None
        else:
            if data.kind() != "ObservationTask":
                logging.error("get_task(): Not a task object") 
                return None
        memcache.add(n, pack(data))
    return data

def get_journal(username, journal_name):
    n = C_JOURNAL %(username, journal_name)
    data = unpack(memcache.get(n))
    if data is None:
        journal_key = get_journal_key(username, journal_name)
        if journal_key:
            data = db.get(journal_key)
        memcache.add(n, pack(data))

    return data

def get_journal_key(username, journal_name):
    n = C_JOURNAL_KEY %(username, journal_name)
    data = memcache.get(n)
    if data is None:
        user_key = db.Key.from_path('User', username)
        data = models.Journal.all(keys_only=True).ancestor(user_key).filter('name', journal_name.decode('utf-8')).get()
        memcache.add(n, data)

    return data

def get_entry(username, journal_name, entry_id, entry_key=None):
    n = C_ENTRY %(username, journal_name, entry_id)
    data = memcache.get(n)
    if data is None:
        if not entry_key:
            entry_key = get_entry_key(username, journal_name, entry_id)

        entry = get_by_key(entry_key)
        # try async queries here
        content = get_by_key(entry.content_key)

        if entry.blobs:
            blobs = pack(db.get(entry.blob_keys))
        else:
            blobs = []

        data = (pack(entry), pack(content), blobs)
        memcache.add(n, data)

    entry, content, blobs = data
    entry = unpack(entry)
    content = unpack(content)
    blobs = unpack(blobs)

    return entry, content, blobs

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

def get_blog_entries_page(page):
    n = C_BLOG_ENTRIES_PAGE %page
    data = unpack(memcache.get(n))
    if data is None:
        if page < 1:
            page = 1

        entries = get_blog_entries_keys_page(page)
        data = [get_by_key(i) for i in entries]
        memcache.add(n, pack(data))

    return data

# returns all blog entry keys sorted by descending date
def get_blog_entries_keys():
    n = C_BLOG_ENTRIES_KEYS
    data = memcache.get(n)
    if data is None:
        # todo: fix limit to 1000 most recent blog entries
        data = models.BlogEntry.all(keys_only=True).filter('draft', False).order('-date').fetch(1000)
        memcache.add(n, data)

    return data

# returns blog entry keys of given page
def get_blog_entries_keys_page(page):
    n = C_BLOG_ENTRIES_KEYS_PAGE %page
    data = memcache.get(n)
    if data is None:
        entries = get_blog_entries_keys()
        data = entries[(page  - 1) * models.BlogEntry.ENTRIES_PER_PAGE:page * models.BlogEntry.ENTRIES_PER_PAGE]
        memcache.add(n, data)

        if not data:
            logging.warning('Page %i requested from blog, but only %i entries, %i pages.', page, len(entries), len(entries) / models.BlogEntry.ENTRIES_PER_PAGE + 1)

    return data

# called when a new blog entry is posted, and we must clear all the entry and page cache
def clear_blog_entries_cache():
    keys = [C_BLOG_ENTRIES_KEYS, C_BLOG_COUNT, C_BLOG_TOP]

    # add one key per page for get_blog_entries_page and get_blog_entries_keys_page
    for p in range(1, get_blog_count() / models.BlogEntry.ENTRIES_PER_PAGE + 2):
        keys.extend([C_BLOG_ENTRIES_PAGE %p, C_BLOG_ENTRIES_KEYS_PAGE %p])

    memcache.delete_multi(keys)

def get_blog_count():
    n = C_BLOG_COUNT
    data = memcache.get(n)
    if data is None:
        try:
            data = models.Config.get_by_key_name('blog_count').count
        except:
            data = 0

        memcache.add(n, data)

    return data

def get_blog_top():
    n = C_BLOG_TOP
    data = memcache.get(n)
    if data is None:
        keys = get_blog_entries_keys()[:25]
        blogentries = db.get(keys)
        data = utils.render('blog-top.html', {'top': blogentries})
        memcache.add(n, data)

    return data
