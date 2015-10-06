""" Modles.py intro
etc.....
"""

from __future__ import with_statement
import datetime
import logging
import re
from google.appengine.api import images
from google.appengine.ext import ndb
import webapp2

import hashlib
import geojson
class DerefModel(ndb.Model):
	def get_key(self, prop_name):
		#return getattr(self.__class__, prop_name).get_value_for_datastore(self)
		return getattr(self.__class__, prop_name)

class DerefExpando(ndb.Expando):
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

class User(ndb.Model):
	""" ndb.User builds on google user
	
	"""

	name = ndb.StringProperty(required=True, indexed=False)
	lname = ndb.StringProperty(indexed=True)
	email = ndb.StringProperty()
	register_date = ndb.DateTimeProperty(auto_now_add=True)
	last_active = ndb.DateTimeProperty(auto_now=True)
	token = ndb.StringProperty(required=True, indexed=False)
	
	areas_observing = ndb.KeyProperty(repeated=True, default=None) 
	""" list of areas we watch - Not Used
	"""
	areas_subscribing = ndb.KeyProperty(repeated=True, default=None) # list of areas I subscribe to  (only for local)
	
	role = ndb.StringProperty(required=True, choices=set(["volunteer", "local", "admin", "viewer"]))	
	"""roles for bunjil app users are either volunteer, local, admin or viewer. 
	"""
	
	# not required
	first_entry = ndb.DateTimeProperty()
	last_entry = ndb.DateTimeProperty()
	entry_days = ndb.IntegerProperty(required=True, default=0)

	# these two properties will be deleted
	source = ndb.StringProperty(choices=USER_SOURCE_CHOICES)
	uid = ndb.StringProperty()

	google_id = ndb.StringProperty()
	allowed_data = ndb.IntegerProperty(required=True, default=50 * 2 ** 20) 
	""" allowed_data has a 50 MB default
	"""
	used_data = ndb.IntegerProperty(required=True, default=0)

	areas_count = ndb.IntegerProperty(required=True, default=0)

	journal_count = ndb.IntegerProperty(required=True, default=0)
	entry_count = ndb.IntegerProperty(required=True, default=0)

	facebook_id = ndb.StringProperty()
	facebook_enable = ndb.BooleanProperty(indexed=False)
	facebook_token = ndb.StringProperty(indexed=False)

	twitter_id = ndb.StringProperty()
	twitter_enable = ndb.BooleanProperty(indexed=False)
	twitter_key = ndb.StringProperty(indexed=False)
	twitter_secret = ndb.StringProperty(indexed=False)


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


class UserFollowersIndex(ndb.Model): 
	""" UserFollowersIndex - A User has a list of followers (other users) in an UserFollowersIndex(key=user).

	"""
	users = ndb.StringProperty(repeated=True)

class UserFollowingIndex(ndb.Model):
	"""UserFollowingIndex - A User has a list of other users they follow in a UserFollowingIndex(key=area)

	"""
	users = ndb.StringProperty(repeated=True)

class AreaFollowersIndex(ndb.Model):  
	"""AreaFollowersIndex - An Area has a list of users in an AreaFollowersIndex(key=user)
	"""
	users = ndb.StringProperty(repeated=True)
	
	@staticmethod
	def get_key (area_name_decoded):
		return ndb.Key('AreaOfInterest', area_name_decoded, 'AreaFollowersIndex', area_name_decoded)
	

class UserFollowingAreasIndex(ndb.Model): 
	"""UserFollowingAreasIndex - A User has a list of areas in a UserFollowingAreasIndex(key=area). Adding a list of area keys.
	moving from list of string to list of keys
	"""
	areas = ndb.StringProperty(repeated=True)
	area_keys = ndb.KeyProperty(kind='AreaOfInterest', repeated=True)

	@staticmethod
	def get_key(username):
		return ndb.Key('User', username, 'UserFollowingAreasIndex', username)

	@staticmethod # returns a list of area names that the user follows.
	def get_by_username(username):
		return UserFollowingAreasIndex.get_key(username).get()
	

class AreaOfInterest(ndb.Model):

	ENTRIES_PER_PAGE = 5 #TODO Move to Settings.py
	MAX_AREAS = 24	   #TODO Move to Settings.py
	
	PUBLIC_AOI = 0		
	"""Everyone can see and follow this area.share
	"""
	
	UNLISTED_AOI = 1	
	"""Anyone with the link can see and follow this area.share
	"""
	
	
	PRIVATE_AOI = 2		 
	"""Only the owner can see or follow this area.share
	"""
	
	# Area Description
	name = ndb.StringProperty(required=True)
	#description = ndb.StringProperty(multiline=True) # text might be better type as it is not indexed.
	description = ndb.TextProperty()		# What? text type is longer but is not indexed.
	description_why = ndb.TextProperty() # text type is longer but is not indexed.
	description_who = ndb.TextProperty() # #who looks after this area?
	description_how = ndb.TextProperty() # text type is longer but is not indexed.
	
	threats = ndb.TextProperty()	  # text type is longer but is not indexed.
	
	type = ndb.StringProperty()
	wiki = ndb.StringProperty() # beware max url 500 - like to a story about this area.
	
	cells = ndb.KeyProperty(repeated=True, default=None) 
	"""list of Landsat cells overlapping this area - calculated on new.
	"""
	entry_count = ndb.IntegerProperty(required=True, default=0) 
	"""reports related to this area - not used yet
	"""
	
	max_latlon = ndb.GeoPtProperty(required=True, default=None)
	min_latlon = ndb.GeoPtProperty(required=True, default=None)

	ft_link =  ndb.StringProperty() 
	"""link to a fusion table defining the Geometry of area boundary.
	"""
	
	ft_docid =  ndb.StringProperty() 
	"""A fusion table's document id.
	"""
	## Geometry
	area_location = ndb.GeoPtProperty(required=False, default=None) #make this required.
	
	coordinates = ndb.GeoPtProperty(repeated=True, default=None) # When a fusion table is provided in boundary_ft, this is the convexHull of the FT.
	boundary_fc = ndb.TextProperty(required = True) # ee.FeatureCollection or park boundary in JSON string format

	bound = ndb.FloatProperty(repeated=True, default=None)
	
	# Parameters for viewing Area
	map_center = ndb.GeoPtProperty(required=True, default=None)
	map_zoom	= ndb.IntegerProperty(required=True, default=1)
	
	#User (subscriber) who created AOI 
	created_by = ndb.UserProperty(verbose_name=None, auto_current_user=False, auto_current_user_add=True)  #set automatically when created. never changes.
	#owner = ndb.ReferenceProperty(User) #key to subscriber that created area.   # set by caller. could be reassigned.
	owner = ndb.KeyProperty(kind=User) #key to subscriber that created area.   # set by caller. could be reassigned.
	share = ndb.IntegerProperty(required=True, default=PUBLIC_AOI) #set to hide area. see @properties below
	
	followers_count = ndb.IntegerProperty(required=True, default=0) # count user following this area.
	
	#timestamps
	created_date = ndb.DateTimeProperty(auto_now_add=True)
	last_modified = ndb.DateTimeProperty(auto_now=True)
	
	def __unicode__(self):
		return unicode(self.name)


	@property
	def pages(self):
		if self.entry_count == 0:
			return 1
		return (self.entry_count + self.ENTRIES_PER_PAGE - 1) / self.ENTRIES_PER_PAGE

	def url(self, page=1):
		if page > 1:
			#return webapp2.uri_for('view-area', username=self.key.parent().name(), area_name= self.name, page=page)
			return webapp2.uri_for('view-area',  area_name= self.name, page=page)
		else:
			#return webapp2.uri_for('view-area', username=self.key.parent().name(),  area_name= self.name)
			return webapp2.uri_for('view-area', area_name= self.name)

	def tasks_url(self, page=1):
		if page > 1:
			#return webapp2.uri_for('view-area', username=self.key.parent().name(), area_name= self.name, page=page)
			return webapp2.uri_for('view-obstasks', area_name= self.name,  page=page)
		else:
			#return webapp2.uri_for('view-area', username=self.key.parent().name(),  area_name= self.name)
			return webapp2.uri_for('view-obstasks', area_name= self.name)

	@property
	def area_location_feature(self):
		return { "type": "Point", "coordinates": [self.area_location.lon, self.area_location.lat], "properties": {"featureName": "area_location"} }
	
	@property
	def shared_str(self):
		if self.share == self.PUBLIC_AOI:
			return 'public'
		elif self.share == self.UNLISTED_AOI:
			return 'unlisted'
		elif self.share == self.PRIVATE_AOI:
			return 'private'	
		else:
			return 'error'	

	def set_shared(self, share_str):
		if share_str == 'public':
			self.share = self.PUBLIC_AOI
			return self.share
		elif share_str == 'unlisted':
			self.share = self.UNLISTED_AOI
			return self.share
		elif share_str == 'private':
			self.share = self.PRIVATE_AOI
			return self.share
		else:
			logging.error('set_shared() invalid value provided.{0!s}'.format(share_str))
			return 'error'	# no change to database.

	
	#CellList() returns a cached list of the area's cells as a json dictionary
	def CellList(self):
		cell_list = []
		for cell_key in self.cells:
			cell = cell_key.get()
			if cell is not None:
				celldict = cell.Cell2Dictionary()
				if celldict is not None:
					celldict['index']  = len(cell_list)
					cell_list.append(celldict)
			else:
				logging.error ("AreaofInterest::CellList() no cell returned from key %s ", cell_key)
			
		returnstr = 'AreaofInterest::CellList() area {0!s} has cells {1!s}'.format(self.name.encode('utf-8'), cell_list)
		logging.debug(returnstr)
			
		return cell_list

	def summary_dictionary(self): # main parameters included for list of areas.
		return {
				'id': self.key.urlsafe(),			 # unique id for this area.
				'url': self.url(),						 # url to view area
				'tasks_url': self.tasks_url(),   # url to view tasks for this area
				'name': self.key.string_id(), 
				'owner': self.owner.string_id(), 
				'created_date': self.created_date, 
				'follower_count': self.followers_count,
				'share' : self.share
		}

	"""
	geojsonArea() returns boundary as a geojson dictionary
	After http://google-app-engine-samples.googlecode.com/svn-history/r4/trunk/geodatastore/jsonOutput
	"""
	def geojsonArea(self):

		coords = []
		for c in self.coordinates:
			p = {'lat': c.lat, 'lng': c.lon}
			coords.append(p)
		
		center = []
		center.append(geojson.Point((self.map_center.lat, self.map_center.lon)))
		geojson_obj =	 { 
			"type": "FeatureCollection",
			"properties": {
						"area_name" :self.name,
						"shared" :self.shared_str,
						"area_url" : self.url(),
						'owner': self.owner.string_id(), #area owner. 
						"area_description": {
							   "description": self.description,
							   "description_why": self.description_why,
							   "description_who": self.description_who,
							   "description_how": self.description_how,
							   "wiki": self.wiki,
							   "threats": self.threats
						},
						"fusion_table": {
							   "ft_link": self.ft_link,
								"ft_docid": self.ft_docid,
								 "boundary_fc": self.boundary_fc
						 }
			},
			"features": [
				  { "type": "ViewPort",
						"geometry": center, 
						"properties": {
							"name": "map_center", 
							"map_zoom" :self.map_zoom
						}
				  },
				  { "type": "Feature",
						"geometry": {
									   "type": "Polygon", 
									   "coordinates" : coords,
						 },
						 "properties": {
							   "name": "boundary"
						 }
			  }
			]
		}
		geojson_str = geojson.dumps(geojson_obj)
		logging.debug("area geojson: %s",  geojson_str)
		return geojson_str
	
	#CountMonitoredCells() returns a number of cells that are monitored.
	def CountMonitoredCells(self):
		#cell_list = []
		cell_count = 0
		for cell_key in self.cells:
			cell = cell_key.get()
			if cell is not None:
				if cell.monitored == True:
					cell_count += 1
			else:
				logging.error ("AreaofInterest::CountMonitoredCells() no cell returned from key %s ", cell_key)
				return -1
		logging.debug("AreaofInterest::CountMonitoredCells()=%d", cell_count )
		return cell_count


'''
Landsat Cell represents an 170sq km area where each image is captured. 
Each path and row identifies a unique cell.
An AOI makes overlaps a set of one or more cells - and creates a constant list of these.
Each cell has a different schedule when new images arrive.

Note that multiple LandsatCell objects for the same Landsat Cell(p,r) can be created, one for each parent area to which it belongs.

The normal name for a Cell is a Swath.				
'''
class LandsatCell(ndb.Model):
	#constants - not changed once created. Created when AOI is created. 
	path = ndb.IntegerProperty(required=True, default=0)	 # Landsat Path
	row  = ndb.IntegerProperty(required=True, default=0)	 # Landsat Row
	aoi = ndb.KeyProperty(kind=AreaOfInterest) #key to area that includes this cell
	
	#center = ndb.GeoPtProperty(required=False, default=None) # Geographic Center of Cell - not set or used.
	#bound = ndb.ListProperty(float, default=None)			# Geographic Boundary of Cell- not set or used
	
	overlap = ndb.FloatProperty(required = False) #What proportion of this cell overlaps the AOI (>0, <=1). 
	image_id = ndb.StringProperty(required =False) # An ID of a Landsat image for this cell (may not be latest)
	
	monitored = ndb.BooleanProperty(required = True, default = False) # Set if cell is monitored for new data (i.e selected in view-area)

	'''
	Cell2Dictionary()converts a cell object into a dictionary of the path,row, monitored 
	and date of latest image stored in
	 datastore for L8 collection (other collections to follow)
	'''	
	def Cell2Dictionary(self):
		#cell_list.append({"path":cell.path, "row":cell.row, "monitored":cell.monitored})
		
		celldict = {"path":int(self.path), "row":int(self.row), "monitored":"false", "LC8_latest_capture":"none", "result":"ok"}
		
		if self.monitored:
			celldict['monitored'] = "true"
		q = self.latestObservation('LANDSAT/LC8_L1T_TOA')
		#print 'latestObservation ', q
		if q is not None: #and len(q) <> 0:
			celldict['LC8_latest_capture']	= q.captured.strftime("%Y-%m-%d @ %H:%M")
		return celldict
	
	def latestObservation(self, collectionName="L8"): # query for latest observation from given imageCollection.
		q = Observation.query(Observation.image_collection == collectionName, ancestor = self.key).order(-Observation.captured).fetch(1)
		if q is not None and len(q) <> 0:
			return q[0]
		else:
			return None

	@staticmethod
	def get_cell(path, row, area_name):
		if area_name is not None:
			#area_key = AreaOfInterest.query(AreaOfInterest.name == area_name.decode('utf-8')).fetch(keys_only=True)
			cell_name=str(path*1000+row)
			cell_key = ndb.Key('AreaOfInterest', area_name.decode('utf-8'), 'LandsatCell', cell_name)
			return cell_key.get() #LandsatCell.get_by_id(cell_name,  parent=area_key)
		else:
			return LandsatCell.query().filter(LandsatCell.path == int(path)).filter(LandsatCell.row == int(row)).get()

'''
class Overlay describes a visualisation of an image asset.
It includes the map_id and token, an algorithm and information about the type. 
Used for a (Landsat) satelite image that has been retrieved and converted to a usable (visible/NDVI) format.
The image is based on an Observatioin Asset.
Note that the Overlay is an asset in the earth engine that has a limited expiry date.
If the tiles returned are 404 then it is necessary to recreate the overlay.
'''
class Overlay(ndb.Model):
	map_id	= ndb.StringProperty(required=False, default=None)	 # RGB Map Overlay Id generated in GEE - 
	token	  = ndb.StringProperty(required=False, default=None)	 # RGB Map Overlay Token might have expired.
	algorithm = ndb.StringProperty(required=False)				#identifies how the image was created - e.g. NDVI, RGB etc. #TODO How to specify this.
	overlay_role	  = ndb.StringProperty(required=False)		#Purpose of this asset for the task. expected values: 'LATEST', 'PREVIOUS'. 
	
	def Overlay2Dictionary(self):		
		obsdict = {
			"map_id"		:self.map_id, 
			"token"		  :self.token, 
			"algorithm"	 :self.algorithm,
			"overlay_role":self.overlay_role, 
			"parent"		 :str(self.key.parent()),
			"key"			 :self.key.urlsafe()
		}
		return obsdict

	@staticmethod # make it static so ndb recognises the kind='Overlay'
	def get_from_encoded_key(encoded_key):
		ovl_key = ndb.Key(urlsafe=encoded_key)
		if not ovl_key:
			logging.error('Overlay:get_from_encoded_key() -  could not read key in url') 
			return None	
		ovl =ovl_key.get()
		if not ovl:
			logging.error('Overlay:get_from_encoded_key() -  no overlay from urlkey') 
			return None
		return ovl
	


'''
class Observation (could rename to ObservationAsset) describes a Landsat satellite image.

An Observation contains a list of zero or more Overlays, each Overlay is a visualization of the ObservationAsset.

The main use is the captured date. Once this observation has been actioned, it becomes the latest, against which future observations are base-lined for change detection.
This allows the app to redraw the overlay computed by earth engine on a new browser session without recalculating it - providing the overlay token has not expired.
In which case, app will need to regenerate the observation.	

Some Observations have no image_id as they are composites of many images.
'''

class Observation(ndb.Model):
	image_collection = ndb.StringProperty(required=False)			#identifies the ImageCollection name, not an EE object.
	image_id  = ndb.StringProperty(required=False)				   # LANDSAT Image ID of Image - key to query EE.
	captured  = ndb.DateTimeProperty(required=False)				 # sysdate or date Image was captured - could be derived by EE from collection+image_id.
	obs_role  = ndb.StringProperty(required=False)		#Purpose of this asset for the task. expected values: 'LATEST', 'PREVIOUS'. 
	overlays  = ndb.KeyProperty(repeated=True, default=None) # list of keys to overlays (visualisations of this observation asset) 
	#landsatCell = ndb.ReferenceProperty(LandsatCell) #defer initialization to init to avoid forward reference to new class defined. http://stackoverflow.com/questions/1724316/referencing-classes-in-python - use parent instead. 
	
	@staticmethod # make it static so ndb recognises the kind='Observation'
	def get_from_encoded_key(encoded_key):
		obskey = ndb.Key(urlsafe=encoded_key)
		if not obskey:
			logging.error('Observation:get_from_encoded_key() -  could not read key in url') 
			return None	
		obs =obskey.get()
		if not obs:
			logging.error('Observation:get_from_encoded_key() -  no observation found from urlkey') 
			return None
		return obs
	
	def Observation2Dictionary(self):		
		obsdict = {
			"image_collection":self.image_collection, 
			"image_id" : self.image_id,	 
			"captured" : self.captured.strftime("%Y-%m-%d @ %H:%M"), 
			"obs_role" : self.obs_role,	 # ex 'latest'
			"encoded_key"   : self.key.urlsafe(),
			"overlays"  : []
		}
		#obsdict['encoded_key'] = self.key.urlsafe()
		for ovl_key in self.overlays:
			overlay = ovl_key.get()
			if overlay is not None:
				obsdict['overlays'].append(overlay.Overlay2Dictionary())
		return obsdict

'''
class Task is an observation task, based on a landsat image in an AOI. The task includes a user who is responsible for completing the task.
Each task has a unique ID.
'''

class ObservationTask(ndb.Model):
	OBSTASKS_PER_PAGE = 5
	# Observation
	name = ndb.StringProperty()
	aoi = ndb.KeyProperty(kind=AreaOfInterest) #key to area that includes this cell
	
	#privacy and sharing
	share = ndb.IntegerProperty(required=True, default=AreaOfInterest.PUBLIC_AOI) #set to hide area. see @properties below
	aoi_owner = ndb.KeyProperty(kind=User) #,collection_name='aoi_owner') #owner of the aoi- not the volunteer assigned to task. Allows quicker filtering of private areas..

	observations = ndb.KeyProperty(repeated=True) #key to observations related to this task. E.g if two images are in the same path and published at same time.

	#people -	 Expected to be a user  who is one of the area's followers. volunteering to follow the AOI
	assigned_owner = ndb.KeyProperty(kind=User) #, collection_name='assigned_owner') # user who is currently assigned the the task
	#original_owner = ndb.KeyProperty(kind=User) #, collection_name='original_user') # user originally assigned the the task - 
	
	#timestamps
	created_date = ndb.DateTimeProperty(auto_now_add=True)
	last_modified = ndb.DateTimeProperty(auto_now=True)
	
	#workflow
	status = ndb.StringProperty() #Task's workflow
	priority = ndb.IntegerProperty() #Task's priority - zero is highest priority. Other followers may be given same task but at a lower priority.
	
	#TODO: add list of references to reports
	#TODO: add an Activity record.
	
	@property
	def pages(self, obstask_count):
		if obstask_count == 0:
			return 1
		return (obstask_count + self.OBSTASK_PER_PAGE - 1) / self.OBSTASKS_PER_PAGE


	def taskurl(self):
			username=self.assigned_owner.string_id()
			task_id= self.key.id()
			#print 'taskurl: ', username, ' task id: ', task_id
			return webapp2.uri_for('view-obstask', task_id=task_id)

	
	def listurl(self, page=1, username=None): #show a list of recent tasks
		#logging.debug("listurl %s ", username )
		if page > 1:
			return webapp2.uri_for('view-obstasks',  username = username, user2view= self.assigned_owner.name, task_name= self.key.id(), page=page)
		else:
			return webapp2.uri_for('view-obstasks', username = username, user2view= self.assigned_owner.name,  task_name= self.key.id())
			
	def shared_str(self):
		if self.share == AreaOfInterest.PUBLIC_AOI:
			return 'public'
		elif self.share == AreaOfInterest.UNLISTED_AOI:
			return 'unlisted'
		elif self.share == AreaOfInterest.PRIVATE_AOI:
			return 'private'	
		else:
			return 'unspecified'	

'''
A Journal consists of user entries. Journals used for recording observations from tasks are a special class as they also record the image id.
Based on journalr.org 
'''
class Journal(ndb.Model):
	ENTRIES_PER_PAGE = 5
	MAX_JOURNALS = 100

	journal_type= ndb.StringProperty(required=True, default="journal") #"journal", "observations", "reports" etc.
	#name = ndb.StringProperty(required=True) # with ndb can use id now
	created_date = ndb.DateTimeProperty(auto_now_add=True)
	last_entry = ndb.DateTimeProperty()
	first_entry = ndb.DateTimeProperty()
	last_modified = ndb.DateTimeProperty(auto_now=True)
	entry_count = ndb.IntegerProperty(required=True, default=0)
	entry_days = ndb.IntegerProperty(required=True, default=0)

	chars = ndb.IntegerProperty(required=True, default=0)
	words = ndb.IntegerProperty(required=True, default=0)
	sentences = ndb.IntegerProperty(required=True, default=0)

	# all frequencies are per week
	freq_entries = ndb.FloatProperty(required=True, default=0.)
	freq_chars = ndb.FloatProperty(required=True, default=0.)
	freq_words = ndb.FloatProperty(required=True, default=0.)
	freq_sentences = ndb.FloatProperty(required=True, default=0.)

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
		return unicode(self.key.string_id)

	@property
	def pages(self):
		if self.entry_count == 0:
			return 1
		return (self.entry_count + self.ENTRIES_PER_PAGE - 1) / self.ENTRIES_PER_PAGE

	def url(self, page=1):
		if page > 1:
			return webapp2.uri_for('view-journal', username=self.key.parent().string_id(), journal_name=self.key.string_id(), page=page)
		else:
			return webapp2.uri_for('view-journal', username=self.key.parent().string_id(), journal_name=self.key.string_id())
	
	@staticmethod
	def get_journal(username, journal_name):
		user_key = ndb.Key('User', username)
		journal_key = ndb.Key('Journal', journal_name, parent=user_key)
		#print 'journal_key', journal_key
		return journal_key.get()		
		
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

class EntryContent(ndb.Model):
	subject = ndb.StringProperty()
	tags = ndb.StringProperty(repeated=True)
	text = ndb.TextProperty()
	rendered = ndb.TextProperty(default='')
	markup = ndb.StringProperty(required=True, indexed=False, choices=CONTENT_TYPE_CHOICES, default=RENDER_TYPE_TEXT)
	images = ndb.StringProperty(repeated=True)

	@staticmethod
	def get_entrycontent_key(journal):
		entry_id = Entry.allocate_ids(1)[0] # return next available entry_id inside parents space. [0] is start, [1] is end.
		return ndb.Key('EntryContent', entry_id, parent=journal.key)

class Entry(ndb.Model):
	date = ndb.DateTimeProperty(auto_now_add=True)
	created = ndb.DateTimeProperty(required=True, auto_now_add=True)
	last_edited = ndb.DateTimeProperty(required=True, auto_now=True)

	content = ndb.IntegerProperty(required=True) # key id of EntryContent
	blobs = ndb.StringProperty(repeated=True)

	chars = ndb.IntegerProperty(required=True, default=0)
	words = ndb.IntegerProperty(required=True, default=0)
	sentences = ndb.IntegerProperty(required=True, default=0)

	dropbox_rev = ndb.StringProperty(indexed=False)
	google_docs_id = ndb.StringProperty(indexed=False)

	WORD_RE = re.compile("[A-Za-z0-9']+")
	SENTENCE_RE = re.compile("[.!?]+")

	@property
	def time(self):
		if not self.date.hour and not self.date.minute and not self.date.second:
			return ''
		else:
			return self.date.strftime('%H:%M')

	@property
	def content_key(self):
		return ndb.Key('EntryContent', long(self.content), parent=self.key)

	@property
	def blob_keys(self):
		return [ndb.Key('Blob', long(i), parent=self.key) for i in self.blobs]

	@staticmethod
	def get_entry_key(journal, entry_id = None):
		if entry_id ==  None:
			entry_id = Entry.allocate_ids(1)[0] # return next available entry_id inside parents space. [0] is start, [1] is end.
		return ndb.Key('Entry', long(entry_id), parent=journal.key)

	@staticmethod
	def get_entry(username, journal_name, entry_id, entry_key=None):
		journal = Journal.get_journal(username, journal_name)
		if not journal:
			logging.error('Entry.get_entry(): Error no journal called %s for user %s',  journal_name, username )
			assert journal
			return None, None, None
		if not entry_key:
			#logging.debug('Entry.get_entry(): Error no entry_id %s, for user %s, journal %s', entry_id, username, journal_name )
			entry_key = Entry.get_entry_key(journal, entry_id)  #get_entry_key(username, journal_name, entry_id)
		if not entry_key:
			return None, None, None
		entry = entry_key.get()

		if entry:
			content=EntryContent.get_by_id(long(entry.content), parent = journal.key)
			if not content :
				logging.error('Entry.get_entry(): Error. No content')
			if entry.blobs:
				blobs = ndb.get_multi(entry.blob_keys)
			else:
				blobs = []
			return entry, content, blobs
		else:
			return None, None, []
	

	@staticmethod
	def get_entries(journal, latestFirst=True):
		q= Entry.query(ancestor = journal.key)
		if latestFirst:
			entries= q.order(-Entry.date)
		else:
			entries = q.order(Entry.date)
		return entries.fetch(2)
	
ACTIVITY_NEW_JOURNAL = 1
ACTIVITY_NEW_ENTRY = 2
ACTIVITY_FOLLOWING = 3
ACTIVITY_SAVE_ENTRY = 4
ACTIVITY_NEW_AREA = 5
ACTIVITY_NEW_OBS = 6
ACTIVITY_NEW_REPORT = 7
ACTIVITY_NEW_FEEDBACK = 8
ACTIVITY_DELETE_AREA = 9


ACTIVITY_CHOICES = [
	ACTIVITY_NEW_JOURNAL,
	ACTIVITY_NEW_ENTRY,
	ACTIVITY_FOLLOWING,
	ACTIVITY_SAVE_ENTRY,
	ACTIVITY_NEW_AREA,
	ACTIVITY_NEW_OBS,
	ACTIVITY_NEW_REPORT,
	ACTIVITY_NEW_FEEDBACK,
	ACTIVITY_DELETE_AREA
]

ACTIVITY_ACTION = {
	ACTIVITY_NEW_JOURNAL:	 'created a new journal',
	ACTIVITY_NEW_ENTRY:	 'started a new journal entry',
	ACTIVITY_FOLLOWING:	 'started following',
	ACTIVITY_SAVE_ENTRY:	 'updated a journal entry',
	ACTIVITY_NEW_AREA:		 'created a new area of interest',
	ACTIVITY_NEW_OBS: 'created a new observation',
	ACTIVITY_NEW_REPORT: 'created a new report',
	ACTIVITY_NEW_FEEDBACK: 'created new feedback',
	ACTIVITY_DELETE_AREA: 'deleted an area of interest'
}

class Activity(DerefModel):
	RESULTS = 50

	user = ndb.StringProperty(required=True)
	img = ndb.StringProperty(indexed=False)
	date = ndb.DateTimeProperty(auto_now_add=True)
	action = ndb.IntegerProperty(required=True, choices=ACTIVITY_CHOICES)
	object = ndb.KeyProperty()

	def get_action(self):
		r = ACTIVITY_ACTION[self.action]

		if self.action == ACTIVITY_FOLLOWING:
			#name = self.get_key('object').name()
			name = self.get_key('object')
			r += ' <a href="%s">%s</a>' %(webapp2.uri_for('user', username=name), name)

		return r

	@staticmethod
	def create(user, action, activity):
		a = Activity(user=user.name, img=user.gravatar('30'), action=action, object=activity)
		ar = a.put()
		
		#receivers = cache.get_followers(user.name)
		#receivers.append(user.name)
		#a.get_result() 
		
		#ai = ActivityIndex(parent=a, receivers=receivers)
		ai = ActivityIndex(parent=ar)
		ai.put()

class ActivityIndex(ndb.Model):
	receivers = ndb.StringProperty(repeated=True)
	date = ndb.DateTimeProperty(auto_now_add=True)

BLOB_TYPE_IMAGE = 1
BLOB_TYPE_PDF = 2

BLOB_TYPE_CHOICES = [
	BLOB_TYPE_IMAGE,
	BLOB_TYPE_PDF,
]


class Blob(DerefExpando):
	MAXSIZE = 4 * 2 ** 20 # 4MB

	blob = ndb.BlobKeyProperty(required=True)
	type = ndb.IntegerProperty(required=True, choices=BLOB_TYPE_CHOICES)
	name = ndb.StringProperty(indexed=False)
	size = ndb.IntegerProperty()
	url = ndb.StringProperty(indexed=False)

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

	@staticmethod
	def get_blob_key(entry, blob_id = None):
		if blob_id ==  None:
			blob_id = Blob.allocate_ids(1)[0] # return next available entry_id inside parents space. [0] is start, [1] is end.
		return ndb.Key('Blob', long(blob_id), parent=entry.key)

	@staticmethod
	def get_blob(username, journal_name, entry_id, entry_key=None):
		journal = Journal.get_journal(username, journal_name)

		if not entry_key:
			entry_key = Entry.get_entry_key(journal, entry_id)  #get_entry_key(username, journal_name, entry_id)
		entry = entry_key.get()

		if entry:
			content=EntryContent.get_by_id(long(entry.content), parent = journal.key)
			if not content :
				logging.error('Entry.get_entry(): Error. No content')
			if entry.blobs:
				blobs = ndb.get_multi(entry.blob_keys)
			else:
				blobs = []
			return entry, content, blobs
		else:
			return None		
	
		#handmade_key = ndb.Key('Blob', 1, parent=entry_key)
		#blob_id = ndb.allocate_ids(handmade_key, 1)[0]
		#blob_key = ndb.Key.from_path('Blob', blob_id, parent=entry_key)
		blob_key  = Blob.get_blob_key(entry)
		new_blob = Blob(key=blob_key, blob=blob, type=blob_type, name=blob.filename, size=blob.size)


RENDER_TYPE_CHOICES = [
	RENDER_TYPE_HTML,
	RENDER_TYPE_MARKDOWN,
	RENDER_TYPE_RST,
	RENDER_TYPE_TEXT,
	RENDER_TYPE_TEXTILE,
]



class BlogEntry(ndb.Model):
	ENTRIES_PER_PAGE = 10

	date = ndb.DateTimeProperty(required=True, auto_now_add=True)
	draft = ndb.BooleanProperty(required=True, default=True)
	markup = ndb.StringProperty(required=True, indexed=False, choices=RENDER_TYPE_CHOICES, default=RENDER_TYPE_MARKDOWN)
	title = ndb.StringProperty(required=True, indexed=False, default='Title')
	text = ndb.TextProperty(default='')
	rendered = ndb.TextProperty(default='')
	user = ndb.StringProperty(required=True)
	avatar = ndb.StringProperty()
	slug = ndb.StringProperty(indexed=False)

	@property
	def url(self):
		if not self.slug:
			self.slug = str(self.key.urlsafe())

		return webapp2.uri_for('blog-entry', entry=self.slug)

class Config(ndb.Expando):
	pass
