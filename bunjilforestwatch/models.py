
from __future__ import with_statement

import datetime
import logging
import re

from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.ext import db

import cache
import hashlib
import urllib
import utils
import webapp2
import ee

class DerefModel(db.Model):
	def get_key(self, prop_name):
		return getattr(self.__class__, prop_name).get_value_for_datastore(self)

class DerefExpando(db.Expando):
	def get_key(self, prop_name):
		return getattr(self.__class__, prop_name).get_value_for_datastore(self)

USER_SOURCE_FACEBOOK = 'facebook'
USER_SOURCE_GOOGLE = 'google'
USER_SOURCE_TWITTER = 'twitter'

USER_SOURCE_CHOICES = [
	USER_SOURCE_FACEBOOK,
	USER_SOURCE_GOOGLE,
]

USER_SOCIAL_NETWORKS = [
	USER_SOURCE_FACEBOOK,
	USER_SOURCE_TWITTER,
]

#registered User builds on google user.
class User(db.Model):
	name = db.StringProperty(required=True, indexed=False)
	lname = db.StringProperty(indexed=True)
	email = db.EmailProperty()
	register_date = db.DateTimeProperty(auto_now_add=True)
	last_active = db.DateTimeProperty(auto_now=True)
	token = db.StringProperty(required=True, indexed=False)
	
	areas_observing = db.ListProperty(db.Key, default=None) # list of areas we watch - Not Used
	areas_subscribing = db.ListProperty(db.Key, default=None) # list of areas I subscribe to  (only for local)
	
	role = db.StringProperty(required=True, choices=set(["volunteer", "local", "admin", "viewer"]))	#roles for bunjil app users. 

# not required
	first_entry = db.DateTimeProperty()
	last_entry = db.DateTimeProperty()
	entry_days = db.IntegerProperty(required=True, default=0)

	# these two properties will be deleted
	source = db.StringProperty(choices=USER_SOURCE_CHOICES)
	uid = db.StringProperty()

	google_id = db.StringProperty()

	allowed_data = db.IntegerProperty(required=True, default=50 * 2 ** 20) # 50 MB default
	used_data = db.IntegerProperty(required=True, default=0)

	areas_count = db.IntegerProperty(required=True, default=0)

	journal_count = db.IntegerProperty(required=True, default=0)
	entry_count = db.IntegerProperty(required=True, default=0)

	facebook_id = db.StringProperty()
	facebook_enable = db.BooleanProperty(indexed=False)
	facebook_token = db.StringProperty(indexed=False)

	twitter_id = db.StringProperty()
	twitter_enable = db.BooleanProperty(indexed=False)
	twitter_key = db.StringProperty(indexed=False)
	twitter_secret = db.StringProperty(indexed=False)


# not really required
	def count(self):
		if self.entry_count and self.last_entry and self.first_entry:
			self.entry_days = (self.last_entry - self.first_entry).days + 1
			weeks = self.entry_days / 7.
			self.freq_entries = self.entry_count / weeks
			#self.freq_chars = self.chars / weeks
			#self.freq_words = self.words / weeks
			#self.freq_sentences = self.sentences / weeks
		else:
			self.entry_days = 0
			self.freq_entries = 0.
			#self.freq_chars = 0.
			#self.freq_words = 0.
			#self.freq_sentences = 0.

	def set_dates(self):
		self.last_entry = datetime.datetime.now()

		if not self.first_entry:
			self.first_entry = self.last_entry

	def __str__(self):
		return str(self.name)

	def gravatar(self, size=''):
		if size:
			size = '&s=%s' %size

		if not self.email:
			email = ''
		else:
			email = self.email.lower()

		return '//www.gravatar.com/avatar/' + hashlib.md5(email).hexdigest() + '?d=mm%s' %size

	def can_upload(self):
		return self.bytes_remaining > 0

	@property
	def bytes_remaining(self):
		return self.allowed_data - self.used_data

	@property
	def sources(self):
		return [i for i in USER_SOURCE_CHOICES if getattr(self, '%s_id' %i)]


class UserFollowersIndex(db.Model):
	users = db.StringListProperty()

class UserFollowingIndex(db.Model):
	users = db.StringListProperty()

class AreaFollowersIndex(db.Model):  #A Area has a list of users in an AreaFollowersIndex(key=user)
    users = db.StringListProperty()

class UserFollowingAreasIndex(db.Model): #A User has a list of areas in a UserFollowingAreasIndex(key=area)
    areas = db.StringListProperty()
    


class AreaOfInterest(db.Model):

	ENTRIES_PER_PAGE = 5 #TODO Move to Settings.py
	MAX_AREAS = 24       #TODO Move to Settings.py

	# Area Description
	name = db.StringProperty(required=True)
	#description = db.StringProperty(multiline=True) # text might be better type as it is not indexed.
	description = db.TextProperty() # text might be better type as it is not indexed.

	type = db.StringProperty()
	wiki = db.LinkProperty() # link to s a story about this area.
	#tags = db.ListProperty(unicode,default=None) #TODO: Caused a unicode not callable error. Not yet implemented.
	
	cells = db.ListProperty(db.Key, default=None) # list of Landsat cells overlapping this area - calculated on new.
	entry_count = db.IntegerProperty(required=True, default=0) # reports related to this area - not used yet
	
	max_path = db.IntegerProperty(required=False, default=-1) # these are not importantand will not be set correctly.
	min_path = db.IntegerProperty(required=False, default=-1)
	max_row  = db.IntegerProperty(required=False, default=-1)
	min_row  = db.IntegerProperty(required=False, default=-1)
	
	#Geometry of area boundary
	coordinates = db.ListProperty(db.GeoPt, default=None) # TODO: Replace with fc.
	boundary_fc = db.TextProperty(required = True) # ee.FeatureCollection or park boundary in JSON string format
	bound = db.ListProperty(float, default=None)
	max_latlon = db.GeoPtProperty(required=True, default=None)
	min_latlon = db.GeoPtProperty(required=True, default=None)

	
	# Parameters for viewing Area
	map_center = db.GeoPtProperty(required=True, default=None)
	map_zoom    = db.IntegerProperty(required=True, default=1)
	
	#User (subscriber) who created AOI 
	created_by = db.UserProperty(verbose_name=None, auto_current_user=False, auto_current_user_add=True)
	owner = db.ReferenceProperty(User) #key to subscriber that created area.
	private = db.BooleanProperty(required=True, default=False) #set to keep area hidden.
	
	#timestsamps
	created_date = db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now=True)
	
	@property
	def observers(self):
			return User.all().filter('areas_observing', self.key())
	
	# all frequencies are per week

	def __unicode__(self):
		return unicode(self.name)

	@property
	def pages(self):
		if self.entry_count == 0:
			return 1
		return (self.entry_count + self.ENTRIES_PER_PAGE - 1) / self.ENTRIES_PER_PAGE

	def url(self, page=1):
		if page > 1:
			#return webapp2.uri_for('view-area', username=self.key().parent().name(), area_name= self.name, page=page)
			return webapp2.uri_for('view-area',  area_name= self.name, page=page)
		else:
			#return webapp2.uri_for('view-area', username=self.key().parent().name(),  area_name= self.name)
			return webapp2.uri_for('view-area', area_name= self.name)

	def CellList(self):
		cell_list = []
		for cell_key in self.cells:
			#cell = cache.get_cell_from_key(cell_key)
			cell = cache.get_cell_from_key(cell_key)
			if cell is not None:
				celldict = cell.Cell2Dictionary()
				if celldict is not None:
					cell_list.append(celldict)
			else:
				logging.error ("AreaofInterest::CellList() no cell returned from key %s ", cell_key)
			
			returnstr = 'AreaofInterest::CellList() area {0!s} has cells {1!s}'.format(self.name.encode('utf-8'), cell_list)
			#logging.debug(returnstr)
			
		return cell_list
	

'''
Landsat Cell represents an 170sq km area where each image is captured. 
Each path and row identifies a unique cell.
An AOI makes overlaps a set of one or more cells - and creates a constant list of these.
Each cell has a different schedule when new images arrive.

Note that multiple LandsatCell objects for the same Landsat Cell(p,r) can be created, one for each parent area to which it belongs.
                
'''
class LandsatCell(db.Model):
	#constants - not changed once created. Created when AOI is created. 
	path = db.IntegerProperty(required=True, default=0)     # Landsat Path
	row  = db.IntegerProperty(required=True, default=0)     # Landsat Row
	#Can filter on these using imageCollection.filterMetadata('WRS_PATH', 'EQUALS', 40).filterMetadata('WRS_ROW', 'EQUALS', 30)
	
	center = db.GeoPtProperty(required=False, default=None) # Geographic Center of Cell
	bound = db.ListProperty(float, default=None)            # Geographic Boundary of Cell
	#created_by = db.UserProperty(verbose_name=None, auto_current_user=False, auto_current_user_add=True)
	
	aoi = db.ReferenceProperty(AreaOfInterest) #key to area that includes this cell
	
	#FIXME: Multiple AOI could reference the same cell so change to a list...
	
	#L8_latest   = db.ReferenceProperty(Observation, default=None)
	#L8_previous = db.ReferenceProperty(Observation, default=None)
	#L7_latest   = db.ReferenceProperty(Observation, default=None)
	#L7_previous = db.ReferenceProperty(Observation, default=None)
	monitored = db.BooleanProperty(required = True, default = False) # Set if cell is monitored for new data (i.e selected in view-area)

	'''
	Cell2Dictionary()converts a cell object into a dictionary of the path,row, monitored 
	and date of latest image stored in datastore for L8 collection (other collections to follow)
	'''	
	def Cell2Dictionary(self):
		#cell_list.append({"path":cell.path, "row":cell.row, "monitored":cell.monitored})
		
		celldict = {"path":int(self.path), "row":int(self.row), "monitored":"false", "LC8_latest_capture":"none", "result":"ok"}
		
		if self.monitored:
			celldict['monitored'] = "true"
		q = self.latestObservation('LANDSAT/LC8_L1T_TOA')
		if q is not None:
			celldict['LC8_latest_capture']	= q.captured.strftime("%Y-%m-%d @ %H:%M")
		#print celldict
		return celldict
	
	def latestObservation(self, collectionName="L8"): # query for latest observation from given imageColleciton.
		#return db.GqlQuery("SELECT * FROM Observation WHERE ((landsatCell = self )AND (collection = collectionName)) ORDER_BY captured ASC LIMIT 1")
		q = Observation.all().ancestor(self).filter('image_collection =', collectionName).order('-captured')
		return q.get()



'''
class Overlay describes a visualisation of an image asset.
It includes the map_id and token, an algorithm and information about the type. 
Used for a (Landsat) satelite image that has been retrieved and converted to a usable (visible/NDVI) format.
The image is based on an Observatioin Asset.
Note that the Overlay is an asset in the earth engine that has a limited expiry date.
If the tiles returned are 404 then it is necessary to recreate the overlay.
'''
class Overlay(db.Model):
	map_id    = db.StringProperty(required=False, default=None) 	# RGB Map Overlay Id generated in GEE - 
	token	  = db.StringProperty(required=False, default=None) 	# RGB Map Overlay Token might have expired.
	algorithm = db.StringProperty(required=False)				#identifies how the image was created - e.g. NDVI, RGB etc. #TODO How to specify this.
	overlay_role      = db.StringProperty(required=False)		#Purpose of this asset for the task. expected values: 'LATEST', 'PREVIOUS'. 
	 
	#observation = db.ReferenceProperty(db.Model) #defer initialization to init to avoid forward reference to new class defined. http://stackoverflow.com/questions/1724316/referencing-classes-in-python - use parent instead. 

	def Overlay2Dictionary(self):		
		obsdict = {
			"map_id":self.map_id, 
			"token":self.token, 
			"algorithm":self.algorithm,
			"overlay_role":self.overlay_role, 
			"parent" : str(self.parent_key()),
			"key": str(self.key())
		}
		return obsdict

'''
class Observation (could rename to ObservationAsset) describes a Landsat satellite image.

An Observation contains a list of zero or more Overlays, each Overlay is a visualization of the ObservationAsset.

The main use is the captured date. Once this observation has been actioned, it becomes the latest, against which future observations are base-lined for change detection.
This allows the app to redraw the overlay computed by earth engine on a new browser session without recalculating it - providing the overlay token has not expired.
In which case, app will need to regenerate the observation.    

Some Observations have no image_id as they are composites of many images.
'''

class Observation(db.Model):
	

	image_collection = db.StringProperty(required=False)			#identifies the ImageCollection name, not an EE object.
	image_id  = db.StringProperty(required=False)           		# LANDSAT Image ID of Image - key to query EE.
	captured  = db.DateTimeProperty(required=False) 				# sysdate or date Image was captured - could be derived by EE from collection+image_id.
	obs_role  = db.StringProperty(required=False)		#Purpose of this asset for the task. expected values: 'LATEST', 'PREVIOUS'. 
	overlays  = db.ListProperty(db.Key, default=None) # list of keys to overlays (visualisations of this observation asset) 
	#landsatCell = db.ReferenceProperty(LandsatCell) #defer initialization to init to avoid forward reference to new class defined. http://stackoverflow.com/questions/1724316/referencing-classes-in-python - use parent instead. 

	def Observation2Dictionary(self):		
			
		obsdict = {
			"image_collection":self.image_collection, 
			"image_id":self.image_id, 	
			"captured": self.captured.strftime("%Y-%m-%d @ %H:%M"), 
			"obs_role":self.obs_role, 	# ex 'latest'
			"key": str(self.key()),		
			"overlays": []
		}
		
		for ovl_key in self.overlays:
			overlay = cache.get_by_key(ovl_key)
			if overlay is not None:
				obsdict['overlays'].append(overlay.Overlay2Dictionary())
		return obsdict

'''
class Task is an observation task, based on a landsat image in an AOI. The task includes a user who is responsible for completing the task.
Each task has a unique ID.
'''    
class ObservationTask(db.Model):
	OBSTASKS_PER_PAGE = 20
	# Observation
	name = db.StringProperty()
	aoi = db.ReferenceProperty(AreaOfInterest) #key to area that includes this cell
	observations = db.ListProperty(db.Key) #key to observations related to this task. E.g if two images are in the same path and published at same time.

	#people - 	Expected to be a user  who is one of the area's followers. volunteering to follow the AOI
	original_owner = db.ReferenceProperty(User, collection_name='original_user') # user originally assigned the the task
	assigned_owner = db.ReferenceProperty(User, collection_name='assigned_user') # user who is currently assigned the the task
	
	#timestsamps
	created_date = db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now=True)

	@property
	def pages(self, obstask_count):
		if obstask_count == 0:
			return 1
		return (obstask_count + self.OBSTASK_PER_PAGE - 1) / self.OBSTASKS_PER_PAGE


	def taskurl(self):
			return webapp2.uri_for('view-obstask',  username=self.assigned_owner.name, task_name= self.key())
			#taskurl = "/obs/" + user.name + "/" + str(new_task.key())
			#linestr += u'<a href=' + taskurl + ' target="_blank">' + taskurl.encode('utf-8') + '</a>'

	
	def listurl(self, page=1, username=None): #show a list of recent tasks
		#logging.debug("listurl %s ", username )
		if username is None:
			#username = user.name
			if page > 1:
				return webapp2.uri_for('view-allobstasks',  username = username , task_name= self.key(), page=page)
			else:
				return webapp2.uri_for('view-allobstasks', username = username , task_name= self.key())

		else:
			if page > 1:
				return webapp2.uri_for('view-obstasks',  username = username, user2view= self.assigned_owner.name, task_name= self.key(), page=page)
			else:
				return webapp2.uri_for('view-obstasks', username = username, user2view= self.assigned_owner.name,  task_name= self.key())
			
'''
A Journal consists of user entries. Journals used for recording observations from tasks are a special class as they also record the image id.
Based on journalr.org 
'''
class Journal(db.Model):
	ENTRIES_PER_PAGE = 5
	MAX_JOURNALS = 10

	journal_type= db.StringProperty(required=True, default="journal") #"journal", "observations", "reports" etc.
	name = db.StringProperty(required=True)
	created_date = db.DateTimeProperty(auto_now_add=True)
	last_entry = db.DateTimeProperty()
	first_entry = db.DateTimeProperty()
	last_modified = db.DateTimeProperty(auto_now=True)
	entry_count = db.IntegerProperty(required=True, default=0)
	entry_days = db.IntegerProperty(required=True, default=0)

	chars = db.IntegerProperty(required=True, default=0)
	words = db.IntegerProperty(required=True, default=0)
	sentences = db.IntegerProperty(required=True, default=0)

	# all frequencies are per week
	freq_entries = db.FloatProperty(required=True, default=0.)
	freq_chars = db.FloatProperty(required=True, default=0.)
	freq_words = db.FloatProperty(required=True, default=0.)
	freq_sentences = db.FloatProperty(required=True, default=0.)

	def count(self):
		if self.entry_count:
			self.entry_days = (self.last_entry - self.first_entry).days + 1
			weeks = self.entry_days / 7.
			self.freq_entries = self.entry_count / weeks
			self.freq_chars = self.chars / weeks
			self.freq_words = self.words / weeks
			self.freq_sentences = self.sentences / weeks
		else:
			self.entry_days = 0
			self.freq_entries = 0.
			self.freq_chars = 0.
			self.freq_words = 0.
			self.freq_sentences = 0.

	def __unicode__(self):
		return unicode(self.name)

	@property
	def pages(self):
		if self.entry_count == 0:
			return 1
		return (self.entry_count + self.ENTRIES_PER_PAGE - 1) / self.ENTRIES_PER_PAGE

	def url(self, page=1):
		if page > 1:
			return webapp2.uri_for('view-journal', username=self.key().parent().name(), journal_name=self.name, page=page)
		else:
			return webapp2.uri_for('view-journal', username=self.key().parent().name(), journal_name=self.name)

RENDER_TYPE_HTML = 'HTML'
RENDER_TYPE_MARKDOWN = 'markdown'
RENDER_TYPE_RST = 'reStructured Text'
RENDER_TYPE_TEXT = 'plain text'
RENDER_TYPE_TEXTILE = 'textile'

CONTENT_TYPE_CHOICES = [
	RENDER_TYPE_MARKDOWN,
	RENDER_TYPE_RST,
	RENDER_TYPE_TEXT,
	RENDER_TYPE_TEXTILE,
]

class EntryContent(db.Model):
	subject = db.StringProperty()
	tags = db.StringListProperty()
	text = db.TextProperty()
	rendered = db.TextProperty(default='')
	markup = db.StringProperty(required=True, indexed=False, choices=CONTENT_TYPE_CHOICES, default=RENDER_TYPE_TEXT)
	images = db.StringListProperty()


class Entry(db.Model):
	date = db.DateTimeProperty(auto_now_add=True)
	created = db.DateTimeProperty(required=True, auto_now_add=True)
	last_edited = db.DateTimeProperty(required=True, auto_now=True)

	content = db.IntegerProperty(required=True) # key id of EntryContent
	blobs = db.StringListProperty()

	chars = db.IntegerProperty(required=True, default=0)
	words = db.IntegerProperty(required=True, default=0)
	sentences = db.IntegerProperty(required=True, default=0)

	dropbox_rev = db.StringProperty(indexed=False)
	google_docs_id = db.StringProperty(indexed=False)

	WORD_RE = re.compile("[A-Za-z0-9']+")
	SENTENCE_RE = re.compile("[.!?]+")

	@property
	def time(self):
		if not self.date.hour and not self.date.minute and not self.date.second:
			return ''
		else:
			return self.date.strftime('%I:%M %p')

	@property
	def content_key(self):
		return db.Key.from_path('EntryContent', long(self.content), parent=self.key())

	@property
	def blob_keys(self):
		return [db.Key.from_path('Blob', long(i), parent=self.key()) for i in self.blobs]


ACTIVITY_NEW_JOURNAL = 1
ACTIVITY_NEW_ENTRY = 2
ACTIVITY_FOLLOWING = 3
ACTIVITY_SAVE_ENTRY = 4
ACTIVITY_NEW_AREA = 5
ACTIVITY_NEW_OBS = 6
ACTIVITY_NEW_REPORT = 7
ACTIVITY_NEW_FEEDBACK = 8



ACTIVITY_CHOICES = [
	ACTIVITY_NEW_JOURNAL,
	ACTIVITY_NEW_ENTRY,
	ACTIVITY_FOLLOWING,
	ACTIVITY_SAVE_ENTRY,
	ACTIVITY_NEW_AREA
]

ACTIVITY_ACTION = {
	ACTIVITY_NEW_JOURNAL: 	'created a new journal',
	ACTIVITY_NEW_ENTRY: 	'started a new journal entry',
	ACTIVITY_FOLLOWING: 	'started following',
	ACTIVITY_SAVE_ENTRY: 	'updated a journal entry',
	ACTIVITY_NEW_AREA: 		'created a new area of interest',
}

class Activity(DerefModel):
	RESULTS = 25

	user = db.StringProperty(required=True)
	img = db.StringProperty(indexed=False)
	date = db.DateTimeProperty(auto_now_add=True)
	action = db.IntegerProperty(required=True, choices=ACTIVITY_CHOICES)
	object = db.ReferenceProperty()

	def get_action(self):
		r = ACTIVITY_ACTION[self.action]

		if self.action == ACTIVITY_FOLLOWING:
			name = self.get_key('object').name()
			r += ' <a href="%s">%s</a>' %(webapp2.uri_for('user', username=name), name)

		return r

	@staticmethod
	def create(user, action, object):
		a = Activity(user=user.name, img=user.gravatar('30'), action=action, object=object)
		ar = db.put_async(a)

		#receivers = cache.get_followers(user.name)
		#receivers.append(user.name)
		ar.get_result()
		#ai = ActivityIndex(parent=a, receivers=receivers)
		ai = ActivityIndex(parent=a)
		ai.put()

class ActivityIndex(db.Model):
	receivers = db.StringListProperty()
	date = db.DateTimeProperty(auto_now_add=True)

BLOB_TYPE_IMAGE = 1
BLOB_TYPE_PDF = 2

BLOB_TYPE_CHOICES = [
	BLOB_TYPE_IMAGE,
	BLOB_TYPE_PDF,
]

class Blob(DerefExpando):
	MAXSIZE = 4 * 2 ** 20 # 4MB

	blob = blobstore.BlobReferenceProperty(required=True)
	type = db.IntegerProperty(required=True, choices=BLOB_TYPE_CHOICES)
	name = db.StringProperty(indexed=False)
	size = db.IntegerProperty()
	url = db.StringProperty(indexed=False)

	def get_url(self, size=None, name=None):		
		if self.type == BLOB_TYPE_IMAGE:
			if not self.url:
				self.url = images.get_serving_url(self.blob)

			url = self.url

			if size:
				url += '=s' + size

			return url
		else:
			kwargs = {'key': self.get_key('blob')}

			if name is True:
				name = self.name
			if name:
				kwargs['name'] = name

			return webapp2.uri_for('blob', **kwargs)

RENDER_TYPE_CHOICES = [
	RENDER_TYPE_HTML,
	RENDER_TYPE_MARKDOWN,
	RENDER_TYPE_RST,
	RENDER_TYPE_TEXT,
	RENDER_TYPE_TEXTILE,
]

class BlogEntry(db.Model):
	ENTRIES_PER_PAGE = 10

	date = db.DateTimeProperty(required=True, auto_now_add=True)
	draft = db.BooleanProperty(required=True, default=True)
	markup = db.StringProperty(required=True, indexed=False, choices=RENDER_TYPE_CHOICES, default=RENDER_TYPE_MARKDOWN)
	title = db.StringProperty(required=True, indexed=False, default='Title')
	text = db.TextProperty(default='')
	rendered = db.TextProperty(default='')
	user = db.StringProperty(required=True)
	avatar = db.StringProperty()
	slug = db.StringProperty(indexed=False)

	@property
	def url(self):
		if not self.slug:
			self.slug = str(self.key().id())

		return webapp2.uri_for('blog-entry', entry=self.slug)

class Config(db.Expando):
	pass
