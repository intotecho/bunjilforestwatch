"""
#Wrappers for Global Forest Watch Glad-ALert APU Commenced 25/04/2016
@author: cgoodman. Can be shared.
# Copyright (c) 2013-16 Chris Goodman <chris@bunjilforestwatch.net>

"""

import models
import json
from google.appengine.api import urlfetch #change timeout from 5 to 60 s. https://stackoverflow.com/questions/13051628/gae-appengine-deadlineexceedederror-deadline-exceeded-while-waiting-for-htt
#import urllib
import datetime
from google.appengine.ext import ndb
import cache
import logging
import csv
import numpy as np
from ee.batch import Export
import httplib2
import ee
import eeservice
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import googleapiclient
import io
import settings
import time
import apiservices
import ee.batch

'''
create_table() creates a fusion table with the provided schema using the service accounts permisisons
The table belongs to the app's service account.
create_table() makes the table visible to anoyone with the link.
@service - see create_table_service()
@param schema: the name, description and structure of the table. See: https://developers.google.com/fusiontables/docs/v2/reference/table/insert
@param data optionally describes the row data to import. - See https://developers.google.com/fusiontables/docs/v2/reference/table/importRows
'''


def create_table(ft_service, schema, data=None):
    drive_service = apiservices.create_drive_service()
    newtable = ft_service.table().insert(body=schema).execute()
    fileId = newtable["tableId"]

    permissions = drive_service.permissions()
    permissions.create(fileId=fileId,
                       body={"type": "anyone", "role": "writer"},
                       sendNotificationEmail=False).execute()

    FT_URL = "https://www.google.com/fusiontables/data?docid=%s" % fileId
    logging.debug('Created fusion table: %s %s', FT_URL, newtable)

    if data is not None:
        #quoted_data = urllib.quote(data)
        fh = io.BytesIO(data.encode())
        media_body = MediaIoBaseUpload(fh, mimetype='application/octet-stream',  chunksize=1024*1024, resumable=False)

        try:
            val = ft_service.table().importRows(tableId=fileId,
                                            media_body=media_body, startLine=1,
                         isStrict=True, encoding="UTF-8", delimiter="," ).execute()
            print 'create_table() importRows result:', val
        except TypeError, e:
            logging.error("get_alerts() type error %s ", e)
            return None
    return newtable

'''
Creates a fusion table to store GLAD alerts from GFW.
'''
def createAlertsFusionTable(name, since_date_str, to_date_str, alerts):

    #This schema maps to the unprocessed CSV from GFW.
    '''
    schema = {
        "name": name,
        "description": 'GLAD ALERTS from ' + since_date_str + ' to ' + to_date_str,
        "attribution": "UMD-GLAD, WRI Global Forest Watch, bunjilforewstwatch",
        "attributionLink" : "http://www.glad.umd.edu/projects/global-forest-watch",
        "isExportable": True,
        "columns": [
            {
                "name": "date",
                "type": "DATETIME"
            },
            {
                "name": "the_geom",
                "type": "STRING"
            },
            {
                "name": "lat",
                "type": "NUMBER"
            },
            {
                "name": "long",
                "type": "NUMBER"
            }
        ]
    }
    '''

    # This schema maps to the processed CSV from GFW - ideal for FT.
    #LOCATION to contain string of two numbers separated by space "lat long"
    targetschema = {
        "name": name,
        "description": 'GLAD ALERTS from ' + since_date_str + ' to ' + to_date_str,
        "attribution": "UMD-GLAD, WRI Global Forest Watch, bunjilforewstwatch",
        "attributionLink" : "http://www.glad.umd.edu/projects/global-forest-watch",
        "isExportable": True,
        "columns": [
            {
                "name": "date",
                "type": "DATETIME"
            },
            {
                "name": "latlong",
                "type": "LOCATION"
            }
        ]
    }

    service = apiservices.create_table_service()
    newtable = create_table(service, schema=targetschema, data=alerts)
    return newtable


def testupdate(tableid):
    '''
    NOT CALLED
    # sql(sql=None, hdrs=None, typed=None)
    UPDATE <table_id>
    SET <column_name> = <value> {, <column_name> = <value> }*
    WHERE ROWID = <row_id>

    select p.name, p.id, l.id from
    '''
    service = apiservices.create_table_service()
    rows =  service.query().sql(sql="SELECT *  FROM %s" % (tableid)).execute()
    newtable = service.query().sql(sql="UPDATE %s SET latlong = lat ' ' long WHERE ROWID=%s" % (tableid, rows)).execute()
    logging.info("Updated Table %s ", tableid)
    return

def handleCheckForGladAlertsInArea(handler, area_name):
    area = cache.get_area(None, area_name)
    if not area:
        area = cache.get_area(None, area_name)
        logging.error('CheckForGladAlertsInAreaHandler: Area not found!')
        return handler.error(400)
    else:
        logging.debug('CheckForGladAlertsInAreaHandler: check-new-area-images for area_name %s', area_name)

    if area.name == u'peru6test':
        print "TEST MATCH"
        testupdate("1TwGcemZzzdJZmSuGDuOtsJEEUw8NWWKNtfCEGb9Y")
        handler.response.set_status(500)
        return handler.response.write("Tested Update Table ")

    feat = area.get_boundary_hull_geojson()
    geom = json.dumps(feat['geometry'])

    today_dt = datetime.datetime.today()
    today_str = today_dt.strftime('%Y-%m-%d')

    if area.last_alerts_date <> None:
        since_date = area.last_alerts_date.strftime('%Y-%m-%d')
    else:
        since_date = '2016-05-08' # no alerts have been collected. No alerts are earlier than this so collect them all.
    since_date = '2016-05-01' # no alerts have been collected. No alerts are earlier than this so collect them all.
    today_str = '2016-05-18'
    # call the API
    table_name = area.name + "-" + since_date + "-" + today_str
    try:
        alerts_result, ft, count  = getAlerts('glad-alerts', geom, table_name, since_date, today_str, 'csv')
    except TypeError, e:
        handler.response.set_status(500)
        return handler.response.write("Type error in getAlerts - no data? %s" % e)

    #logging.debug(json.loads(alerts_result))

    if alerts_result:
        if alerts_result.status_code == 200:
            area.last_alerts_date = today_dt
            area.last_alerts_raw_ft = ft['tableId']
            area.put()
            msg = "handleCheckForGladAlertsInArea() Created Fusion Table: " + \
                  apiservices.fusiontable_url(ft['tableId'], ft['name']) + \
                  ' with ' + str(count) + 'alerts.'
            handler.response.write(msg)
            #clusters = alerts2Clusters(area)
            #handler.response.set_status(result.status_code)
            #handler.response.write(clusters)
        else:
            msg = "handleCheckForGladAlertsInArea() error: " +\
                str(result.content) + ' payload:' + json.dumps(geom)
            #logging.error(msg)
            handler.response.set_status(result.status_code)
            handler.response.write(msg)
    else:
        handler.response.set_status(500)
        return handler.response.write("Exception in glad API")

'''
getAlerts() calls Global Forest Watch API https://github.com/wri/gfw-api
@param: alert_type, example 'glad-alerts', 'forma-alerts'
@param: polygon is a GeoJSON encoded Polygon or MultiPolygon
@param: since_date, alerts from this date inclusive. 'YYYY-MM-DD'
@param: to_date, alerts to this date inclusive. 'YYYY-MM-DD'
@param: format, one of 'geojson', 'csv', 'kml', 'shp', or 'svg'. Only kml is really supported.

Get GLAD ALERTS for an area since the give date.
Calls GFW with the boundary  of a given an AreaOfInterest

  returns a list of GLAD alerts as a JSON dictionary
    {
        "rows": [
        {
            "date": "2015-11-13T00:00:00Z",
            "the_geom": "0101000020E61000008532E9B54DCA52C0DAE4A7A56AA51EC0",
            "lat": -7.66153963887447,
            "long": -75.160993077976
        }...
        ]
    }

  parameters: area
  parameters: since_date, in YYYY-MM-DD format.

  API: http://github.com/wri/gfw-api

  See also: http://beta.gfw-apis.appspot.com/forest-change/glad-alerts/admin/COD/5?thresh=10

  GET http://api.globalforestwatch.org/forest-change/glad-alerts?period=2015-10-01,2016-04-06

  HTTP parameter period:
  Period of interest, as comma separated begin and end dates, inclusive.
  Dates are in YYYY-MM-DD format. Examples: period=2006-10-08,2008-10-01
  for an alert count between 2006-10-08 and 2008-10-01 inclusive,

  PAYLOAD = HTTP parameter period:
  geojson
  GeoJSON encoded Polygon or MultiPolygon for calculating alerts within their area.

  {"geojson":'{"type":"Polygon","coordinates":[[[12.8,8.9],[13.3,-7.3],[32.5,-6.6],[32.5,7.7],[12.8,8.9]]]}'}

'''

def getAlerts(alert_type, polygon, table_name, since_date, to_date, format):
    headers = {}
    url= 'http://api.globalforestwatch.org/forest-change/' + alert_type + \
         '?period=' + since_date + ',' + to_date

    payload = {}
    payload['geojson'] = polygon
    logging.debug('getAlerts: url=%s', url )
    try:
        get_download_url_result = urlfetch.fetch(url,
                                method='POST',
                                deadline=15,
                                payload= urllib.urlencode(payload)
                                )

        if get_download_url_result.status_code == 200:
            logging.debug('getAlerts: getdownload url OK')
            try:
                apiresult = json.loads(get_download_url_result.content)
                download_url = apiresult["download_urls"][format]
            except KeyError, k:
                logging.error("Could not parse download_url in response")
                return None
            except TypeError, e:
                logging.error("Could not parse download_url in response %s ", e)
                return None

            logging.debug('getAlerts: download url: %s', download_url)
            try:
                alerts_result = urlfetch.fetch(download_url,
                                method='GET',
                                deadline=60
                                )
                #print 'alerts_content ', alerts_result.content
                if alerts_result.status_code == 200:
                    #print 'alerts_result: ', alerts_result
                    if format == 'csv':
                        ft, count = handleAlertDataCSV(table_name, since_date, to_date, alerts_result.content)
                        return get_download_url_result, ft, count
                    #'''
                    #elif format == 'kml':
                    #    X = handleAlertDataKML(alerts_result.content)
                    ##elif format == 'json':
                    #    X = handleAlertDataGeoJson(alerts_result.content)
                    #'''
                    else:
                        logging.error('getAlerts() format not recognised. Use csv %s', format)
                        return get_download_url_result, None, 0
                else:
                    logging.error("getAlerts() Downloading URL error %s", alerts_result.status_code)

            except urlfetch.InvalidURLError:
                logging.error("Download URL is an empty string")
            except urlfetch.DownloadError:
                logging.error("Download Server cannot be contacted")
        else:
            logging.error("getAlerts() Fetch Download URL error %s", get_download_url_result.status_code)

        return get_download_url_result, None, 0

    except urlfetch.InvalidURLError:
        logging.error("GetAlerts URL is an empty string or invalid")
    except urlfetch.DownloadError:
        logging.error("GetAlerts Server cannot be contacted")
    return None

'''
convertCSVForFusion()

@param csvdata: Expects data, database, lat, long\n

1. Removes the headings in first row
2. Creates new headings to match FT.
2. Strips out the cartodb DB reference column
3. Joins lat and long into a single column
4. returns new data and number of alerts converted.
'''
def convertCSVForFusion(csvdata):
    converted_data = "date,latlong\n" #new headings
    alertcount = 0
    rows = csvdata.split('\n')
    #print 'rows in csvdata:', len(rows)
    headings = rows.pop(0)
    #logging.debug('headings: ', headings)
    for r in rows:
        p = r.split(',')
        if len(p) > 3:
            date = p[0]
            lat = p[2]
            lng = p[3]
            s = date + ', ' + lat + ' ' + lng + '\n'
            alertcount += 1
            print s
            converted_data += s
    logging.info("convertCSVForFusion()num alerts: %d , %s", alertcount, len(converted_data))
    return converted_data, alertcount

def handleAlertDataCSV(table_name, since_date, to_date, csvdata):

    if csvdata:
        converted_data, count = convertCSVForFusion(csvdata)
        if count:
            ft = createAlertsFusionTable(table_name, since_date, to_date, converted_data)
            return ft, count
        else:
            logging.error('handleAlertDataCSV() No alerts')
            return None
    else:
        logging.error('handleAlertDataCSV() No input data')
        return None

''' NOT USED

def handleAlertDataKML(kmldata):
    logging.debug('handleAlertDataKML')
    #print kmldata
    #ft = createAlertsFusionTable('helloname', 'jan 2015', 'jan 2016', kmldata)
    return ft

def handleAlertDataGeoJson(geojson_data):
    logging.debug('handleAlertDataGeoJson')

    # area.put()
    handler.response.write(alerts_result)
    # uploadAlerts(alerts_result)

    # ft = createFusionTable(area.lastRawGladAlerts)
    #ft = createAlertsFusionTable('helloname', 'jan 2015', 'jan 2016', alerts_result)
    # print ft

    clusters = alerts2Clusters(area.lastRawGladAlerts, ft)
    handler.response.set_status(result.status_code)
    handler.response.write(clusters)

    return geojson_data
'''


'''
alerts2Clusters() calls Earth Engine to process the alerts to a FeatureCollection
Cluster points     into     polygons.
Based on an answer from Noel Gorelich, GoogleGroups April 27 2016
https://groups.google.com/d/msg/google-earth-engine-developers/3Oq1t9dBUqE/ft50BYTxDQAJ
@param area: an Area of Interest - reads the last raw alerts fusion table ID.

'''

def alerts2Clusters(area):

    ft = area.last_alerts_raw_ft
    print 'ft:%s'%ft

    if not eeservice.initEarthEngineService():
        logging.error('Sorry, Server Credentials Error')

    alerts_fc = ee.FeatureCollection("ft:" + ft)

    '''
    #test_fc = ee.FeatureCollection(
    #    ee.Feature(ee.Geometry.Point(-74, -7.902456)))
    task = ee.batch.Export.table.toDrive(alerts_fc, description='ExportClusterTask',
                folder=None, fileNamePrefix='clust', fileFormat='geoJSON')

    state = task.status()['state']
    while state in ['READY', 'RUNNING']:
        print state + '...'
        time.sleep(1)
        state = task.status()['state']
    print 'Done.', task.status()
    print 'Completed task', task

    task2 = ee.batch.Export.table.toCloudStorage({
        'collection': alerts_fc,
        'description': 'testname',
        'bucket': 'bfw-ee-cluster-tables',
        'fileNamePrefix': 'test_prefix',
        'fileFormat': 'CSV'
    })
    task2.start()
    state = task2.status()['state']
    while state in ['READY', 'RUNNING']:
        print state + '...'
        time.sleep(1)
        state = task2.status()['state']
    '''

    dates = alerts_fc.aggregate_count_distinct('date')
    print ('Number of different dates in alert data', dates.getInfo())

    img = ee.Image(0).byte().paint(alerts_fc, 1)
    #alert_img = img.mask(img)
    dist = img.distance(ee.Kernel.euclidean(20000, "meters"))
    cluster_img = dist.lt(18000)

    clusters = img.addBands(cluster_img).updateMask(cluster_img).reduceToVectors(
        reducer=ee.Reducer.first(),
        geometry =alerts_fc,
        geometryType ='polygon', #or bb
        scale = 1000,
        crs = "EPSG:3857",
        bestEffort = True
    )

    clusters = clusters.map(lambda f: f.convexHull(10).set({'AreaInHa': f.geometry().area(100).divide(100 * 100)}))

    #select removes unnecessary properties.
    clusters = clusters.select(['points', 'AlertsInCluster', 'AreaInHa'])

    # count totals var
    #.filterMetadata('WRS_PATH', 'equals', path)
    biggest_cluster = clusters.filter(ee.Filter.neq('AreaInHa', None)).reduceColumns(
               reducer    = ee.Reducer.max(),
                selectors  = ['AreaInHa']
            )

    total_area = clusters.filter(ee.Filter.neq('AreaInHa', None)).reduceColumns(
            reducer = ee.Reducer.sum(),
            selectors = ['AreaInHa']
        )

    '''
    Cluster Feature Collection with List of Points
    '''

    #Define a spatial filter, with distance < 10.
    distFilter = ee.Filter.withinDistance(
        distance = 10,
        leftField = '.geo',
        rightField = '.geo',
        maxError = 10
    )
    distSaveAll = ee.Join.saveAll(matchesKey = 'points', measureKey ='distance')
    clustersWithPoints = distSaveAll.apply(clusters, alerts_fc, distFilter)

    #Add a Count of points in each cluster
    clustersWithPoints = clustersWithPoints.map(lambda f: f.set({'AlertsInCluster': ee.List(ee.Feature(f).get('points')).length(),'AlertsDate': ee.Feature(ee.List(ee.Feature(f).get('points')).get(0)).get('date')     }))

    most_populous_cluster = clustersWithPoints.reduceColumns(
        reducer = ee.Reducer.max(),
        selectors= ['AlertsInCluster']
    )

    clustersWithPoints = clustersWithPoints.set(
        {
        'NumberOfAlerts:': alerts_fc.size(),
        'NumberOfClusters': clusters.size(),
        'ClustersTotalArea': total_area.get('sum'),
        'DistinctDates': dates,
        'MostAlertsInCluster': most_populous_cluster.get('max')
        }
    )
    '''
    #Replace points as a list of Features with a Multipoint array - assumes all the same date.
        reducePointProperties = function(f):
            eef = ee.Feature(f)
            glist = ee.List(eef.get('points')).map(lambda p : p.geometry())
            mp = ee.Algorithms.GeometryConstructors.MultiPoint(glist)
            return eef.set('points', mp)
        }
        clustersWithPoints = clustersWithPoints.map(reducePointProperties)

    '''
    clustersWithPoints = clustersWithPoints.map(lambda f:f.set('points', ee.Algorithms.GeometryConstructors.MultiPoint(ee.List(ee.Feature(f).get('points')).map(lambda p : ee.Feature(p).geometry()))))

    test_fc = ee.FeatureCollection([{"type": "Feature", "geometry": {"type": "Point", "coordinates": [-74.916831, -7.902456]},
      "properties": {"date": "2016-04-13T00:00:00Z"}}])

    task = ee.batch.Export.table.toDrive(clustersWithPoints, description='ExportClusterTask',
                                         folder='clusters', fileNamePrefix='clust', fileFormat='geoJSON')
    task.start()
    state = task.status()['state']
    while state in ['READY', 'RUNNING']:
        print state + '...'
        time.sleep(1)
        state = task.status()['state']
    print 'Done.', task.status()
    print 'Completed task', task

    '''
    task = ee.batch.Export.table.toCloudStorage({
        'collection': test_fc,
        'description': 'clustersWithPoints',
        'bucket': 'bfw-ee-cluster-tables',
        'fileNamePrefix': 'cluster_with_alert_points ',
        'fileFormat': 'KML'
    })
    '''

    #info = clustersWithPoints.getInfo() # won't work for big clusters
    #logging.info('Clusters With Points', info)
    return

'''
handleAlerts2Clusters
@param: area_name
Assumes area has a new fusion table
It process the data in the table to clusters.
not sure how to display the cluster yet.
maybe a new FT.
'''
def handleAlerts2Clusters(handler, area_name):
    #if not eeservice.initEarthEngineService():  # we need earth engine now.
    #    logging.error('Sorry, Server Credentials Error')
    # credentials = eeservice.EarthEngineService.credentials
    # fc = ee.FeatureCollection(fc)

    area = cache.get_area(None, area_name)
    if not area:
        area = cache.get_area(None, area_name)
        logging.error('handleAlerts2Clusters: Area not found!')
        handler.response.set_status(400)
        return handler.response.write('handleCheckForGladAlertsInAllAreas() area not found!')
    else:
        logging.debug('handleAlerts2Clusters: check-new-area-images for area_name %s', area_name)

    ret = checkGladFootprint(area_name)
    print 'checkGladFootprint: ', ret

    if area.last_alerts_raw_ft:
        clusters = alerts2Clusters(area)
        return handler.response.write('handleAlerts2Clusters() clustered!')
    else:
        handler.response.set_status(400)
        return handler.response.write('handleCheckForGladAlertsInAllAreas() No fusion table in area!')


def handleCheckForGladAlertsInAllAreas(handler):
    handler.response.set_status(500)
    return handler.response.write('handleCheckForGladAlertsInAllAreas() Not implemented!')


def checkGladFootprint(area_name):

    area = cache.get_area(None, area_name)
    if not area:
        return False

    if not eeservice.initEarthEngineService():
        logging.error('Sorry, Server Credentials Error')
        return False

    #outline is a polygon surrounding kalimantan and no other part of Indonesia.
    outline_fc = ee.FeatureCollection(ee.Feature({
        "type": "Polygon",
        "coordinates": [[
            [120.47607421874999, 4.23685605976896],
            [109.40185546874999, 4.784468966579375],
            [108.2373046875,    -2.5479878714713835],
            [116.49902343749999,-4.8282597468669755],
            [120.47607421874999, 4.23685605976896]
        ]]
    }))

    countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
    congo = countries.filterMetadata('Country', 'equals', 'Congo')
    peru = countries.filterMetadata('Country', 'equals', 'Peru')
    indonesia = countries.filterMetadata('Country', 'equals', 'Indonesia')
    kalimantan = indonesia.geometry().intersection(outline_fc)
    footprint = congo.merge(peru).merge(kalimantan)
    feat = area.get_boundary_hull_fc()
    geom = json.dumps(feat['geometry'])

    if footprint.intersects(area.boundary):
        return True
    return False


def testupdate(tableid):
    '''
    NOT CALLED
    # sql(sql=None, hdrs=None, typed=None)
    UPDATE <table_id>
    SET <column_name> = <value> {, <column_name> = <value> }*
    WHERE ROWID = <row_id>

    select p.name, p.id, l.id from
    '''
    service = apiservices.create_table_service()
    rows =  service.query().sql(sql="SELECT *  FROM %s" % (tableid)).execute()
    newtable = service.query().sql(sql="UPDATE %s SET latlong = lat ' ' long WHERE ROWID=%s" % (tableid, rows)).execute()
    logging.info("Updated Table %s ", tableid)
    return
