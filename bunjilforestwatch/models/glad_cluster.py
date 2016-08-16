from google.appengine.ext import ndb

from models import AreaOfInterest


class GladCluster(ndb.Model):
    """

    """
    area = ndb.KeyProperty(kind=AreaOfInterest)  # key to the GladCluster that created the case.

    first_alert_time = ndb.DateTimeProperty(required=True, indexed=False, auto_now_add=True)
    geo_json = ndb.StringProperty(required=True, indexed=False)
