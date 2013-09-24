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
getLatestLandsatImage(array of points, string as name of ee.imagecollection)
returns the latest image from the collection that overlaps the boundary coordinates.
Also clips the image to the coordinates to reduce the size.
'''
    
def getLatestLandsatImage(boundary_polygon, collection_name, latest_depth, opt_path = None, opt_row = None):
    #logging.info('boundary_polygon %s type: %s', boundary_polygon, type(boundary_polygon))
    feat = ee.Geometry.Polygon(boundary_polygon)
    #logging.info('feat %s', feat)
    image_collection = ee.ImageCollection(collection_name)
    boundary_feature = ee.Feature(feat, {'name': 'areaName', 'fill': 1})
    park_boundary = ee.FeatureCollection(boundary_feature)
    info = park_boundary.getInfo()
    end_date   = datetime.datetime.today()
    secsperyear = 60 * 60 * 24 * 365 #  365 days * 24 hours * 60 mins * 60 secs
    start_date = end_date - datetime.timedelta(seconds = 1 * secsperyear )
    logging.debug('start:%s, end:%s ',start_date,  end_date)

    sortedCollection = ee.ImageCollection(image_collection.filterBounds(park_boundary).filterDate(start_date, end_date).sort('system:time_start', False ))
    resultingCollection = sortedCollection
    if opt_path is not None and opt_row is not None:
        #filter Landsat by Path/Row and date
        if ("L7" in collection_name):
            row_fieldname = "STARTING_ROW"
        else:
            row_fieldname = "WRS_ROW"
        resultingCollection = sortedCollection.filterMetadata('WRS_PATH', 'equals', opt_path).filterMetadata(row_fieldname, 'equals', opt_row)
    
    #logging.info('Collection description : %s', sortedCollection.getInfo())
  
    scenes  = resultingCollection.getInfo()
    #logging.info('Scenes: %s', sortedCollection)
    #because sort has a bug, always in wrong order, so pop the last one. Otherwise would apply limit(1)
    try:
        feature = scenes['features'][len(scenes)-latest_depth]
    except IndexError:
        feature = scenes['features'].pop()
        
    #for feature in scenes['features']: 
    id = feature['id']   
    #logging.info('getLatestLandsatImage found scene: %s', id)
    latest_image = ee.Image(id)
    props = latest_image.getInfo()['properties'] #logging.info('image properties: %s', props)
    test = latest_image.getInfo()['bands']
    print (test)
    crs = latest_image.getInfo()['bands'][0]['crs']
    #path    = props['WRS_PATH']
    #row     = props['STARTING_ROW']
    system_time_start= datetime.datetime.fromtimestamp(props['system:time_start'] / 1000) #convert ms
    date_str = system_time_start.strftime("%Y-%m-%d @ %H:%M")

    logging.info('getLatestLandsatImage id: %s, date:%s latest:%d', id, date_str, latest_depth )
    x = latest_image.getInfo()
    latest_image.name = id
    latest_image.capture_date = date_str
    x['mynewkey'] = id 
    #x.capture_date = date_str
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
        byteimage = upres.multiply(255).byte()
        return(byteimage)    

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

def getL8SharpImage(coords, depth):
    image = getLatestLandsatImage(coords, 'LANDSAT/LC8_L1T_TOA', depth)
    sharpimage = SharpenLandsat8HSVUpres(image)
    #red = 'red'
    #green = 'green'
    #blue = 'blue'    
    #byteimage = sharpimage.multiply(255).byte()
    #path = getOverlayPath(byteimage, "L8TOA", red, green, blue)
    return sharpimage

def getL8LatestNDVIImage(image):
    NDVI_PALETTE = {'FFFFFF','00FF00'}
    ndvi = image.normalizedDifference(["B4", "B3"]);   
    
    #addToMap(ndvi.median(), {min:-1, max:1}, "Median NDVI");
    #getMapId(ndvi, {min:-1, max:1, palette:NDVI_PALETTE}, "NDVI");
    
    newImage = image.addBands(ndvi); #keep all the metadata of image, but add the new bands.
    print('getL8NDVIImage: ', newImage)

    mapparams = {    #'bands':  'red, green, blue', 
                     'min': -1,
                     'max': 1,
                     'palette': 'FF00FF, 00FF00',
                     #'gamma': 1.2,
                     'format': 'jpg'
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
    #original image is used for original metadata lost in image - nice to figure out a cleaner solution 
    crs = image.getInfo()['bands'][0]['crs']
    p05 = []
    p95 = []
    p05 = getPercentile(image, 5, crs)
    p95 = getPercentile(image, 80, crs) # not 95
    min = str(p05[red]) + ', ' + str(p05[green]) + ', ' + str(p05[blue])
    max = str(p95[red]) + ', ' + str(p95[green]) + ', ' + str(p95[blue])
    print('Percentile  5%: ', min)
    print('Percentile 95%: ', max)
    # Define visualization parameters, based on the image statistics.
    mapparams = {    'bands':  'red, green, blue', 
                     'min': min,
                     'max': max,
                     'gamma': 1.2,
                     'format': 'jpg'
                }   
    mapid  = image.getMapId(mapparams)
    # copy some image props to mapid for browser to display
    info = image.getInfo() #logging.info("info", info)
    props = info['properties']
    mapid['date_acquired'] = props['DATE_ACQUIRED']
    mapid['id'] = props['system:index']
    mapid['path'] = props['WRS_PATH']
    mapid['row'] = props['WRS_ROW']
    return mapid

def getTiles(mapid): #not used
    tilepath = ee.data.getTileUrl(mapid, 0, 0, 1)
    logging.info('getTiles: %s',       tilepath)
    return tilepath

def GetMap(coords, depth): # not used except test
        image = getLatestLandsatImage(coords, 'LANDSAT/LC8_L1T_TOA', depth)
       
        sharpimage = SharpenLandsat8HSVUpres(image)
        #byteimage = sharpimage.multiply(255).byte()
        red = 'red'
        green = 'green'
        blue = 'blue'
        mapid = getVisualMapId(sharpimage, red, green, blue)

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

def getL8SharpOverlay(coords, depth):
    
    image = getLatestLandsatImage(coords, 'LANDSAT/LC8_L1T_TOA', depth)
    sharpimage = SharpenLandsat8HSVUpres(image)
    red = 'red'
    green = 'green'
    blue = 'blue'    
    #byteimage = sharpimage.multiply(255).byte()
    path = getOverlayPath(sharpimage, "L8TOA", red, green, blue)
    return path

