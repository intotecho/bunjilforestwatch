import logging

import webapp2
from google.appengine.ext.webapp import blobstore_handlers

import cache
import models
from google.appengine.api import users

import secrets
from webapp2_extras import sessions

import utils


class BaseHandler(webapp2.RequestHandler):
    """This class docstring shows how to use sphinx and rst syntax
    BaseHandler class provides common functionality that all app handlers derive from.

       - **parameters**, **types**, **return** and **return types**::
    The first line is brief explanation, which may be completed with
    a longer one. For instance to discuss about its methods. The only
    method here is :func:`function1`'s. The main idea is to document
    the class and methods's arguments with

    - **parameters**, **types**, **return** and **return types**::

          :param arg1: description
          :param arg2: description
          :type arg1: type description
          :type arg1: type description
          :return: return description
          :rtype: the return type description

    - and to provide sections such as **Example** using the double commas syntax::

          :Example:

          followed by a blank line !

      which appears as follow:

      :Example:

      followed by a blank line

    - Finally special sections such as **See Also**, **Warnings**, **Notes**
      use the sphinx syntax (*paragraph directives*)::

          .. seealso:: blabla
          .. warnings also:: blabla
          .. note:: blabla
          .. todo:: blabla

    .. note::
        There are many other Info fields but they may be redundant:
            * param, parameter, arg, argument, key, keyword: Description of a
              parameter.
            * type: Type of a parameter.
            * raises, raise, except, exception: That (and when) a specific
              exception is raised.
            * var, ivar, cvar: Description of a variable.
            * returns, return: Description of the return value.
            * rtype: Return type.

    .. note::
        There are many other directives such as versionadded, versionchanged,
        rubric, centered, ... See the sphinx documentation for more details.

    Here below is the results of the :func:`function1` docstring.

    """

    def render(self, _template, context={}):
        """returns (arg1 / arg2) + arg3

        renders a template in a user's context by calling utils.rv()
        adds some app specific functionality such as additional messages.
       - **parameters**, **types**, **return** and **return types**::
        This is a longer explanation, which may include math with latex syntax
        :math:`\\alpha`.
        Then, you need to provide optional subsection in this order (just to be
        consistent and have a uniform documentation. Nothing prevent you to
        switch the order):

          - parameters using ``:param <name>: <description>``
          - type of the parameters ``:type <name>: <description>``
          - returns using ``:returns: <description>``
          - examples (doctest)
          - seealso using ``.. seealso:: text``
          - notes using ``.. note:: text``
          - warning using ``.. warning:: text``
          - todo ``.. todo:: text``

        **Advantages**:
         - Uses sphinx markups, which will certainly be improved in future
           version
         - Nice HTML output with the See Also, Note, Warnings directives


        **Drawbacks**:
         - Just looking at the docstring, the parameter, type and  return
           sections do not appear nicely

        :param arg1: the first value
        :param arg2: the first value
        :param arg3: the first value
        :type arg1: int, float,...
        :type arg2: int, float,...
        :type arg3: int, float,...
        :returns: arg1/arg2 +arg3
        :rtype: int, float

        :Example:

        >>> import template
        >>> a = template.MainClass1()
        >>> a.function1(1,1,1)
        2

        .. note:: can be useful to emphasize
            important feature
        .. seealso:: :class:`MainClass2`
        .. warning:: arg2 must be non-zero.
        .. todo:: check that arg2 is non zero.
        """
        context['session'] = self.session
        context['user'] = self.session.get('user')
        context['messages'] = self.get_messages()
        context['active'] = _template.partition('.')[0]

        ga = ''
        if 'localhost' in self.request.url:
            self.add_message("warning",
                             "Local - Production instance at <a href='http://www.bunjilforestwatch.net'>www.bunjilforestwatch.net</a>")
            ga = secrets.GOOGLE_ANALYTICS_DEV

        if 'bunjilfw' in self.request.url:
            self.add_message("warning", "Test Instance - Production is now at bunjilforestwatch.net")
            ga = secrets.GOOGLE_ANALYTICS_TEST

        if 'appbfw-test' in self.request.url:
            self.add_message("info", "Production is now at bunjilforestwatch.net")
            ga = secrets.GOOGLE_ANALYTICS_TEST

        if 'appbfw' in self.request.url:
            self.add_message("warning", "Warning not using sercure url bunjilforestwatch.net")
            ga = secrets.GOOGLE_ANALYTICS_PROD

        if 'bunjilforestwatch' in self.request.url:
            ga = secrets.GOOGLE_ANALYTICS_PROD
            # self.add_message("info", "Production")

        context['google_analytics'] = ga

        for k in ['login_source']:
            if k in self.session:
                context[k] = self.session[k]

        # logging.info('BaseHandler: render template %s with context <<%s>>,', _template, context)
        # logging.debug('BaseHandler: messages %s', context['messages'])
        # print '\033[1;33mRed like Radish\033[1;m'
        # print '\033[1;34mRed like Radish\033[1;m \x1b[0m'
        # print('\033[31m' + 'some red text')
        # print('\033[30m' + 'reset to default color')

        # logging.debug('BaseHandler:\033[1;31m Color Console Test\033[1;m  \x1b[0m %s', "Reset to Default Color")

        rv = utils.render(_template, context)

        self.response.write(rv)

    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        # logging.info('BaseHandler:dispatch %s', self.request)

        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session(backend='datastore')

    #
    def populate_user_session(self, user=None):
        """This should be called any time the session data needs to be updated.
        session['var'] = var should never be used, except in this function
        This function adds the below data to the data returned to the template.
        """

        if 'user' not in self.session and not user:
            logging.error("populate_user_session() - no user!")
            return
        elif not user:
            user = cache.get_user(self.session['user']['name'])

        self.session['user'] = {
            'admin': users.is_current_user_admin(),
            'avatar': user.gravatar(),
            'email': user.email,
            'key': user.key,  # .urlsafe(),
            'name': user.name,
            'token': user.token,
            'role': user.role
        }
        user_key = self.session['user']['key']

        self.session['journals'] = cache.get_journal_list(user_key)
        self.session['areas_list'] = cache.get_areas_list(user_key)  # TODO This list can be long and expensive.
        self.session['following_areas_list'] = cache.get_following_areas_list(user_key)  # used for basehandler menu.

    MESSAGE_KEY = '_flash_message'

    def add_message(self, level, message):
        self.session.add_flash(message, level, BaseHandler.MESSAGE_KEY)

    def get_messages(self):
        return self.session.get_flashes(BaseHandler.MESSAGE_KEY)

    def process_credentials(self, name, email, source, uid):

        User = models.User

        if source == models.USER_SOURCE_GOOGLE:
            user = User.query(
                User.google_id == uid).get()
            # .filter('%s_id' %source, uid).get()
        else:
            logging.error('Only USER_SOURCE_GOOGLE IS IMPLENTED')

        if not user:
            registered = False
            self.session['register'] = {'name': name, 'email': email, 'source': source, 'uid': uid}
        else:
            registered = True
            self.populate_user_session(user)
            self.session['login_source'] = source
            user.put()  # to update last_active

        return user, registered

    def logout(self):
        """ Destroys a user session
        """
        for k in ['user', 'journals', 'areas']:
            if k in self.session:
                del self.session[k]


class BaseUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    """ Alternative Base Class for upload request handlers.
    """
    session_store = None

    def add_message(self, level, message):
        self.session.add_flash(message, level, BaseHandler.MESSAGE_KEY)
        self.store()

    def store(self):
        self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        if not self.session_store:
            self.session_store = sessions.get_store(request=self.request)
        return self.session_store.get_session(backend='datastore')
