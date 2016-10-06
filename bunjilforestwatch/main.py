#!/usr/bin/env python
""" 
.. highlight:: rst

main.py Web Handlers
====================

This document is planned to give a tutorial-like overview of all web handlers in the bunjil forest wastch app.
"""
# from jsonpointer import resolve_pointer



from __future__ import with_statement
import os

from google.appengine.ext import ndb

import glad_data_seeder
from handlers.base_handlers import BaseHandler
from handlers.base_handlers import BaseUploadHandler
from handlers.glad_cluster_handlers import SeedGladClusterData
from handlers.observation_task_handlers import ObservationTaskHandler
from handlers.observation_task_preference_handlers import ObsTaskPreferenceHandler
from handlers.observation_task_preference_handlers import ObsTaskPreferenceResource
from handlers.overlay_handlers import RegenerateOverlayHandler
from handlers.region_handlers import RegionHandler
from observation_task_routers.dummy_router import DummyRouter
from observation_task_routers.simple_router import SimpleRouter
from observation_task_routers.preference_router import PreferenceRouter
from vote_weighting_calculator.simple_vote_calculator import SimpleVoteCalculator

PRODUCTION_MODE = not os.environ.get(
    'SERVER_SOFTWARE', 'Development').startswith('Development')

if not PRODUCTION_MODE:
    from sys import path

    sdk_path = 'C:/Program Files (x86)/Google/google_appengine/'  # https://cloud.google.com/appengine/docs/python/tools/libraries27#vendoring
    path.insert(0, sdk_path)
    import dev_appserver

    dev_appserver.fix_sys_path()

    from google.appengine.tools.devappserver2.python import sandbox

    sandbox._WHITE_LIST_C_MODULES += ['_ctypes', 'gestalt']
    disable_ssl_certificate_validation = True  # bug in HTTPlib i think

LANSAT_CELL_AREA = (185 * 170)  # sq.km  http://iic.gis.umn.edu/finfo/land/landsat2.htm
import logging
#import urllib


from django.utils import html  # used for entry.html markup
import models
import eeservice

import mailer
import base64
import datetime
import re
import geojson
import bleach
import apiservices
import case_workflow.case_workflow_manager
from observation_task_routers import *

from google.appengine.api import files
from google.appengine.api import taskqueue
from google.appengine.api.app_identity import get_default_version_hostname
from google.appengine.api import users
from google.appengine.ext import blobstore

from google.appengine.ext.webapp import blobstore_handlers, urllib
from webapp2_extras import sessions
from google.appengine.api import memcache

# from apiclient.discovery import build
# from oauth2client.appengine import OAuth2Decorator
# from oauth2client.appengine import AppAssertionCredentials

import settings
import secrets
import gladalerts
import region_manager

'''
decorator = OAuth2Decorator(
    client_id=settings.MY_LOCAL_SERVICE_ACCOUNT,
    client_secret=settings.MY_LOCAL_PRIVATE_KEY_FILE,
    scope="https://www.googleapis.com/auth/fusiontables",
    user_agent='bunjilfw')
'''

import json
import webapp2
import cache
import counters
import facebook

import twitter
import utils
from urlparse import urlparse


def rendert(s, p, d={}):
    session = s.session
    d['session'] = session

    if 'user' in session:
        d['user'] = session['user']
    # this is still set after logout (i'm not sure why it's set at all), so use this workaround
    elif 'user' in d:
        del d['user']

    for k in ['login_source']:
        if k in session:
            d[k] = session[k]

    d['messages'] = s.get_messages()
    d['active'] = p.partition('.')[0]

    if settings.GOOGLE_ANALYTICS:
        d['google_analytics'] = settings.GOOGLE_ANALYTICS

    s.response.out.write(utils.render(p, d))


class EarthEngineWarmUpHandler(BaseHandler):
    """ Ensures the App is connected to the EarthEngine API
    Behaves differently for debug dev_server and production.

    """

    initEarthEngine = eeservice.EarthEngineService()
    """ global is only set once.
    """

    def get(self):
        logging.debug('main.py EarthEngineWarmUpHandler')
        initEarthEngine.isReady()
        self.response.status = 202  # The request has been accepted for processing
        self.response.write("EarthEngineWarmUpHandler")
        return

class MainPage(BaseHandler):
    """ Main handler for default page.
    Default page is index.html if not authenticated, or index-user if authenticated.
    """

    def get(self):
        if 'user' in self.session:
            # THIS CAN BE OPTIMISED
            user_key = self.session['user']['key']
            # print self.session['user']['key'], user_key

            journals = cache.get_journals(user_key)
            areas = cache.get_areas(user_key)  # areas created by this user.
            following_areas = cache.get_following_areas(user_key)
            other_areas = cache.get_other_areas_list(user_key)

            following = cache.get_by_keys(cache.get_following(self.session['user']['name']),
                                          'User')  # for journal not areas
            followers = cache.get_by_keys(cache.get_followers(self.session['user']['name']),
                                          'User')  # for journal not areas
            # fixme: why are these the same?

            self.populate_user_session()  # Only need to do this when areas, journals  or followers change
            self.render('index-user.html', {
                'activities': cache.get_activities_follower(self.session['user']['name']),
                'username': self.session['user']['name'],
                'user': self.session['user']['name'],
                'journals': journals,
                'thisuser': True,
                'token': self.session['user']['token'],
                'following': following,  # other users
                'followers': followers,  # other users
                'areas': areas,
                'following_areas': following_areas,
                'other_areas': other_areas,  # other areas.
                'show_navbar': True
            })
        else:
            # not logged in
            tasks = cache.get_obstasks_keys(None, None)  # list of all task keys #TODO is it needed?
            obstasks = cache.get_obstasks_page(0, None, None)  # rendered page of tasks (0 or latest only)

            if obstasks == None or len(obstasks) == 0:
                logging.info('MainPageIndex  - no tasks!')
                obstask = None
                obstasks = None
                tasks = None
            else:
                obstask = cache.get_task(tasks[0])  # template needs this to get listurl to work?

            self.render('index.html', {
                'obstask': obstask,
                'obstasks': obstasks,
                'tasks': tasks,
                'show_navbar': False
            })

class MainPageObsTask(BaseHandler):
    """ Main handler for default page.
    Default page is index.html if not authenticated, or index-user if authenticated.
    """

    def get(self):
        # TODO: to move this logic to the client router instead
        if 'user' in self.session:
            try:
                preference = self.preference;
            except AttributeError:
                # Get preference from datastore
                preference = models.ObservationTaskPreference.get_by_user_key(self.session['user']['key'])
                self.preference = preference

            if preference:
                self.render('bfw-baseEntry-react.html')
            else:
                # Preference can be empty after creation (async issue?)
                # Regardless, we don't care, just render preference entry
                self.redirect(webapp2.uri_for('obsTaskPreference'))
        else:
            self.render('index.html', {
                'show_navbar': False
            })  # not logged in.

class ViewAllAreas(BaseHandler):
    def get(self, username):

        if 'user' in self.session:
            #
            areas = cache.get_areas(self.session['user']['key'])
            all_areas = cache.get_all_areas()
            # logging.info( "areas = %s", areas)

            self.render('view-areas.html', {
                'thisuser': True,
                'token': self.session['user']['token'],
                'areas': areas,
                'show_navbar': True
            })
        else:
            self.render('index.html', {
                'show_navbar': False
            })  # not logged in.


class FacebookCallback(BaseHandler):
    def get(self):
        if 'code' in self.request.GET and 'local_redirect' in self.request.GET:
            local_redirect = self.request.get('local_redirect')
            access_dict = facebook.access_dict(self.request.get('code'), {'local_redirect': local_redirect})

            if access_dict:
                self.session['access_token'] = access_dict['access_token']
                self.redirect(webapp2.uri_for(local_redirect, callback='callback'))
                return

        self.redirect(webapp2.uri_for('main2'))


class GoogleLogin(BaseHandler):
    def get(self):
        current_user = users.get_current_user()
        user, registered = self.process_credentials(current_user.nickname(), current_user.email(),
                                                    models.USER_SOURCE_GOOGLE, current_user.user_id())
        if not registered:
            if 'role' in self.request.GET:
                role = self.request.get('role')
            else:
                role = "unknown"
            self.redirect(webapp2.uri_for('register', role=role))

        else:
            self.redirect(webapp2.uri_for('main'))


class FacebookLogin(BaseHandler):
    def get(self):
        if 'callback' in self.request.GET:
            user_data = facebook.graph_request(self.session['access_token'])

            if user_data is not False and 'username' in user_data and 'email' in user_data:
                user, registered = self.process_credentials(user_data['username'], user_data['email'],
                                                            models.USER_SOURCE_FACEBOOK, user_data['id'])

                if not registered:
                    self.redirect(webapp2.uri_for('register'))
                    return
        else:
            self.redirect(facebook.oauth_url({'local_redirect': 'login-facebook'}, {'scope': 'email'}))
            return

        self.redirect(webapp2.uri_for('main'))


class RegisterUserHandler(BaseHandler):
    USERNAME_RE = re.compile("^[a-z0-9][a-z0-9_]+$")

    def get(self):
        return self.post()

    def post(self):

        if 'register' in self.session:
            errors = {}
            if 'role' in self.request.POST:
                role = self.request.get('role')
            elif 'role' in self.request.GET:
                role = self.request.get('role')
            else:
                role = "unknown"

            if not role or role == 'unknown':
                role = self.request.get('roleoptionsRadios')
                # print 'options ' + role
            if not role:
                role = "unknown"

            current_user = users.get_current_user()
            if current_user:
                email = current_user.email()
            else:
                email = None

            if 'submit' in self.request.POST:
                username = self.request.get('username')
                lusername = username.lower()
                # email = self.request.get('email')
                # lusers = models.User.all(keys_only=True).filter('lname', lusername).get()
                existing_user = models.User.get_by_id(lusername)  # .fetch(keys_only=True)
                if not RegisterUserHandler.USERNAME_RE.match(lusername):
                    if username and username[0] == '_':
                        errors['username'] = 'Username cannot begin with a dash.'
                    else:
                        errors['username'] = 'Username may only contain alphanumeric characters or dashes.'
                elif lusername in RESERVED_NAMES or existing_user:
                    errors['username'] = 'Username is already taken.'
                else:
                    source = self.session['register']['source']
                    uid = self.session['register']['uid']
                    '''
                    if not email:
                        errors['email'] = 'You must have an email to use this service.'
                        email = None
                    '''

                    user = models.User.get_or_insert(username,
                                                     role=role,
                                                     name=username,
                                                     lname=lusername,
                                                     email=email,
                                                     facebook_id=uid if source == models.USER_SOURCE_FACEBOOK else None,
                                                     google_id=uid if source == models.USER_SOURCE_GOOGLE else None,
                                                     token=base64.urlsafe_b64encode(os.urandom(30))[:32],
                                                     )

                    if getattr(user, '%s_id' % source) != uid:
                        errors['username'] = 'Username is already taken.'
                    else:
                        del self.session['register']
                        self.populate_user_session(user)
                        counters.increment(counters.COUNTER_USERS)
                        mailer.new_user_email(user)  # mail to admin

                        if role == 'local':
                            self.add_message('Success',
                                             '%s, Welcome to Bunjil Forest Watch. Now create a new area that you want monitored.' % user)
                            self.redirect(webapp2.uri_for('new-area'))
                        else:
                            self.add_message('Success', '%s, Welcome new volunteer. Choose an area to follow.' % user)
                            self.redirect(webapp2.uri_for('main'))
                        return
            else:
                email = self.session['register']['email']
                username = email.split('@')[0]  # use first part of email as suggested username

            self.render('register.html', {'username': username, 'email': email, 'errors': errors, 'role': role})
        else:
            self.redirect(webapp2.uri_for('main'))


class NewUserHandler(BaseHandler):  # NOT CALLED !!! see RegisterUserHandler

    def get(self):
        logging.critical('NewUserHandler should not be called')
        if 'role' in self.request.GET:
            role = self.request.get('role')
        else:
            role = "unknown"
        self.render('new-user.html', {
            'show_navbar': False,
            'role': role
        })

    def post(self):
        logging.critical('NewUserHandler should not be called')
        if 'register' in self.session:
            errors = {}

            if 'submit' in self.request.POST:
                username = self.request.get('username')
                lusername = username.lower()
                email = self.request.get('email')
                lusers = models.User.all(keys_only=True).filter('lname', lusername).get()

                if not RegisterUserHandler.USERNAME_RE.match(lusername):
                    errors[
                        'username'] = 'Username may only contain alphanumeric characters or dashes and cannot begin with a dash.'
                elif lusername in RESERVED_NAMES or lusers:
                    errors['username'] = 'Username is already taken.'
                else:
                    source = self.session['register']['source']
                    uid = self.session['register']['uid']

                    if not email:
                        errors['email'] = 'You must have an email to use this service.'
                        email = None

                    user = models.User.get_or_insert(username,
                                                     role=rolechoice,
                                                     name=username,
                                                     lname=lusername,
                                                     email=email,
                                                     facebook_id=uid if source == models.USER_SOURCE_FACEBOOK else None,
                                                     google_id=uid if source == models.USER_SOURCE_GOOGLE else None,
                                                     token=base64.urlsafe_b64encode(os.urandom(30))[:32],
                                                     )

                    if getattr(user, '%s_id' % source) != uid:
                        errors['username'] = 'Username is already taken.'
                    else:
                        del self.session['register']
                        self.populate_user_session(user)
                        counters.increment(counters.COUNTER_USERS)
                        mailer.new_user_email(user)
                        if role == 'local':
                            self.add_message('Success',
                                             '%s, Welcome to Bunjil Forest Watch. Now create a new area that you want monitored.' % user)
                            self.redirect(webapp2.uri_for('new-area'))
                        else:
                            self.add_message('Success', '%s, Welcome new volunteer. Choose an area to follow.' % user)
                            self.redirect(webapp2.uri_for('main'))
                        return
            else:
                username = ''
                email = self.session['register']['email']
            self.render('register.html', {'username': username, 'email': email, 'errors': errors})
        else:
            self.redirect(webapp2.uri_for('main'))


class Logout(BaseHandler):
    def get(self):
        self.logout()
        self.redirect(users.create_logout_url(webapp2.uri_for('main')))


class GoogleSwitch(BaseHandler):
    def get(self):
        self.logout()
        self.redirect(users.create_logout_url(webapp2.uri_for('login-google', protected_url='/')))


class AccountHandler(BaseHandler):  # superseded for now by user.html. no menu path to this.
    def get(self):
        if 'user' not in self.session:
            self.add_message('danger', 'You must log in to access your account.')
            self.redirect(webapp2.uri_for('main'))
            return

        u = cache.get_user(self.session['user']['name'])
        changed = False

        if 'callback' in self.request.GET:
            if 'access_token' in self.session:
                user_data = facebook.graph_request(self.session['access_token'])

                if u.facebook_id and user_data['id'] != u.facebook_id:
                    self.add_message('danger', 'This account has already been attached to a facebook account.')
                else:
                    u.facebook_id = user_data['id']
                    u.facebook_enable = True
                    u.facebook_token = self.session['access_token']
                    changed = True
                    self.add_message('success', 'Facebook integration enabled.')
        elif 'disable' in self.request.GET:
            disable = self.request.get('disable')
            if disable in models.USER_SOCIAL_NETWORKS or disable in models.USER_BACKUP_NETWORKS:
                setattr(u, '%s_enable' % disable, False)
                self.add_message('success', '%s posting disabled.' % disable.title())
                changed = True
        elif 'enable' in self.request.GET:
            enable = self.request.get('enable')
            if enable in models.USER_SOCIAL_NETWORKS or enable in models.USER_BACKUP_NETWORKS:
                setattr(u, '%s_enable' % enable, True)
                self.add_message('success', '%s posting enabled.' % enable.title())
                changed = True
        elif 'deauthorize' in self.request.GET:
            deauthorize = self.request.get('deauthorize')
            changed = True
            if deauthorize == models.USER_SOURCE_FACEBOOK:
                u.facebook_token = None
                u.facebook_enable = False
                self.add_message('success', 'Facebook posting deauthorized.')
            elif deauthorize == models.USER_SOURCE_TWITTER:
                u.twitter_key = None
                u.twitter_secret = None
                u.twitter_enable = None
                self.add_message('success', 'Twitter posting deauthorized.')
            elif deauthorize == models.USER_BACKUP_GOOGLE_DOCS:
                utils.google_revoke(u.google_docs_token)
                u.google_docs_token = None
                u.google_docs_enable = None
                self.add_message('success', 'Google Docs backup deauthorized.')

        if changed:
            u.put()
            cache.set_keys([u])

        self.render('account.html', {
            'u': u,
            'show_navbar': True,
            # 'backup':
            'social': {
                'facebook': {
                    'auth_text': 'authorize' if not u.facebook_token else 'deauthorize',
                    'auth_url': facebook.oauth_url({'local_redirect': 'account'}, {
                        'scope': 'publish_stream,offline_access'}) if not u.facebook_token else webapp2.uri_for(
                        'account', deauthorize='facebook'),
                    'enable_class': 'disabled' if not u.facebook_token else '',
                    'enable_text': 'enable' if not u.facebook_enable or not u.facebook_token else 'disable',
                    'enable_url': '#' if not u.facebook_token else webapp2.uri_for('account',
                                                                                   enable='facebook') if not u.facebook_enable else webapp2.uri_for(
                        'account', disable='facebook'),
                    'label_class': 'warning' if not u.facebook_token else 'success' if u.facebook_enable else 'important',
                    'label_text': 'not authorized' if not u.facebook_token else 'enabled' if u.facebook_enable else 'disabled',
                },
                'twitter': {
                    'auth_text': 'authorize' if not u.twitter_key else 'deauthorize',
                    'auth_url': webapp2.uri_for('twitter', action='login') if not u.twitter_key else webapp2.uri_for(
                        'account', deauthorize='twitter'),
                    'enable_class': 'disabled' if not u.twitter_key else '',
                    'enable_text': 'enable' if not u.twitter_enable or not u.twitter_key else 'disable',
                    'enable_url': '#' if not u.twitter_key else webapp2.uri_for('account',
                                                                                enable='twitter') if not u.twitter_enable else webapp2.uri_for(
                        'account', disable='twitter'),
                    'label_class': 'warning' if not u.twitter_key else 'success' if u.twitter_enable else 'important',
                    'label_text': 'not authorized' if not u.twitter_key else 'enabled' if u.twitter_enable else 'disabled',
                },
            },
        })

    def post(self):
        changed = False
        u = cache.get_user(self.session['user']['name'])

        if 'settings' in self.request.POST:
            if 'email' in self.request.POST:
                email = self.request.get('email')
                if not email:
                    email = None
                email = email.replace("'", "").replace('"', "")  # Not XSS sanitised
                self.add_message('info', 'Email address updated.')

                if self.session['user']['email'] != email:
                    u.email = email
                    changed = True

        if 'social' in self.request.POST:
            self.add_message('success', 'Social media settings saved.')

            facebook_enable = 'facebook' in self.request.POST and self.request.get('facebook') == 'on'
            if u.facebook_enable != facebook_enable:
                u.facebook_enable = facebook_enable
                changed = True

        if changed:
            u.put()
            cache.set_keys([u])
            self.populate_user_session()

        self.redirect(webapp2.uri_for('account'))


'''
ExistingAreaHandler supports GET to View the Area and PUT(PATCH) to update the area.
DELETE is not supported.
'''

class ExistingAreaHandler(BaseHandler):

    def delete(self, area_name):
        #TODO Make deleteArea RESTFUL
        self.response.set_status(400)
        return self.response.out.write("Sorry HTTP DELETE not supported. Use:  /area/< area_name >/delete")

    '''
    PATCH Area - owner can update an existing area
    The method is post but it is actually overriden to a PATCH, x-http-method-override
    '''
    def post(self, area_name):

        if self.request.headers['x-http-method-override'] == 'PATCH':
            logging.info("AreaHandler() PATCHING area ")
        else:
            self.response.set_status(405)
            return self.response.out.write(
                '{"status": "error", "reason": "post not accepted without x-http-method-override to PATCH" }')

        current_user = users.get_current_user()
        if not current_user:
            abs_url = urlparse(self.request.uri)
            original_url = abs_url.path
            logging.info('No user logged in. Redirecting from protected url: ' + original_url)
            self.response.set_status(401)
            return self.response.out.write('{"status": "error", "reason": "not logged in" }')

        user, registered = self.process_credentials(current_user.nickname(), current_user.email(),
                                                    models.USER_SOURCE_GOOGLE, current_user.user_id())

        if not registered:
            self.response.set_status(401)
            return self.response.out.write('{"status": "error", "reason": "not logged in" }')
        try:
            username = self.session['user']['name']
        except:
            logging.error('Should never get this exception')
            self.response.set_status(500)
            return self.response.out.write('{"status": "error", "reason": "exception in user session" }')

        if 'user' not in self.session:
            self.response.set_status(403)
            return self.response.out.write('{"status": "error", "reason": "user not in session" }')

        area = cache.get_area(area_name)
        if not area:
            self.response.set_status(404)
            return self.response.out.write('{"status": "error", "reason": "area not found" }')

        if not area or (area.owner.string_id() != user.name):
            self.response.set_status(403)
            return self.response.out.write('{"status": "error", "reason": "user not owner of area" }')

        if (area.owner.string_id() != user.name) and (user.role != 'admin'):
            self.response.set_status(403)
            # "Only the owner '{0!s}' of area '{1!s}' or admin can update an area.".format(area.owner, area.name)
            return self.response.out.write('{"status": "error", "reason": "user not owner of area" }')

        patch_ops_str = self.request.body.decode('utf-8')
        logging.debug("UpdateArea() with: {0!s}".format(patch_ops_str))

        try:
            patch_ops = json.loads(patch_ops_str)
        except:
            self.response.set_status(400)
            return self.response.out.write('{"status": "error", "reason": "JSON Parse error in patch request" }')

        status = 404
        op_results = []

        for operation in patch_ops:
            safe_value = bleach.linkify(bleach.clean(operation['value']))

            if operation['path'] == "/features/mapview":

                try:
                    lat_str = operation['value']['geometry']['coordinates'][1]
                    if not lat_str:
                        return self.response.write('error no lat param')

                    lng_str = operation['value']['geometry']['coordinates'][0]
                    if not lng_str:
                        return self.response.write('error no lng param ')

                    zoom = operation['value']['properties']['zoom']

                except KeyError:
                    self.response.set_status(400)
                    return self.response.write('error reading mapview params')

                area.map_zoom = int(zoom)
                area.map_center = ndb.GeoPt(float(lat_str), float(lng_str))
                op_results.append({"result": "Updated maview", "value": safe_value, "id": "n/a"})
                status = 200

            if operation['path'] == "/features/geojsonboundary":

                # print 'update boundary with: ', operation['value']

                eeFeatureCollection, status, errormsg = models.AreaOfInterest.get_eeFeatureCollection(
                    operation['value'])
                # print  eeFeatureCollection, status, errormsg
                if eeFeatureCollection == None:
                    self.response.set_status(status)
                    #op_results.append({"result": "Could not update boundary", "value": errormsg, "id": "n/a"})
                    #return self.response.out.write("Could not convert boundary to feature collection: " + errormsg)
                    status = 400
                    return self.response.write('{"status": "error", "reason": "Could not convert boundary to feature collection %s":  }' %(errormsg))
                else:

                    def update_txn(area, boundary_hull_dict):
                        area.set_boundary_fc(boundary_hull_dict, True)
                        area.set_boundary_geojsonstr(operation['value'])
                        area.region = region_manager.find_regions(eeFeatureCollection)
                        area.put()
                        return

                    boundary_hull_dict = models.AreaOfInterest.calc_boundary_fc(eeFeatureCollection)
                    ndb.transaction(lambda: update_txn(area, boundary_hull_dict), xg=True)

                    #area.set_boundary_fc(eeFeatureCollection, True)
                    #area.boundary_geojsonstr = json.dumps(operation['value'])
                    op_results.append({"result": "Updated boundary_geojsonstr",
                                       "value":  area.boundary_geojsonstr,
                                       "id": "n/a"})
                    status = 200

            if operation['path'] == "/properties/fusion_table":
                area.ft_docid = safe_value
                op_results.append({"result": "Updated fusion table id", "value": safe_value, "id": "n/a"})
                status = 200

            if operation['path'] == "/properties/boundary_type":
                def update_txn_boundary_type(area):
                    area.boundary_type = safe_value
                    area.put()
                ndb.transaction(lambda: update_txn_boundary_type(area), xg=True)
                op_results.append({"result": "Updated boundary_type", "value": safe_value, "id": "n/a"})
                status = 200

            if operation['path'] == "/properties/area_description/description":
                area.description = safe_value
                op_results.append({"result": "Updated description_what", "value": safe_value, "id": operation['id']})
                status = 200

            if operation['path'] == "/properties/area_description/description_why":
                area.description_why = safe_value
                op_results.append({"result": "Updated description_why", "value": safe_value, "id": operation['id']})
                status = 200

            if operation['path'] == "/properties/area_description/description_how":
                area.description_how = safe_value
                op_results.append({"result": "Updated description_how", "value": safe_value, "id": operation['id']})
                status = 200

            if operation['path'] == "/properties/area_description/description_who":
                area.description_who = safe_value
                op_results.append({"result": "Updated description_who", "value": safe_value, "id": operation['id']})
                status = 200

            if operation['path'] == "/properties/area_description/threats":
                area.threats = safe_value
                op_results.append({"result": "Updated threats", "value": safe_value, "id": operation['id']})
                status = 200

            if operation['path'] == "/properties/area_description/wiki":
                area.wiki = safe_value
                op_results.append({"result": "Updated wiki", "value": safe_value, "id": operation['id']})
                status = 200

            if operation['path'] == "/properties/shared":

                if area.set_shared(safe_value) == 'error':
                    logging.error('Shared, invalid value {0!s}'.format(safe_value))
                    self.response.set_status(400)
                    return self.response.write('{"status": "error", "reason": "bad value for shared" }')

                op_results.append({"result": "Updated shared", "value": safe_value, "id": operation['id']})
                status = 200

        if status != 200:
            self.response.set_status(status)
            op_results.append(
                {"result": "Error No valid path found for area", "value": safe_value, "id": operation['id']})
            return self.response.write('{"status": "error", "reason": "Error No valid path found for op" }')

        try:
            key = area.put()
            print 'put area key %s', key
        except Exception, e:
            self.response.set_status(500)
            message = 'Exception saving area to db {0!s}'.format(e)
            logging.error(message)
            return self.response.out.write('{"status": "error", "reason": ' + message + '}')

        #try:
            #cache.clear_area_cache(self.session['user']['key'], area.key) #@fixme DOES IT WORK?
            #cache.flush()
            # cache.delete([cache.C_AREA %(username, area.name),
            #              cache.C_AREA %(None, area.name)])
        #except Exception, e:
        #    self.response.set_status(500)
        #    message = 'Exception clearing cache {0!s}'.format(e)
        #    logging.error(message)
        #    return self.response.out.write('{"status": "error", "reason": ' + message + '}')

        results = {
            "status": "ok",
            "updates": op_results
        }

        # response_str = results
        logging.info('Patched Area: {0!s} with result {1!s} '.format(area_name, results))

        self.response.set_status(200)
        return self.response.out.write(json.dumps(results))


    '''
    GET: to View Existing Area
    '''
    def get(self, area_name):
        area_name = area_name
        current_user = users.get_current_user()
        if not current_user:
            abs_url = urlparse(self.request.uri)
            original_url = abs_url.path
            logging.info('No user logged in. Redirecting from protected url: ' + original_url)
            self.add_message('danger', 'You must log in to view areas.')
            return self.redirect(users.create_login_url(original_url))
        user, registered = self.process_credentials(current_user.nickname(), current_user.email(),
                                                    models.USER_SOURCE_GOOGLE, current_user.user_id())

        if not registered:
            return self.redirect(webapp2.uri_for('register'))
        try:
            username = self.session['user']['name']
        except:
            logging.error('Should never get this exception')
            self.add_message('danger', 'You must log in to see this page.')

            if 'user' not in self.session:
                self.redirect(webapp2.uri_for('main'))
                return

        area = cache.get_area(area_name)
        if not area or (
                    area.share == area.PRIVATE_AOI and area.owner.string_id() != user.name and not users.is_current_user_admin()):
            self.add_message('danger', "Area not found!")
            logging.error('AreaHandler: Area not found! %s', area_name)
            self.redirect(webapp2.uri_for('main'))
        else:
            if (area.share == area.PRIVATE_AOI and area.owner.string_id() != user.name and users.is_current_user_admin()):
                self.add_message(u'warning',
                                 "Only admin and owner can view this area: '{0:s}'!".format(area_name.decode('utf-8')))

            # Make a list of the cells that overlap the area with their path, row and status.
            # This may be an empty list for a new area.

            cell_list = []
            cell_list = area.cell_list()
            observations = {}

            if area.ft_docid is not None and len(area.ft_docid) <> 0:
                # print 'fusion table DocId', area.ft_docid
                area.isfusion = True
            else:
                # print 'no fusion table in area', area.ft_docid, area.boundary_fc
                area.isfusion = False

            area_followers_index = cache.get_area_followers(area_name)
            # print 'area_followers ', area_followers_index,
            if area_followers_index:
                area_followers = area_followers_index.users
            else:
                area_followers = []

            # print 'user ', user.name, user.role

            if (area.owner.string_id() == user.name):
                is_owner = True
                show_delete = True
            else:
                is_owner = False
                show_delete = False

            if users.is_current_user_admin():
                show_delete = True

            geojson_area = json.dumps(area.toGeoJSON())
            # print 'geojson_area: ', geojson_area
            self.render('view-area.html', {
                'username': user.name,
                'area_json': geojson_area,
                'area': area,
                # 'boundary_ft' : area.boundary_ft,
                'show_navbar': True,
                'show_delete': show_delete,
                'is_owner': is_owner,
                'is_new': False,
                'celllist': json.dumps(cell_list),  # to be replaced by jsonarea
                'area_followers': area_followers,
                'obslist': json.dumps(observations)
            })


'''
NewAreaHandler supports GET to show the new area form and POST to create a new area
'''
class NewAreaHandler(BaseHandler):

    # get - display New Area form
    def get(self):

        logging.info('get new area form')

        current_user = users.get_current_user()
        if not current_user:
            abs_url = urlparse(self.request.uri)
            original_url = abs_url.path
            logging.info('No user logged in. Redirecting from protected url: ' + original_url)
            self.add_message('danger', 'You must log in to create a new area .')
            return self.redirect(users.create_login_url(original_url))
        user, registered = self.process_credentials(current_user.nickname(), current_user.email(),
                                                    models.USER_SOURCE_GOOGLE, current_user.user_id())

        if not registered:
            return self.redirect(webapp2.uri_for('register'))

        try:
            username = self.session['user']['name']
        except:
            logging.error('Should never get this exception')
            self.add_message('danger', 'You must log in to create a new area.')

            if 'user' not in self.session:
                self.redirect(webapp2.uri_for('main'))
                return

        latlng = self.request.headers.get("X-Appengine-Citylatlong")  # user's location to center initial new map
        if latlng == None:
            logging.info('AreaHandler: No X-Appengine-Citylatlong in header')  # not unusual in debug mode.
            latlng = '8.2, 22.2'

        # send a blank area for templates
        default_area = {
            "description": "",
            "description_who": "",
            "description_how": "",
            "description_why": "",
            "threats": "",
            "wiki": ""
        }

        #test_area = cache.get_area(None, 'kali35').toGeoJSON()
        self.render('new-area.html', {
            # 'country': country,
            'area': default_area,
            #'area_json': test_area,
            'latlng': latlng,
            'username': username,
            'show_navbar': True,
            'show_delete': True,
            'is_owner': True,
            'wizard': True,  # area not created yet
            'is_new': True,  # area not created yet

        })

        # New Area form submitted.

    # @decorator.oauth_aware
    def post(self):
        '''
        POST to Create a new Area
        @param new_area_geojson_str - defines the new area as a geojson string.
               This may optionally contain a boundary_feature named 'boundary' - depending on the new area form design
        '''

        ### get logged in user
        try:
            username = self.session['user']['name']
            user = cache.get_user(username)
            if not user:
                raise KeyError

        except KeyError:
            # Redirect to login page.
            abs_url  = urlparse(self.request.uri)
            original_url = abs_url.path
            logging.info('No user logged in. Redirecting from protected url: ' + original_url)
            return self.redirect(users.create_login_url(original_url))


        ### read geojson dict of area properties
        try:
            new_area_geojson_str = self.request.body.decode('utf-8', 'replace')  # .decode('utf-8')
            logging.debug("AreaHandler() new_area_geojson_str: %s ", new_area_geojson_str)
            new_area = geojson.loads(new_area_geojson_str)
        except (ValueError, KeyError) as e:
            logging.error("AreaHandler() Exception : {0!s}".format(e))
            if isinstance(e, KeyError):
                self.response.set_status(400, message='No new_area_geojson_str parameter provided')
            elif isinstance(e, ValueError):
                logging.error("AreaHandler() Value Exception : {0!s} parsing new_area_geojson_str".format(e))
                self.response.set_status(400, message='Error parsing new_area data E1184')
            return self.response.out.write('Error reading new area data E1189')

        ### area_name
        logging.info("AreaHandler() request to create new area %s", new_area)
        try:
            area_name = new_area['properties']['area_name'].encode('utf-8')  # allow non-english area names.
        except KeyError, e:
            self.response.set_status(400)
            return self.response.out.write('Create area requires a name.')

        existing_area = cache.get_area(area_name)
        if existing_area:
            logging.error('Cannot POST to Area - name already exists')
            return self.error(404)
        ### check if too many areas created.
        areas_count = user.get_area_count()
        logging.debug('User has created %d area.', areas_count)
        if areas_count >= models.AreaOfInterest.MAX_AREAS:
            if (user.role != 'admin'):
                message = 'Sorry, you have created too many areas. Max Areas = {0!s}'.format(
                    models.AreaOfInterest.MAX_AREAS)
                logging.error(message)
                self.response.set_status(400)
                return self.response.out.write(message)
            else:
                self.add_message('warning', "Extra Areas permitted for admin ")
        elif areas_count >= models.AreaOfInterest.MAX_AREAS - 1:
            self.add_message('warning',
                             "You won't be able to create any more areas unless you first delete one of your existing areas")

        ### check EE service
        if not eeservice.initEarthEngineService():  # we need earth engine now.
            self.response.set_status(503)
            return self.response.out.write('Sorry, Google Earth Engine not available right now. Please try again later')

        ###pre-init variables to create area in case they don't appear in the geojson object
        maxlatlon = ndb.GeoPt(0, 0)
        minlatlon = ndb.GeoPt(0, 0)
        area_location = ndb.GeoPt(0, 0)
        boundary_hull = None
        boundary_geojsonstr = None # no boundary defined yet.
        boundary_type = new_area['properties']['boundary_type']
        boundary_feature = None  # client may optionally pass boundary on a Feature named 'boundary'
        total_area = 0
        coords = []
        ft_docid = None
        center_pt = []
        shared = 'private'

        ### Fusion Tables - @todo: This will move to a feature collection at some point
        if boundary_type == 'fusion':
            ft_docid = new_area['properties']['fusion_table']['ft_docid']
            logging.debug('AreaHandler name: %s has fusion boundary:%s', area_name, ft_docid)

            try:
                coords, total_area, maxlatlon, minlatlon, center, zoom = self.get_fusion_boundary(ft_docid)
            except:
                logging.error("Exception: {0!s} reading fusion table: {1!s}".format(e, ft_docid))
                self.add_message('danger', "Error reading fusion table: {0!s}".format(e))

                if isinstance(e, webapp2.HTTPException):
                    self.response.set_status(e.code)
                else:
                    self.response.set_status(404, message='')
            return self.response.out.write('Could not define boundary - error reading fusion table')
            self.add_message('warning', "Fusion Tables are still experimental - Please reports any bugs")

        for feature in new_area['features']:
            try:
                name = feature['properties']['name']
                coordinates = feature['geometry']['coordinates']
            except KeyError:
                errmsg = "A feature must have ['properties']['name'] and ['geometry']['coordinates']"
                logging.error(errmsg % feature)
                self.response.set_status(400, message=errmsg)
                return self.response.out.write(errmsg)

            ### get map view
            if name == "mapview":  # get the view settings to display the area.
                zoom = feature['properties']['zoom']
                center = ndb.GeoPt(float(coordinates[1]), float(coordinates[0]))

            ### get center point
            if name == "area_location":  # get the view settings to display the area.
                area_location = ndb.GeoPt(
                    float(coordinates[1]),
                    float(coordinates[0]))

            ### get drawn or geojson imported boundary
            if name == "boundary":
                boundary_feature = feature
                pass

        ### check area is not too small or too big.
        area_in_cells = total_area / LANSAT_CELL_AREA
        if total_area > (LANSAT_CELL_AREA * 6):  # limit area to an arbitrary maximum size where the system breaks down.
            self.add_message('danger',
                             'Sorry, your area is too big (%d sq km = %d Landsat images). Try a smaller area.' % (
                             total_area, area_in_cells))
            self.response.set_status(403, message='')
            return self.response.out.write('Area too big (%d sq km = %d Landsat images!)' % (total_area, area_in_cells))


        def txn(user_key, area):
            user = user_key.get()
            ndb.put_multi([user, area])
            return user, area

        one_month_ago = datetime.datetime.today() - datetime.timedelta(days=30) # starting point for GLAD Alerts

        try:
            area = models.AreaOfInterest(
                id=area_name, name=area_name,
                region=[],
                owner=self.session['user']['key'],
                description=new_area['properties']['area_description']['description'].decode('utf-8'),
                description_why=new_area['properties']['area_description']['description_why'].decode('utf-8'),
                description_who=new_area['properties']['area_description']['description_who'].decode('utf-8'),
                description_how=new_area['properties']['area_description']['description_how'].decode('utf-8'),
                threats=new_area['properties']['area_description']['threats'].decode('utf-8'),
                wiki=new_area['properties']['area_description']['wiki'].decode('utf-8'),
                ft_docid=ft_docid,
                area_location=area_location,
                boundary_hull=boundary_hull,
                boundary_geojsonstr=boundary_geojsonstr,
                map_center=center, map_zoom=zoom,
                max_latlon=maxlatlon, min_latlon=minlatlon,
                glad_monitored=False,
                last_glad_alerts_date=one_month_ago
            )
        except e:
            self.add_message('danger', 'Error creating area. %s' % (e))
            self.response.set_status(500, message='')
            return self.response.out.write('Error creating area. %s' % (e))

        ### set sharing for area
        try:
            shared = new_area['properties']['shared']
        except KeyError, e:
            logging.error('AreaHandler: No shared attribute provided for new area %s. Setting to private', area_name)
            shared = 'private'
        area.set_shared(shared)

        ### set boundary if one was provided.
        if boundary_feature != None:
            area.set_boundary_fc(eeFeatureCollection, False)
            area.region = find_regions(eeFeatureCollection)

        ### update the area and the referencing user
        try:
            user, area = ndb.transaction(lambda: txn(self.session['user']['key'], area), xg=True)
            models.Activity.create(user, models.ACTIVITY_NEW_AREA, area.key)
            self.add_message('success',
                             'Created your new area of interest: %s covering about %d sq.km' % (area.name, total_area))

            #cache.clear_area_cache(user.key, area.key)
            # clear_area_followers(area.key)
            #cache.set(cache.pack(user), cache.C_KEY, user.key)

            counters.increment(counters.COUNTER_AREAS)
        except Exception, e:
            # self.add_message('danger', "Error creating area.  Exception: {0!s}".format(e))
            self.response.set_status(500, message="Exception creating area... {0!s}".format(e))
            return self.response.out.write("Exception creating area... {0!s}".format(e))

        ### if auto-follow, add user as follower or area
        if new_area['properties']['self_monitor'] == True:
            # try:
            logging.debug('Requesting self-monitoring for %s' % (area.name))
            FollowAreaHandler.followArea(username, area.name, True)
            # except Exception, e:
            #    message = "Area created but exception in followArea() auto-following area Exception:{0!s}".format(e)
            #    self.response.set_status(500, message=message)
            #    logging.error(message)
            #    return self.response.out.write(message)
            #    raise e
        else:
            logging.info('Area creator did not request self-monitoring for %s' % (area.name))

        ### return the new area as a standard json object
        try:
            geojson_area = json.dumps(area.toGeoJSON())
            self.response.set_status(200)
            return self.response.out.write(geojson_area)
            ### success!!!

        except ValueError, e:
            message = "New Area produced exception in json ... {0!s}".format(e)
            self.response.set_status(500, message)
            logging.error(message)
            return self.response.out.write(message)


class DeleteAreaHandler(BaseHandler):
    def get(self, area_name):
        current_user = users.get_current_user()
        if not current_user:
            abs_url = urlparse(self.request.uri)
            original_url = abs_url.path
            logging.info('No user logged in. Redirecting from protected url: ' + original_url)
            self.add_message('danger', 'You must log in to delete an area .')
            return self.redirect(users.create_login_url(original_url))
        user, registered = self.process_credentials(current_user.nickname(), current_user.email(),
                                                    models.USER_SOURCE_GOOGLE, current_user.user_id())

        if not registered:
            return self.redirect(webapp2.uri_for('register'))
        try:
            username = self.session['user']['name']
        except:
            logging.error('Should never get this exception')
            self.add_message('danger', 'You must log in to delete an area.')

            if 'user' not in self.session:
                self.redirect(webapp2.uri_for('main'))
                return

        cell_list = []

        area = cache.get_area(area_name)

        if not area:
            #self.add_message('danger', 'Delete Area failed - Area not found.')
            #logging.error('DeleteArea: Area not found! %s', area_name)  # XSS should not return area to client.
            results = {
                "status": "error",
                "updates":  "Area not found"
            }
            return self.error(404)
        cell_list = area.cell_list()
        observations = {}
        if area.ft_docid is not None and len(area.ft_docid) != 0:
            area.isfusion = True
        else:
            area.isfusion = False

        file_id = area.folder_id # delete the folder for this glad area.

        area_followers = models.AreaFollowersIndex.get_by_id(area.name.encode('utf-8'), parent=area.key)
        # if user does not own area or user is not admin - disallow

        if (area.owner.string_id() != user.name) and  (not users.is_current_user_admin()):
            msg = 'Only the owner of an area or admin can delete an area %s %s' %(area.owner, user.role)
            logging.error(msg)

            #self.add_message('danger',
            #                 "Only the owner of an area or admin can delete an area. owner:'{0!s}' user:'{1!s}'".format(
            #                     area.owner, user))

            results = {
                "status": "error",
                "updates": msg
            }
            self.response.set_status(403)
            return self.response.out.write(json.dumps(results))

        # remove area from other user's area_following lists.
        area_followers_index = cache.get_area_followers(area_name)

        # print 'area_followers_index ', area_followers_index

        def txn(user_key, area, area_followers_index):
            user = user_key.get()
            user.put()
            for cell_key in area.cells:
                cell_key.delete()
            if area_followers_index is not None:
                area_followers_index.key.delete()
            area.key.delete()

            return

        owner_key = area.owner
        logging.debug('owner_key: %s', owner_key)

        try:
            # ndb.run_in_transaction_options(xg_on, txn, owner_key, area, area_followers_index)
            ndb.transaction(lambda: txn(owner_key, area, area_followers_index), xg=True)

            #cache.clear_area_cache(user.key, area.key)
            #cache.clear_area_followers(area.key)
            #cache.set(cache.pack(user), cache.C_KEY, user.key)

            models.Activity.create(user, models.ACTIVITY_DELETE_AREA, area.key)
            counters.increment(counters.COUNTER_AREAS, -1)

            msg = 'Deleted area of interest: {0!s}'.format(area_name)
            if file_id:
                delete_result = apiservices.delete_file(file_id)
                if delete_result != None:
                    msg += " But could not delete folder for %s" %area_name
                    logging.error(msg)

            results = {
                "status": "ok",
                "updates": msg
            }
            self.response.set_status(200)
            return self.response.out.write(json.dumps(results))

        except Exception as e:
            msg= 'Sorry, Could not delete area: Exception {0!s}'.format(e)  # XSS safe
            results = {
            "status": "error",
            "updates": msg
            }
            self.response.set_status(500)
            return self.response.out.write(json.dumps(results))


'''
SelectCellHandler is called by Ajax when a user clicks on a Landsat Cell in the browser.
This toggles the 'monitored' flag in the cell object in the datastore and flushes the cell and area cache.
TODO: Add the latest observation date (if known) to the return.
'''


class SelectCellHandler(BaseHandler):
    def get(self, area_name, celldata):
        # get cell info in request.
        self.populate_user_session()
        cell_feature = json.loads(celldata)
        # print 'cell_feature ', cell_feature
        path = cell_feature['properties']['path']
        row = cell_feature['properties']['row']
        displayAjaxResponse = 'Cell {0:d} {1:d}'.format(path, row)

        area = cache.get_area(area_name)
        username = self.session['user']['name']

        if not area or area.owner.string_id() != username:
            logging.info('selectCell() not area owner')
            response = {'error': 'Only area owner can select cell for monitoring'}
            return self.response.write(json.dumps(response))

        # build cell info in response.
        cell = cache.get_cell(path, row, area_name)
        # print "cell", cell
        if cell is not None:
            # Update the followed flag.
            if cell.monitored == True:
                cell.monitored = False
            else:
                cell.monitored = True
            cell.put()
            cell_dict = cell.Cell2Dictionary()
            cache.delete([cache.C_CELL_KEY % cell.key,
                          cache.C_CELL % (path, row, area_name),
                          cache.C_CELLS % (cell.aoi)])
            cell_dict['monitoredCount'] = area.count_monitored_cells()
            self.response.write(json.dumps(cell_dict))
        else:
            logging.error('Selected Cell does not exist %d %d', path, row)
            self.response.write({'danger': 'Not a cell'})
        return

    def post(self):
        # print 'SelectCellHandler post'
        name = self.request.get('name')
        descr = self.request.get('description')
        # logging.debug('SelectCellHandler name: %s description:%s', name, descr)

        try:
            coordinate_geojson_str = self.request.get('coordinates').decode('utf-8')
            # logging.debug("SelectCellHandler() coordinate_geojson_str: ", coordinate_geojson_str)
            geojsonBoundary = geojson.loads(coordinate_geojson_str)

        except:
            return self.render('view-area.html', {
                'username': name
            })

        self.render('view-area.html')


class NewJournal(BaseHandler):
    def get(self):
        self.render('new-journal.html')

    def post(self):
        name = self.request.get('name')

        if len(self.session['journals']) >= models.Journal.MAX_JOURNALS:
            self.add_message('danger', 'Only %i journals allowed.' % models.Journal.MAX_JOURNALS)
        elif not name:
            self.add_message('danger', 'Your journal needs a name.')
        else:
            journal = models.Journal(id=name, parent=self.session['user']['key'])  # FIXME not XS safe.
            for journal_url, journal_name, journal_type in self.session['journals']:
                if journal.key.string_id() == journal_name:
                    self.add_message('danger', 'You already have a journal called %s.' % name)
                    break
            else:
                def txn(user_key, journal):
                    user = user_key.get()
                    user.journal_count += 1
                    ndb.put_multi([user, journal])
                    return user, journal

                journal.journal_type = "journal"
                user, journal = ndb.transaction(lambda: txn(self.session['user']['key'], journal))
                if journal == None:
                    self.add_message('danger', 'Error storing journal.')
                    logging.error("Error storing journal")

                cache.clear_journal_cache(user.key)
                cache.set(cache.pack(user), cache.C_KEY, user.key)
                self.populate_user_session()
                counters.increment(counters.COUNTER_AREAS)
                models.Activity.create(user, models.ACTIVITY_NEW_JOURNAL, journal.key)
                self.add_message('success', 'Created your journal %s.' % name)
                self.redirect(webapp2.uri_for('new-entry', username=self.session['user']['name'], journal=journal,
                                              journal_name=journal.key.string_id()))
                return

        self.render('new-journal.html')


'''
Use Earth Engine to work out which cells overlap an AreaOfInterest.
Store the result in aoi.cells.
Each cell identified by landsat Path and Row.
Also checks if area is in glad footprint and stores result.
'''
class GetLandsatCellsHandler(BaseHandler):
    # This handler responds to Ajax request, hence it returns a response.write()

    def get(self, area_name):
        area = cache.get_area(area_name)
        if not area or area is None:
            getCellsResult = {'result': 'error', 'reason': 'no area'}
            logging.info('GetLandsatCellsHandler - area %s not found', area_name)
            return self.error(404)

        cell_list = area.cell_list()
        result = 'success'
        if len(cell_list) == 0:

            # logging.debug('GetLandsatCellsHandler area.name: %s type: %d area.key: %s', area.name, type(area), area.key)
            if not eeservice.initEarthEngineService():  # we need earth engine now.
                result = 'danger'
                reason = 'Sorry, Cannot contact Google Earth Engine right now to create visualization. Please come back later'
                self.add_message('danger', reason)
                logging.error(reason)
                getCellsResult = {'result': result, 'reason': reason}
                return self.response.write(json.dumps(getCellsResult))

            else:
                eeservice.getLandsatCells(area)
                cell_list = area.cell_list()
                monitored_count = sum(c['monitored'] == 'true' for c in cell_list)
                reason = 'Your area is covered by {0:d} Landsat Cells of which {1:d} were selected for monitoring\n'.format(
                    len(area.cells), monitored_count)
                if area.glad_monitored & area.hasBoundary():
                    reason += 'GLAD alerts Enabled. '
                    reason += gladalerts.handleCheckForGladAlertsInArea(self, area);

                else:
                    reason += 'GLAD alerts Not available'
                self.add_message('success', reason)
                logging.debug(reason)
        else:
            reason = 'calculate previously'
        getCellsResult = {'result': result, 'reason': reason, 'cell_list': cell_list,
                          'monitored_count': monitored_count}
        self.response.write(json.dumps(getCellsResult))
        return

class LandsatOverlayRequestHandler(BaseHandler):  # 'new-landsat-overlay'
    # This handler responds to Ajax request, hence it returns a response.write()

    def get(self, area_name, action, satelite, algorithm, latest, **opt_params):
        area = cache.get_area(area_name)
        returnval = {}

        if not area:
            returnval['result'] = "error"
            returnval['reason'] = 'LandsatOverlayRequestHandler: Invalid area ' + area_name
            self.add_message('danger', returnval['reason'])
            logging.error(returnval['reason'])
            self.response.write(json.dumps(returnval))
            return

        if not self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            logging.info('LandsatOverlayRequestHandler(): Ajax request expected ')

        logging.debug("LandsatOverlayRequestHandler area:%s, action:%s, satellite:%s, algorithm:%s, latest:%s",
                      area_name, action, satelite, algorithm, latest)  # , opt_params['path'], opt_params['row'])
        if not area:
            logging.info('LandsatOverlayRequestHandler - bad area returned %s, %s', area, area_name)
            self.error(404)
            return

        if not eeservice.initEarthEngineService():  # we need earth engine now.
            returnval['result'] = "error"
            returnval['reason'] = 'Cannot contact  Earth Engine. Try again later'
            self.add_message('danger', returnval['reason'])
            logging.error(returnval['reason'])
            self.response.write(json.dumps(returnval))
            return

        if area.get_boundary_hull_fc() == None:
            returnval['result'] = "error"
            returnval['reason'] = 'Sorry, cannot create overlay. Area %s does not have a valid location or boundary' % (
            area.name)
            self.add_message('danger', returnval['reason'])
            logging.error(returnval['reason'])
            self.response.write(json.dumps(returnval))
            return

        map_id = eeservice.getLandsatOverlay(area.get_boundary_hull_fc(), satelite, algorithm, latest, opt_params)
        if not map_id:
            returnval['result'] = "error"
            returnval['reason'] = 'Earth Engine did not provide a map_id. Try again later'
            self.add_message('danger', returnval['reason'])
            logging.error(returnval['reason'])
            self.response.write(json.dumps(returnval))
            return

        # Save observation - will it work if no path or row?
        if 'path' in opt_params and 'row' in opt_params:
            path = int(opt_params['path'])
            row = int(opt_params['row'])

            # logging.debug("LandsatOverlayRequestHandler() path %s, row %s", path, row)
            cell = cache.get_cell(path, row, area_name)
            if cell is not None:
                # captured_date = datetime.datetime.strptime(map_id['date_acquired'], "%Y-%m-%d")
                obs = models.GladClusterCollection(parent=area.key,
                                                   image_collection=map_id['collection'],
                                                   captured=map_id['capture_datetime'],
                                                   image_id=map_id['id'])
            else:
                returnval['result'] = "error"
                returnval['reason'] = 'LandsatOverlayRequestHandler - cache.get_cell error'
                self.add_message('danger', returnval['reason'])
                logging.error(returnval['reason'])
                self.response.set_status(500)
                self.response.write(json.dumps(returnval))

        else:
            # TODO: Do we really want some Observation with the parent being aoi instead of cell?
            obs = models.GladClusterCollection(parent=area.key, image_collection=map_id['collection'],
                                               captured=map_id['capture_datetime'], image_id=map_id['id'], obs_role='ad-hoc')
        obs.put()
        ovl = models.Overlay(parent=obs.key,
                             map_id=map_id['mapid'],
                             token=map_id['token'],
                             overlay_role='special',
                             image_collection=map_id['collection'],
                             algorithm=algorithm)

        ovl.put()  # Do first to create a key.
        obs.overlays.append(ovl.key)
        obs.put()  # TODO put inside a tx
        cache.set_keys([obs, ovl])

        # logging.info("map_id %s", map_id) logging.info("tile_path %s",area.tile_path)
        returnval = ovl.Overlay2Dictionary()
        returnval['result'] = "success"
        returnval['reason'] = "LandsatOverlayRequestHandler() created " + ovl.overlay_role + " " + ovl.algorithm + " overlay."
        logging.debug(returnval['reason'])
        # self.populate_user_session() - no user in Ajax call.
        self.response.write(json.dumps(returnval))




class ImageOverlayHandler(BaseHandler):
    """
    Handlers for fetching or updating image overlays from an LANDSAT image_id
    """
    def get(self, image_id, algorithm, role, **opt_params):
        """
        Find and return an overlay. If not found, create it.
        @returns a dictionary that contains
        - the result code, 'error' or 'success'
        - the result message
        - if success, the overlay as a dictionary see models.Overlay.Overlay2Dictionary()

        This handler responds to Ajax request, hence it returns a response.write()
        """

        ovl = models.Overlay.find_overlay(image_id, algorithm, role, opt_params)
        if not ovl:
            ovl = models.Overlay.create(image_id, algorithm, role, opt_params)
        return ovl

    def update(self, image_id, algorithm, role):
        'regenrerate the mapid and token for an existing overlay whose asset has expired'
        returnval = {}

        ovl = models.Overlay.find_overlay(image_id, algorithm, role, opt_params)
        if not ovl:
            returnval['result'] = "error"
            returnval['reason'] = "ImageOverlayHandler - Could not find ImageOverlay"
        else:
            returnval['overlay'] = ovl.update(opt_params)
        if returnval['result'] != 'success':
            logging.error(returnval['reason'])
        return self.response.write(json.dumps(returnval))


class CreateOverlayHandler(BaseHandler):
    """
    This handler responds to Ajax request, hence it returns a response.write()
    CreateOverlayHandler() create a new overlay and appends it to the observation
        @param observation key:
        @param role:
        @param algorithm:
    """

    def get(self, obskey_encoded, role, algorithm):
        obs = models.GladClusterCollection.get_from_encoded_key(obskey_encoded)

        returnval = {}

        if not obs:
            # print 'CreateOverlayHandler ', obskey, 'obs', obs
            returnval['result'] = "error"
            returnval['reason'] = "CreateOverlayHandler() -  no Observation entity found with id:[%d]" % long(obs_id)
            logging.error(returnval['reason'])
            return self.response.write(json.dumps(returnval))

        logging.debug("CreateOverlayHandler() Creating %s %s visualization of image %s from collection :%s", role,
                      algorithm, obs.image_id, obs.image_collection)

        eeservice.initEarthEngineService()  # we need earth engine now.
        if not eeservice.initEarthEngineService():  # we need earth engine now. logging.info(initstr)
            returnval['result'] = "error"
            returnval['reason'] = "CreateOverlayHandler() - Cannot contact Google Earth Engine to generate overlay"
            logging.error(returnval['reason'])
            return self.response.write(json.dumps(returnval))

        if role == 'latest':
            map_id = eeservice.getLandsatImageById(obs.image_collection, obs.image_id, algorithm)
        elif role == 'special':
            map_id = eeservice.getLandsatImageById(obs.image_collection, obs.image_id, algorithm)
        elif role == 'prior':
            map_id = eeservice.getPriorLandsatOverlay(obs)
        else:
            returnval['result'] = "error"
            returnval['reason'] = "CreateOverlayHandler() - Unknown role " + role + " (use 'latest' or 'prior'). "
            logging.error(returnval['reason'])
            return self.response.write(json.dumps(returnval))

        if not map_id:
            returnval['result'] = "error"
            returnval['reason'] = "CreateOverlayHandler() Earth Engine did not return Overlay"
            logging.error(returnval['reason'])
            # self.populate_user_session()
            self.response.write(json.dumps(returnval))
            return

        # captured_date = datetime.datetime.strptime(map_id['date_acquired'], "%Y-%m-%d")
        ovl = models.Overlay(parent=obs.key,
                             map_id=map_id['mapid'],
                             token=map_id['token'],
                             overlay_role=role,  # is it safe to assume?
                             algorithm=algorithm)

        # obs.captured = map_id['capture_datetime'] #we already  had this?

        ovl.put()  # Do first to create a key.
        obs.overlays.append(ovl.key)
        obs.put()  # TODO put inside a tx
        cache.set_keys([obs, ovl])  # Does this work?

        returnval['overlay'] = ovl.Overlay2Dictionary()
        returnval['result'] = "success"
        returnval['reason'] = "CreateOverlayHandler() added " + role + " " + algorithm + " overlay"
        logging.debug(returnval['reason'])
        self.response.write(json.dumps(returnval))

        # self.populate_user_session()


# if Image is known.
class UpdateOverlayAjaxHandler(BaseHandler):
    # This handler responds to Ajax request, hence it returns a response.write()

    def get(self, ovlkey, algorithm):

        ovl = models.Overlay.get_from_encoded_key(ovlkey)
        returnval = {}

        if not ovl:
            returnval['result'] = "error"
            returnval['reason'] = "UpdateOverlayHandler Could not find Image"
            logging.error(returnval['reason'])
            return self.response.write(json.dumps(returnval))

        obs = ovl.key.parent().get()

        if not obs:
            returnval['result'] = "error"
            returnval['reason'] = "UpdateOverlayHandler() - overlay has no parent observation"
            logging.error(returnval['reason'])
            return self.response.write(json.dumps(returnval))

        logging.debug("UpdateOverlayHandler() visualization of image %s from collection :%s", obs.image_id,
                      obs.image_collection)

        eeservice.initEarthEngineService()  # we need earth engine now.
        if not eeservice.initEarthEngineService():  # we need earth engine now. logging.info(initstr)
            returnval['result'] = "error"
            returnval['reason'] = "UpdateOverlayHandler() - Cannot contact Google Earth Engine to update overlay"
            logging.error(returnval['reason'])
            return self.response.write(json.dumps(returnval))

        ovl.algorithm = algorithm  # shouldn't change?

        if ovl.overlay_role == 'latest':
            map_id = eeservice.getLandsatImageById(obs.image_collection, obs.image_id, ovl.algorithm)
        elif ovl.overlay_role == 'special':
            map_id = eeservice.getLandsatImageById(obs.image_collection, obs.image_id, algorithm)
        elif ovl.overlay_role == 'prior':
            map_id = eeservice.getPriorLandsatOverlay(obs)
        else:
            returnval['result'] = "error"
            returnval['reason'] = "UpdateOverlayHandler() - Unknown role " + ovl.overlay_role + "(use 'latest' or 'prior')."
            logging.error(returnval['reason'])
            return self.response.write(json.dumps(returnval))

        if not map_id:
            returnval['result'] = "error"
            returnval['reason'] = "UpdateOverlayHandler Could not find Image"
            logging.error(returnval['reason'])
            # self.populate_user_session()
            self.response.write(json.dumps(returnval))
            return

        ovl.map_id = map_id['mapid']
        ovl.token = map_id['token']

        ovl.put()
        cache.set_keys([ovl])

        returnval['overlay'] = ovl.Overlay2Dictionary()
        returnval['result'] = "success"
        returnval['reason'] = "UpdateOverlayHandler() updated " + ovl.overlay_role + " " + ovl.algorithm + " overlay"
        logging.debug(returnval['reason'])

        self.populate_user_session()
        self.response.write(json.dumps(returnval))


'''
    Legacy: Old_ObservationTaskHandler() when a user clicks on a link in an obstask email they come here to see the new image.
'''
class Old_ObservationTaskAjaxHandler(BaseHandler):
    def get(self, task_id):

        obstask = models.Old_ObservationTask.get_by_id(long(task_id))
        if obstask is None:
            self.add_message('danger', "Task not found. Old_ObservationTaskAjaxHandler")
            resultstr = "Task not found. Old_ObservationTaskAjaxHandler: key {0!s}".format(task_id)
            logging.error(resultstr)
            return self.response.write(resultstr)

        username = None
        current_user = users.get_current_user()
        if not current_user:
            # abs_url  = urlparse(self.request.uri)
            # original_url = abs_url.path
            # logging.info('No user logged in. Cannot access protected url' + original_url)
            # return self.redirect(users.create_login_url(original_url))
            show_nav = True
            is_owner = False  # not area owner
            user = None
        else:
            user, registered = self.process_credentials(current_user.nickname(), current_user.email(),
                                                        models.USER_SOURCE_GOOGLE, current_user.user_id())
            username = self.session['user']['name']
            show_nav = True
            if current_user.nickname != obstask.assigned_owner:
                self.add_message('info', "You {0!s} are not assigned to this task. Task assigned to {1!s}".format(
                    current_user.nickname, obstask.assigned_owner.string_id()))
            self.populate_user_session(user)
        task_owner = obstask.assigned_owner.string_id()

        area = obstask.aoi.get()
        if area is None:
            self.add_message('danger', "Old_ObservationTaskAjaxHandler: Task for deleted area. ")
            resultstr = "Task's area not found. Old_ObservationTaskAjaxHandler: key {0!s}".format(task_id)
            logging.error(resultstr)
            return self.response.write(resultstr)

        area_name = area.name.encode('utf-8')
        cell_list = area.cell_list()
        geojson_area = json.dumps(area.toGeoJSON())

        resultstr = "New Task for {0!s} to check area {1!s}".format(task_owner, area_name)

        # debugstr = resultstr + " task: " + str(task_id) + " has " + str(len(obstask.observations)) + "observations"
        obslist = []
        for obs_key in obstask.observations:
            obs = obs_key.get()  # cache.get_by_key(obs_key) messy double cache
            if obs is not None:
                obslist.append(obs.Observation2Dictionary())  # includes a list of precomputed overlays
            else:
                logging.error("Missing Observation from cache")

        if user and area.owner.string_id() == user.name:
            is_owner = True
        else:
            is_owner = False

        return self.render('view-obstask.html', {
            'username': username,
            'area_json': geojson_area,
            'area': area,
            'task': obstask,
            'owner': task_owner,
            'is_owner': is_owner,  # area owner
            'show_delete': False,
            'show_navbar': show_nav,
            # 'area_followers': area_followers,
            'obslist': json.dumps(obslist),
            'celllist': json.dumps(cell_list)
        })


<<<<<<< HEAD
class ObservationTaskHandler(BaseHandler):
    def get(self, router_name='SIMPLE'):

        try:
            username = self.session['user']['name']
            user = cache.get_user(username)
            if not user:
                raise KeyError
                # TODO: use proper page redirects and redirect to login page.

        except KeyError:
            return self.response.write('You must be logged in!')

        router = None
        if router_name == 'DUMMY':
            router = DummyRouter()
        elif router_name == 'SIMPLE':
            router = SimpleRouter()
        else:
            result_str = "Specified router not found"
            logging.error(result_str)
            self.response.set_status(404)
            return self.response.write(result_str)

        result = router.get_next_observation_task(user)
        if result is None:
            self.response.set_status(404)
            return self.response.write("No uncompleted tasks available")

        return self.response.write(result.to_JSON())
        self.response.set_status(200)

    def post(self):
        """
            Accepts an observation task response
            
            Example request body
            {
                "vote_category": "FIRE",
                "case_id": 4573418615734272
            }
        :return:
        """
        try:
            username = self.session['user']['name']
            user = cache.get_user(username)
            if not user:
                raise KeyError

        except KeyError:
            self.response.set_status(401)
            return

        observation_task_response = json.loads(self.request.body)
        # TODO: use a json encoder and us a Decoding Error for the validation
        if observation_task_response['vote_category'] is not None:
            if observation_task_response['case_id'] is not None:
                # TODO: consider moving this check down into a JSON decoding function or BLL module
                if observation_task_response['vote_category'] in models.VOTE_CATEGORIES:
                    case = models.Case.get_by_id(id=observation_task_response['case_id'])
                    if case is None:
                        # TODO: consider moving this check down into a BLL module
                        self.response.set_status(404)
                        return

                    # Check if user has already completed task
                    if models.ObservationTaskResponse \
                        .query(models.ObservationTaskResponse.user == user.key,
                               models.ObservationTaskResponse.case == case.key).fetch():
                        self.response.set_status(400)
                        return

                    observation_task_entity = models.ObservationTaskResponse(user=user.key,
                                                                             case=case.key,
                                                                             vote_category=
                                                                             observation_task_response['vote_category'],
                                                                             case_response=
                                                                             observation_task_response,
                                                                             task_duration_seconds=
                                                                             observation_task_response['task_duration_seconds'])
                    observation_task_entity.put()

                    vote_calculator = SimpleVoteCalculator()
                    case.votes.add_vote(observation_task_response['vote_category'],
                                        vote_calculator.get_weighted_vote(
                                            user, case, observation_task_response['task_duration_seconds']))
                    case.put()

                    case_manager = case_workflow.case_workflow_manager.CaseWorkflowManager()
                    case_manager.update_case_status(case)

                    self.response.set_status(201)

                    return

        self.reponse.set_status(400)
        return

def checkForNewInArea(area):
    """
    checkForNewInArea() is a function to check if any new images for the specified area.
    Called by CheckForNewInAllAreasHandler() and CheckForNewInAreaHandler()
    returns a HTML formatted string

    This is not a handler and can be moved to another file
    """

    area_followers = models.AreaFollowersIndex.get_by_id(area.name, parent=area.key)
    linestr = u'<h2>Area:<b>{0!s}</b></h2>'.format(area.name)
    obstask_cachekeys = []

    if area_followers:
        monitored_cells = 0
        linestr += u'<p>Monitored cells ['
        new_observations = []
        for cell_key in area.cells:  # TODO Could use cache.get_cells(area_key)
            cell = cell_key.get()
            if cell is not None:
                if cell.monitored:
                    monitored_cells += 1
                    linestr += u'({0!s}, {1!s}) '.format(cell.path, cell.row)
                    obs = eeservice.checkForNewObservationInCell(area, cell, "LANDSAT/LC8_L1T_TOA")
                    if obs is not None:
                        linestr += 'New '
                        new_observations.append(obs.key)
            else:
                logging.error(
                    u"CheckForNewInAreaHandler() in area:{0!s} no cell returned from key:{1!s} ".format(area.name,
                                                                                                        cell_key))
        if monitored_cells == 0:
            linestr += u'] Monitoring disabled for Area. Edit area cells to monitor</p>'
        else:
            linestr += u']</p>'

        # send each follower of this area an email with reference to a task.
        if new_observations:
            linestr += models.Old_ObservationTask.createObsTask(area, new_observations, "LANDSATIMAGE", area_followers.users)
        else:
            linestr += u"<ul><li>No new observations found.</li></ul>"
    else:
        linestr += u'Area has no followers. Skipping check for new observations.<br>'.format(area.name)

    logging.debug(linestr)
    return linestr


'''
CheckForNewInAllAreasHandler() looks at each subscribed area of interest.
It checks each monitored cell to see if there is a new image in EE since the last check.
This is called by the cron task, but may be kicked of by admin.
Not: Includes private and unlisted areas in the check. So the tasks lists must be filtered.
'''
class CheckForNewInAllAreasHandler(BaseHandler):
    def get(self):
        logging.info("Cron CheckForNewInAllAreasHandler check-new-images")
        initstr = u"<h1>Check areas for new observations</h1>"
        initstr += u"<p>The scheduled task is looking for new images over all areas of interest</p>"
        initstr += u"<p>The area must have at least one cell selected for monitoring and at least one follower for a observation task to be created.</p>"
        initstr += u"<p>If an observation task is created, the first follower of the area receives an email with an observation task.</p>"

        if not eeservice.initEarthEngineService():  # we need earth engine now. logging.info(initstr)
            initstr = u'CheckForNewInAllAreasHandler: Cannot contact Google Earth Engine right now to create your area. Please come back later'
            self.response.set_status(503)
            return self.response.write(initstr)

        returnstr = initstr

        all_areas = cache.get_all_areas()  # includes unlisted and private areas.
        # hostname = utils.get_custom_hostname()
        for area in all_areas:
            returnstr += checkForNewInArea(area)

        self.response.write(returnstr.encode('utf-8'))


'''
CheckForNewInAreaHandler() looks at a single area of interest and checks each monitored cell.
It checks if there is a new image in EE since the last check.
This function is called by admin only.
#TODO: It could be refactored with CheckAllAreasHadler.
'''
class CheckForNewInAreaHandler(BaseHandler):
    def get(self, area_name):

        area = cache.get_area(area_name)
        if not area:
            area = cache.get_area(area_name)
            logging.error('CheckForNewInAreaHandler: Area not found!')
            return self.error(404)
        else:
            logging.debug('CheckForNewInAreaHandler   check-new-area-images for area_name %s', area_name)

        initstr = u"<h1>Check area for new observations</h1>"
        initstr += u"<p>The area must have at least one cell selected for monitoring and at least one follower for a observation task to be created.</p>"
        initstr += u"<p>If an observation task is created, the first follower of the area receives an email with an observation task.</p>"

        if not eeservice.initEarthEngineService():  # we need earth engine now. logging.info(initstr)
            initstr = u'CheckForNewInAreaHandler: Sorry, Cannot contact Google Earth Engine now. Please try again later'
            # self.add_message('danger', initstr)
            self.response.set_status(500)
            return self.response.write(initstr)


        returnstr = initstr + checkForNewInArea(area)  # self.request.headers.get('host', 'no host'))
        return self.response.write(returnstr.encode('utf-8'))


class CheckForGladAlertsInAllAreasHandler(BaseHandler):
    """
    CheckForGladAlertsInAllAreasHandler() looks at a single area of interest and gets GLAD-ALERTS
    Takes no argmuments.
    @param noupdate: if set, then the last_alert_date in the area is not updated to todays date
    Expected to be called by a job in cron.yaml
    """

    def get(self, noupdate=None):
        returnstr = '<h1>CheckForGladAlertsInAllAreasHandler</h1>'

        all_areas = cache.get_all_glad_areas()  # includes unlisted and private areas in GLAD footprint.

        for area in all_areas:
            if area.glad_monitored & area.hasBoundary():
                returnstr += '<h2>' + area.name + ' </h3><br/>' + gladalerts.handleCheckForGladAlertsInArea(self, area, noupdate) + '<br/>'
        #cache.flush()
        self.response.write(returnstr.encode('utf-8'))

class CheckForGladAlertsInAreaHandler(BaseHandler):

    def get(self, area_name, noupdate=None):
        '''
        CheckForGladAlertsInAreaHandler() looks at a single area of interest and gets GLAD-ALERTS
        '''
        area = cache.get_area(area_name)
        if not area:
            area = cache.get_area(area_name)
            logging.error('CheckFoArGladAlertsInAreaHandler: Area not found!')
            return self.error(400)
        else:
            logging.debug('CheckForGladAlertsInAreaHandler: check-new-area-images for area_name %s', area_name)

            response = gladalerts.handleCheckForGladAlertsInArea(self, area, noupdate)
            self.response.write(response)
            return

'''
ProcessAlerts2ClustersHandler() looks at a single area of interest and gets GLAD-ALERTS
'''
class ProcessAlerts2ClustersHandler(BaseHandler):

    def get(self, area_name):
        # for a in areas
        return gladalerts.handleAlerts2Clusters(self, area_name)

'''
DistributeGladClusters() takes a GLAD-ALERT cluster and sends it to volunteers as tasks
'''
class DistributeGladClusters(BaseHandler):

    def get(self, area_name):
        # for a in areas
        return gladalerts.distributeGladClusters(self, area_name)


'''
DistributeGladClusters() takes a GLAD-ALERT cluster and sends it to volunteers as tasks
'''
class RunAreaTest(BaseHandler):

    def get(self, test_name, area_name):
        # for a in areas
        area = cache.get_area(area_name)
        if not area:
            area = cache.get_area(area_name)
            logging.error('RunAreaTest: Area not found!')
            return self.error(404)
        else:
            logging.debug('Run Test %s: area_name %s', test_name, area_name)
        if test_name == 'test1':
            logging.debug('Test1: area_name %s', area_name)
            return

'''
MailTestHandler() - This handler sends a test email
'''
class MailTestHandler(BaseHandler):
    def get(self):
        #     username = []
        #     if 'user' in self.session:
        #         areas = cache.get_areas(ndb.Key(self.session['user']['key'])) # areas user created
        #         self.populate_user_session() #Only need to do this when areas, journals  or followers change
        #         username = "myemail@gmail.com"
        #
        #     else:
        #         username = "myotheremail@gmail.com"

        user = cache.get_user(self.session['user']['name'])
        tasks = models.Old_ObservationTask.query().order(-models.Old_ObservationTask.created_date).fetch(2)
        # mailer.new_image_email(user)
        if not tasks:
            return self.handle_error("No tasks to test mailer")
        resultstr = mailer.new_image_email(tasks[0], self.request.headers.get('host', 'no host'))

        self.response.write(resultstr)


class ViewJournal(BaseHandler):
    # FIXME: Pagination for view-journals does not work.
    def get(self, username, journal_name):
        page = int(self.request.get('page', 1))
        journal = models.Journal.get_journal(username, journal_name.decode('utf-8'))
        if 'user' not in self.session or username != self.session['user']['name']:
            self.error(403)
            return

        if not journal:
            logging.error('ViewJournal() cannot find journal %s', journal_name)
            self.error(404)
        else:
            dict = {
                'username': username,
                'journal': journal,
                'entries': cache.get_entries_page(username, journal_name, page, journal.key),
                'page': page,
                'show_navbar': True,
                'pagelist': utils.page_list(page, journal.pages),
            }
            logging.debug('ViewJournal journal_name %s %s', journal_name, journal)
            logging.debug(dict)
            self.render('view-journal.html', dict)


''' ViewObservationTasksHandler() displays a rendered list of ObservationTasks for a user, or an area or all. Most recent on top.
'''


class ViewObservationTasksHandler(BaseHandler):
    def ViewTasks(self):
        page = int(self.request.get('page', 1))
        u = self.request.get('user2view')
        a = self.request.get('area_name')
        user2view = None if u == "" or u == "None" else u
        area_name = None if a == "" or a == "None" else a

        # get the logged in user.
        current_user = users.get_current_user()
        # print 'current_user: ', current_user
        if not current_user:
            abs_url = urlparse(self.request.uri)
            original_url = abs_url.path
            logging.debug('No user logged in. Showing in anon mode : ' + original_url)
            user = None
            show_nav = False
        else:
            user = cache.get_user(self.session['user']['name'])  # user from current session
            show_nav = True

        if area_name:
            area = cache.get_area(area_name)
            if area:
                # if user does not own area or user is not admin - disallow
                if (area.shared_str == 'private') and (area.owner.string_id() != user.name) and (user.role != 'admin'):
                    message = "Cannot show tasks for non-public area: '{0!s}', except to owner: '{1!s}'.".format(
                        area_name, area.owner)
                    logging.error(message)
                    return self.response.write(message)
            else:
                logging.error('Requested area {0!s} not found '.format(area_name))
                return self.response.write('Requested area not found')  # Don't print area to avoid XSS attack.

        tasks = cache.get_obstasks_keys(user2view, area_name)  # list of all task keys
        obstasks = cache.get_obstasks_page(page, user2view, area_name)  # rendered page of tasks #TODO is it needed?

        if obstasks == None or len(obstasks) == 0:
            logging.info('ViewObservationTasksHandler - no tasks!')
            obstask = None
            obstasks = None
            pages = 0
            tasks = None
        else:
            logging.debug('ViewObservationTasks: user:%s, area:%s, page:%d', user2view, area_name,
                          page)  # Move here to XSS sanitise user2view
            pages = len(tasks) / models.Old_ObservationTask.OBSTASKS_PER_PAGE
            if pages < 1:
                pages = 1

            if page < 1 or page > pages:
                self.error(404)
                return

            obstask = cache.get_task(tasks[0])  # template needs this to get listurl to work?
            logging.info('ViewObservationTasksHandler showing %d tasks for user %s', len(obstasks), user2view)

        self.render('view-obstasks.html', {
            'username': current_user,  # logged in user
            'user2view': user2view,  # or none
            'area_name': area_name,  # or none
            'obstask': obstask,
            'obstasks': obstasks,
            'tasks': tasks,
            'pages': pages,
            'page': page,
            'show_navbar': show_nav,
            'filter': filter,  # not used
            'pagelist': utils.page_list(page, pages)
        })

    def ViewObservationTasksForAll(self):
        # page = int(self.request.get('page', 1))
        logging.debug('ViewObservationTasksForAll')
        return self.ViewTasks()


class AboutHandler(BaseHandler):
    def get(self):
        self.render('about.html', {
            'show_navbar': True
        })


class DonateHandler(BaseHandler):
    def get(self):
        self.render('donate.html')


class ActivityHandler(BaseHandler):
    def get(self):
        username = self.session['user']['name']
        logging.debug('ActivityHandler: %s', username)
        # if users.is_current_user_admin():
        self.render('activity.html',
                    {
                        'show_navbar': True,
                        'activities': cache.get_activities(username)
                    })


class FeedsHandler(BaseHandler):
    def get(self, feed):
        token = self.request.get('token')
        xml = cache.get_feed(feed, token)

        if not xml:
            self.error(404)
        else:
            self.response.out.write(xml)


class UserHandler(BaseHandler):
    def get(self, username):
        u = cache.get_user(username)

        if not u:
            self.error(404)
            return

        journals = cache.get_journals(u.key)
        # logging.info ("journals %s", journals)
        areas = cache.get_areas(u.key)
        # logging.info ("areas %s", areas)
        activities = cache.get_activities(username=username)
        following = cache.get_following(username)
        followers = cache.get_followers(username)
        # following_areas= cache.get_following_areas(username)

        # logging.info ("following %s, followers %s", following, followers)

        if 'user' in self.session:
            is_following = username in cache.get_following(self.session['user']['name'])
            thisuser = self.session['user']['name'] == u.name
        else:
            logging.debug("%s has no followers", username)
            is_following = False
            thisuser = False

            # logging.info ("u is %s", u)

        if not thisuser:
            u.email = "**masked**"

        self.render('user.html', {
            'u': u,
            'journals': journals,
            'activities': activities,
            'following': following,
            'followers': followers,
            'is_following': is_following,
            'thisuser': thisuser,  # True if user being shown is thisuser
            'areas': areas,
            'show_navbar': True,
        })


"""
        self.render('user.html', {
            'u': u,
            'journals': journals,
            'activities': activities,
            'following': following,
            'followers': followers,
            'is_following': is_following,
            'thisuser': thisuser
            #'areas': areas
        })
"""


class ViewJournalsHandler(BaseHandler):
    def get(self, username):
        u = cache.get_user(username)

        if not u:
            self.error(404)
            return

        journals = cache.get_journals(u.key)
        # logging.info ("journals %s", journals)
        areas = cache.get_areas(u.key)
        # logging.info ("areas %s", areas)
        activities = cache.get_activities(username=username)
        following = cache.get_following(username)
        followers = cache.get_followers(username)
        # following_areas= cache.get_following_areas(username)

        # logging.info ("following %s, followers %s", following, followers)

        if 'user' in self.session:
            is_following = username in cache.get_following(self.session['user']['name'])
            thisuser = self.session['user']['name'] == u.name
        else:
            logging.debug("%s has no followers", username)
            is_following = False
            thisuser = False

            # logging.info ("u is %s", u)

        self.render('view-journals.html', {
            'u': u,
            'journals': journals,
            'activities': activities,
            'following': following,
            'followers': followers,
            'is_following': is_following,
            'thisuser': thisuser,  # True if user being shown is thisuser
            'areas': areas,
            'show_navbar': True,
        })


class FollowHandler(BaseHandler):
    def get(self, username, area):
        user = cache.get_user(username)
        if not user or 'user' not in self.session:
            self.add_message('error', 'Area not found.')
            return self.error(404)

        thisuser = self.session['user']['name']

        self.redirect(webapp2.uri_for('user', username=username))

        # don't allow users to follow themselves
        if thisuser == username:
            self.add_message('error', 'Area not found.')
            return self.error(403)
            return

        if 'unfollow' in self.request.GET:
            op = 'del'
            unop = 'add'
        else:
            op = 'add'
            unop = 'del'

        xg_on = ndb.create_transaction_options(xg=True)

        def txn(thisuser, area, op):
            tu, oa = ndb.get_multi([thisuser, area])

            if not tu:
                tu = models.AreasFollowingIndex(key=thisuser)
            if not ou:
                oa = models.AreasFollowersIndex(key=area)

            changed = []
            if op == 'add':
                if thisuser.name() not in ou.users:
                    ou.users.append(thisuser.name())
                    changed.append(ou)
                if otheruser.name() not in tu.users:
                    tu.users.append(otheruser.name())
                    changed.append(tu)
            elif op == 'del':
                if thisuser.name() in ou.users:
                    ou.users.remove(thisuser.name())
                    changed.append(ou)
                if otheruser.name() in tu.users:
                    tu.users.remove(otheruser.name())
                    changed.append(tu)

            changed.put()

            return tu, ou

        followers_key = ndb.Key.from_path('User', username, 'UserFollowersIndex', username)
        following_key = ndb.Key.from_path('User', thisuser, 'UserFollowingIndex', thisuser)

        following, followers = ndb.run_in_transaction_options(xg_on, txn, following_key, followers_key, op)

        if op == 'add':
            self.add_message('success', 'You are now watching %s.' % username)
            models.Activity.create(cache.get_by_key(self.session['user']['key']), models.ACTIVITY_FOLLOWING, user)
        elif op == 'del':
            self.add_message('success', 'You are no longer watching %s.' % username)

        cache.set_multi({
            cache.C_FOLLOWERS % username: followers.users,
            cache.C_FOLLOWING % thisuser: following.users,
        })


class FollowAreaHandler(BaseHandler):
    @staticmethod
    def followArea(username, area_name, follow):
        '''
        If follow, add user to area's followers
        else remove user from area's followers
        user is added to (removed from) an index of the area's followers and area is added to (removed from) a list of areas the user is following.
        The areas's list of users: AreaFollowersIndex, is created if necessary
        The users's list of areas: UserFollowingAreasIndex, is created if necessary

        If follow is true, a journal is created for storing reports called Observations for {area_name}.
        The journal is not deleted in an unfollow, and if it already exists it is not an error.

        Args:
            username: The user who is to be added/removed from the areas followers.
            area_name: The area to be followed.
            follow: True to follow, False to unfollow.

        Returns:
        '''

        area = cache.get_area(area_name)
        if not area:
            self.add_message('error', 'Area not found.')
            self.response.set_status(404)
            self.response.out.write('{"status": "error", "reason": "area not found" }')
            return False

        user = cache.get_user(username)
        if not user:
            logging.error("followArea(): User not found")
            return False

        if follow == False:
            op = 'del'
        else:
            op = 'add'

        def txn(userfollowingareas_key, areafollowers_key, area, user, op):
            areasUserFollows, areasFollowers = ndb.get_multi([userfollowingareas_key, areafollowers_key])
            if not areasUserFollows:
                logging.info(u"FollowArea() User %s is following their first area", user.name)
                areasUserFollows = models.UserFollowingAreasIndex(key=userfollowingareas_key)
            if not areasFollowers:
                logging.info(u"FollowArea() adding first follower to area {0:s}".format(area.name))
                areasFollowers = models.AreaFollowersIndex(key=areafollowers_key)

            changed = []
            if op == 'add':
                if user.name not in areasFollowers.users:
                    areasFollowers.users.append(user.name)
                    changed.append(areasFollowers)
                    # print 'user.name type', type(user.name)

                if area.name not in areasUserFollows.areas:
                    # print 'area.name type', type(area.name)
                    # print 'area string_id() type', type(area.key.string_id())
                    # print 'area id() type', type(area.key.id())
                    areasUserFollows.areas.append(area.name)
                    areasUserFollows.area_keys.append(area.key)
                    changed.append(areasUserFollows)
                    changed.append(area)
                models.Activity.create(user, models.ACTIVITY_FOLLOWING, area.key)

            elif op == 'del':
                if user.name in areasFollowers.users:
                    areasFollowers.users.remove(user.name)
                    changed.append(areasFollowers)
                else:
                    logging.error(
                        u"FollowArea() user not in area's followers! {0:s}".format(userfollowingareas_key.string_id()))

                if area.name in areasUserFollows.areas:
                    changed.append(area)
                    areasUserFollows.areas.remove(area.name)
                    try:
                        areasUserFollows.area_keys.remove(area.key)
                    except:
                        logging.error(
                            u"FollowArea() Cannot remove follower - area.key {0:s} not in area_keys".format(area.key))
                    changed.append(areasUserFollows)
                else:
                    logging.error(u"FollowArea() Cannot remove area. Area not in user's list of areas")

                models.Activity.create(user, models.ACTIVITY_UNFOLLOWING, area.key)
            ndb.put_multi(changed)
            return areasUserFollows, areasFollowers

        UserFollowingAreas_key = models.UserFollowingAreasIndex.get_key(username)
        AreaFollowersIndex_key = models.AreaFollowersIndex.get_key(area_name)
        # print 'AreaFollowersIndex_key.encoded', AreaFollowersIndex_key
        areas_following, followers = ndb.transaction(
            lambda: txn(UserFollowingAreas_key, AreaFollowersIndex_key, area, user, op), xg=True)

        if op == 'add':
            ########### create a journal for each followed area - should be in above txn and a function call as duplicated ##############
            journal_name = 'Observations for ' + area_name  # .decode('utf-8') # name is used by view-obstask.html to make reports.
            existing_journal = models.Journal.get_journal(username, journal_name)
            if existing_journal:
                logging.warning('User already has a journal called {0:s}!'.format(journal_name))
                journal = existing_journal
            else:
                journal = models.Journal(parent=user.key, id=journal_name)
                # logging.error('FIXME no journal created due to self reference')
                journal.journal_type = "observations"

                def txn2(user_key, journal):
                    user = user_key.get()
                    user.journal_count += 1
                    ndb.put_multi([user, journal])
                    return user, journal

                user, journal = ndb.transaction(lambda: txn2(user.key, journal))
                cache.clear_journal_cache(user.key)
                models.Activity.create(user, models.ACTIVITY_NEW_JOURNAL, journal.key)
                cache.set(cache.pack(user), cache.C_KEY, user.key)

        return True

    def get(self, area_name):
        '''
        @fixme username from request path should be removed and get username from serssion.
        '''
        area = cache.get_area(area_name)
        if not area:
            self.error(404)
            return

        if 'user' not in self.session:
            logging.error("FollowAreaHandler() Error: user not logged in")
            self.error(404)
            return

        username = self.session['user']['name']

        if 'unfollow' in self.request.GET:
            if FollowAreaHandler.followArea(username, area_name, False) == True:
                self.add_message('success',
                                 u'You are no longer watching area <em>{0:s}</em>.'.format(area_name.decode('utf-8')))
                self.add_message('success', u'Created journal <em>{0:s}</em>.'.format(name.decode('utf-8')))
        else:
            if FollowAreaHandler.followArea(username, area_name, True) == True:
                self.add_message('success', u'You are now watching area <em>{0:s}</em>. Journal created'.format(
                    area_name.decode('utf-8')))

        #cache.flush()  # FIXME: Better fix by setting data into the cache as this will be expensive!!!
        #cache.clear_area_cache(self.session['user']['key'], area.key)

        self.populate_user_session()
        if 'unfollow' in self.request.GET:
            self.redirect(webapp2.uri_for('main'))
        else:
            self.redirect(webapp2.uri_for('view-area', area_name=area.name))
        return


class NewEntryHandler(BaseHandler):
    def get(self, username, journal_name, images=""):  # journal=None
        images = self.request.GET.get('sat_image', '')
        # print "NewEntryHandler: ", journal_name, images
        ownername = username
        author = self.session['user']['name']  # current user
        if author != ownername:
            logging.info("NewEntryHandler: non-owner %s creating entry in journal %s of %s", author, journal_name,
                         ownername)
            # self.error(403)
            # return

        user = cache.get_user(author)
        if not user:
            logging.error("NewEntryHandler(): User not found")
            return self.error(404)

        owner = cache.get_user(ownername)
        if not owner:
            logging.error("NewEntryHandler(): Owner not found")
            return self.error(404)

        journal = models.Journal.get_journal(author, journal_name)
        if journal == None:
            logging.error("NewEntryHandler(): Journal not found: %s", journal_name)
            return self.error(404)

        entry_key = models.Entry.get_entry_key(journal)
        content_key = models.EntryContent.get_entrycontent_key(journal)
        content = models.EntryContent(key=content_key)
        entry = models.Entry(key=entry_key, content=content_key.integer_id())

        if images:
            # content.images= [i.strip() for i in self.request.get('images').split(',')]
            content.images = [i.strip() for i in images.split(',')]
        else:
            images = []

        def txn(user, journal, entry, content):
            journal.entry_count += 1
            user.entry_count += 1
            ndb.put_multi([user, journal, entry, content])
            return user, journal

        user, journal = ndb.transaction(lambda: txn(user, journal, entry, content), xg=True)
        # move this to new entry saving for first time
        models.Activity.create(user, models.ACTIVITY_NEW_ENTRY, entry.key)

        counters.increment(counters.COUNTER_ENTRIES)
        cache.clear_entries_cache(journal.key)
        cache.set_keys([user, journal, entry, content])
        cache.set(cache.pack(journal), cache.C_JOURNAL, owner, journal_name)

        if user.facebook_token and user.facebook_enable:
            taskqueue.add(queue_name='retry-limit', url=webapp2.uri_for('social-post'),
                          params={'entry_key': entry_key, 'network': models.USER_SOURCE_FACEBOOK,
                                  'username': user.name})
        if user.twitter_key and user.twitter_enable:
            taskqueue.add(queue_name='retry-limit', url=webapp2.uri_for('social-post'),
                          params={'entry_key': entry_key, 'network': models.USER_SOURCE_TWITTER, 'username': user.name})

        self.redirect(
            webapp2.uri_for('view-entry', username=owner, journal_name=journal_name, entry_id=entry_key.integer_id()))


class ViewEntryHandler(BaseHandler):
    def get(self, username, journal_name, entry_id):

        if self.session['user']['name'] != username:
            self.error(403)
            return

        user = cache.get_user(username)

        journal_name = journal_name.decode('utf-8')

        journal = models.Journal.get_journal(username, journal_name)
        if journal == None:
            logging.error("ViewEntryHandler(): Journal not found %s", journal_name)
            return self.error(404)

        # logging.info('ViewEntryHandler journal_name %s %s', journal_name, journal)
        entry, content, blobs = models.Entry.get_entry(username, journal_name, entry_id)
        if not entry:
            logging.error("ViewEntryHandler(): Entry %s not found for user %s in journal %s ", entry_id, username,
                          journal_name)
            self.error(404)
            return

        if 'pdf' in self.request.GET:
            logging.error("ViewEntryHandler(): PDF not supported.")

        if not journal:
            type = "default"
        else:
            type = journal.journal_type

        self.render('entry.html', {
            'blobs': blobs,
            'content': content,
            'entry': entry,
            'show_navbar': True,
            'journal_type': type,
            'journal_name': journal_name,
            'render': cache.get_entry_render(username, journal_name, entry_id),
            'username': username,
            'upload_url': webapp2.uri_for('upload-url', username=username, journal_name=journal_name,
                                          entry_id=entry_id),
            'can_upload': user.can_upload(),
            'markup_options': utils.render_options(models.CONTENT_TYPE_CHOICES, content.markup),
        })


class GetUploadURL(BaseHandler):
    def get(self, username, journal_name, entry_id):
        logging.debug('GetUploadURL()')
        # user = cache.get_by_key(self.session['user']['key'])
        user = cache.get_user(self.session['user']['name'])
        if user.can_upload() and user.name == username:
            self.response.out.write(blobstore.create_upload_url(
                webapp2.uri_for('upload-file',
                                username=username,
                                journal_name=journal_name,
                                entry_id=entry_id
                                ),
                max_bytes_per_blob=models.Blob.MAXSIZE
            ))
        else:
            self.response.out.write('')


class SaveEntryHandler(BaseHandler):
    def post(self):
        username = self.request.get('username')
        journal_name = self.request.get('journal_name').decode('utf-8')
        entry_id = long(self.request.get('entry_id'))
        delete = self.request.get('delete')

        if username != self.session['user']['name']:
            self.error(403)
            return

        self.redirect(webapp2.uri_for('view-entry', username=username, journal_name=journal_name, entry_id=entry_id))

        entry, content, blobs = models.Entry.get_entry(username, journal_name, entry_id)

        if delete == 'delete':
            journal_key = entry.key.parent()
            user_key = journal_key.parent()

            def txn_delete(user_key, journal_key, entry_key, content_key, blobs):
                entry = ndb.get(entry_key)
                delete = [entry_key, content_key]
                delete.extend([i.key for i in blobs])
                ndb.delete_async(delete)

                user, journal = ndb.get([user_key, journal_key])
                journal.entry_count -= 1
                user.entry_count -= 1

                journal.chars -= entry.chars
                journal.words -= entry.words
                journal.sentences -= entry.sentences

                user.chars -= entry.chars
                user.words -= entry.words
                user.sentences -= entry.sentences

                for i in blobs:
                    user.used_data -= i.size

                user.count()
                user.put()

                # just deleted the last journal entry
                if journal.entry_count == 0:
                    journal.last_entry = None
                    journal.first_entry = None

                # only 1 left (but there are 2 in the datastore still)
                else:
                    # find last entry
                    entries = models.Entry.all().ancestor(journal).order('-date').fetch(2)
                    logging.info('%s last entries returned', len(entries))
                    for e in entries:
                        if e.key != entry.key:
                            journal.last_entry = e.date
                            break
                    else:
                        logging.error('Did not find n last entry not %s', entry.key)

                    # find first entry
                    entries = models.Entry.all().ancestor(journal).order('date').fetch(2)
                    logging.info('%s first entries returned', len(entries))
                    for e in entries:
                        if e.key != entry.key:
                            journal.first_entry = e.date
                            break
                    else:
                        logging.error('Did not find n first entry not %s', entry.key)

                journal.count()
                journal.put()
                return user, journal

            user, journal = ndb.transaction(lambda: txn_delete(user_key, journal_key, entry.key, content.key, blobs))

            blobstore.delete([i.get_key('blob') for i in blobs])

            ndb.delete([entry.key, content.key])
            counters.increment(counters.COUNTER_ENTRIES, -1)
            counters.increment(counters.COUNTER_CHARS, -entry.chars)
            counters.increment(counters.COUNTER_SENTENCES, -entry.sentences)
            counters.increment(counters.COUNTER_WORDS, -entry.words)
            cache.clear_entries_cache(journal_key)
            cache.set_keys([user, journal])
            cache.set(cache.pack(journal), cache.C_JOURNAL, username, journal_name)
            self.add_message('success', 'Entry deleted.')
            self.redirect(webapp2.uri_for('view-journal', username=username, journal_name=journal_name))

        else:
            subject = self.request.get('subject').strip()
            tags = self.request.get('tags').strip()
            images = self.request.get('images').strip()
            text = self.request.get('text').strip()
            markup = self.request.get('markup')
            blob_list = self.request.get_all('blob')

            date = self.request.get('date').strip()
            time = self.request.get('time').strip()
            if not date:
                newdate = entry.date
            else:
                if not time:
                    time = '00:00'
                try:
                    # Bootstrap3's date-control format 2014-12-31 23:59
                    newdate = datetime.datetime.strptime('{0!s} {1!s}'.format(date, time), '%Y-%m-%d %H:%M')
                except:
                    self.add_message('danger', 'Couldn\'t understand that date: {0!s} {1!s}'.format(date, time))
                    newdate = entry.date

            if tags:
                tags = [i.strip() for i in self.request.get('tags').split(',')]
            else:
                tags = []
            if images:
                images = [i.strip() for i in self.request.get('images').split(',')]
            else:
                images = []

            def txn_save(entry_key, content_key, rm_blobs, subject, tags, images, text, markup, rendered, chars, words,
                         sentences, date):

                ndb.delete_multi_async(b.key for b in rm_blobs)

                user, journal, entry = ndb.get_multi([entry_key.parent().parent(), entry_key.parent(), entry_key])

                dchars = -entry.chars + chars
                dwords = -entry.words + words
                dsentences = -entry.sentences + sentences

                journal.chars += dchars
                journal.words += dwords
                journal.sentences += dsentences

                # user.chars += dchars
                # user.words += dwords
                # user.sentences += dsentences

                entry.chars = chars
                entry.words = words
                entry.sentences = sentences

                entry.date = date

                user.set_dates()
                user.count()

                content = models.EntryContent(key=content_key)
                content.subject = subject
                content.tags = tags
                content.images = images
                content.text = text
                content.markup = markup
                content.rendered = rendered

                for i in rm_blobs:
                    user.used_data -= i.size
                    entry.blobs.remove(str(i.key.id()))

                ndb.put_multi([user, entry, content])

                # just added the first journal entry
                if journal.entry_count == 1:
                    journal.last_entry = date
                    journal.first_entry = date
                else:
                    # find last entry
                    entries = models.Entry.get_entries(journal, True)
                    logging.info('%s last entries returned', len(entries))
                    for e in entries:
                        if e.key != entry.key:
                            if date > e.date:
                                journal.last_entry = date
                            else:
                                journal.last_entry = e.date
                            break
                    else:
                        logging.error('Did not find n last entry not %s', entry.key)

                    # find first entry
                    # entries = models.Entry.query(ancestor = journal).order('date').fetch(2)
                    entries = models.Entry.get_entries(journal, False)
                    logging.info('%s first entries returned', len(entries))
                    for e in entries:
                        if e.key != entry.key:
                            if date < e.date:
                                journal.first_entry = date
                            else:
                                journal.first_entry = e.date
                            break
                    else:
                        logging.error('Did not find n first entry not %s', entry.key)

                journal.count()
                journal.put()
                return user, journal, entry, content, dchars, dwords, dsentences

            rm_blobs = []

            for b in blobs:
                bid = str(b.key)
                if bid not in blob_list:  # blob_list is list of blobs already in entry. No need so save them again.
                    b.key.delete()
                    rm_blobs.append(b)

            for b in rm_blobs:
                blobs.remove(b)

            rendered = utils.markup(text, markup)

            if text:
                nohtml = html.strip_tags(rendered)
                chars = len(nohtml)
                words = len(entry.WORD_RE.findall(nohtml))
                sentences = len(entry.SENTENCE_RE.split(nohtml))
            else:
                chars = 0
                words = 0
                sentences = 0

            user, journal, entry, content, dchars, dwords, dsentences = ndb.transaction(
                lambda: txn_save(entry.key, content.key, rm_blobs, subject, tags, images, text, markup, rendered, chars,
                                 words, sentences, newdate))
            models.Activity.create(cache.get_user(username), models.ACTIVITY_SAVE_ENTRY, entry.key)

            counters.increment(counters.COUNTER_CHARS, dchars)
            counters.increment(counters.COUNTER_SENTENCES, dsentences)
            counters.increment(counters.COUNTER_WORDS, dwords)

            entry_render = utils.render('entry-render.html', {
                'blobs': blobs,
                'content': content,
                'entry': entry,
                'show_navbar': True,
                'entry_url': webapp2.uri_for('view-entry', username=username, journal_name=journal_name,
                                             entry_id=entry_id),
            })
            cache.set(entry_render, cache.C_ENTRY_RENDER, username, journal_name, entry_id)
            cache.set_keys([user, journal])
            cache.set_multi({
                cache.C_KEY % user.key: cache.pack(user),
                cache.C_ENTRY_RENDER % (username, journal_name, entry_id): entry_render,
                cache.C_ENTRY % (username, journal_name, entry_id): (
                cache.pack(entry), cache.pack(content), cache.pack(blobs)),
            })

            self.add_message('success', 'Your entry has been saved.')

        cache.clear_entries_cache(entry.key.parent())
        cache.set((cache.pack(entry), cache.pack(content), cache.pack(blobs)), cache.C_ENTRY, username, journal_name,
                  entry_id)


class UploadHandler(BaseUploadHandler):
    def post(self, username, journal_name, entry_id):
        logging.debug("UploadHandler() username %s journal_name %s", username, urllib.unquote(journal_name))
        # print 'uploadhandler1'
        if username != self.session['user']['name']:
            self.error(403)
            return
        user = cache.get_user(username)

        uploads = self.get_uploads()
        entry, content, blobs = models.Entry.get_entry(username, urllib.unquote(journal_name), entry_id)

        blob_type = -1
        if len(uploads) == 1:
            blob = uploads[0]
            if blob.content_type.startswith('image/'):
                blob_type = models.BLOB_TYPE_IMAGE

        # blob_type = models.BLOB_TYPE_IMAGE #testing only delete this line.

        if not entry or self.session['user']['name'] != username or blob_type == -1:
            for upload in uploads:
                upload.delete()
            return

        def txn(user, entry, blob):
            # user, entry = ndb.get_multi([user_key, entry_key])
            user.used_data += blob.size
            entry.blobs.append(str(blob.key.id()))
            ndb.put_multi([user, entry, blob])
            return user, entry

        blob_key = models.Blob.get_blob_key(entry)
        # print 'blob_key', blob_key


        new_blob = models.Blob(key=blob_key, blob=blob.key(), type=blob_type, name=blob.filename, size=blob.size)
        new_blob.get_url()

        user, entry = ndb.transaction(lambda: txn(user, entry, new_blob))
        cache.delete([
            cache.C_KEY % user.key,
            cache.C_KEY % entry.key,
            cache.C_ENTRY % (username, journal_name, entry_id),
            cache.C_ENTRY_RENDER % (username, journal_name, entry_id),
        ])
        cache.clear_entries_cache(entry.key.parent())

        self.redirect(
            webapp2.uri_for('upload-success', blob_id=blob.key, name=new_blob.key.string_id(), size=new_blob.size,
                            url=new_blob.get_url()))


class UploadSuccess(BaseHandler):
    def get(self):
        d = dict([(i, self.request.get(i)) for i in [
            'blob_id',
            'name',
            'size',
            'url',
        ]])

        self.response.out.write(json.dumps(d))


class FlushMemcache(BaseHandler):  # Admin Only Function
    def get(self):
        cache.flush()
        self.render('admin.html', {
            'msg': ' memcache flushed',
            'show_navbar': True})


class AdminDashboardHandler(BaseHandler):  # Admin Only Function
    def get(self):
        self.render('admin.html', {
            'msg': ' Admin Dashboard',
            'show_navbar': True})

class MarkupHandler(BaseHandler):
    def get(self):
        self.render('markup.html')


# class SecurityHandler(BaseHandler):
#    def get(self):
#        self.render('security.html')

class UpdateUsersHandler(BaseHandler):  # Admin Only Function for user maintenance.
    def get(self):
        q = models.User.all(keys_only=True)
        cursor = self.request.get('cursor')

        if cursor:
            q.with_cursor(cursor)

        def txn(user_key):
            u = ndb.get(user_key)

            # custom update code here

            u.put()
            return u

        LIMIT = 10
        ukeys = q.fetch(LIMIT)
        for u in ukeys:
            user = ndb.run_in_transaction(txn, u)
            self.response.out.write('<br>updated %s: %s' % (user.name, user.lname))

        if len(ukeys) == LIMIT:
            self.response.out.write('<br><a href="%s">next</a>' % webapp2.uri_for('update-users', cursor=q.cursor()))
        else:
            self.response.out.write('<br>done')


class BlobHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, key):
        blob_info = blobstore.BlobInfo.get(key)

        name = self.request.get('name')
        if name == 'True':
            name = True

        if not blob_info:
            self.error(404)
        else:
            self.send_blob(blob_info, save_as=name)


# from https://github.com/ryanwi/twitteroauth/blob/master/source/main.py
class TwitterHandler(BaseHandler):
    def get(self, action):
        if 'user' not in self.session:
            self.redirect(webapp2.uri_for('main'))
            return

        self._client = twitter.oauth_client(self)

        if action == 'login':
            self.login()
        elif action == 'callback':
            self.callback()

    def login(self):
        # get a request token
        raw_request_token = self._client.get_request_token()

        self.session['twitter_token'] = raw_request_token.key
        self.session['twitter_secret'] = raw_request_token.secret

        # get the authorize url and redirect to twitter
        authorize_url = self._client.get_authorize_url(raw_request_token)
        self.redirect(authorize_url)

    def callback(self):
        if 'denied' in self.request.GET:
            self.redirect(webapp2.uri_for('account'))

        # lookup request token
        raw_oauth_token = self.request.get('oauth_token')

        # get an access token for the authorized user
        oauth_token = twitter.oauth_token(self.session['twitter_token'], self.session['twitter_secret'])
        raw_access_token = self._client.get_access_token(oauth_token)

        # get the screen_name
        self._client = twitter.oauth_client(self, raw_access_token)
        screen_name = self._client.get('/account/verify_credentials')['screen_name']

        # store access token
        def txn(user_key, screen_name, key, secret):
            u = ndb.get(user_key)
            u.twitter_id = screen_name
            u.twitter_key = key
            u.twitter_secret = secret
            u.twitter_enable = True
            u.put()
            return u

        user = ndb.run_in_transaction(txn, self.session['user']['key'], screen_name, raw_access_token.key,
                                      raw_access_token.secret)
        cache.set_keys([user])
        self.redirect(webapp2.uri_for('account'))


class SocialPost(BaseHandler):
    def post(self):
        entry_key = ndb.Key(self.request.get('entry_key'))
        network = self.request.get('network')
        username = self.request.get('username')

        MESSAGE = 'Wrote a new entry on Bunjil.'
        NAME = 'my observations'
        link = utils.absolute_uri('user', username=username)

        user = cache.get_by_key(entry_key.parent().parent())

        if network == models.USER_SOURCE_FACEBOOK and all([user.facebook_token, user.facebook_enable]):
            data = facebook.graph_request(user.facebook_token, method='POST', path='/feed', payload_dict={
                'message': MESSAGE,
                'link': link,
                'name': NAME,
            })
        if network == models.USER_SOURCE_TWITTER and all([user.twitter_id, user.twitter_key, user.twitter_secret]):
            oauth_token = twitter.oauth_token(user.twitter_key, user.twitter_secret)
            client = twitter.oauth_client(None, oauth_token)
            status = client.post('/statuses/update', status='%s %s' % (MESSAGE, link))


class FollowingHandler(BaseHandler):
    def get(self, username):
        u = cache.get_user(username)
        following = cache.get_by_keys(cache.get_following(username), 'User')
        followers = cache.get_by_keys(cache.get_followers(username), 'User')

        self.render('following.html', {'u': u, 'following': following, 'followers': followers})


class DownloadJournalHandler(BaseHandler):
    def get(self, username, journal_name):
        if username != self.session['user']['name']:
            self.error(403)
            return

        journal = models.Journal.get_journal(username, journal_name.decode('utf-8'))

        if not journal:
            self.error(404)
            return

        DATE_FORMAT = '%m/%d/%Y'
        errors = []
        error = None
        try:
            from_date = datetime.datetime.strptime(self.request.get('from'), DATE_FORMAT)
        except ValueError:
            if 'from' in self.request.GET:
                errors.append('from')
            from_date = journal.first_entry

        try:
            to_date = datetime.datetime.strptime(self.request.get('to'), DATE_FORMAT)
        except ValueError:
            if 'to' in self.request.GET:
                errors.append('to')
            to_date = journal.last_entry

        if not errors and 'format' in self.request.GET and from_date and to_date:
            key_name = 'pdf-%s-%s' % (from_date, to_date)
            key = ndb.Key.from_path('Blob', key_name, parent=journal_key)
            pdf_blob = ndb.get(key)

            # either no cached entry, or it's outdated
            if not pdf_blob or pdf_blob.date < journal.last_modified:
                if pdf_blob:
                    pdf_blob.blob.delete()

                file_name = files.blobstore.create(mime_type='application/pdf')
                title = '%s: %s to %s' % (journal.name, from_date.strftime(DATE_FORMAT), to_date.strftime(DATE_FORMAT))

                entries = []
                for entry_key in models.Entry.all(keys_only=True).ancestor(journal).filter('date >=', from_date).filter(
                        'date <', to_date + datetime.timedelta(1)).order('date'):
                    entries.append(cache.get_entry(username, journal_name, entry_key.id(), entry_key))

                with files.open(file_name, 'a') as f:
                    error = utils.convert_html(f, title, entries)
                files.finalize(file_name)
                pdf_blob = models.Blob(
                    key=key,
                    blob=files.blobstore.get_blob_key(file_name),
                    type=models.BLOB_TYPE_PDF,
                    name='%s - %s - %s to %s' % (
                    username, utils.deunicode(journal_name.decode('utf-8')), from_date.strftime(DATE_FORMAT),
                    to_date.strftime(DATE_FORMAT)),
                    date=journal.last_modified,
                )

                if error:
                    pdf_blob.blob.delete()
                    self.add_message('danger', 'Error while converting to PDF: %s' % error)
                else:
                    pdf_blob.put()

            if not error:
                self.redirect(pdf_blob.get_url(name=True))
                return

        self.render('download-journal.html', {
            'journal': journal,
            'username': username,
            'errors': errors,
            'from': self.request.get('from', from_date.strftime(DATE_FORMAT)),
            'to': self.request.get('to', to_date.strftime(DATE_FORMAT)),
        })



'''
letsEncrypt
https://github.com/fabito/letsencrypt-appengine/blob/master/well_known.py
'''
class AcmeChallenge(ndb.Model):
    solution = ndb.StringProperty(indexed=False)

    def full_solution(self):
        print self.solution
        return self.key.id() + "." + self.solution


class AcmeChallengeHandler(webapp2.RequestHandler):
    def get(self, challenge_id):
        challenge_key = ndb.Key(AcmeChallenge, challenge_id)
        self.response.headers['Content-Type'] = 'text/plain'
        acme_challenge = challenge_key.get()

        if acme_challenge is None:
            self.response.write("ACME key not stored")
        else:
            self.response.write(acme_challenge.full_solution())

    def post(self, challenge_id, **kwargs):
        """
        Avoid using this POST to set keys as it is allows anyone to claim the domain.
        INstead just post the ACME key and value into the datastore.
        Args:
            challenge_id:
            **kwargs:
        Returns:
        """
        self.response.headers['Content-Type'] = 'text/plain'
        return self.response.write('POST Disabled by admin') # uncomment below.
        '''
        challenge, solution = challenge_id.split(".")
        challenge = AcmeChallenge(id=challenge, solution=solution)
        challenge.put()
        self.response.write(challenge_id)
        '''

class GoogleCallback(BaseHandler):
    def get(self):
        if 'user' not in self.session:
            return

        if self.request.get('action') == 'authorize':
            self.redirect(str(utils.google_url()))
            return

        if 'token' in self.request.GET:
            def txn(user_key, token):
                u = ndb.get(user_key)
                u.google_docs_token = token
                u.google_docs_enable = True
                u.put()
                return u

            try:
                session_token = utils.google_session_token(self.request.get('token'))
                user = ndb.run_in_transaction(txn, self.session['user']['key'], session_token.get_token_string())
                cache.set_keys([user])
                self.add_message('success', 'Google Docs authorized.')
            except Exception, e:
                self.add_message('danger', 'An error occurred with Google Docs. Try again.')
                logging.error('Google Docs error: %s', e)

            self.redirect(webapp2.uri_for('account'))


class ListAssetsHandler(BaseHandler):
    def get(self):
        list = apiservices.list_file_by_owner() # list_tables()
        return self.response.write(list)

        output = ""
        for  item in list['items']:
            #move to a template
            output += '<ul>' +  '<a href="https://www.google.com/fusiontables/data?docid=' + item['tableId'] + '">' + item['name'] + '</a></ul>'
        self.response.write("<h1>Fusion Tables owned by application</h1>: %s" % output ) #json.dumps(list, indent=4, sort_keys=True)


class DeleteAssetHandler(BaseHandler):
    def get(self, file_id):
        ret = apiservices.delete_file(file_id)
        if ret == None:
            return self.response.write("Deleted OK")
        else:
            self.response.set_status(500)
            return self.response.out.write(ret)

class CreateFolder(BaseHandler):
    def get(self, parent_id, folder_name):
        if len(parent_id) <= 1:
            folder_id = apiservices.create_folder(folderName=folder_name, parentID=None) #root folder
        else:
            folder_id = apiservices.create_folder(folderName=folder_name, parentID=parent_id)

        listing = '<h1>Created Folder</h1><br/><p><a href="https://drive.google.com/open?id=' + folder_id + '">' + bleach.clean(folder_name) + '</a></p>'
        listing += '<h2>Parent Folder</h2><br/><p><a href="https://drive.google.com/open?id=' + parent_id + '">' + 'parent' + '</a></p>'

        return self.response.write(listing)

class ListFolders(BaseHandler):
    def get(self):
        ret = apiservices.list_folders()
        if ret == None:
            return self.response.write("Listed OK")
        else:
            self.response.set_status(500)
            return self.response.out.write(ret)

class ListFoldersPlain(BaseHandler):
    def get(self):
        list = apiservices.list_folders()
        return self.response.write(list)

class ListFolders(BaseHandler):

    def get(self, page_token=None):
        next_page_token, items = apiservices.get_folder_list(page_token)
        self.render('folders.html', {
            'list': items,
            'next_page_token': next_page_token,
            'prev_page_token': page_token,
        })

class ListFolder(BaseHandler):
    def get(self, folder_id):
        return apiservices.get_latest_file(folder_id)


class ListExportTasks(BaseHandler):
    def get(self):
        return self.response.write(eeservice.list_exports()) #json.dumps(list, indent=4, sort_keys=True)





SECS_PER_WEEK = 60 * 60 * 24 * 7

config = {
  'webapp2_extras.sessions': {
      'secret_key': settings.COOKIE_KEY,
      'session_max_age': SECS_PER_WEEK,
      'cookie_args': {'max_age': SECS_PER_WEEK},
  },
}

app = webapp2.WSGIApplication([
    webapp2.Route(r'_ah/warmup', handler=EarthEngineWarmUpHandler, name='earth-engine'),
    webapp2.Route(r'/', handler=MainPageObsTask, name='main2'),
    webapp2.Route(r'/old', handler=MainPage, name='main'),

    webapp2.Route('/.well-known/acme-challenge/<challenge_id>', AcmeChallengeHandler, methods=['GET', 'POST']),
    # google site verification

    # webapp2.Route(r'/login/google/<protected_url>', handler=GoogleLogin, name='login-google'),
    webapp2.Route(r'/login/google', handler=GoogleLogin, name='login-google'),
    webapp2.Route(r'/login/facebook', handler=FacebookLogin, name='login-facebook'),
    webapp2.Route(r'/logout', handler=Logout, name='logout'),
    webapp2.Route(r'/logout/google', handler=GoogleSwitch, name='logout-google'),

    webapp2.Route(r'/about', handler=AboutHandler, name='about'),
    webapp2.Route(r'/account', handler=AccountHandler, name='account'),
    webapp2.Route(r'/activity', handler=ActivityHandler, name='activity'),

    webapp2.Route(r'/blob/<key>', handler=BlobHandler, name='blob'),
    webapp2.Route(r'/donate', handler=DonateHandler, name='donate'),

    webapp2.Route(r'/facebook', handler=FacebookCallback, name='facebook'),
    webapp2.Route(r'/google', handler=GoogleCallback, name='google'),
    webapp2.Route(r'/feeds/<feed>', handler=FeedsHandler, name='feeds'),
    webapp2.Route(r'/following/<username>', handler=FollowingHandler, name='following'),

    webapp2.Route(r'/register', handler=RegisterUserHandler, name='register'),
    webapp2.Route(r'/new/user', handler=NewUserHandler, name='new-user'),

    webapp2.Route(r'/admin', handler=AdminDashboardHandler, name='admin-dashboard'),
    webapp2.Route(r'/admin/flush', handler=FlushMemcache, name='flush-memcache'),
    webapp2.Route(r'/admin/update/users', handler=UpdateUsersHandler, name='update-users'),
    webapp2.Route(r'/admin/checknew', handler=CheckForNewInAllAreasHandler, name='check-new-all-images'),
    webapp2.Route(r'/admin/checknew/<area_name>', handler=CheckForNewInAreaHandler, name='check-new-area-images'),
    webapp2.Route(r'/admin/assets', handler=ListAssetsHandler, name='list-assets'),
    webapp2.Route(r'/admin/assets/delete/<file_id>', handler=DeleteAssetHandler, name='delete-asset'),
    webapp2.Route(r'/admin/folders', handler=ListFolders, name='list-drive-folders'),
    webapp2.Route(r'/admin/folders/<page_token>', handler=ListFolders, name='list-drive-folders'),
    webapp2.Route(r'/admin/folder/create/<parent_id>/<folder_name>', handler=CreateFolder, name='create-drive-folder'),
    webapp2.Route(r'/admin/folder/list/<folder_id>', handler=ListFolder, name='list-drive-folder'),
    webapp2.Route(r'/admin/exports', handler=ListExportTasks, name='list-exports-tasks'),
    webapp2.Route(r'/admin/test/<test_name>/<area_name>', handler=RunAreaTest, name='area-test'),

    webapp2.Route(r'/admin/alerts/glad/seed', handler=SeedGladClusterData),
    webapp2.Route(r'/admin/alerts/glad/checknew', handler=CheckForGladAlertsInAllAreasHandler, name='alerts-glad-all'),
    webapp2.Route(r'/admin/alerts/glad/checknew/<noupdate>', handler=CheckForGladAlertsInAllAreasHandler, name='alerts-glad-all'),
    webapp2.Route(r'/admin/alerts/glad/<area_name>', handler=CheckForGladAlertsInAreaHandler, name='alerts-glad-area'),
    webapp2.Route(r'/admin/alerts/glad/<area_name>/<noupdate>', handler=CheckForGladAlertsInAreaHandler, name='alerts-glad-area'),
    webapp2.Route(r'/admin/alerts/glad2clusters/<area_name>', handler=ProcessAlerts2ClustersHandler, name='alerts-glad2cluster-area'),
    webapp2.Route(r'/admin/alerts/glad/distribute_cluster/<area_name>', handler=DistributeGladClusters,
                                                          name='alerts-glad2cluster-area'),

    webapp2.Route(r'/admin/obs/list', handler=ViewObservationTasksHandler, handler_method='ViewObservationTasksForAll',
                    name='view-obstasks'),
    webapp2.Route(r'/markup', handler=MarkupHandler, name='markup'),

    # webapp2.Route(r'/api-docs', include('rest_framework.urls', namespace='rest_framework')),
    webapp2.Route(r'/new/journal', handler=NewJournal, name='new-journal'),
    webapp2.Route(r'/save', handler=SaveEntryHandler, name='entry-save'),
    webapp2.Route(r'/mailtest', handler=MailTestHandler, name='mail-test'),

    webapp2.Route(r'/selectcell/<area_name>/<celldata>', handler=SelectCellHandler, name='select-cell'),

    webapp2.Route(r'/twitter/<action>', handler=TwitterHandler, name='twitter'),
    webapp2.Route(r'/upload/file/<username>/<journal_name>/<entry_id>', handler=UploadHandler, name='upload-file'),
    webapp2.Route(r'/upload/success', handler=UploadSuccess, name='upload-success'),
    webapp2.Route(r'/upload/url/<username>/<journal_name>/<entry_id>', handler=GetUploadURL, name='upload-url'),


    webapp2.Route(r'/myareas', handler=ViewAllAreas, name='view-areas'),  # view my areas
    webapp2.Route(r'/<username>/myareas', handler=ViewAllAreas, name='view-areas'),  # view someone else's areas.

    webapp2.Route(r'/area', handler=NewAreaHandler, name='new-area'),  # create area
    webapp2.Route(r'/area/<area_name>/delete', handler=DeleteAreaHandler, name='delete-area'),
    # delete area (owner or admin)
    # webapp2.Route(r'/area/<area_name>/update/view/<lat:\d+>/<lng:\d+>/<zoom:\d+>/', handler=UpdateAreaViewHandler, name='area-save-view'),

    webapp2.Route(r'/area/<area_name>/getcells', handler=GetLandsatCellsHandler, name='get-cells'),  # ajax
    webapp2.Route(r'/area/<area_name>', handler=ExistingAreaHandler, name='view-area'),  # view area.
    webapp2.Route(r'/area/<area_name>/follow', handler=FollowAreaHandler, name='follow-area'),  # start following area
    webapp2.Route(r'/area/<area_name>/action/<action>/<satelite>/<algorithm>/<latest>',
                    handler=LandsatOverlayRequestHandler, name='new-landsat-overlay'),
    webapp2.Route(r'/area/<area_name>/action/<action>/<satelite>/<algorithm>/<latest>/<path:\d+>/<row:\d+>',
                    handler=LandsatOverlayRequestHandler, name='new-landsat-overlay'),

    webapp2.Route(r'/observation-task/<router_name>/next', handler=ObservationTaskHandler, name="next-task", methods=['GET']),
    webapp2.Route(r'/observation-task/next', handler=ObservationTaskHandler, name="next-task", methods=['GET']),
    webapp2.Route(r'/observation-task/response', handler=ObservationTaskHandler, name="next-task", methods=['POST']),

    webapp2.Route(r'/overlay/regenerate/<overlay_key>', handler=RegenerateOverlayHandler, name='regenerate-overlay'),

    webapp2.Route(r'/observation-task/preference', handler=ObsTaskPreferenceHandler, name='obsTaskPreference'),
    webapp2.Route(r'/observation-task/preference/resource', handler=ObsTaskPreferenceResource, name='obsTaskPreferenceResource'),

    webapp2.Route(r'/region', handler=RegionHandler, name='RegionHandler'),

    # observation tasks see also admin/obs/list
    webapp2.Route(r'/obs/list', handler=ViewObservationTasksHandler, handler_method='ViewObservationTasksForAll',
                  name='view-obstasks'),
    webapp2.Route(r'/obs/overlay/create/<obskey_encoded>/<role>/<algorithm>', handler=CreateOverlayHandler,
                  name='create-overlay'),
    webapp2.Route(r'/obs/overlay/update/<overlay_key>/<algorithm>', handler=UpdateOverlayAjaxHandler, name='update-overlay'),
    webapp2.Route(r'/obs/<task_id>', handler=Old_ObservationTaskAjaxHandler, name='view-obstask'),


    webapp2.Route(r'/overlay/<landsat_id>/<role>/<algorithm>', handler=ImageOverlayHandler,
                  name='overlay-create'),


    webapp2.Route(r'/tasks/social_post', handler=SocialPost, name='social-post'),
    # this section must be last, since the regexes below will match one and two -level URLs
    webapp2.Route(r'/<username>/journals', handler=ViewJournalsHandler, name='view-journals'),
    webapp2.Route(r'/<username>', handler=UserHandler, name='user'),
    webapp2.Route(r'/<username>/journal/<journal_name>', handler=ViewJournal, name='view-journal'),
    webapp2.Route(r'/<username>/journal/<journal_name>/<entry_id:\d+>', handler=ViewEntryHandler, name='view-entry'),
    webapp2.Route(r'/<username>/journal/<journal_name>/download', handler=DownloadJournalHandler,
                    name='download-journal'),
    webapp2.Route(r'/<username>/journal/<journal_name>/new/<images:[^/]+>', handler=NewEntryHandler, name='new-entry'),
    webapp2.Route(r'/<username>/journal/<journal_name>/new', handler=NewEntryHandler, name='new-entry')


    # webapp2.Route(r'/tasks/backup', handler=BackupHandler, name='backup'),
    # (decorator.callback_path, decorator.callback_handler())

], debug=True, config=config)

RESERVED_NAMES = set([
    '',
    '_ah',
    'warmup',
    '.well-known',
    '<username>',
    'about',
    'assets',
    'myareas',
    'observation-task',
    'next',
    'account',
    'activity',
    'area',
    'areas',
    'admin',
    'blob',
    'checknew',
    'contact',
    'delete',
    'docs',
    'donate',
    'entry',
    'engine',
    'exports',
    'facebook',
    'features',
    'feeds',
    'file',
    'folder'
    'folders'
    'follow',
    'followers',
    'following',
    'google',
    'googledocs',
    'googleplus',
    'help',
    'image',
    'journal',
    'journals',
    'login',
    'logout',
    'list',
    'markup',
    'mailtest',
    'new',
    'news',
    'oauth',
    'obs',
    'overlay',
    'obstasks'
    'openid',
    'prior',
    'privacy',
    'register',
    'save',
    # 'security',
    'site',
    'selectcell',
    'stats',
    'observatory',
    'tasks',
    'terms',
    'test',
    'twitter',
    'upload',
    'user',
    'users',
    'old',
    'region',
    'overlay'
])

# assert that all routes are listed in RESERVED_NAMES
for i in app.router.build_routes.values():

  name = i.template.partition('/')[2].partition('/')[0]
  if name not in RESERVED_NAMES:
      import sys

      logging.critical('%s not in RESERVED_NAMES', name)
      logging.error('%s not in RESERVED_NAMES' % name)
      sys.exit(1)
