'''
Created on 25/05/2013
@author: cgoodman
'''

#import PIL
#from PIL import ImageTk
#from PIL import TKInter
#from oauth2client.appengine import AppAssertionCredentials
#SCOPES = ('https://www.googleapis.com/auth/earthengine.readonly')
#credentials = AppAssertionCredentials(scope=SCOPES)
#scopes = [
#  'https://www.googleapis.com/auth/earthengine.readonly' #,
  #'https://www.googleapis.com/auth/earthbuilder.readonly'
#]
#scopes = ' '.join(scopes) 
#import pycrypto
#from PyCryptoSignedJWT import PyCryptoSignedJwtAssertionCredentials

import sys
import logging
logging.basicConfig(level=logging.DEBUG)
import settings
import oauth2client.client
import datetime
import ee

def initEarthEngineService():

    SCOPES = ('https://www.googleapis.com/auth/earthengine.readonly')
    
    #private_key = open(settings.MY_PRIVATE_KEY_FILE, 'rb').read()
    #private_key = open(settings.MY_PRIVATE_KEY_FILE).read()
    
    #creds = oauth2client.client.SignedJwtAssertionCredentials(
    #       settings.MY_SERVICE_ACCOUNT, , ee.OAUTH2_SCOPE)
    creds = ee.ServiceAccountCredentials(settings.MY_SERVICE_ACCOUNT, settings.MY_PRIVATE_KEY_FILE)
    
    ee.Initialize(creds) 
    #ee.Initialize(ee.ServiceAccountCredentials(settings.MY_SERVICE_ACCOUNT, settings.MY_PRIVATE_KEY_FILE))

# Get a download URL for an image.

def Collection2ImageTest():
    collection = ee.ImageCollection('L7_L1T')
    logging.info('collection type %s', type(collection)) # logs <class 'ee.imagecollection.ImageCollection'>
    
    collection2 =  collection.filterBounds(park_boundary).filterDate(start_date, end_date)
    logging.info('collection2 type %s', type(collection2)) # logs <class 'ee.imagecollection.ImageCollection'>
    
    collection3 = collection2.median() #.sort('system:time_start', False)
    logging.info('collection3 type %s', type(collection3)) # logs <class 'ee.collection.Collection'>
    
    collection4 = collection2.limit(2)
    logging.info('collection4 type %s', type(collection4)) # logs <class 'ee.collection.Collection'>
    
    
def getLatestLandsat_Visible(boundary_polygon):
    
    park_boundary = ee.FeatureCollection([
    ee.Feature(
        ee.Feature.Polygon(boundary_polygon),
        {'name': 'areaName', 'fill': 1}),
    ])
    #logging.info('park_boundary %s', park_boundary)
   
    end_date   = datetime.datetime.today()
    secsperyear = 60 * 60 * 24 * 365 #  365 days * 24 hours * 60 mins * 60 secs
    start_date = end_date - datetime.timedelta(seconds=3 * secsperyear )
    #logging.debug('start:%s, end:%s, fc %s',start_date,  end_date, fc)
        
    mycollection = ee.ImageCollection('L7_L1T').filterBounds(park_boundary).filterDate(start_date, end_date)
    sortedCollection = ee.ImageCollection(ee.ImageCollection(mycollection.sort('system:time_start', False )).limit(2)) #note cast to ee,ImageCollection() resolves bug in sort() for ee ver 0.13
    #logging.info('Collection description : %s', sortedCollection.getInfo())
        
    scenes  = sortedCollection.getInfo() #.features
    #logging.info('Scenes: %s', sortedCollection)
    
    for feature in scenes['features']:
        id = feature['id']
        #logging.info('Scene id: %s, %s', id, i)
        image = ee.Image(id)
        props = image.getInfo()['properties']
        #logging.info('impage properties: %s', props)
        
        path    = props['WRS_PATH']
        row     = props['STARTING_ROW']
        #datestr = props['system:time_start']
        system_time_start= datetime.fromtimestamp(props['system:time_start'] / 1000)
        #why two? datatime.datetime?        
        date_format_str = "%Y-%m-%d @ %H:%M"
        date_str = system_time_start.strftime(date_format_str)

        logging.info('getLatestLandsat_Visible id: %s, path: %s, row: %s, date:%s', id, path, row, fdate)
        
        #Select the visible red, green and blue bands.
        map = image.getMapId({'bands': '30, 20, 10', 'gain': '1.4, 1.4, 1.1'})
        #logging.info('map: %s', map )
        
        #addToMap(image.select('30', '20', '10') /*.clip(fc)*/, {gain: '1.4, 1.4, 1.1'});
        #img= medianImage.select(["30", "20", "10"]);
        #img =  landsat_collection.getMapId(image.select('30', '20', '10'), {gain: '1.4, 1.4, 1.1'})
        #colour_image = sortedLandsatCollection.mosaic().select('40', '30', '20')
        path = image.getDownloadUrl({
            'scale': 30,
            'crs': 'EPSG:4326',
            'region': boundary_polygon,
            'format': 'png'
        })
        return path
    
########################################

#unit test
initEarthEngineService()
#test 1
coords = [[-109.05, 41], [-109.05, 37], [-102.05, 37], [-102.05, 41]]
getLatestLandsat_Visible(coords)

#test 2
fc = ee.FeatureCollection('ft:1urlhdLW2pA66f2xS0yzmO-LaESYdclD7-17beg0') #Yarra Ranges N.P.
getLatestLandsat_Visible(fc)

