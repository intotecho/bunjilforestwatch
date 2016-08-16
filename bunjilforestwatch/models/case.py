from google.appengine.ext import ndb
from models.glad_cluster import GladCluster


class Case(ndb.Model):
    """

    """

    glad_cluster = ndb.KeyProperty(kind=GladCluster)  # key to the GladCluster that created the case.

    status = ndb.StringProperty(required=True, indexed=True)

    creation_time = ndb.DateTimeProperty(required=True, indexed=False, auto_now_add=True)

    # Voting Data
    fire_votes = ndb.IntegerProperty(indexed=False)
    deforestation_votes = ndb.IntegerProperty(indexed=False)
    agriculture_votes = ndb.IntegerProperty(indexed=False)
    road_votes = ndb.IntegerProperty(indexed=False)
    unsure_votes = ndb.IntegerProperty(indexed=False)

    confidence = ndb.IntegerProperty(indexed=False)