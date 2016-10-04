import logging

import eeservice
import models


def regenerate_overlay(overlay):

    if overlay is None:
        return

    eeservice.initEarthEngineService()  # we need earth engine now.
    if not eeservice.initEarthEngineService():  # we need earth engine now. logging.info(initstr)
        logging.error('Could not contact Google Earth Engine to fetch latest area overlays')
        return

    map_id = eeservice.getLandsatImageById(overlay.image_collection, overlay.image_id, overlay.algorithm)
    overlay.map_id = map_id['mapid']
    overlay.token = map_id['token']
    overlay.put()
    return overlay


def fetch_latest_overlay(area):
    """
    :param area:
    :return: Latest LANDSAT image overlay for area. Creates new overlay if none already exists.
    """

    if not area:
        return

    if not eeservice.initEarthEngineService():  # we need earth engine now.
        logging.error('Could not contact Google Earth Engine to fetch latest area overlays')
        return

    if area.get_boundary_hull_fc() is None:
        logging.error('Could not create overlay. Area %s does not have a valid location or boundary' % (
            area.name))
        return

    map_id = eeservice.getLandsatOverlay(area.get_boundary_hull_fc(), 'l8', 'rgb', 0, [])

    overlays = models.Overlay.query(models.Overlay.map_id == map_id['mapid']).fetch()
    if len(overlays) == 0:
        overlay = models.Overlay(image_id=map_id['id'],
                                 map_id=map_id['mapid'],
                                 token=map_id['token'],
                                 image_collection=map_id['collection'],
                                 algorithm='rgb')
        overlay.put()
        overlays = [overlay]
    return overlays
