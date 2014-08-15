#### test prior overlay ####
import logging
logging.basicConfig(level=logging.DEBUG)

import ee
import settings

disable_ssl_certificate_validation = True # bug in HTTPlib i think
B9_THRESHOLD = 5200 #originally  5200

def testPriorLandsatOverlay(image_id, image_collection):

    ref_image = ee.Image(image_id)
    props = ref_image.getInfo()['properties'] #logging.info('image properties: %s', props)
    path = props['WRS_PATH']
    row = props['WRS_ROW']
    
    system_time = datetime.datetime.fromtimestamp((props['system:time_start'] / 1000) -3600) #convert ms
    date_str = system_time.strftime("%Y-%m-%d @ %H:%M")

    before     = system_time - datetime.timedelta(days=1)
    earliest   = system_time - datetime.timedelta(days=(3*365))
    before_str   = before.strftime("%Y-%m-%d")
    earliest_str = earliest.strftime("%Y-%m-%d")
    
    logging.info('getPriorLandsatOverlay id: %s, captured:%s from %s to :%s', image_id, date_str, earliest_str, before_str)
    
    resultingCollection = ee.ImageCollection(image_collection).filterDate(earliest, before).filterMetadata('WRS_PATH', 'equals', path).filterMetadata('WRS_ROW', 'equals', row).filterMetadata('default:SUN_ELEVATION', 'GREATER_THAN', 0)

    # Optional step that adds QA bits as separate bands to make it easier to debug.
    collectionUnmasked = resultingCollection.map(add_date).map(L8AddQABands)
    collectionMasked = collectionUnmasked.map(maskL8)
    
    sky = collectionMasked.qualityMosaic('system:time_start') # latest pixel.
    
    rgbVizParams = {'bands': 'B4,B3,B2', 'min':5000, 'max':30000, 'gamma': 1.6, 'format': 'png'}
    mapid  = ref_image.getMapId(rgbVizParams)
    return mapid

def getQABits(image, start, end, newName):
    # Compute the bits we need to extract.
    pattern = 0
    for i in range (start, end): 
        pattern += math.pow(2, i)
    
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


def testInitEarthEngineService():
    try:
        logging.info("Initialising Earth Engine authenticated connection")
        EE_CREDENTIALS = ee.ServiceAccountCredentials(settings.MY_LOCAL_SERVICE_ACCOUNT, settings.MY_LOCAL_PRIVATE_KEY_FILE)
        ee.Initialize(EE_CREDENTIALS)
        return True
    except Exception, e:
        
        logging.error("Failed to connect to Earth Engine. Exception: %s", e)
        return False



#testInitEarthEngineService()
#testPriorLandsatOverlay('LC8_L1T_TOA/LC81690542014201LGN00', 'LC8_L1T_TOA')

################# EOF ############################################
