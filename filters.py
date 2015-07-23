# Copyright (c) 2011 Matt Jibson <matt.jibson@gmail.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#

import datetime
import logging

import webapp2

def url(ob, name=''):
	if ob == 'feeds':
		return webapp2.uri_for(ob, feed=name)
	elif ob == 'user':
		return webapp2.uri_for(ob, username=name)
	
	elif ob == 'view-obstasks':
			return webapp2.uri_for(ob)
		
	elif ob == 'delete-area':
		return webapp2.uri_for(ob, area_name=name)
		
	elif ob == 'user-feeds':
		return webapp2.uri_for('feeds', feed='user-%s' %name)
	elif ob == 'follow':
		return webapp2.uri_for(ob, username=name)
	elif ob in ['new-entry', 'download-journal']:
		return webapp2.uri_for(ob, username=name.key.parent().string_id(), journal_name=name.key.string_id())
	elif ob == 'blog-entry':
		return webapp2.uri_for(ob, entry=name)
	elif ob == 'edit-blog':
		return webapp2.uri_for(ob, blog_id=name)
	elif ob == 'following':
		return webapp2.uri_for(ob, username=name)
	elif ob == 'register':
		return webapp2.uri_for(ob, role=name)
	else:
		return webapp2.uri_for(ob)


def user_area_url(username, area_name):
	return webapp2.uri_for('view-area', username=username, area_name=area_name)

def area_tasks_url(area):
	return webapp2.uri_for('view-obstasks', area_name=area.name)

def area_url(area, page=1):
	return area.url(page)

def user_task_url(username, task_name):
	return webapp2.uri_for('view-task', username=username, task_name=task_name)

def task_url(task, page=1):
	return task.url(page)


def area_prev(ob, page):
	return area_url(ob, str(page - 1))

def area_next(ob, page):
	return area_url(ob, str(page + 1))

def user_journal_url(username, journal_name):
	return webapp2.uri_for('view-journal', username=username, journal_name=journal_name)

def journal_url(journal, page=1):
	return journal.url(page)

def journal_prev(ob, page):
	return journal_url(ob, str(page - 1))

def journal_next(ob, page):
	return journal_url(ob, str(page + 1))


def obstask_url(obstask):
	return obstask.taskurl()

def obstasks_url(obstask, user2view, area_name, page=1):
	if page > 1:
		return webapp2.uri_for('view-obstasks',   area_name=area_name, user2view=user2view, page=page)
	else:
		return webapp2.uri_for('view-obstasks',  area_name=area_name, user2view=user2view )

def obstasks_prev(ob, user2view, area_name, page):
	return obstasks_url(ob,  user2view, area_name, str(page - 1))

def obstasks_next(ob, user2view, area_name, page):
	return obstasks_url(ob, user2view, area_name, str(page + 1))

def blog_url(page=1):
	return webapp2.uri_for('blog', page=page)

def blog_prev(page):
	return blog_url(page - 1)

def blog_next(page):
	return blog_url(page + 1)

JDATE_FMT = '%A, %b %d, %Y %I:%M %p'
JDATE_NOTIME_FMT = '%A, %b %d, %Y'
def jdate(date):
	if not date.hour and not date.minute and not date.second:
		fmt = JDATE_NOTIME_FMT
	else:
		fmt = JDATE_FMT

	return date.strftime(fmt)

SDATE_FMT = '%B %d, %Y'
def sdate(date):
	return date.strftime(SDATE_FMT)

def entry_subject(sub, date):
	if sub:
		return sub

	return date.strftime(JDATE_FMT)

def timesince(value, default='just now'):
	now = datetime.datetime.utcnow()
	diff = now - value
	periods = (
		(diff.days / 365, 'year', 'years'),
		(diff.days / 30, 'month', 'months'),
		(diff.days / 7, 'week', 'weeks'),
		(diff.days, 'day', 'days'),
		(diff.seconds / 3600, 'hour', 'hours'),
		(diff.seconds / 60, 'minute', 'minutes'),
		(diff.seconds, 'second', 'seconds'),
	)
	for period, singular, plural in periods:
		if period:
			return '%d %s ago' % (period, singular if period == 1 else plural)
	return default

def floatformat(value):
	return '%.1f' %value

def pluralize(value, ext='s'):
	return ext if value != 1 else ''

def date(value, fmt):
	return value.strftime(fmt)

    # filesizeformat in jinja 2.6 is broken, use this from their current github
def filesizeformat(value, binary=False):
	"""Format the value like a 'human-readable' file size (i.e. 13 kB,
	4.1 MB, 102 Bytes, etc).  Per default decimal prefixes are used (Mega,
	Giga, etc.), if the second parameter is set to `True` the binary
	prefixes are used (Mebi, Gibi).
	"""
	bytes = float(value)
	base = binary and 1024 or 1000
	prefixes = [
		(binary and 'KiB' or 'kB'),
		(binary and 'MiB' or 'MB'),
		(binary and 'GiB' or 'GB'),
		(binary and 'TiB' or 'TB'),
		(binary and 'PiB' or 'PB'),
		(binary and 'EiB' or 'EB'),
		(binary and 'ZiB' or 'ZB'),
		(binary and 'YiB' or 'YB')
	]
	if bytes == 1:
		return '1 Byte'
	elif bytes < base:
		return '%d Bytes' % bytes
	else:
		for i, prefix in enumerate(prefixes):
			unit = base ** (i + 2)
			if bytes < unit:
				return '%.1f %s' % ((base * bytes / unit), prefix)
		return '%.1f %s' % ((base * bytes / unit), prefix)

filters = dict([(i, globals()[i]) for i in [
	'blog_next',
	'blog_prev',
	'blog_url',
	'date',
	'entry_subject',
	'filesizeformat',
	'floatformat',
	'jdate',
	'journal_next',
	'journal_prev',
	'journal_url',
	'obstasks_next',
	'obstasks_prev',
	'obstasks_url',
	'area_next',
	'area_prev',
	'area_url',
	'area_tasks_url',
	'pluralize',
	'sdate',
	'timesince',
	'task_url',
	'url',
	'user_journal_url',
	'user_area_url',
	'user_task_url'
]])
