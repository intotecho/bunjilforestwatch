'''
Wrappers for some Earth Engine Routines
Created on 25/05/2013
@author: cgoodman

'''


import sys
import logging
logging.basicConfig(level=logging.DEBUG)
import settings
import oauth2client.client
import datetime
import ee
import json

'''
initEarthEngineService()
Call once per session to authenticate to EE
'''
def initEarthEngineService():
    SCOPES = ('https://www.googleapis.com/auth/earthengine.readonly')
    creds = ee.ServiceAccountCredentials(settings.MY_SERVICE_ACCOUNT, settings.MY_PRIVATE_KEY_FILE)
    ee.Initialize(creds) 
    
    
'''
getLatestLandsatImage(array of points, ee.imagecollection)
returns the latest image from the collection that overlaps the boundary coordinates.
Also clips the image to the coordinates to reduce the size.
'''
    
def getLatestLandsatImage(boundary_polygon, image_collection):
    #logging.info('boundary_polygon %s type: %s', boundary_polygon, type(boundary_polygon))
    feat = ee.Geometry.Polygon(boundary_polygon)
    #logging.info('feat %s', feat)
    
    boundary_feature = ee.Feature(feat, {'name': 'areaName', 'fill': 1})
    park_boundary = ee.FeatureCollection(boundary_feature)
    info = park_boundary.getInfo()
    end_date   = datetime.datetime.today()
    secsperyear = 60 * 60 * 24 * 365 #  365 days * 24 hours * 60 mins * 60 secs
    start_date = end_date - datetime.timedelta(seconds = 1 * secsperyear )
    logging.debug('start:%s, end:%s ',start_date,  end_date)

    sortedCollection = ee.ImageCollection(image_collection.filterBounds(park_boundary).filterDate(start_date, end_date).sort('system:time_start', False )) #note cast to ee,ImageCollection() resolves bug in sort() for ee ver 0.13
    #logging.info('Collection description : %s', sortedCollection.getInfo())
  
    scenes  = sortedCollection.getInfo()
    #logging.info('Scenes: %s', sortedCollection)
    #because sort has a bug, always in wrong order, so pop the last one. Otherwise would apply limit(1)
    feature = scenes['features'].pop()
    #for feature in scenes['features']: 
    id = feature['id']   
    logging.info('Scene id: %s', id)
    latest_image = ee.Image(id)
    props = latest_image.getInfo()['properties'] #logging.info('image properties: %s', props)
    crs = latest_image.getInfo()['bands'][0]['crs']
    #path    = props['WRS_PATH']
    #row     = props['STARTING_ROW']
    system_time_start= datetime.datetime.fromtimestamp(props['system:time_start'] / 1000) #convert ms
    date_str = system_time_start.strftime("%Y-%m-%d @ %H:%M")

    logging.info('getLatestLandsatImage id: %s, date:%s', id, date_str)
    return latest_image  #.clip(park_boundary)

def getLatestLandsat7HSVUpres(boundary_polygon):
    #logging.info('boundary_polygon %s type: %s', boundary_polygon, type(boundary_polygon))
    feat = ee.Geometry.Polygon(boundary_polygon)
    #logging.info('feat %s', feat)
    
    feature = ee.Feature(feat, {'name': 'areaName', 'fill': 1})
    park_boundary = ee.FeatureCollection(feature )
    info = park_boundary.getInfo()
    logging.debug('boundary_coords= %s', info['features'][0]['geometry']['coordinates'])
    #TEST WITH FUSION TABLE
    #park_boundary_ft = ee.FeatureCollection('ft:1urlhdLW2pA66f2xS0yzmO-LaESYdclD7-17beg0')
    #info_ft = park_boundary_ft.getInfo()
    #logging.info('boundary_coords_ft= %s', info_ft['features'][0]['geometry']['coordinates'])
     
    end_date   = datetime.datetime.today()
    secsperyear = 60 * 60 * 24 * 365 #  365 days * 24 hours * 60 mins * 60 secs
    start_date = end_date - datetime.timedelta(seconds = 1 * secsperyear )
    logging.debug('start:%s, end:%s ',start_date,  end_date)
        
    sortedCollection = ee.ImageCollection(ee.ImageCollection('L7_L1T').filterBounds(park_boundary).filterDate(start_date, end_date).sort('system:time_start', False ).limit(1)) #note cast to ee,ImageCollection() resolves bug in sort() for ee ver 0.13
    #logging.info('Collection description : %s', sortedCollection.getInfo())
  
    scenes  = sortedCollection.getInfo()
    #logging.info('Scenes: %s', sortedCollection)
    
    for feature in scenes['features']:
        id = feature['id']   #logging.info('Scene id: %s, %s', id, i)
        image1 = ee.Image(id)
        props = image1.getInfo()['properties'] #logging.info('image properties: %s', props)
        crs = image1.getInfo()['bands'][0]['crs']
        path    = props['WRS_PATH']
        row     = props['STARTING_ROW']
        
        system_time_start= datetime.datetime.fromtimestamp(props['system:time_start'] / 1000)
        date_format_str = "%Y-%m-%d @ %H:%M"
        date_str = system_time_start.strftime(date_format_str)

        logging.info('getLatestLandsat_Visible id: %s, path: %s, row: %s, date:%s', id, path, row, date_str)
        #Convert to HSV, swap in the pan band, and convert back to RGB. 
        #Example from https://ee-api.appspot.com/#5ea3dd541a2173702cfe6c7a88346475
        rgb = image.select(['30', '20', '10']).unitScale(0, 255) #Select the visible red, green and blue bands.
        gray = image.select(['80']).unitScale(0, 155)
        huesat = rgb.rgbtohsv().select(['hue', 'saturation'])
        upres = ee.Image.cat(huesat, gray).hsvtorgb().clip(park_boundary)
        return upres

def SharpenLandsat7HSVUpres(image):
        #Convert to HSV, swap in the pan band, and convert back to RGB. 
        #Javascript Example from https://ee-api.appspot.com/#5ea3dd541a2173702cfe6c7a88346475
        #Pan sharpen Landsat 8
        rgb = image.select(['30', '20', '10']).unitScale(0, 255) #Select the visible red, green and blue bands.
        pan = image.select(['80']).unitScale(0, 155)
        huesat = rgb.rgbtohsv().select(['hue', 'saturation'])
        upres = ee.Image.cat(huesat, pan).hsvtorgb()  
        return(upres)    

def SharpenLandsat8HSVUpres(image):
        #Convert to HSV, swap in the pan band, and convert back to RGB. 
        #Javascript Example from https://ee-api.appspot.com/#5ea3dd541a2173702cfe6c7a88346475
        #Pan sharpen Landsat 8
        rgb = image.select("B4","B3","B2")
        pan = image.select("B8")
        huesat = rgb.rgbtohsv().select(['hue', 'saturation'])
        upres = ee.Image.cat(huesat, pan).hsvtorgb()  
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
    imgbands = image.getInfo()['bands']
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

def getL8SharpOverlay(coords):
    
    image = getLatestLandsatImage(coords, ee.ImageCollection('LANDSAT/LC8_L1T_TOA'))
    sharpimage = SharpenLandsat8HSVUpres(image)
    red = 'red'
    green = 'green'
    blue = 'blue'    
    byteimage = sharpimage.multiply(255).byte()
    path = getOverlayPath(byteimage, "L8TOA", red, green, blue)
    return path

def getL8SharpImage(coords):
    image = getLatestLandsatImage(coords, ee.ImageCollection('LANDSAT/LC8_L1T_TOA'))
    sharpimage = SharpenLandsat8HSVUpres(image)
    red = 'red'
    green = 'green'
    blue = 'blue'    
    byteimage = sharpimage.multiply(255).byte()
    #path = getOverlayPath(byteimage, "L8TOA", red, green, blue)
    return byteimage

def getMapId(image, red, green, blue):

    crs = image.getInfo()['bands'][0]['crs']
    p05 = []
    p95 = []
    p05 = getPercentile(image, 5, crs)
    p95 = getPercentile(image, 95, crs)
    min = str(p05[red]) + ', ' + str(p05[green]) + ', ' + str(p05[blue])
    max = str(p95[red]) + ', ' + str(p95[green]) + ', ' + str(p95[blue])
    print('Percentile  5%: ', min)
    print('Percentile 95%: ', max)
    # Define visualization parameters, based on the image statistics.
    mapparams = {    'bands':  'red, green, blue', 
                     'min': min,
                     'max': max,
                     'gamma': 1.2
                }   
    mapid  = image.getMapId(mapparams) 
    return mapid

def getTiles(mapid): #not used
    tilepath = ee.data.getTileUrl(mapid, 0, 0, 1)
    logging.info('getTiles: %s',       tilepath)
    return tilepath

def GetMap(coords):
        image = getLatestLandsatImage(coords, ee.ImageCollection('LANDSAT/LC8_L1T_TOA'))
        sharpimage = SharpenLandsat8HSVUpres(image)
        byteimage = sharpimage.multiply(255).byte()
        red = 'red'
        green = 'green'
        blue = 'blue'
        mapid = getMapId(byteimage,  red, green, blue)

#### UNIT TESTS ######

#fc = ee.FeatureCollection('ft:1urlhdLW2pA66f2xS0yzmO-LaESYdclD7-17beg0') #Yarra Ranges N.P.

import unittest

class TestEEService(unittest.TestCase):
    coords = [
              [        145.3962206840515,        -37.71424496764925      ], 
              [        146.049907207489,        -37.705553487215816      ], 
              [        146.00733518600464,        -37.239075302021824    ], 
              [        145.29871702194214,        -37.233608599437034    ]
              ]  
    
    def setUp(self):
        initEarthEngineService()
        
    def TestGetMap(self):
        #image = getLatestLandsatImage(self.coords, ee.ImageCollection('LANDSAT/LC8_L1T_TOA'))
        #sharpimage = SharpenLandsat8HSVUpres(image)
        #byteimage = sharpimage.multiply(255).byte()
        #red = 'red'
        #green = 'green'
        #blue = 'blue'
        #mapid = getMap(byteimage,  red, green, blue)
        mapid = GetMap(self.coords)
        self.assertEqual(True, True, 'TestGetMap failed')
     
    def TestGetTiles(self):
        mapid = GetMap(self.coords)
        red = 'red'
        green = 'green'
        blue = 'blue'
        tileurl = getTiles(byteimage,  red, green, blue)
        print tileurl
        self.assertEqual(tilepath.startswith("https://earthengine.googleapis.com//map"), True, 'TestGetTiles failed')
     
    def TestL7Thumbs(self):
        
        image = getLatestLandsat7HSVUpres(coords)
        getThumbnailPath(image)
        self.assertEqual(1, 2, 'test failed')
        pass
    
    def TestL8Thumbs(self):
        coords = [
              [        145.3962206840515,        -37.71424496764925      ], 
              [        146.049907207489,        -37.705553487215816      ], 
              [        146.00733518600464,        -37.239075302021824      ], 
              [        145.29871702194214,        -37.233608599437034      ]
              ]    
        
        testimage= ee.Image("LANDSAT/LC8_L1T_TOA/LC80440342013170LGN00")
        sharpimage = SharpenLandsat8HSVUpres(testimage)
        getThumbnailPath(sharpimage)
        self.assertEqual(1, 1, 'L8 thumbs failed')
        pass
     
    def TestL7Overlay(self):
        image = getLatestLandsatImage(self.coords, ee.ImageCollection('L7_L1T'))
        #red = 'B4'
        #green = 'B3'
        #blue = 'B2'
        sharpimage = SharpenLandsat7HSVUpres(image)
        red = 'red'
        green = 'green'
        blue = 'blue'    
        byteimage = sharpimage.multiply(255).byte()
        path = getOverlayPath(byteimage, "L7", red, green, blue)
        self.assertEqual(path.startswith("https://earthengine.googleapis.com//api/download?docid"), True, 'L7 overlay failed')
          
    def TestL8Overlay(self):
        image = getLatestLandsatImage(self.coords, ee.ImageCollection('LANDSAT/LC8_L1T_TOA'))
        sharpimage = SharpenLandsat8HSVUpres(image)
        red = 'red'
        green = 'green'
        blue = 'blue'    
        byteimage = sharpimage.multiply(255).byte()
        path = getOverlayPath(byteimage, "L8TOA", red, green, blue)
        self.assertEqual(path.startswith("https://earthengine.googleapis.com//api/download?docid"), True, 'L8 overlay failed')
   
    def TestGetAlgorithms(self):
        algorithms = ee.data.getAlgorithms()
        #print type(algorithms) =Dictionary.
        for f in algorithms:
            print  f + ', \tDescr: ' + algorithms.get(f)['description']
        self.assertEqual(True, True, 'TestAlgorithms failed')
             
        