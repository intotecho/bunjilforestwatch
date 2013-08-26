'''
Created on 25/05/2013

'''


import sys
import logging
logging.basicConfig(level=logging.DEBUG)
import settings
import oauth2client.client
import datetime
import ee
import json
def initEarthEngineService():
    SCOPES = ('https://www.googleapis.com/auth/earthengine.readonly')
    creds = ee.ServiceAccountCredentials(settings.MY_SERVICE_ACCOUNT, settings.MY_PRIVATE_KEY_FILE)
    ee.Initialize(creds) 
    
def getLatestLandsat8HSVUpres(boundary_polygon):
    #logging.info('boundary_polygon %s type: %s', boundary_polygon, type(boundary_polygon))
    feat = ee.Geometry.Polygon(boundary_polygon)
    #logging.info('feat %s', feat)
    
    feature = ee.Feature(feat,{'name': 'areaName', 'fill': 1})
        
    park_boundary = ee.FeatureCollection(feature)
    info = park_boundary.getInfo()
    logging.info('boundary_coords= %s', info['features'][0]['geometry']['coordinates'])
    
    end_date   = datetime.datetime.today()
    secsperyear = 60 * 60 * 24 * 365 #  365 days * 24 hours * 60 mins * 60 secs
    start_date = end_date - datetime.timedelta(seconds = 1 * secsperyear )
    logging.debug('start:%s, end:%s ',start_date,  end_date)
        
    #sortedCollection = ee.ImageCollection(ee.ImageCollection('LANDSAT/LC8_L1T_TOA').filterBounds(park_boundary).filterDate(start_date, end_date).sort('system:time_start', False ).limit(1)) #note cast to ee,ImageCollection() resolves bug in sort() for ee ver 0.13
    #logging.info('Collection description : %s', sortedCollection.getInfo())
    
    a = ee.ImageCollection(ee.ImageCollection(ee.ImageCollection('LANDSAT/LC8_L1T_TOA').filterBounds(park_boundary)))
    b = ee.ImageCollection(a.filterDate(start_date, end_date))
    c = ee.ImageCollection(b.sort('system:time_start', False )) #note cast to ee,ImageCollection() resolves bug in sort() for ee ver 0.13
    sortedCollection = ee.ImageCollection(c) #.limit(1))
  
    scenes  = sortedCollection.getInfo()
    #logging.info('Scenes: %s', sortedCollection)
    
    for feature in scenes['features']:
        id = feature['id']   #logging.info('Scene id: %s, %s', id, i)
        image1 = ee.Image(id)
        props = image1.getInfo()['properties'] 
        logging.info('image properties: %s', props)
        crs = image1.getInfo()['bands'][0]['crs']
        path    = props['WRS_PATH']
        row     = props['WRS_ROW']
        datestr = props['system:time_start']
        system_time_start= datetime.datetime.fromtimestamp(props['system:time_start'] / 1000)
        #why two? datatime.datetime?        
        date_format_str = "%Y-%m-%d @ %H:%M"
        date_str = system_time_start.strftime(date_format_str)

        logging.info('getLatestLandsat8HSVUpres id: %s, date:%s', id, date_str)
        #Select the visible red, green and blue bands.
        #map = image1.getMapId({'bands': '30, 20, 10', 'gain': '1.4, 1.4, 1.1'})
        return image1 #.clip(park_boundary)

def SharpenLandsat8HSVUpres(image1):
        #Convert to HSV, swap in the pan band, and convert back to RGB. 
        #Example from https://ee-api.appspot.com/#5ea3dd541a2173702cfe6c7a88346475
        #rgb = image1.select(['B4', 'B3', 'B2']).unitScale(0, 255)
        ##gray = image1.select(['B8']).unitScale(0, 155)
        #huesat = rgb.rgbtohsv().select(['hue', 'saturation'])
        #upres = ee.Image.cat(huesat, gray).hsvtorgb().clip(park_boundary)
        #return upres

        #Pan sharpen Landsat 8
        rgb = image1.select("B4","B3","B2")
        pan = image1.select("B8")
        huesat = rgb.rgbtohsv().select(['hue', 'saturation'])
        upres = ee.Image.cat(huesat, pan).hsvtorgb()   #.clip(park_boundary)
        #var vis = {min:0.01, max:0.5, gamma:1.2};
        return(upres)
    

###################################
# Image statistics

# Calculate the 5% and 95% values for each band in a Landsat image,
# and use them to construct visualization parameters for displaying the image.
#
# Example created: August 8, 2013
# NOTE: The syntax for the reducer objects is expected to change in the near future
#       so check the developers list if this example stops working.

# Return the percentile values for each band in an image.
def getPercentile(image, percentile, crs):
    return image.reduceRegion(
        ee.Reducer.percentile(percentile), # reducer
        None, # geometry (Defaults to the footprint of the image's first band)
        None, # scale (Set automatically because bestEffort == true)
        crs,
        None, # crsTransform,
        True  # bestEffort
        ).getInfo()

# Get a download URL for an image.
def getOverlayPath(image):    
    crs = image.getInfo()['bands'][0]['crs']
    
    # Get the percentile values for each band.
    p05 = []
    p95 = []
    
    p05 = getPercentile(image, 5, crs)
    p95 = getPercentile(image, 95, crs)

    # Print out the image ststistics.
    print('5%', p05, '95%', p95)
    #### try to work out bands syntax for visparams ####
    
    
    #red = 'B4'
    #green = 'B3'
    #blue = 'B2'
        
    bands1 = [  {u'id': u'B4'},
                   {u'id': u'B3'},
                   {u'id': u'B2'} ]
    

    # Define visualization parameters, based on the image statistics.
    visparams = {'name': 'landsat8img',
                     'bands':  json.dumps(bands1), # none of the above work.
                     #'crs': crs,
                     #'format': 'png',
                     'min': p05,
                     'max': p95,
                     #'gamma': 1.2,
                     #'scale': 30,
                     #'gain':  0.1, 
                     #'region' : boundary_polygon,
                     'filePerBand' : False
                }

    props = image.getInfo()
   
    path      = image.getDownloadUrl(visparams)
    print path
    return path

########################################

import unittest
import urllib2

class TestEEService(unittest.TestCase):
    
    def setUp(self):
        initEarthEngineService()
        
    def TestL8VisOverlay(self):
        coords = [
              [        145.3962206840515,        -37.71424496764925      ], 
              [        146.049907207489,        -37.705553487215816      ], 
              [        146.00733518600464,        -37.239075302021824      ], 
              [        145.29871702194214,        -37.233608599437034      ]
              ]    
        
        #image = getLatestLandsat8HSVUpres(coords)
        testimage= ee.Image("LANDSAT/LC8_L1T_TOA/LC80440342013170LGN00").unitScale(0,255).toByte()
        getOverlayPath(testimage)
        self.assertEqual(1, 1, 'L8 overlay failed')
        pass