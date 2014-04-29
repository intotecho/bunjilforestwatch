'''
Wrappers for some Earth Engine Routines
Created on 25/05/2013
@author: cgoodman

'''
import sys
from google.appengine.ext import db
import logging
import cache
import models # only for Observations.

logging.basicConfig(level=logging.DEBUG)

import os
from os import environ
#logging.debug('PYTHONPATH: %s',os.environ['PYTHONPATH'])
#logging.debug('HTTP_PROXY: %s',os.environ['HTTP_PROXY'])
#logging.debug('HTTPS_PROXY: %s',os.environ['HTTPS_PROXY'])

#if os.environ['EARTHENGINE_BYPASS'].startswith('T'): 
#    logging.info('EARTHENGINE_BYPASS is %s. Earth Engine Calls are disabled..',os.environ['EARTHENGINE_BYPASS'])

import oauth2client.client
from oauth2client.appengine import AppAssertionCredentials

from oauth2client import util # to disable positional parameters warning.

import datetime
import json

import settings
#You have to create your own keys. 

#if os.environ['EARTHENGINE_BYPASS'].startswith('T'): 
#    logging.info('EARTHENGINE_BYPASS is %s. Earth Engine Calls are disabled..',os.environ['EARTHENGINE_BYPASS'])
#else:
import ee
    

'''
initEarthEngineService()
Call once per session to authenticate to EE
SERVER_SOFTWARE: In the development web server, this value is "Development/X.Y" where "X.Y" is the version of the runtime. 
When running on App Engine, this value is "Google App Engine/X.Y.Z".

'''
earthengine_intialised = False

def initEarthEngineService():

    #SCOPES = ('https://www.googleapis.com/auth/earthengine.readonly') # still needed?

    global earthengine_intialised
    if earthengine_intialised == False:
        try:
            if os.environ['SERVER_SOFTWARE'].startswith('Development'): 
                logging.info("Initialising Earth Engine authenticated connection from devserver")
                EE_CREDENTIALS = ee.ServiceAccountCredentials(settings.MY_LOCAL_SERVICE_ACCOUNT, settings.MY_LOCAL_PRIVATE_KEY_FILE)
            else:
                logging.info("Initialising Earth Engine authenticated connection from App Engine")
                EE_CREDENTIALS = AppAssertionCredentials(ee.OAUTH2_SCOPE)
            ee.Initialize(EE_CREDENTIALS) 
            earthengine_intialised = True
            util.positional_parameters_enforcement = util.POSITIONAL_IGNORE   # avoid the WARNING [util.py:129] new_request() takes at most 1 positional argument (4 given)
        except Exception, e:
            #self.add_message('error', 'An error occurred with Earth Engine. Try again.')
            logging.error("Failed to connect to Earth Engine. Exception: %s", e)
            pass

'''
checkNew() looks at each subscribed area of interest and checks to see if there is a new image in EE since the last check.
'''
    
def checkNewAllAreas():
    #for each Area
    all_areas = cache.get_all_areas()
    logging.info( "checkNewAllAreas(): areas = %s", all_areas)
    for area in all_areas:
        checkNewForArea(area, "LANDSAT/LC8_L1T_TOA")
        checkNewForArea(area, "LANDSAT/LE7_L1T_TOA") # old value "LANDSAT/L7_L1T" 
    return True


'''
checkNewForCell() checks the collection for the latest image and compares it to the last stored. 
    If a newer image is found, the observation is added and the function returns True.
    If no new image is found, the function returns False. 
    An error is logged if no images are found. 
    If no observation exists, one is created.
'''

def checkNewForCell(area, cell, collection_name):
    poly = [] #TODO Move poly to a method of models.AOI
    for geopt in area.coordinates:
        poly.append([geopt.lon, geopt.lat])
    latest_image = getLatestLandsatImage(poly, collection_name, 0, params = [cell.path, cell.row]) # most recent image for this cell in the collection
    if latest_image is not None:
        storedlastObs = cell.latestObservation(collection_name)             #FIXME - Need to use the cache here.
        if storedlastObs is None or latest_image.capture_datetime > storedlastObs.captured: #captured_date = datetime.datetime.strptime(map_id['date_acquired'], "%Y-%m-%d")
            obs = models.Observation(parent = cell, image_collection = collection_name, captured = latest_image.capture_datetime, image_id = latest_image.name, rgb_map_id = None, rgb_token = None,  algorithm = None)
            db.put(obs)
            if storedlastObs is None:
                logging.debug('checkNewForCell FIRST observation for %s %s %s %s', area.name, collection_name, cell.path, cell.row)
            else:
                logging.debug('checkNewForCell NEW observation for %s %s %s %s', area.name, collection_name, cell.path, cell.row)
            return True
        else:
            logging.debug('checkNewForCell no newer observation for %s %s %s %s', area.name, collection_name, cell.path, cell.row)
            return False
    else:
        logging.error('checkNewForCell no matching image in collection %s %s %s %s', area.name, collection_name, cell.path, cell.row)
        return False
    return True

'''
getLandsatImage(array of points, string as name of ee.imagecollection)
returns the 'depth' latest image from the collection that overlaps the boundary coordinates.
Could also clip the image to the coordinates to reduce the size.
return type is ee.Image(). Some attributes are appended to the object.
    capture_date, is a string rep of the system_date.
'''
secsperyear = 60 * 60 * 24 * 365 #  365 days * 24 hours * 60 mins * 60 secs

    
def getLatestLandsatImage(boundary_polygon, collection_name, latest_depth, params):
    #logging.info('boundary_polygon %s type: %s', boundary_polygon, type(boundary_polygon))
    cw_feat = ee.Geometry.Polygon(boundary_polygon)
    feat = cw_feat.buffer(0, 1e-10)
    #logging.info('feat %s', feat)
    boundary_feature = ee.Feature(feat, {'name': 'areaName', 'fill': 1})
    
    #boundary_feature_buffered = boundary_feature.buffer(0, 1e-10) # force polygon to be CCW so search intersects with interior.
    #logging.debug('Temporarily disabled buffer to allow AOI points in clockwise order due to EEAPI bug')

    #boundary_feature_buffered = boundary_feature 
    park_boundary = ee.FeatureCollection(boundary_feature)
    
    end_date   = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(seconds = 1 * secsperyear/2 )
    logging.debug('getLatestLandsatImage() start:%s, end:%s ',start_date,  end_date)
    #logging.debug('getLatestLandsatImage() park boundary as FC %s ',park_boundary)

    image_collection = ee.ImageCollection(collection_name)
    #print image_collection.getInfo()
    
    if ('lpath' in params) and ('lrow' in params): 
        
        path = int(params['lpath'])
        row = int(params['lrow'])
        image_name =  collection_name[8:11] + "%03d%03d" %(path, row)
        logging.debug("logging.debug: image name: %s", image_name)
        #filter Landsat by Path/Row and date
        resultingCollection = image_collection.filterBounds(park_boundary).filterDate(start_date, end_date).filterMetadata('WRS_PATH', 'equals', path).filterMetadata('WRS_ROW', 'equals', row)#) #latest image form this cell.
    else:
        resultingCollection = image_collection.filterDate(start_date, end_date).filterBounds(park_boundary) # latest image from any cells that overlaps the area. 
    
    sortedCollection = resultingCollection.sort('system:time_start', False )
    
    #logging.info('Collection description : %s', sortedCollection.getInfo())
      #logging.debug("sortedCollection: %s", sortedCollection)
    scenes  = sortedCollection.getInfo()
    #logging.info('Scenes: %s', sortedCollection)
    
    try:
        feature = scenes['features'][int(latest_depth)]
        print 'feature: ', feature
    except IndexError:
        try:
            feature = scenes['features'][0]
        except IndexError:
            logging.error("No Scenes in Filtered Collection")
            logging.debug("scenes: ", scenes)
            return 0

    
    id = feature['id']   
    #logging.info('getLatestLandsatImage found scene: %s', id)
    latest_image = ee.Image(id)
    props = latest_image.getInfo()['properties'] #logging.info('image properties: %s', props)
    test = latest_image.getInfo()['bands']

    crs = latest_image.getInfo()['bands'][0]['crs']
    #path    = props['WRS_PATH']
    #row     = props['STARTING_ROW']
    system_time_start= datetime.datetime.fromtimestamp(props['system:time_start'] / 1000) #convert ms
    date_str = system_time_start.strftime("%Y-%m-%d @ %H:%M")

    logging.info('getLatestLandsatImage id: %s, date:%s latest:%s', id, date_str, latest_depth )
    x = latest_image.getInfo()
    latest_image.name = id
    latest_image.capture_date = date_str
    latest_image.capture_datetime = system_time_start
    
    #x['mynewkey'] = id 
    return latest_image  #.clip(park_boundary)

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
        # Display before and after layers using the same vis parameters.
        #var visparams = {min: [0.15, 0.15, 0.25],
        #         max: [1, 0.9, 0.9],
        #         gamma: 1.6};
        
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

# def getL8SharpImage(coords, depth): # wont use now
#     image = getLatestLandsatImage(coords, 'LANDSAT/LC8_L1T_TOA', depth)
#     sharpimage = SharpenLandsat8HSVUpres(image)
#     return sharpimage

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
        ee.Reducer.percentile([percentile]), # reducer
        None, # geometry (Defaults to the footprint of the image's first band)
        None, # scale (Set automatically because bestEffort == true)
        crs,
        None, # crsTransform,
        True  # bestEffort
        ).getInfo()


def getL8LatestNDVIImage(image):
    NDVI_PALETTE = {'FF00FF','00FF00'}
    ndvi = image.normalizedDifference(["B4", "B3"]).median();   
    
    #addToMap(ndvi.median(), {min:-1, max:1}, "Median NDVI");
    #getMapId(ndvi, {min:-1, max:1, palette:NDVI_PALETTE}, "NDVI");
    
    newImage = image.addBands(ndvi); #keep all the metadata of image, but add the new bands.
    print('getL8NDVIImage: ', newImage)

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
    p05 = []
    p95 = []
    p05 = getPercentile(image, 5, crs)
    p95 = getPercentile(image, 95, crs) 
    min = str(p05[red]) + ', ' + str(p05[green]) + ', ' + str(p05[blue])
    max = str(p95[red]) + ', ' + str(p95[green]) + ', ' + str(p95[blue])
    logging.debug('Percentile  5%% %s 95%% %s', min, max)
    
    # Define visualization parameters, based on the image statistics.
    mapparams = {    'bands':  'red, green, blue', 
                     'min': min,
                     'max': max,
                     'gamma': 1.2,  #was 1.2
                     'format': 'png'
                }   
    mapid  = image.getMapId(mapparams)
    return mapid

def getThumbnailPath(image):
        # GET THUMBNAIL
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
    imgbands = image.get('bands')
    #for b in imgbands:
    #    print b
    # Get the percentile values for each band.
    p05 = []
    p95 = []
    p05 = getPercentile(image, 5, crs)
    p95 = getPercentile(image, 95, crs)
    # Print out the image ststistics.
    print('Percentile  5%: ', p05)
    print('Percentile 95%: ', p95)

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
    path      = image.getDownloadUrl(visparams)
    logging.info('getOverlayPath: %s',       path)
    return path


def getLandsatOverlay(coords, satellite, algorithm, depth, params):
    if satellite == 'l8':
        collection_name = 'LANDSAT/LC8_L1T_TOA'
        image = getLatestLandsatImage(coords, collection_name, depth, params)
        if not image:
            logging.error('getLatestLandsatImage() no image found')
            return 0
        if algorithm == 'rgb':
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
            mapid['id'] = props['system:index']
            mapid['path'] = props['WRS_PATH']
            mapid['row'] = props['WRS_ROW']
            mapid['collection'] = collection_name
            
            return mapid
        elif algorithm == 'ndvi':
            print "l8 ndvi"
            
    elif satellite == 'l7':
        collection_name = 'LANDSAT/LE7_L1T'  #Old name was 'LANDSAT/L7_L1T' 
        image = getLatestLandsatImage(coords, collection_name, depth, params)
        if not image:
            logging.error('getLatestLandsatImage() no image found')
            return 0
        if algorithm == 'rgb':
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
            return mapid
        
        elif algorithm == 'ndvi':
           print "l7 ndvi"

        
'''
getPathRow returns max or min value of the sort_property in a collection.

Example:
    max_path = getPathRow(boundCollection,"WRS_PATH", False)
    min_path = getPathRow(boundCollection,"WRS_PATH", True)
    max_row  = getPathRow(boundCollection,"WRS_ROW", False)
    min_row  = getPathRow(boundCollection,"WRS_ROW", True)
'''
def getPathRow(collection, sort_property, ascending):
    limited_collection_info = (collection.limit(1, sort_property, ascending).getInfo())        
    try:
        max_prop= limited_collection_info['features'][0]['properties'][sort_property]
        return max_prop
    except IndexError:
        print 'getPathRow(): Index Exception'
        return -1

    
#determine the overlapping cells from the image collection returned and store them in area.cells.
def getLandsatCells(area):
    #TODO: Better to store area.coordinates as an ee.FeatureCollection type. Then this is not repeated for each new image.
    boundary_polygon = []
    for geopt in area.coordinates:
        boundary_polygon.append([geopt.lon, geopt.lat])
        
    #logging.info('boundary_polygon %s type: %s', boundary_polygon, type(boundary_polygon))
    cw_feat = ee.Geometry.Polygon(boundary_polygon)
    feat = cw_feat.buffer(0, 1e-10)
    
    #logging.info('feat %s', feat)
    boundary_feature = ee.Feature(feat, {'name': 'areaName', 'fill': 1})
    #boundary_feature_buffered = boundary_feature.buffer(0, 1e-10) # force polygon to be CCW so search intersects with interior.
    #logging.debug('getLandsatCells: Temporarily disabled buffer to allow AOI points in clockwise order due to EEAPI bug')

    boundary_feature_buffered = boundary_feature 
    park_boundary = ee.FeatureCollection(boundary_feature_buffered)
    #info = park_boundary.getInfo()
    end_date   = datetime.datetime.today()
    start_date = end_date - datetime.timedelta(seconds = 1 * secsperyear ) #years.
    #logging.debug('start:%s, end:%s ',start_date,  end_date)

    boundCollection = ee.ImageCollection('LANDSAT/LC8_L1T_TOA').filterBounds(park_boundary).filterDate(start_date, end_date)
    #boundCollection = image_collection.filterBounds(park_boundary).filterDate(start_date, end_date)

    max_path = getPathRow(boundCollection,"WRS_PATH", False)
    min_path = getPathRow(boundCollection,"WRS_PATH", True)
    max_row  = getPathRow(boundCollection,"WRS_ROW", False)
    min_row  = getPathRow(boundCollection,"WRS_ROW", True)
    logging.debug('getLandsatCells(): max_path: %d, min_path: %d, max_row %d, min_row: %d', max_path, min_path, max_row, min_row)
    return (max_path, min_path, max_row, min_row)
    
 



################# NOT USED ############################################
