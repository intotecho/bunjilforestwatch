"""
#Wrappers for Earth Engine Routines Commenced 25/05/2013
@author: cgoodman can be shared.
# Copyright (c) 2013-14 Chris Goodman <bunjilforestwatch@gmail.com>
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

import logging
import gladalerts

from google.appengine.ext import db # is it required?

import cache
#from models import Observation # only required for Observations model.
import models

import os
#logging.debug('PYTHONPATH: %s',os.environ['PYTHONPATH'])
#logging.debug('HTTP_PROXY: %s',os.environ['HTTP_PROXY'])
#logging.debug('HTTPS_PROXY: %s',os.environ['HTTPS_PROXY'])

#from oauth2client.contrib.appengine import AppAssertionCredentials
from oauth2client import util # to disable positional parameters warning.

import datetime
import json
import settings #You have to import your own private keys. 
import ee
import oauth2client.client
from google.appengine.api import urlfetch #change timeout from 5 to 60 s. https://stackoverflow.com/questions/13051628/gae-appengine-deadlineexceedederror-deadline-exceeded-while-waiting-for-htt
from ee.oauthinfo import OAuthInfo

#from oauth2client.service_account import ServiceAccountCredentials

# from http://stackoverflow.com/questions/3086091/debug-jinja2-in-google-app-engine/3694434#3694434
PRODUCTION_MODE = not os.environ.get(
    'SERVER_SOFTWARE', 'Development').startswith('Development')
    

'''
initEarthEngineService()
Call once per session to authenticate to EE
SERVER_SOFTWARE: In the development web server, this value is "Development/X.Y" where "X.Y" is the version of the runtime. 
When running on App Engine, this value is "Google App Engine/X.Y.Z".

'''
def reallyinitEarthEngineService():
    util.positional_parameters_enforcement = util.POSITIONAL_IGNORE   # avoid the WARNING [util.py:129] new_request() takes at most 1 positional argument (4 given)
    OAuthInfo.SCOPE += ' https://www.googleapis.com/auth/fusiontables.readonly'
    OAuthInfo.SCOPE += ' https://www.googleapis.com/auth/fusiontables'
    OAuthInfo.SCOPE += ' https://www.googleapis.com/auth/drive'
    OAuthInfo.SCOPE += ' https://www.googleapis.com/auth/drive.file'
    try:
        if os.environ['SERVER_SOFTWARE'].startswith('Development'): 
            logging.info("Initialising Earth Engine authenticated connection from devserver")
            try:  
                acct = os.environ['MY_SERVICE_ACCOUNT']
                key = os.environ['MY_PRIVATE_KEY_FILE']
            except KeyError: 
                logging.warning("Environment variable MY_SERVICE_ACCOUNT and MY_PRIVATE_KEY_FILE not set. Using settings.py")
                logging.debug (os.environ)
                acct = settings.MY_LOCAL_SERVICE_ACCOUNT
                key = settings.MY_LOCAL_PRIVATE_KEY_FILE
            
            EE_CREDENTIALS = ee.ServiceAccountCredentials(acct, key)
        else:
            logging.info("Initialising Earth Engine authenticated connection from App Engine")
            EE_CREDENTIALS = AppAssertionCredentials(OAuthInfo.SCOPE)
            #EE_CREDENTIALS= ServiceAccountCredentials.from_json_keyfile_name(key, OAuthInfo.SCOPE)

        ee.Initialize(EE_CREDENTIALS) 
        #print EE_CREDENTIALS
        # permit long wait for response from earth engine
        #urlfetch.set_default_fetch_deadline(60000)
        return EE_CREDENTIALS
    except TypeError, e: #Exception, e:
        logging.error("Failed to connect to Earth Engine Google API. Exception: %s", e)
        return False

class EarthEngineService():

    #this will call reallyinitEarthEngineService() when module is imported.  
    #logging.info("Init class EarthEngineService")
    earthengine_intialised = False
    credentials = None
    
    @staticmethod
    def isReady():
        if not EarthEngineService.earthengine_intialised:
            #logging.info("Initialising EarthEngineService ...")
            EarthEngineService.earthengine_intialised = True
            EarthEngineService.credentials = reallyinitEarthEngineService()
        else:
            if not PRODUCTION_MODE:
                logging.debug("Dev: EarthEngineService is Ready")
                
        return EarthEngineService.earthengine_intialised



#to maintain backward compatibility with existing calls ...
def initEarthEngineService():
    return EarthEngineService.isReady()
                                      

'''
checkForNewObservationInCell() checks the collection for the latest image and compares it to the last stored. 
    If a newer image is found, the observation is added and the function returns True.
    If no new image is found, the function returns False. 
    An error is logged if no images are found. 
    If no observation exists, one is created.
'''
def checkForNewObservationInCell(area, cell, collection_name):
    #poly = [] #TODO Move poly to a method of models.AOI
    #//for geopt in area.coordinates:
    #//    poly.append([geopt.lon, geopt.lat]) 
        
    params = {'path':cell.path, 'row':cell.row}
    #print 'area', area, ' params: ', params
    latest_image = getLatestLandsatImage(area.get_boundary_hull_fc(), collection_name, 0, params) # most recent image for this cell in the collection
    if latest_image is not None:
        storedlastObs = cell.latestObservation(collection_name)
        if storedlastObs is None or latest_image.system_time_start > storedlastObs.captured: #captured_date = datetime.datetime.strptime(map_id['date_acquired'], "%Y-%m-%d")
            
            obs = models.Observation(parent=cell.key, image_collection=collection_name, captured=latest_image.system_time_start, image_id=latest_image.name, obs_role="latest")
            obs.put()
            if storedlastObs is None:
                logging.debug('checkForNewObservationInCell FIRST observation for %s %s %s %s', area.name, collection_name, cell.path, cell.row)
            else:
                logging.debug('checkForNewObservationInCell NEW observation for %s %s %s %s', area.name, collection_name, cell.path, cell.row)
                
            return obs
        else:
            logging.debug('checkForNewObservationInCell no newer observation for %s %s %s %s', area.name, collection_name, cell.path, cell.row)
            return None
    else:
        logging.error('checkForNewObservationInCell no matching image in collection %s %s %s %s', area.name, collection_name, cell.path, cell.row)
        return None
    return None

'''
getLatestLandsatImage(eeFeatureCollection, string as name of ee.imagecollection)

    returns the 'depth' latest image from the collection that overlaps the boundary coordinates.
    Could also clip the image to the coordinates to reduce the size.
    return type is ee.Image(). Some non-ee attributes are appended to the object.
        capture_date, is a string rep of the system_date.
'''
secsperyear = 60 * 60 * 24 * 365 #  365 days * 24 hours * 60 mins * 60 secs

def getLatestLandsatImage(park_boundary, collection_name, latest_depth, params):
    #feat = boundary_hull_fc.buffer(0, 1e-10) # buffer will force polygon to be CCW so search intersects with interior.
    #logging.info('feat %s', feat)
    #boundary_feature = ee.Feature(feat, {'name': 'areaName', 'fill': 1})
    #park_boundary = ee.FeatureCollection(boundary_feature)
    
    end_date   = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(seconds = 1 * secsperyear/2 )
    #logging.debug('getLatestLandsatImage() start:%s, end:%s ',start_date,  end_date)
    #logging.debug('getLatestLandsatImage() park boundary as FC %s ',park_boundary)

    image_collection = ee.ImageCollection(collection_name)

    if ('path' in params) and ('row' in params): 

        path = int(params['path'])
        row = int(params['row'])
        logging.debug("filter Landsat Collection by Path=%d Row=%d and date", path, row)
        resultingCollection = image_collection.filterBounds(park_boundary).filterDate(start_date, end_date).filterMetadata('WRS_PATH', 'equals', path).filterMetadata('WRS_ROW', 'equals', row)#) #latest image form this cell.
    else:
        logging.debug("filter Landsat Collection by date and bounds only")
        resultingCollection = image_collection.filterDate(start_date, end_date).filterBounds(park_boundary) # latest image from any cells that overlaps the area. 
    
    sortedCollection = resultingCollection.sort('system:time_start', False )
    #logging.debug('sortedCollection: %s', sortedCollection)
    scenes = sortedCollection.getInfo()

    try:
        feature = scenes['features'][int(latest_depth)]
    except IndexError:
        try:
            feature = scenes['features'][0]
        except IndexError:
            logging.warning("No Scenes in Filtered Collection")
            logging.debug("scenes: ", scenes)
            return None
 
    iid = feature['id']   
    logging.info('getLatestLandsatImage found scene: %s', iid)
    latest_image = ee.Image(iid)
    urlfetch.set_default_fetch_deadline(120000)

    ee.data.setDeadline(60000)

    props = latest_image.getInfo()['properties'] #logging.info('image properties: %s', props)
    system_time_start= datetime.datetime.fromtimestamp(props['system:time_start'] / 1000) #convert ms
    date_str = system_time_start.strftime("%Y-%m-%d @ %H:%M")

    if ('path' in params) and ('row' in params): 
        logging.info('getLatestLandsatImage id: %s, date:%s latest for [%d,%d] :%s, ', iid, date_str, path, row, latest_depth, )
    else:
        logging.info('getLatestLandsatImage id: %s, date:%s latest:%s', iid, date_str, latest_depth )
    
    # add some properties to Image object to make them easier to retrieve later.
    latest_image.name = iid
    latest_image.capture_date = date_str
    latest_image.system_time_start = system_time_start
    
    return latest_image  #.clip(park_boundary)



'''
getLandsatImageById(collection_name,image_id, algorithm )

'''

def getLandsatImageById(collection_name,image_id, algorithm):

    image = ee.Image(image_id)
    props = image.getInfo()['properties'] #logging.info('image properties: %s', props)
    
    system_time_start = datetime.datetime.fromtimestamp(props['system:time_start'] / 1000) #convert ms
    date_str = system_time_start.strftime("%Y-%m-%d @ %H:%M")

    logging.info('getLandsatImageById id: %s, date:%s', image_id, date_str)
    # add some properties to Image object to make them easier to retrieve later.
    image.name = image_id
    image.capture_date = date_str
    image.system_time_start = system_time_start
    
    return visualizeImage(collection_name, image, algorithm)


def getQABits(image, start, end, newName):
    # Compute the bits we need to extract.
    pattern = 0
    for i in range (start, end): 
        #pattern += math.pow(2, i) 
        pattern += 2**i
    return image.select([0], [newName]).bitwise_and(pattern).right_shift(start)
                  

def L8AddQABands(image) :
    # Landsat 8 QA Band ref: http:#landsat.usgs.gov/L8QualityAssessmentBand.php
    # Select the Landsat 8 QA band.
    QABand = image.select('BQA')
    image = image.addBands(getQABits(QABand, 4, 5, "WaterConfidence")) 
    image = image.addBands(getQABits(QABand, 10, 11, "SnowIceConfidence")) 
    image = image.addBands(getQABits(QABand, 12, 13, "CirrusConfidence")) 
    image = image.addBands(getQABits(QABand, 14, 15, "CloudConfidence"))
    return image

# cloud masking function
def L8Cloudmask(image):
    # Select the Landsat 8 QA band.
    QABand = image.select('BQA')
    # Create a binary mask based on the cloud quality bits (bits 14&15).
    cirrusBits = getQABits(QABand, 12, 13, "CirrusConfidence")
    cloudBits = getQABits(QABand, 14, 15, "CloudConfidence")
    cloudMask = (cloudBits.eq(1)).And(cirrusBits.eq(1))
    return cloudMask

def maskL8(image):
    mask = L8Cloudmask(image)
    maskedImage = image.mask(mask)
    return maskedImage

def add_date(image):
    timestamp = image.metadata('system:time_start')
    return image.addBands(timestamp)

'''
 SimpleCloudScore, an example of computing a cloud-free composite with L8
 by selecting the least-cloudy pixel from the collection.
'''

# A mapping from a common name to the sensor-specific bands.

LC8_BANDS = ['B2',   'B3',    'B4',  'B5',  'B6',    'B7',    'B10']
STD_NAMES = ['blue', 'green', 'red', 'nir', 'swir1', 'swir2', 'temp']

#Compute a cloud score.  This expects the input image to have the common
# band names: ["red", "blue", etc], so it can work across sensors.

def rescale(img, exp, thresholds): 
    return img.expression(exp, {'img': img}).subtract(thresholds[0]).divide(thresholds[1] - thresholds[0])

def cloudScore (img): 
    # A helper to apply an expression and linearly rescale the output.
    #Compute several indicators of cloudyness and take the minimum of them.
    score = ee.Image(1.0)

    #Clouds are reasonably bright in the blue band.
    score = score.min(rescale(img, 'img.blue', [0.1, 0.3]))

    #Clouds are reasonably bright in all visible bands.
    score = score.min(rescale(img, 'img.red + img.green + img.blue', [0.2, 0.8]))

    #Clouds are reasonably bright in all infrared bands.
    score = score.min( rescale(img, 'img.nir + img.swir1 + img.swir2', [0.3, 0.8]))

    #Clouds are reasonably cool in temperature.
    score = score.min(rescale(img, 'img.temp', [300, 290]))

    #However, clouds are not snow.
    ndsi = img.normalizedDifference(['green', 'swir1'])
    
    #return score.min(rescale(ndsi, 'img', [0.8, 0.6]))
    return score.min(rescale(ndsi, 'img', [0.8, 0.6]))

def cloud_invert(img):
    score1 = cloudScore(img.select(LC8_BANDS, STD_NAMES))
    score = ee.Image(1).subtract(score1).select([0], ['cloudscore'])
    return img.addBands(score)
    
def simpleCloudScoreOverlay():

    # TEST HARNESS
    collection = ee.ImageCollection('LC8_L1T_TOA').filterDate('2013-05-01', '2013-07-01').map(cloud_invert)
    #print (collection)
    
    cloudfree =  collection.qualityMosaic('cloudscore') #extract latest pixel
    
    vizParams = {'bands': 'B4,B3,B2', 'max': 0.4, 'gamma': 1.6}
    
    display(mymap)
    
    mymap.center(-120.24487, 37.52280, 8);
    
    mymap.addLayer(
        image = cloudfree,
        vis_params = vizParams,           
        name = "SimpleCloudFree"
    )    
    return 

#simpleCloudScoreOverlay()

'''
getPriorLandsatOverlay(obs)
#Based on https://ee-api.appspot.com/ ->Scripts -> Simple Cloud Score
'''

def getPriorLandsatOverlay(obs):

    ref_image = ee.Image(obs.image_id)
    props = ref_image.getInfo()['properties'] #logging.info('image properties: %s', props)
    path = props['WRS_PATH']
    row = props['WRS_ROW']
    
    system_time = datetime.datetime.fromtimestamp((props['system:time_start'] / 1000) -3600) #convert ms
    date_str = system_time.strftime("%Y-%m-%d @ %H:%M")

    before     = obs.captured - datetime.timedelta(days=1)
    earliest   = obs.captured - datetime.timedelta(days=(3*365))
    before_str   = before.strftime("%Y-%m-%d")
    earliest_str = earliest.strftime("%Y-%m-%d")
    
    logging.info('getPriorLandsatOverlay() id: %s, captured:%s from %s to :%s %d/%d', obs.image_id, date_str, earliest_str, before_str, path, row)
    
    collection = ee.ImageCollection('LC8').filterDate(earliest, before).filterMetadata('WRS_PATH', 'equals', path).filterMetadata('WRS_ROW', 'equals', row).filterMetadata('default:SUN_ELEVATION', 'GREATER_THAN', 0).map(cloud_invert)
                                             
    image_object =  collection.qualityMosaic('cloudscore') #extract latest pixel
    
    #crs = image_object.getInfo()['bands'][0]['crs']
    
    #pcdict = getPercentile(image_object, [5,95], crs)
    #imin = str(100 * pcdict['B4_p5']) + ', '  + str(100 * pcdict['B3_p5'])  + ', ' + str(100 * pcdict['B2_p5'])
    #imax = str(100 * pcdict['B4_p95']) + ', ' + str(100 * pcdict['B3_p95']) + ', ' + str(100 * pcdict['B2_p95'])
    #logging.debug('Prior Percentiles  5%% %s 95%% %s', imin, imax)
    

    rgbVizParams = {'bands': 'B4,B3,B2', 'min':5000, 'max':30000, 'gamma': 1.2, 'format': 'png'}
    #rgbVizParams = {'bands': 'B4,B3,B2', 'max':0.4, 'gamma': 1.2, 'format': 'png'}
    
    return  image_object.getMapId(rgbVizParams)

def getPriorLandsatOverlay_oldalgorithm(obs):

    ref_image = ee.Image(obs.image_id)
    props = ref_image.getInfo()['properties'] #logging.info('image properties: %s', props)
    path = props['WRS_PATH']
    row = props['WRS_ROW']
    
    system_time = datetime.datetime.fromtimestamp((props['system:time_start'] / 1000) -3600) #convert ms
    date_str = system_time.strftime("%Y-%m-%d @ %H:%M")

    before     = obs.captured - datetime.timedelta(days=1)
    earliest   = obs.captured - datetime.timedelta(days=(3*365))
    before_str   = before.strftime("%Y-%m-%d")
    earliest_str = earliest.strftime("%Y-%m-%d")
    
    logging.info('getPriorLandsatOverlay() id: %s, captured:%s from %s to :%s %d/%d', obs.image_id, date_str, earliest_str, before_str, path, row)
    
    resultingCollection = ee.ImageCollection('LC8').filterDate(earliest, before).filterMetadata('WRS_PATH', 'equals', path).filterMetadata('WRS_ROW', 'equals', row).filterMetadata('default:SUN_ELEVATION', 'GREATER_THAN', 0)
    
    # Optional step that adds QA bits as separate bands to make it easier to debug.
    collectionUnmasked = resultingCollection.map(add_date).map(L8AddQABands)
   
    collectionMasked = collectionUnmasked.map(maskL8) #mask out cloud affected pixes
    
    image_object = collectionMasked.qualityMosaic('system:time_start') #extract latest pixel
    
    #[method for method in dir(image_object) if not method.startswith('_')] # print all methods in ee object.

    crs = image_object.getInfo()['bands'][0]['crs']
    pcdict = getPercentile(ref_image, [5,95], crs)
    
    imin  = str(100 * pcdict['B4_p5']) + ', '  + str(100 * pcdict['B3_p5'])  + ', ' + str(100 * pcdict['B2_p5'])
    imax = str(100 * pcdict['B4_p95']) + ', ' + str(100 * pcdict['B3_p95']) + ', ' + str(100 * pcdict['B2_p95'])
    logging.debug('Prior Percentiles  5%% %s 95%% %s', imin, imax)
    
    #rgbVizParams = {'bands': 'B4,B3,B2', 'min':5000, 'max':30000, 'gamma': 1.6, 'format': 'png'}
    rgbVizParams = {'bands': 'B4,B3,B2', 'min':imin, 'max':imax, 'gamma': 1.6, 'format': 'png'}
    
   
    
    return  image_object.getMapId(rgbVizParams)

#B9_THRESHOLD = 4200 #originally  5200

'''
    SharpenLandsat7HSVUpres()
    
    Pan Sharpening is an image fusion method in which high-resolution panchromatic data is fused with lower resolution multispectral data 
    to create a colorized high-resolution dataset. The resulting product should only serve as an aid to literal analysis and not for further spectral analysis

    References: http://landsat.usgs.gov/panchromatic_image_sharpening.php
                Javascript Example https://ee-api.appspot.com/b38107da4a6c487a706b860ec41d9dc9
        
'''
def SharpenLandsat7HSVUpres(image):
        
        logging.debug ('SharpenLandsat7HSVUpres: image.getInfo() %s', image.getInfo())
        # Grab a sample L7 image and pull out the RGB and pan bands
        # in the range (0, 1).  (The range of the pan band values waschosen to roughly match the other bands.)
        rgb = image.select(['B3', 'B2', 'B1']).unitScale(0, 255) #Select the visible red, green and blue bands. # was 30, 40 50 on old collection nanme
        pan = image.select(['B8']).unitScale(0, 155) # was 80 on old colleciton name.

        #Convert to HSV, swap in the pan band, and convert back to RGB.
        huesat = rgb.rgbtohsv().select(['hue', 'saturation'])
        upres = ee.Image.cat(huesat, pan).hsvtorgb()  
        byteimage = upres.multiply(255).byte()
        newImage = image.addBands(byteimage); #keep all the metadata of image, but add the new bands.
        return(newImage)

def SharpenLandsat8HSVUpres(image):
        #Convert to HSV, swap in the pan band, and convert back to RGB. 
        #Javascript Example from https://ee-api.appspot.com/#5ea3dd541a2173702cfe6c7a88346475
        #Pan sharpen Landsat 8
        rgb = image.select("B4","B3","B2")
        pan = image.select("B8")
        huesat = rgb.rgbtohsv().select(['hue', 'saturation'])
        upres = ee.Image.cat(huesat, pan).hsvtorgb()  
        byteimage = upres.multiply(255).byte()
        newImage = image.addBands(byteimage); #keep all the metadata of image, but add the new bands.
        return(newImage) 


###################################
# getPercentile(image, percentile, crs)
#
# Return the percentile values for each band in an image.
# 
# If percentile is passed as[5,95] then this will calculate the 5% and 95% values for each band in a Landsat image.
# We use these to construct visualization parameters for displaying the image. Mainly interested in RGB but all bands are returned.
#
# Example on groups list: August 8, 2013
#
#===============================================================================

def getPercentile(image, percentile, crs):
    return image.reduceRegion(
        ee.Reducer.percentile(percentile), # reducer
        None, # geometry (Defaults to the footprint of the image's first band)
        1000, # scale (Set automatically because bestEffort == true)
        crs,
        None, # crsTransform,
        True  # bestEffort
        ).getInfo()

def getL8LatestNDVIImage(image):
    NDVI_PALETTE = {'FF00FF','00FF00'}
    ndvi = image.normalizedDifference(["B4", "B3"]).median();   
    
    newImage = image.addBands(ndvi); #keep all the metadata of image, but add the new bands.
    logging.debug('getL8NDVIImage:%s ', newImage)

    mapparams = {    #'bands':  'red, green, blue', 
                     'min': -1,
                     'max': 1,
                     'palette': 'FF00FF, 00FF00',
                     #'gamma': 1.2,
                     'format': 'png'
                }   
    mapid  = ndvi.getMapId(mapparams)
  
    # copy some image props to mapid for browser to display
    info = image.getInfo() #logging.info("info", info)
    props = info['properties']
    mapid['date_acquired'] = props['DATE_ACQUIRED']
    mapid['id'] = props['system:index']
    mapid['path'] = props['WRS_PATH']
    mapid['row'] = props['WRS_ROW']
    return mapid


def getVisualMapId(image, red, green, blue):
    #original image is used for original metadata lost in image so caller must keep a reference to the image
    crs = image.getInfo()['bands'][0]['crs']
    
    #print 'crs: ' + crs
    
    pcdict = getPercentile(image, [5,95], crs)
  
    min = str(pcdict['red_p5']) + ', '  + str(pcdict['green_p5'])  + ', ' + str(pcdict['blue_p5'])
    max = str(pcdict['red_p95']) + ', ' + str(pcdict['green_p95']) + ', ' + str(pcdict['blue_p95'])
    logging.debug('Percentiles  5%% [%s] 95%% [%s]', min, max)
    
    # Define visualization parameters, based on the image statistics.
    mapparams = {    'bands':  'red, green, blue', 
                     'min': min,
                     'max': max,
                     'gamma': 1.2,  #was 1.2
                     'format': 'png'
                }   
    mapid  = image.getMapId(mapparams)
    return mapid

def getThumbnailPath(image): # Function Not Used.

        crs = image.getInfo()['bands'][0]['crs']
        imgbands = image.getInfo()['bands']
        for b in imgbands:
            print b
        p05 = []
        p95 = []
        p05 = getPercentile(image, 5, crs)
        p95 = getPercentile(image, 95, crs)
        print('Percentile  5%: ', p05)
        print('Percentile 95%: ', p95)
        
        red = 'red'
        green = 'green'
        blue = 'blue'
        bands1 = [  {u'id': red},
                    {u'id': green},
                    {u'id': blue}   ]
        
        thumbnail_params = {
                     'bands': json.dumps(bands1),
                     #'crs': crs,
                     'format': 'png',
                     'size' : 2000,
                     'min': p05,
                     'max': p95,         
                     #'min': [p05['red'], p05['green'], p05['blue']],
                     #'max': [p95['red'], p95['green'], p95['blue']],                 
                     'gamma': 1.2,
                     }
        
        thumbpath = image.getThumbUrl(thumbnail_params)
        logging.info('thumbnail url: %s', thumbpath)
        return thumbpath

# Get a download URL for a GeoTIFF overlay.
def getOverlayPath(image, prefix, red, green, blue):

    crs = image.getInfo()['bands'][0]['crs']
    #imgbands = image.get('bands')
    
    p05 = []
    p95 = []
    p05 = getPercentile(image, 5, crs)
    p95 = getPercentile(image, 95, crs)
    # Print out the image ststistics.
    #print('Percentile  5%: ', p05)
    #print('Percentile 95%: ', p95)

    bands1 = [     {u'id': red},
                   {u'id': green},
                   {u'id': blue}   ]
    
    # Define visualization parameters, based on the image statistics.
    dt = datetime.datetime.now()
    filename = dt.strftime(prefix + "_%a%Y%b%d_%H%M")
    print filename
    visparams = {'name': filename,
                     'bands':  json.dumps(bands1), # none of the above work.
                     #'crs': crs,
                     #'format': 'png',
                     'min': p05,
                     'max': p95,
                     'gamma': 1.2,
                     #'scale': 30,
                     #'gain':  0.1, 
                     #'region' : boundary_polygon,    
                     'filePerBand' : False
                }   
    path      = image.getDownloadUrl(visparams) #deprecated
    logging.info('getOverlayPath: %s',       path)
    return path

'''
visualizeImage()
parameters:
    collection_name - name of EE image collection LANDSAT/LC8_L1T_TOA or LANDSAT/LE7_L1T
    image -  returned by ee.Image.
    algorithm: - What visualisation of the image to return
            'rgb' - visual
            'ndvi' - NDVI
    depth:
        0 return the latest image in the collection 
        1 return the image before that.
        2 return the image before 1. 

Returns an earth engine mapid that can be displayed on a google map with additional attributues from the ee.Image object:

'''
def visualizeImage(collection_name, image, algorithm):
    if algorithm is None:
        algorithm = 'rgb'
    if collection_name == 'LANDSAT/LC8_L1T_TOA' :
        if algorithm.lower() == 'rgb':
            sharpimage = SharpenLandsat8HSVUpres(image)
            red = 'red'
            green = 'green'
            blue = 'blue'    
            #path = getOverlayPath(sharpimage, "L8TOA", red, green, blue)
            mapid = getVisualMapId(sharpimage, red, green, blue)
            info = image.getInfo() #logging.info("info", info)
            #print info
            props = info['properties']
            mapid['date_acquired'] = props['DATE_ACQUIRED']
            mapid['capture_datetime'] = image.system_time_start
            mapid['id'] = props['system:index']
            mapid['path'] = props['WRS_PATH']
            mapid['row'] = props['WRS_ROW']
            mapid['collection'] = collection_name
            
            return mapid
        elif algorithm.lower() == 'ndvi':
            print "l8 ndvi not implemented"
            return None
            
    elif collection_name == 'LANDSAT/LE7_L1T':  #Old name was 'LANDSAT/L7_L1T' 
        if algorithm.lower() == 'rgb':
            sharpimage = SharpenLandsat7HSVUpres(image) #doesn't work with TOA.
            red   = 'red'
            green = 'green'
            blue  = 'blue'    
            mapid = getVisualMapId(sharpimage, red, green, blue)
            props = image.getInfo()['properties'] 
            #props = info['properties']
            mapid['date_acquired'] = props['DATE_ACQUIRED']
            mapid['id'] = props['system:index']
            mapid['path'] = props['WRS_PATH']
            mapid['row'] = props['WRS_ROW']
            mapid['collection'] = collection_name
            mapid['capture_datetime'] = image.system_time_start
            
            return mapid
        
        elif algorithm.lower() == 'ndvi':
            print "l7 ndvi not implemented"
            return None


def getLandsatOverlay(boundary_fc, satellite, algorithm, depth, params):
    if satellite.lower() == 'l8':
        collection_name = 'LANDSAT/LC8_L1T_TOA'
    elif satellite.lower() == 'l7':
        collection_name = 'LANDSAT/LE7_L1T'  #Old name was 'LANDSAT/L7_L1T' 
    else:
        logging.error('getLandsatOverlay() collection %s not recognised defaulting to L8', satellite.lower())  
        collection_name = 'LANDSAT/LC8_L1T_TOA'

    image = getLatestLandsatImage(boundary_fc, collection_name, depth, params)
    
    if not image:
        logging.error('getLatestLandsatImage() no image found')
        return 0
    return visualizeImage(collection_name, image, algorithm)

        
'''
getPathRow returns max or min value of the sort_property in a collection.
#FIXME - THis has a bug. It is not returning the expected values. However, I am no longer using it. So low priority.
Example:
    max_path = getPathRow(boundCollection,"WRS_PATH", False)
    min_path = getPathRow(boundCollection,"WRS_PATH", True)
    max_row  = getPathRow(boundCollection,"WRS_ROW", False)
    min_row  = getPathRow(boundCollection,"WRS_ROW", True)
'''
def getPathRow(collection, sort_property, ascending):
    limited_collection_info = (collection.limit(1, sort_property, ascending).getInfo())        
    try:
        max_prop = limited_collection_info['features'][0]['properties'][sort_property]
        return max_prop
    except IndexError:
        logging.error('getPathRow(): Index Exception %s %s', sort_property, ascending)
        return -1

#determine the overlapping cells from the image collection returned and store them in area.cells.
'''
getLandsatCells() is given an AreaOfInterest and returns a list of overlapping cells (Landsat Swathes).

  parameters: area, and AreaOfInterest.
  
  Normally, this function is only called once for an area whe it does not have any cells in its cellList.
  Otherwise, duplicate cells may be created.
  
  The function first extracts its boundary.
  
  Then it calls earth engine to generate a collection of L7 images from the last 2 years.
  It queries the collection for the images with the min and max paths and min and max row. This includes cells that don't overlap the area.
  It then loops through each path and row within these bounds to check for an image with that path row combination.
  If found, then the path/row cell overlaps the area and is added to the cells list.
  It returns the cell list as well as setting the max and min coordinates.
  If there has never been an image collected in 2 years, then that cell will be missing.
  
  Once the intersecting path/rows are collected, the function loops through each overlapping given path/row
      it gets an image. 
       then calculate the intersection of the cell with the area's boundary.
       if percentage is min threshold (say 50% of image area) then default-select the cell.
       if percentage is below then deselect cell from auto-monitoring.
       Lastly find any area that is not intersected by any selected cell and find a cell that intersects it.

    @TODO: Could add the latest observation here. First sort in reverse date order.#obs = image_info['properties']['system_date']
    @TODO: There is a more efficient way of getting the list of overlapping cells for an area - with a get distinct query. 
'''
def getLandsatCells(area):
    
    # Test if area already has cellList
    if len(area.cells) != 0 :
        logging.error("getLandsatCells() - deleting area's existing list of %s cells", area.cells)
        area.delete_cells()
    
    # Get the area's boundary or location and convert to a FeatureCollection.    
    fc = area.get_boundary_hull_fc()
    park_geom = fc.geometry()
    park_area = park_geom.area(100).getInfo()

    if park_area < 10 : # no boundary defined.
        logging.warning("getLandsatCells() - No Park Area %d", park_area)
        park_area = 10

     #print "getLandsatCells():", park_area, park_geom
        
    # Get an imageCollection of all L7 images from recent years that overlap the area, load just the image metadata ['features'].
    end_date   = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(weeks = 104) # last 2 years.
    boundCollection = ee.ImageCollection('LANDSAT/LE7_L1T').filterBounds(fc).filterDate(start_date, end_date) #.sort('system:time_start', False )
    features = boundCollection.getInfo()['features']
    
    logging.info('getLandsatCells() %s', features)
    #Find one of each cell (p,r) in collection. Calculate and store how much of the park the cell overlaps and add it to a tmp list.
    cellList = [] #local array of unique cells will be later stored in area.cellList.
    
    for image_info in features:
        p = int(image_info['properties']['WRS_PATH'])
        r = int(image_info['properties']['WRS_ROW'])
        cell_name=str(p*1000+r)
        #if not cell_name in cellnames:
        if not any(c.key.string_id() == cell_name for c in cellList):
            try:
                image_id= image_info['properties']['system:index']
                image = ee.Image(image_id)
                image_geom = image.geometry() # should be relatively constant
                overlap_geom = image_geom.intersection(park_geom, 10)
                overlap_area  = overlap_geom.area(10).getInfo()
            except Exception, e:
                logging.error("findcell exception {0!s}".format(e)) #Image not found?
                continue
            overlap = overlap_area/park_area 
           
            cell = models.LandsatCell(parent=area.key, id=cell_name, aoi=area.key, path=p, row=r, monitored=False , overlap=overlap, image_id=image_id)
            cellList.append(cell)
            
        else:
            pass  # found a duplicate, skipping
    
    # Now we have a list of cells, before we store them work out which ones should default to monitored?
        
    # Sort the cellList so that cells which overlap the largest area of the park are first.
    
    cellList.sort(key=lambda x: x.overlap, reverse=True)
        
    remaining_geom = park_geom #Each time a cell is selected, it's footprint is removed from the park.
    remaining_area = park_area   #When zero, the whole park has been covered.


    for cell in cellList:
        if remaining_area > 0: # select more cells
            try:
                image = ee.Image(cell.image_id)
                image_geom = image.geometry()
                
                new_overlap_geom =  image_geom.intersection(remaining_geom, 10)
                new_overlap_area  = new_overlap_geom.area(10).getInfo()
                new_overlap = new_overlap_area/park_area

                cell.monitored = True if ((new_overlap > 0.01) or (area.hasBoundary() == False)) else False # If overlap is above arbitrary threshold (1%) default is to monitor cell, user can change later.
                if cell.monitored:
                    remaining_geom = remaining_geom.difference(new_overlap_geom)
                    remaining_area = remaining_geom.area(10).getInfo()
            except Exception, e:
                logging.error("exception {0!s}".format(e)) #Image not found?
                new_overlap= 0 
                new_overlap_area = 0 
                continue
        else:
            # skip remaining cells, we have our set and just want to print them out.
            new_overlap= 0 
            new_overlap_area = 0 

        logging.debug("Cell {0:s} overlaps {1:.1f}% of your park's area, {2:.1f}% uniquely. {3:s}. Remaining area {4:.1f}% ".format( \
                   cell.key.string_id(), (cell.overlap*100), (new_overlap*100), ('Monitored' if cell.monitored else 'Unmonitored'), (remaining_area/park_area*100)) )

    area.glad_monitored = False
    try:
        area.glad_monitored = gladalerts.geometryIsInGladAlertsFootprint(park_geom) # area.get_boundary_hull_fc().geometry()
    except:
        logging.error('error getting GLAD footprint')


    #Store the cells and the area's cellList.
    def txn_saveCellList(cellList, area):
        for cell in cellList:
            cell.put()
            area.cells.append(cell.key) 
        area.put()
        return cellList

    db.run_in_transaction(txn_saveCellList, cellList, area)


    cache.flush() # FIXME: get user to call cache.set(area, cells)
    return True




################# EOF ############################################
