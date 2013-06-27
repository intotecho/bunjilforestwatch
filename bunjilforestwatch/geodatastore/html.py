#!/usr/bin/python2.5
#
# Copyright 2008 Google Inc. All Rights Reserved.

"""One-line documentation for html module.

A detailed description of html.
"""

__author__ = 'pamelafox@google.com (Pamela Fox)'

import wsgiref.handlers
import os

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.api import users

class BasePage(webapp.RequestHandler):
  def get(self):
    self.render(self.getTemplateFilename(), self.getTemplateValues())

  def getTemplateValues(self, title):
    if users.GetCurrentUser():
      login_url = users.CreateLogoutURL(self.request.uri)
      login_linktext = 'Logout'
      login_name = users.GetCurrentUser().email()
    else:
      login_url = users.CreateLoginURL(self.request.uri)
      login_linktext = 'Login'
      login_name = 'Not logged in'

    template_values = {
      'login': {
        'url': login_url,
        'linktext': login_linktext,
        'name': login_name,
        'admin': users.is_current_user_admin()
      },
      'title': title
    }
    return template_values

  def getTemplateFilename(self):
    return "base.html"

  def render(self, filename, template_values):
    path = os.path.join(os.path.dirname(__file__), 'templates', filename)
    self.response.out.write(template.render(path, template_values))

##
# Page class for the personal view
class AdminPage(BasePage):
  ##
  # Returns a dictionary with values for the template
  def getTemplateValues(self):
    template_values = BasePage.getTemplateValues(self, 'Admin')
    return template_values

  ##
  # Returns the filename of the template to use when
  # rendering
  def getTemplateFilename(self): 
    return "admin.html"

##
# Page class for the personal view
class QueryPage(BasePage):
  ##
  # Returns a dictionary with values for the template
  def getTemplateValues(self):
    template_values = BasePage.getTemplateValues(self, 'Query')
    return template_values

  ##
  # Returns the filename of the template to use when
  # rendering
  def getTemplateFilename(self): 
    return "query.html"

##
# Page class for the personal view
class MapDisplayPage(BasePage):
  ##
  # Returns a dictionary with values for the template
  def getTemplateValues(self):
    template_values = BasePage.getTemplateValues(self, 'Map')
    return template_values

  ##
  # Returns the filename of the template to use when
  # rendering
  def getTemplateFilename(self): 
    return "mapdisplay.html"
  
##
# Page class for the locator view
class LocatorPage(BasePage):
  ##
  # Returns a dictionary with values for the template
  def getTemplateValues(self):
    template_values = BasePage.getTemplateValues(self, 'Locator')
    return template_values

  ##
  # Returns the filename of the template to use when
  # rendering
  def getTemplateFilename(self): 
    return "locator.html"

application = webapp.WSGIApplication(
    [('/', AdminPage),
     ('/admin', AdminPage),
     ('/mapdisplay', MapDisplayPage),
     ('/locator', LocatorPage),
     ('/query', QueryPage)],
    debug=False)
wsgiref.handlers.CGIHandler().run(application)
