import ee
import eeservice
import logging


def get_regions():
    # Return JSON format of all region and its details
    return {
        "region_data": [
            {
                "region_id": 1,
                "region_name": 'congo'
            },
            {
                "region_id": 2,
                "region_name": 'peru'
            },
            {
                "region_id": 3,
                "region_name": 'indonesia'
            }
        ]
    }


def find_regions(area_fc):
    """
     @param: area_fc an ee.Geometry representing an area of interest defined by a user
     @returns: a list of regions intersecting with the provided area
    """

    if not eeservice.initEarthEngineService():
        logging.error('Sorry, Server Credentials Error')
        return False

    area_geom = area_fc.geometry().convexHull(100)
    regions = []

    if _is_in_congo(area_geom):
        regions.append('congo')
    if _is_in_peru(area_geom):
        regions.append('peru')
    if _is_in_indonesia(area_geom):
        regions.append('indonesia')

    return regions


def _is_in_peru(area_geom):
    peru = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw').filterMetadata('Country', 'equals', 'Peru').geometry()
    return area_geom.intersects(peru).getInfo()


def _is_in_congo(area_geom):
    congo = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw').filterMetadata('Country', 'equals', 'Congo').geometry()
    return area_geom.intersects(congo).getInfo()


def _is_in_indonesia(area_geom):
    indonesia = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw').filterMetadata('Country', 'equals', 'Indonesia').geometry()
    return area_geom.intersects(indonesia).getInfo()

