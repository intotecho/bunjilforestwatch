#!/usr/bin/python
#
# library for accessing a web service (API) with the OAuth protocol
# (trying to make web service and web app server independent, not there yet)
#
# This library is a derivative of the tweetapp framework by tav@espians.com available at:
# http://github.com/tav/tweetapp/tree/master
#
# Other credits include:
# The "official" OAuth python library: http://oauth.googlecode.com/svn/code/python/
# The fftogo application: http://github.com/bgolub/fftogo/tree/master
# The FriendFeed python library: http://code.google.com/p/friendfeed-api/
#

""""OAuth library for making RESTful API calls using the OAuth protocol"""

import cgi
import logging
import urllib
import time

from hashlib import sha1
from hmac import new as hmac
from random import getrandbits

from google.appengine.api import urlfetch

# We require a JSON parsing library. These seem to be the most popular.
try:
    import cjson
    decode_json = lambda s: cjson.decode(s.decode("utf-8"), True)
except ImportError:
    try:
        # Django includes simplejson
        from django.utils import simplejson
        decode_json = lambda s: simplejson.loads(s.decode("utf-8"))
    except ImportError:
        import json
        decode_json = lambda s: _unicodify(json.read(s))


# ------------------------------------------------------------------------------
# oauth client
# ------------------------------------------------------------------------------

class OAuthToken(object):
    '''OAuthToken is a data type that represents an End User via either an access or request token.'''

    key = None
    secret = None

    '''
    key = the token
    secret = the token secret
    '''
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def to_string(self):
        return urllib.urlencode({'oauth_token': self.key, 'oauth_token_secret': self.secret})

    # return a token from something like:
    # oauth_token_secret=digg&oauth_token=digg
    # @staticmethod
    def from_string(s):
        params = cgi.parse_qs(s, keep_blank_values=False)
        key = params['oauth_token'][0]
        secret = params['oauth_token_secret'][0]
        return OAuthToken(key, secret)
    from_string = staticmethod(from_string)

    def __str__(self):
        return self.to_string()


class OAuthClient(object):
    """OAuth client."""

    def __init__(self, webapp_api, service_info, token=None):
        self.service_info = service_info
        self.service_key = None
        self.oauth_callback = service_info['oauth_callback']
        self.token = token

    # public methods

    def get(self, api_method, **extra_params):

        if not (api_method.startswith('http://') or api_method.startswith('https://')):
            api_method = '%s%s%s' % (
                self.service_info['default_api_prefix'], api_method,
                self.service_info['default_api_suffix']
                )

        fetch = urlfetch.fetch(self.get_signed_url(
            api_method, self.token, **extra_params
            ))

        if fetch.status_code != 200:
            raise ValueError(
                "Error calling... Got return status: %i [%r]" %
                (fetch.status_code, fetch.content)
                )

        return decode_json(fetch.content)

    def post(self, api_method, **extra_params):

        if not (api_method.startswith('http://') or api_method.startswith('https://')):
            api_method = '%s%s%s' % (
                self.service_info['default_api_prefix'], api_method,
                self.service_info['default_api_suffix']
                )

        payload = self.get_signed_payload(
            api_method, self.token, **extra_params
            )
        headers = {}
        headers["Content-Type"] = "application/x-www-form-urlencoded"

        fetch = urlfetch.fetch(api_method, payload=payload, method=urlfetch.POST, headers=headers)

        if fetch.status_code != 200:
            raise ValueError(
                "Error calling... Got return status: %i [%r]" %
                (fetch.status_code, fetch.content)
                )

        return decode_json(fetch.content)

    # oauth workflow

    def get_request_token(self):
        token_info = self.get_data_from_signed_url(self.service_info['request_token_url'])
        token = OAuthToken.from_string(token_info)
        return token

    def get_access_token(self, oauth_token):
        token_info = self.get_data_from_signed_url(
            self.service_info['access_token_url'], oauth_token
            )
        token = OAuthToken.from_string(token_info)
        return token

    def get_authorize_url(self, oauth_token):
        if self.oauth_callback:
            oauth_callback = {'oauth_callback': self.oauth_callback}
        else:
            oauth_callback = {}

        return self.get_signed_url(
            self.service_info['user_auth_url'], oauth_token, **oauth_callback
            )

    # request marshalling

    def get_data_from_signed_url(self, __url, __token=None, __meth='GET', **extra_params):

        signed_url = self.get_signed_url(__url, __token, __meth, **extra_params)
        fetch = urlfetch.fetch(signed_url)
        if fetch.status_code != 200:
            raise ValueError(
                "Error calling... Got return status: %i [%r]" %
                (fetch.status_code, fetch.content)
                )

        data = fetch.content
        #logging.debug(data)
        return data

    def get_signed_url(self, __url, __token=None, __meth='GET', **extra_params):

        service_info = self.service_info

        kwargs = {
            'oauth_consumer_key': service_info['consumer_key'],
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_version': '1.0',
            'oauth_timestamp': int(time.time()),
            'oauth_nonce': getrandbits(64),
            }

        kwargs.update(extra_params)

        if self.service_key is None:
            self.service_key = self.service_info['consumer_secret']+'&'

        if __token is not None:
            kwargs['oauth_token'] = __token.key
            key = self.service_key + encode(__token.secret)
        else:
            key = self.service_key

        message = '&'.join(map(encode, [
            __meth.upper(), __url, '&'.join(
                '%s=%s' % (encode(k), encode(kwargs[k])) for k in sorted(kwargs)
                )
            ]))

        kwargs['oauth_signature'] = hmac(
            key, message, sha1
            ).digest().encode('base64')[:-1]

        return '%s?%s' % (__url, urllib.urlencode(kwargs))

    def get_signed_payload(self, __url, __token=None, __meth='POST', **extra_params):

        service_info = self.service_info

        kwargs = {
            'oauth_consumer_key': service_info['consumer_key'],
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_version': '1.0',
            'oauth_timestamp': int(time.time()),
            'oauth_nonce': getrandbits(64),
            }

        kwargs.update(extra_params)

        if self.service_key is None:
            self.service_key = self.service_info['consumer_secret']+'&'

        if __token is not None:
            kwargs['oauth_token'] = __token.key
            key = self.service_key + encode(__token.secret)
        else:
            key = self.service_key

        message = '&'.join(map(encode, [
            __meth.upper(), __url, '&'.join(
                '%s=%s' % (encode(k), encode(kwargs[k])) for k in sorted(kwargs)
                )
            ]))

        kwargs['oauth_signature'] = hmac(
            key, message, sha1
            ).digest().encode('base64')[:-1]

        return urllib.urlencode(kwargs)

# ------------------------------------------------------------------------------
# utility functions
# ------------------------------------------------------------------------------

def encode(text):
    return urllib.quote(str(text), '')

def _encodify(s):
    return unicode(s).encode('utf-8')
