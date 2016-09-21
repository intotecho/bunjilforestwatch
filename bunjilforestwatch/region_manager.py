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

    area_geom = area_fc.geometry()
    regions = []

    if _is_in_congo_fc().geometry().intersects(area_geom,100).getInfo():
        regions.append('congo')
    if _is_in_peru_fc().geometry().intersects(area_geom,100).getInfo():
        regions.append('peru')
    if _is_in_indonesia_fc().geometry().intersects(area_geom,100).getInfo():
        regions.append('indonesia')

    return regions


def _is_in_peru_fc():
    countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
    return countries.filterMetadata('Country', 'equals', 'Peru')


def _is_in_congo_fc():
    countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
    return countries.filterMetadata('Country', 'equals', 'Congo')


def _is_in_indonesia_fc():
    countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
    return countries.filterMetadata('Country', 'equals', 'Indonesia')

