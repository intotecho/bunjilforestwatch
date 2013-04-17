
import logging

import oauth
import settings
import utils
import webapp2

URL = 'https://api.twitter.com'

OAUTH_APP_SETTINGS = {
	'consumer_key': settings.TWITTER_KEY,
	'consumer_secret': settings.TWITTER_SECRET,
	'request_token_url': URL + '/oauth/request_token',
	'access_token_url': URL + '/oauth/access_token',
	'user_auth_url': URL + '/oauth/authorize',
	'default_api_prefix': URL,
	'default_api_suffix': '.json',
	'oauth_callback': None, # set later, after webapp2 is configured
}

def oauth_client(app, *args):
	if not OAUTH_APP_SETTINGS['oauth_callback']:
		OAUTH_APP_SETTINGS['oauth_callback'] = utils.absolute_uri('twitter', action='callback')
	return oauth.OAuthClient(app, OAUTH_APP_SETTINGS, *args)

def oauth_token(*args):
	return oauth.OAuthToken(*args)
