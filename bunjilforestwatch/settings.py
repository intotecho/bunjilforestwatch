#Bunjil Forest Watch setttings.py

import logging
logging.basicConfig(level=logging.DEBUG)

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'bunjilforestwatch.net']
    
# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
TIME_ZONE = 'Australia/Melbourne'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

#os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = 'uploads/'  

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = "/media/"  

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = 'static/'  

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
#    'pipeline.finders.PipelineFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

import os
PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
#MANAGERS = ADMINS

'''
#This has no effect without pipeline
PIPELINE_JS = {
    'main': {
        'source_filenames': (
            'js/base-maps.js',
            'js/landsat-grid.js',
            'js/layerslider.js',
            'js/view-maps.js',
            'js/overlay-mgr.js ',
            'js/site.js '
            'js/drawing-tools.js',
        ),
        'output_filename': 'js/main.js'
    },
    'vendor': {
        'source_filenames': (
            'js/vendor/jquery.min.js',
            'js/vendor/bootstrap.min.js',
            'js/vendor/bootbox.min.js',
            'js/vendor/bootstrap-modal-popover.js',
            'js/vendor/custom-tile-overlay.js',
            'js/vendor/draggable-object.js',
            'js/vendor/GeoJSON.js',
            'js/vendor/jquery.nouislider.min.js',
            'js/vendor/polygon-outliner.js',
            'js/vendor/yaml/Yaml.js',
            'js/vendor/yaml/YamlInline.js',
            'js/vendor/yaml/YamlParser.js'                  
        ),
        'output_filename': 'js/vendor.js'
       #// , 'template_name': 'javascript',
    }
}

PIPELINE_CSS = {
    'main': {
        'source_filenames': (
            'bootstrap-responsive.css',
            'bootstrap-social.css',
            'bootstrap.css',
            'jquery.nouislider.css',
            'jquery-ui-1.8.16.custom.css',
            'ui.dropdownchecklist.css',
            'united.bootstrap.min.css',
            'wbpreview-theme.css',
            'site.css'
                ),
        'output_filename': 'css/main.css'
        
    }
}
'''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        'USER': '',
        'PASSWORD': '',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': ''                     # Set to empty string for default.
    }
}

MIDDLEWARE_CLASSES = (
    'google.appengine.ext.ndb.django_middleware.NdbDjangoMiddleware'
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    
    # Uncomment the next line for simple clickjacking protection:
     'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = '{{ project_name }}.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = '{{ project_name }}.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, "templates"),
    os.path.join(PROJECT_PATH, "templates/includes"),
)
TEMPLATE_CONTEXT_PROCESSORS = (
                             'django.core.context_processors.static'
                               )

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework_swagger',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)


SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        } 
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}



#STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage' # According to Glen Robertson
#STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage' # According to Pipeline Read the docs.

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder'
)

import jinja2
try:
    from secrets import *
except ImportError, exp:
    logging.error('no secrets.py')
    pass
'''
import jac
try:
    import jac
    from jac import CompressorExtension
    jinja_env = jinja2.Environment(
                               #extensions=['pipeline.templatetags.ext.PipelineExtension'], #latest pipeline 1.5
                               #extensions=['pipeline.jinja2.ext.PipelineExtension'],            #pipeline 1.3
                               extensions=[CompressorExtension],
                               loader=jinja2.FileSystemLoader( 'templates') 
                               ) # Moved From utils.py
    jinja_env .compressor_output_dir = './static/dist'
    jinja_env .compressor_static_prefix = '/static'
    jinja_env .compressor_source_dirs = './static_files'
    print 'imported jac'

except:
    jinja_env = jinja2.Environment(
                               loader=jinja2.FileSystemLoader( 'templates') 
                               ) # Moved From utils.py
    print 'failed to import jac' 


'''
jinja_env = jinja2.Environment(
                               loader=jinja2.FileSystemLoader( 'templates') 
                               ) # Moved From utils.py
import filters
jinja_env.filters.update(filters.filters)

if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine'):
    # Running on production App Engine
    pass

elif os.getenv('SETTINGS_MODE') == 'prod':
    # Running in development, but want to access the Google Cloud SQL instance
    # in production.
    pass

else:
    # Running in development.
    #print "Local Dev"
    pass

import warnings

#with warnings.catch_warnings(): # doesn't work
#    warnings.filterwarnings("ignore",category=DeprecationWarning)
#    import md5, sha, webob
