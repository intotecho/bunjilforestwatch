
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
	
	areas_observing = db.ListProperty(db.Key, default=None) # list of areas we watch
	areas_subscribing = db.ListProperty(db.Key, default=None) # list of areas I subscribe to  (only for local)
	
# adding for bujilae
	role = db.StringProperty(required=True, choices=set(["volunteer", "local", "admin", "viewer"]))	

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


# not required
	def count(self):
		if self.entry_count and self.last_entry and self.first_entry:
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

		return 'http://www.gravatar.com/avatar/' + hashlib.md5(email).hexdigest() + '?d=mm%s' %size

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


class AreaOfInterest(db.Model):

	ENTRIES_PER_PAGE = 5
	MAX_AREAS = 24

	name = db.StringProperty(required=True)
	created_date = db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now=True)
	entry_count = db.IntegerProperty(required=True, default=0) # reports related to this area

	#subscriber who created aoi
	created_by = db.UserProperty(verbose_name=None, auto_current_user=False, auto_current_user_add=True)
	subscriber = db.UserProperty(verbose_name=None, auto_current_user=True, auto_current_user_add=False) #usually the creator
		
	#subscriber = db.ReferenceProperty(User)
	#boundary	= db.GeoPtProperty(0,0, repeated=True)

	last_observation = db.DateTimeProperty()
	first_observation = db.DateTimeProperty()
	observation_count = db.IntegerProperty(required=True, default=0)

	@property
	def observers(self):
			return User.all().filter('areas_observing', self.key())

	@property
	def subscribers(self):
			return User.all().filter('areas_subscribing', self.key())

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
			return webapp2.uri_for('view-area', username=self.key().parent().name(), area_name=self.name, page=page)
		else:
			return webapp2.uri_for('view-area', username=self.key().parent().name(), area_name=self.name)



class Journal(db.Model):
	ENTRIES_PER_PAGE = 5
	MAX_JOURNALS = 10

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


class ObservationTask(db.Model):
	date = db.DateTimeProperty(auto_now_add=True)
	created = db.DateTimeProperty(required=True, auto_now_add=True)
	last_edited = db.DateTimeProperty(required=True, auto_now=True)

	content = db.IntegerProperty(required=True) # key id of EntryContent
	aoi = db.ReferenceProperty(required = True)
	
	
	@property
	def time(self):
		if not self.date.hour and not self.date.minute and not self.date.second:
			return ''
		else:
			return self.date.strftime('%I:%M %p')


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
