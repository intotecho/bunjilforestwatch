'''
Created on 25/05/2013
@author: cgoodman
'''

import sys
import logging
logging.basicConfig(level=logging.DEBUG)



#import PIL
#from PIL import ImageTk
#from PIL import TKInter

import settings
import oauth2client.client
import datetime

#from oauth2client.appengine import AppAssertionCredentials
#SCOPES = ('https://www.googleapis.com/auth/earthengine.readonly')
#credentials = AppAssertionCredentials(scope=SCOPES)
#scopes = [
#  'https://www.googleapis.com/auth/earthengine.readonly' #,
  #'https://www.googleapis.com/auth/earthbuilder.readonly'
#]
#scopes = ' '.join(scopes) 

import ee
#import pycrypto
#from PyCryptoSignedJWT import PyCryptoSignedJwtAssertionCredentials



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
def testGetImage():
    image1 = ee.Image('srtm90_v4')
    path = image1.getDownloadUrl({
    'scale': 30,
    'crs': 'EPSG:4326',
    'region': '[[-120, 35], [-119, 35], [-119, 34], [-120, 34]]'
    })
    print path
    info = image1.getInfo()
    print info

def getYarraFeatures():
    fc = ee.FeatureCollection('ft:1urlhdLW2pA66f2xS0yzmO-LaESYdclD7-17beg0');
    #print fc.getInfo()


def getLatestLandsat():
    park_boundary = ee.FeatureCollection('ft:1urlhdLW2pA66f2xS0yzmO-LaESYdclD7-17beg0');
    end_date   = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(seconds=3 * 60 * 60 * 24 * 365)    
    landsat_collection = ee.ImageCollection('L7_L1T').filterBounds(park_boundary).filterDate(start_date, end_date)
    sortedLandsatCollection = landsat_collection.sort('system:time_start', False).limit(2);
    #print sortedLandsatCollection.getInfo()
    #scenes  = sortedLandsatCollection.features(); 
    #for i in range(0, scenes.length):
    #    id = scenes[i].id;
    #    print( "SceneID: ", id );

#
#unit test
initEarthEngineService()
#testGetImage()
#getYarraFeatures()
getLatestLandsat()
#drawFirstMap()


#Example of logging a Landsat time property in a human-readable format.  Landsat metadata times are recorded as milliseconds since 00:00:00 UTC on 1 January 1970.
#console.log(
#  'system:time_start :',
 # (new Date(myimage.getInfo().properties['system:time_start'])).toGMTString()
#)

