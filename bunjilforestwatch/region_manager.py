import ee
import eeservice
import logging

def get_regions():
  # Return JSON format of all region and its details
  return {
    "region_data": [
      {
        "region_id": 1,
        "region_name": 'borneo'
      },
      {
        "region_id": 2,
        "region_name": 'peru'
      }
    ]
  };

def find_region(area_fc):
    """
     @returns: a list of regions intersecting with the provided area
     @param: area_fc an ee.Geometry representing an area of interest defined by a user
    """

    if not eeservice.initEarthEngineService():
      logging.error('Sorry, Server Credentials Error')
      return False

    regions = []

    if _get_peru_fc().geometry().intersects(area_fc, 100).getInfo():
      regions.add('peru')
    if _get_congo_fc().geometry().intersects(area_fc, 100).getInfo():
      regions.add('congo')
    if _get_indonesia_fc().geometry().intersects(area_fc, 100).getInfo():
      regions.add('indonesia')

    return regions

def _get_peru_fc():
  countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
  return countries.filterMetadata('Country', 'equals', 'Peru')

def _get_congo_fc():
  countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
  return countries.filterMetadata('Country', 'equals', 'Congo')

def _get_indonesia_fc():
  countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
  return countries.filterMetadata('Country', 'equals', 'Indonesia')
