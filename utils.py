# Copyright (c) 2011 Matt Jibson <matt.jibson@gmail.com>
#
#  Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WIfgsdfghsdfgsdTH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MasdfgawsdfERCHAN     TABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

import cStringIO
import StringIO
import logging
import os
import os.path
import re
import unicodedata

from django.utils import html
#from google.appengine.api import conversion
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext.webapp import template
import jinja2
import webapp2

import cache
import facebook
import filters
import models
import settings

# Fix sys.path
import fix_path
fix_path.fix_sys_path()

from docutils.core import publish_parts
import dropbox
import gdata.data
import gdata.docs.client
import gdata.docs.data
import gdata.docs.service
import gdata.gauth
import markdown
import rst_directive
import textile

env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
env.filters.update(filters.filters)

def prefetch_refprops(entities, *props):
	fields = [(entity, prop) for entity in entities for prop in props]
	ref_keys_with_none = [prop.get_value_for_datastore(x) for x, prop in fields]
	ref_keys = filter(None, ref_keys_with_none)
	ref_entities = dict((x.key(), x) for x in db.get(set(ref_keys)))
	for (entity, prop), ref_key in zip(fields, ref_keys_with_none):
		if ref_key is not None:
			prop.__set__(entity, ref_entities[ref_key])
	return entities

def render(_template, context):
	return env.get_template(_template).render(**context)

NUM_PAGE_DISP = 5
def page_list(page, pages):
	if pages <= NUM_PAGE_DISP:
		return range(1, pages + 1)
	else:
		# this page logic could be better
		half = NUM_PAGE_DISP / 2
		if page < 1 + half:
			page = half + 1
		elif page > pages - half:
			# have to handle even and odd NUM_PAGE_DISP differently
			page = pages - half + abs(NUM_PAGE_DISP % 2 - 1)

		page -= half

		return range(page, page + NUM_PAGE_DISP)

def render_options(options, default=None):
	ret = ''

	for i in options:
		if i == default:
			d = ' selected'
		else:
			d = ''

		ret += '<option%s>%s</option>' %(d, i)

	return ret

def markup(text, format):
	if format == models.RENDER_TYPE_HTML:
		return text
	elif format == models.RENDER_TYPE_TEXT:
		return html.linebreaks(html.escape(text))
	elif format == models.RENDER_TYPE_MARKDOWN:
		return markdown.Markdown().convert(text)
	elif format == models.RENDER_TYPE_TEXTILE:
		return textile.textile(text)
	elif format == models.RENDER_TYPE_RST:
		warning_stream = cStringIO.StringIO()
		parts = publish_parts(text, writer_name='html4css1',
			settings_overrides={
				'_disable_config': True,
				'embed_stylesheet': False,
				'warning_stream': warning_stream,
				'report_level': 2,
		})
		rst_warnings = warning_stream.getvalue()
		if rst_warnings:
			logging.warn(rst_warnings)
		return parts['html_body']
	else:
		raise ValueError('invalid markup')

def deunicode(s):
	return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

def slugify(s):
	s = deunicode(s)
	return re.sub('[^a-zA-Z0-9-]+', '-', s).strip('-')

def convert_html(f, title, entries, output_type='application/pdf'):
	try:
		html = render('pdf.html', {'title': title, 'entries': entries})
		asset = conversion.Asset('text/html', deunicode(html))
		conversion_request = conversion.Conversion(asset, output_type)

		result = conversion.convert(conversion_request)

		if result and result.assets:
			for i in result.assets:
				f.write(i.data)
			return None
		else:
			logging.error('Conversion error: %s', result.error_text)
			return result.error_text
	except Exception, e:
		logging.error('Conversion exception: %s', e)
		return str(e)

def absolute_uri(*args, **kwargs):
	return 'http://' + os.environ['HTTP_HOST'] + webapp2.uri_for(*args, **kwargs)

def dropbox_session():
	return dropbox.session.DropboxSession(settings.DROPBOX_KEY, settings.DROPBOX_SECRET, 'app_folder')

def dropbox_url():
	sess = dropbox_session()
	request_token = sess.obtain_request_token()
	url = sess.build_authorize_url(request_token, oauth_callback=absolute_uri('dropbox'))
	return request_token, url

def dropbox_token(request_token):
	sess = dropbox_session()
	return sess.obtain_access_token(request_token)

def dropbox_put(access_token, path, content, rev=None):
	tokens = dict([i.split('=', 1) for i in access_token.split('&')])
	sess = dropbox_session()
	sess.set_token(tokens['oauth_token'], tokens['oauth_token_secret'])
	client = dropbox.client.DropboxClient(sess)
	return client.put_file(path, content, parent_rev=rev)

GOOGLE_DATA_SCOPES = ['https://docs.google.com/feeds/']
def google_url():
	next = absolute_uri('google')
	return gdata.gauth.generate_auth_sub_url(next, GOOGLE_DATA_SCOPES, session=True)

def google_session_token(token):
	single_use_token = gdata.auth.AuthSubToken()
	single_use_token.set_token_string(token)
	docs_service = gdata.docs.service.DocsService()
	return docs_service.upgrade_to_session_token(single_use_token)

def google_revoke(token):
	docs_service = gdata.docs.service.DocsService()
	docs_service.SetAuthSubToken(token, GOOGLE_DATA_SCOPES)
	docs_service.RevokeAuthSubToken()

def google_folder(service, name, subfolder=None):
	folder_name_query = gdata.docs.service.DocumentQuery(categories=['folder'], params={'showfolders': 'true'})
	folder_name_query['title-exact'] = 'true'
	folder_name_query['title'] = name
	folder_feed = service.Query(folder_name_query.ToUri())

	if folder_feed.entry:
		return folder_feed.entry[0]

	return service.CreateFolder(name, subfolder)

def google_upload(token, path, content, entryid=None):
	docs_service = gdata.docs.service.DocsService()
	docs_service.SetAuthSubToken(token, GOOGLE_DATA_SCOPES)

	file_dir, file_name = path.rsplit('/', 1)
	f = StringIO.StringIO(content)
	ms = gdata.data.MediaSource(file_handle=f, content_type='text/html', content_length=len(content), file_name=file_name)

	if not entryid:
		j_folder = google_folder(docs_service, 'journalr')
		dest_folder = google_folder(docs_service, file_dir, j_folder)

		entry = docs_service.Upload(ms, file_name, folder_or_uri=dest_folder)
		return entry.resourceId.text
	else:
		client = gdata.docs.client.DocsClient()
		authsub = gdata.gauth.AuthSubToken(token)
		client.auth_token = authsub
		entry = client.GetDoc(entryid)
		entry = client.Update(entry, media_source=ms)
