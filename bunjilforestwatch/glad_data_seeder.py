import logging

from google.appengine.ext import ndb

import cache
import eeservice
import geojson
import models
from gladalerts import create_glad_cluster_and_case_entities


def remove_old_seeded_area(old_seeded_area):
    clusters = models.GladCluster.get_glad_clusters_for_area(old_seeded_area)
    for cluster in clusters:
        cases = models.Case.get_cases_for_glad_cluster(cluster)
        for case in cases:
            case.key.delete()

        cluster.key.delete()

    old_seeded_area.key.delete()


def create_area(new_area_geojson_str, logged_in_user):
    """
    Create a new Area
    @param new_area_geojson_str - defines the new area as a geojson string.
           This may optionally contain a boundary_feature named 'boundary' - depending on the new area form design
           :param logged_in_user:
    """

    # read geojson dict of area properties
    try:
        logging.debug("AreaHandler() new_area_geojson_str: %s ", new_area_geojson_str)
        new_area = geojson.loads(new_area_geojson_str)
    except (ValueError, KeyError) as e:
        logging.error("AreaHandler() Exception : {0!s}".format(e))
        if isinstance(e, KeyError):
            logging.error('No new_area_geojson_str parameter provided')
        elif isinstance(e, ValueError):
            logging.error("AreaHandler() Value Exception : {0!s} parsing new_area_geojson_str".format(e))
            logging.error('Error parsing new_area data E1184')
        return False, None

    # area_name
    logging.info("AreaHandler() request to create new area %s", new_area)
    try:
        area_name = new_area['properties']['area_name'].encode('utf-8')  # allow non-english area names.
    except KeyError, e:
        logging.error('Create area requires a name.')
        return False, None

    ft_docid = ''

    try:
        ft_docid = new_area['properties']['fusion_table']['ft_docid'].encode('utf-8')  # allow non-english area names.
    except KeyError, e:
        logging.warning('Seeded area does not have a fusion table id.')

    existing_area = cache.get_area(area_name)
    if existing_area:
        remove_old_seeded_area(existing_area)
        logging.info('Deleted old seed data')

    # check EE service
    if not eeservice.initEarthEngineService():  # we need earth engine now.
        logging.error('Failed to seed data because Google Earth Engine not available right now. Please try again later')
        return False, None

    # pre-init variables to create area in case they don't appear in the geojson object
    maxlatlon = ndb.GeoPt(0, 0)
    minlatlon = ndb.GeoPt(0, 0)
    area_location = ndb.GeoPt(0, 0)
    boundary_hull = None
    boundary_geojsonstr = None  # no boundary defined yet.
    # boundary_type = new_area['properties']['boundary_type']
    boundary_feature = None  # client may optionally pass boundary on a Feature named 'boundary'
    total_area = 0
    # coords = []
    # ft_docid = None
    # center_pt = []
    # shared = 'private'

    for feature in new_area['features']:
        try:
            name = feature['properties']['name']
            coordinates = feature['geometry']['coordinates']
        except KeyError:
            errmsg = "A feature must have ['properties']['name'] and ['geometry']['coordinates']"
            logging.error(errmsg % feature)
            return False, None

        # get map view
        if name == "mapview":  # get the view settings to display the area.
            zoom = feature['properties']['zoom']
            center = ndb.GeoPt(float(coordinates[1]), float(coordinates[0]))

        # get center point
        if name == "area_location":  # get the view settings to display the area.
            area_location = ndb.GeoPt(
                float(coordinates[1]),
                float(coordinates[0]))

        # get drawn or geojson imported boundary
        if name == "boundary_hull":
            # boundary_hull = feature
            boundary_feature = feature
            pass

    # TODO: check area is not too small or too big.

    def txn(area):
        # user = user_key.get()
        area.put()
        return area

    try:
        area = models.AreaOfInterest(
            id=area_name, name=area_name,
            region=new_area['properties']['region_name'].decode('utf-8'),
            owner=logged_in_user.key,
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
            glad_monitored=True,
            folder_id=new_area['properties']['folder_id'].decode('utf-8'),
        )
    except Exception, e:
        logging.error('danger', 'Error creating area. %s' % (e))
        return False, None

    area.set_shared('public')

    # set boundary if one was provided.
    if boundary_feature is not None:
        eeFeatureCollection, status, errormsg = models.AreaOfInterest.get_eeFeatureCollection(
            new_area)
        boundary_hull_dict = models.AreaOfInterest.calc_boundary_fc(eeFeatureCollection)
        area.set_boundary_fc(boundary_hull_dict, False)

    # update the area and the referencing user
    try:
        area = ndb.transaction(lambda: txn(area), xg=True)
        # models.Activity.create(user, models.ACTIVITY_NEW_AREA, area.key)
        logging.info('success',
                     'Created your new area of interest: %s covering about %d sq.km' % (area.name, total_area))

    except Exception, e:
        # self.add_message('danger', "Error creating area.  Exception: {0!s}".format(e))
        logging.error("Exception creating area... {0!s}".format(e))
        return False, None

    # if auto-follow, add user as follower or area
    # if new_area['properties']['self_monitor'] == True:
    #     logging.debug('Requesting self-monitoring for %s' % (area.name))
    #     # FollowAreaHandler.followArea(username, area.name, True)
    #     # TODO: does an area need followers?

    else:
        logging.info('Area creator did not request self-monitoring for %s' % (area.name))

    return True, area


def seed_data(logged_in_user):
    """
    Seeds the data store with a new areas (within the glad monitored zones), glad clusters and cases.
    @returns: True if successful, Message: to show when the request has been handled
    """

    # TODO: use a sub directory and automatically scan and use whole directory for seeding
    with open('seed-data/peru_area.geojson', 'r') as seed_data_file:
        peru_area_goejson_str = seed_data_file.read()

    peru_area_success, peru_area = create_area(peru_area_goejson_str, logged_in_user)

    if not peru_area_success:
        return False, "Error: could not seed data for some reason"

    create_glad_cluster_and_case_entities(peru_area)

    return True, "GladCluster and case data has been seeded successfully. " \
                 "NOTE: any previously seeded data has been removed"
