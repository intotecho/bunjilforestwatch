#secrets-dist.py contains your private keys

SECRET_KEY = 'blah3245d'

ADMINS = (
    # ('Chris', 'chris@bunjilforestwatch.net'),
)


# fill this with data from os.urandom(64)
#not used
COOKIE_KEY = ''

# to enable, set to analytics id: 'UA-12345678-9'
#don't worry about this unless you want to track usage
GOOGLE_ANALYTICS_DEV = u'UA-DEV'
GOOGLE_ANALYTICS_TEST = u'UA-xxxxxx-1'
GOOGLE_ANALYTICS_PROD = u'UA-xxxxxxx-2'

GOOGLE_MAPS_API_KEY = 'SomeKey'


# for bunjilfw - should not be in the distribution files
#Not used don't worry about it
TWITTER_KEY = ''
TWITTER_SECRET = ''


#for devserver, for Windows must use PEM format, not PK12.
#From your appengine account
MY_LOCAL_SERVICE_ACCOUNT = 'XXXXXXX@developer.gserviceaccount.com'
MY_LOCAL_PRIVATE_KEY_FILE = "fileprivatekey.pem"

#This Drive folder_id will change if using a different service account.
#Good for sharing clusters
CLUSTERS_FOLDER_ID = "0B-lTullYuWZ_SWdKelFXREEwRkE"
