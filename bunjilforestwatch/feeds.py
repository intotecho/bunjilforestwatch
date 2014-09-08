
import datetime
import logging
import os

from google.appengine.ext import db

import cache
import utils
import webapp2

def feed(feed, token):
	if feed == 'activity':
		title = 'bunjil user activity'
		link = webapp2.uri_for('activity')
		subtitle = 'Recent activity by bunjil users'

		items = []
		for i in cache.get_activities():
			items.append(mk_item(
				'%s %s' %(i.user, i.get_action()),
				None,
				'%s %s' %(i.user, i.get_action()),
				i.key().id(),
				i.date
			))

	elif feed == 'blog':
		title = 'bunjil blog'
		link = webapp2.uri_for('blog')
		subtitle = 'Recent bunjil blog posts'

		items = []
		for i in cache.get_blog_entries_page(1):
			items.append(mk_item(
				i.title,
				i.url,
				i.rendered,
				i.key().id(),
				i.date
			))

	elif feed.startswith('user-'):
		username = feed.partition('-')[2]
		user_key = db.Key.from_path('User', username)
		user = cache.get_by_key(user_key)

		if user.token == token:
			title = '%s\'s journalr feed' %username
			link = webapp2.uri_for('user', username=username)
			subtitle = 'Recent activity by followed by %s' %username

			items = []
			for i in cache.get_activities_follower(username):
				items.append(mk_item(
					'%s %s' %(i.user, i.get_action()),
					None,
					'%s %s' %(i.user, i.get_action()),
					i.key().id(),
					i.date
				))
		else:
			title = '%s activity feed' %username
			link = webapp2.uri_for('user', username=username)
			subtitle = 'Recent activity by %s' %username

			items = []
			for i in cache.get_activities(username=username):
				items.append(mk_item(
					'%s %s' %(i.user, i.get_action()),
					None,
					'%s %s' %(i.user, i.get_action()),
					i.key().id(),
					i.date
				))

	else:
		return ''

	d = {
		'title': title,
		'link': mk_link(link),
		'subtitle': subtitle,
		'updated': datetime.datetime.utcnow(),
		'items': items,
		'host': os.environ['HTTP_HOST'],
		'journal_url': mk_link(webapp2.uri_for('main')),
		'self_link': mk_link(webapp2.uri_for('feeds', feed=feed)),
	}

	return utils.render('atom.xml', d)

def mk_link(link):
	if link:
		return '//' + os.environ['HTTP_HOST'] + link
	else:
		return ''

def mk_item(title, link, desc, uid, date):
	return {
		'title': title,
		'link': mk_link(link),
		'content': desc,
		'id': uid,
		'date': date,
	}
