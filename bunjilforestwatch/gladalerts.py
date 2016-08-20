"""
#Wrappers for Global Forest Watch Glad-ALert APU Commenced 25/04/2016
@author: cgoodman. Can be shared.
# Copyright (c) 2013-16 Chris Goodman <chris@bunjilforestwatch.net>
"""


import models

'''
import csv
import numpy as np
from googleapiclient.discovery import build
from ee.batch import Export
import settings
import googleapiclient
import httplib2
import utils
import time
from google.appengine.ext import ndb
'''
import json
from google.appengine.api import urlfetch #change timeout from 5 to 60 s. https://stackoverflow.com/questions/13051628/gae-appengine-deadlineexceedederror-deadline-exceeded-while-waiting-for-htt
import urllib
import datetime
import cache
import logging
import ee
import eeservice
from googleapiclient.http import MediaIoBaseUpload
import io

import apiservices
import ee.batch
import ee.data
from google.appengine.ext import deferred


def create_table(ft_service, parent_id, schema, data=None):
    """
    create_table() creates a fusion table with the provided schema using the service accounts permisisons
    The table belongs to the app's service account.
    create_table() makes the table visible to anyone with the link.
    @service - see create_table_service()
    @param schema: the name, description and structure of the table. See: https://developers.google.com/tables/docs/v2/reference/table/insert
    @param data optionally describes the row data to import. - See https://developers.google.com/fusiontables/docs/v2/reference/table/importRows
    """
    drive_service = apiservices.create_drive_service()
    newtable = ft_service.table().insert(body=schema).execute()
    fileId = newtable["tableId"]

    file = drive_service.files().get(fileId=fileId,
                                     fields='parents').execute();

    previous_parents = ",".join(file.get('parents'))
    # Move the file to the new folder
    file_metadata = {
        'mimeType': 'application/vnd.google-apps.fusiontable'
    }
    file = drive_service.files().update(fileId=fileId,
                                        body=file_metadata,
                                        addParents=parent_id,
                                        removeParents=previous_parents,
                                        fields='id, parents').execute()

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

def createAlertsFusionTable(name, parent_id, since_date_str, to_date_str, alerts):

    """
    Creates a fusion table to store GLAD alerts from GFW.
    #This schema maps to the unprocessed CSV from GFW.
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
    """

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
    newtable = create_table(service, parent_id, schema=targetschema, data=alerts)
    return newtable

def saveRawAlerts(name, parent_id, since_date_str, to_date_str, alerts):
    """
    Creates a copy of the raw CASV data from from GFW - for debugging and comparing DBSCAN can remove from production
    """
    filename = 'RAWGLAD_' + name + '_from_' + since_date_str + '_to_' + to_date_str
    file_id = apiservices.create_file(filename, parentID=parent_id, drive_service=None, raw_data=alerts)


def handleCheckForGladAlertsInArea(handler, area, noupdate=None):
    """
    Checks GFW GLAD API for new alerts in area for new period.
    Updates area with fusion table and new date.
    Calls alerts2cluster
    @params noupdate: If set, function does not update area.last_alerts_date to today
    @returns a string which may be an error message.
    """

    if area.glad_monitored == False:
        handler.response.set_status(400)
        return "Area %s not monitored by GLAD Alerts" % area.name

    feat = area.get_boundary_hull_geojson()
    geom = json.dumps(feat['geometry'])

    today_dt = datetime.datetime.today()
    today_str = today_dt.strftime('%Y-%m-%d')  #today_str = '2016-05-18'

    if area.last_alerts_date <> None:
        since_date = area.last_alerts_date.strftime('%Y-%m-%d')
    else:
        since_date_dt = today_dt - datetime.timedelta(days=30) # no alerts have been collected yet. So collect last 30 days.
        since_date = since_date_dt.strftime('%Y-%m-%d')

    # call the API
    table_name = area.name + "-" + since_date + "-" + today_str
    parent_id = area.folder()
    try:
        #alerts_result, ft, count
        resp = getAlerts('glad-alerts', geom, table_name, since_date, today_str, 'csv', parent_id)
    except TypeError, e:
        handler.response.set_status(500)
        logging.error("getAlerts() TypeError exception %s %s" %(e, geom))
        return "handleCheckForGladAlertsInArea()  TypeError exception - no data? %s" % e
    if resp['status'] == 200:
        msg = "<b>handleCheckForGladAlertsInArea()</b> between %s and %s " %(since_date, today_str)
        if resp['download_response'].status_code == 200:
            if resp['fusiontable'] and resp['count'] > 0:
                if not noupdate:
                    area.last_alerts_date = today_dt
                else:
                    logging.info('Noupdate requested - not updating last_alerts_date')

                area.last_alerts_raw_ft = resp['fusiontable']['tableId']
                area.put()
                msg += "Created Fusion Table: " + \
                      apiservices.fusiontable_url(resp['fusiontable']['tableId'], resp['fusiontable']['name']) + \
                      ' with ' + str(resp['count']) + 'alerts.'
                """
                Cluster the Alerts
                """
                msg += alerts2Clusters(area, True)
                return msg
            else:
                area.last_alerts_date = today_dt
                area.put()
                msg += "No Alerts returned."
            return msg
        else:
            msg += "<b>Error:</b> " + area.name + \
                str(resp['download_response'].content) + ' payload:' + json.dumps(geom)
            handler.response.set_status(resp['download_response'].status_code)
            return msg
    else:
        handler.response.set_status(resp['status'])
        return "Exception in glad API %s" %resp['msg']


def getAlerts(alert_type, polygon, table_name, since_date, to_date, format, parent_id):
    """
    getAlerts() calls Global Forest Watch API https://github.com/wri/gfw-api
    @param: alert_type, example 'glad-alerts', 'forma-alerts'
    @param: polygon is a GeoJSON encoded Polygon or MultiPolygon
    @param: since_date, alerts from this date inclusive. 'YYYY-MM-DD'
    @param: to_date, alerts to this date inclusive. 'YYYY-MM-DD'
    @param: format, one of 'geojson', 'csv', 'kml', 'shp', or 'svg'. Only kml is really supported.
    @parent_id: Google Drive Folder where documents are saved

    Get GLAD ALERTS for an area since the give date.
    Calls GFW with the boundary  of a given an AreaOfInterest
    @returns: gladresponse = {
        'geturl_response': None,
        'download_response': None,
        'fusiontable': None,
        'alert count': 0,
        'status_code': 0,
        'errormsg': "OK"
    }
    If status_code is 200, then get_download_response contains a list of GLAD alerts as a JSON dictionary
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
      {"type":"Polygon","coordinates":[[[-76.5,-7],[-76.5,-6.5],[-76,-6.5],[-76,-7],[-76.5,-7]]]}
    """
    resp = {
        'geturl_response': None,
        'download_response': None,
        'fusiontable': None,
        'count': 0,
        'status': 0,
        'msg': "OK"
    }
    if since_date == to_date:
        resp['msg'] = 'getAlerts: SKIPPING - since_date and to_date are the same %s' %to_date
        resp['status'] = 400
        logging.warning(resp['msg'])
        return resp
        #return {'content': msg, 'status_code': '400'}, None, 0

    url= 'http://api.globalforestwatch.org/forest-change/' + alert_type + \
         '?period=' + since_date + ',' + to_date

    request_payload = urllib.urlencode({
        'geojson': polygon
    })

    try:
        resp['geturl_response'] = urlfetch.fetch(url,
                                method='POST',
                                deadline=15,
                                payload=request_payload
                                )

        if resp['geturl_response'].status_code == 200:
            logging.debug('getAlerts: getdownload url OK')
            try:
                apiresult = json.loads(resp['geturl_response'].content)
                download_url = apiresult["download_urls"][format]
            except KeyError, k:
                #logging.error("Could not parse download_url in response")
                #resp['geturl_response'].content += ': KeyError'
                #return resp['geturl_response'], None, 0
                resp['msg'] = 'Could not parse download_url in response'
                resp['status'] = 400
                logging.error(resp['msg'])
                return resp

            except TypeError, e:
                #logging.error("Could not parse download_url in response %s ", e)
                #resp['geturl_response'].content += ': TypeError'
                #return resp['geturl_response'], None, 0
                resp['msg'] = "Could not parse download_url in response %s " %e
                resp['status'] = 400
                logging.error(resp['msg'])
                return resp

            #logging.debug('getAlerts: download url: %s', download_url)
            try:
                resp['download_response'] = urlfetch.fetch(download_url,
                                method='GET',
                                deadline=60
                                )
                try:
                    logging.debug('resp.download_response: %s ', resp['download_response'].status_code)

                    if resp['download_response'].status_code == 200:
                        #print 'resp['download_response']: ', resp['download_response']
                        if format == 'csv':
                            resp['fusiontable'], resp['count'] = handleAlertDataCSV(table_name, parent_id, since_date, to_date, resp['download_response'].content)
                            #return resp['download_response'], ft, count
                            resp['status'] = 200
                            return resp

                        else:
                            #logging.error('getAlerts() format not recognised. Use csv %s', format)
                            #return resp['download_response'], None, 0
                            resp['msg'] = 'getAlerts() format not recognised. Use csv %s', format
                            resp['status'] = 400
                            logging.error(resp['msg'])
                            return resp
                    else:
                        #logging.error("getAlerts() Downloading URL error %s", download_alerts_response.status_code)
                        resp['msg'] = "getAlerts() Downloading URL error %s" %resp['download_response'].status_code
                        resp['status'] = resp['download_response'].status_code
                        logging.error(resp['msg'])
                        return resp
                except Exception as e:
                    #logging.error('Exception processing download result: %s' %e)
                    resp['msg'] = "getAlerts()Exception processing download result: %s" %e
                    resp['status'] = 500
                    logging.error(resp['msg'])
                    return resp

            except urlfetch.InvalidURLError:
                #logging.error("Download URL is an empty string")
                #return {'content': 'Download URL is an empty string', 'status_code': '500'}, None, 0
                resp['msg'] = "Download URL is an empty string"
                resp['status'] = 500
                logging.error(resp['msg'])
                return resp

            except urlfetch.DownloadError:
                #logging.error("Download Server cannot be contacted")
                #return {'content': 'Download Server cannot be contacted', 'status_code': '500'}, None, 0
                resp['msg'] = "Download Server cannot be contacted %s" %download_url
                resp['status'] = 503
                logging.error(resp['msg'])
                return resp

            except Exception as e:
                #logging.error('Download Server exception %s', e)
                #return {'content': 'Exception in Download URL', 'status_code': '500'}, None, 0
                resp['msg'] = "Exception contacting Download Server: %s" %e
                resp['status'] = 503
                logging.error(resp['msg'])
                return resp

        #logging.error("Download URL returned error: %s" %(resp['download_response'].status_code))
        #return {'content': 'Download URL returned error', 'status_code': resp['download_response'].status_code}, None, 0
        resp['msg'] = 'Download URL returned error: %s' %(resp['download_response'].status_code)
        resp['status'] = resp['download_response'].status_code
        logging.error(resp['msg'])
        return resp

    except urlfetch.InvalidURLError:
        #logging.error("GetAlerts URL is an empty string or invalid")
        #return {'content': 'GetAlerts URL is an empty string or invalidL', 'status_code':'500' }, None, 0
        resp['msg'] = 'GetAlerts URL is an empty string or invalid'
        resp['status'] = 400
        logging.error(resp['msg'])
        return resp

    except urlfetch.DownloadError:
        #logging.error("GetAlerts Server cannot be contacted")
        #return {'content': 'GetAlerts Server cannot be contacted', 'status_code':'500' }, None, 0
        resp['msg'] = 'GetAlerts Server cannot be contacted %s' %url
        resp['status'] = 400
        logging.error(resp['msg'])
        return resp


def convertCSVForFusion(csvdata):
    """
    convertCSVForFusion()

    @param csvdata: Expects data, database, lat, long\n

    1. Removes the headings in first row
    2. Creates new headings to match FT.
    2. Strips out the cartodb DB reference column
    3. Joins lat and long into a single column
    4. returns new data and number of alerts converted.
    """
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
            #print s
            converted_data += s
    logging.info("convertCSVForFusion()num alerts: %d , %s", alertcount, len(converted_data))
    return converted_data, alertcount

def handleAlertDataCSV(table_name, parent_id, since_date, to_date, csvdata):
    """
    @returns: a id of a new  fusion table, and the number of alerts received, or None, 0
    """

    if csvdata:
        converted_data, count = convertCSVForFusion(csvdata)
        if count:
            logging.debug('handleAlertDataCSV() %d alerts', count)
            ft = createAlertsFusionTable(table_name, parent_id, since_date, to_date, converted_data)
            saveRawAlerts(table_name, parent_id, since_date, to_date, csvdata)
            return ft, count
        else:
            logging.warning('handleAlertDataCSV() No alerts')
            return None, 0
    else:
        logging.error('handleAlertDataCSV() No input data')
        return None, 0



def alerts2Clusters(area, create_task=True):
    """
    alerts2Clusters() calls Earth Engine to process the alerts to a FeatureCollection
    It Clusters alert points into polygons.
    Based on an answer from Noel Gorelich, GoogleGroups April 27 2016
    https://groups.google.com/d/msg/google-earth-engine-developers/3Oq1t9dBUqE/ft50BYTxDQAJ
    Updated EarthEngine Code at https://code.earthengine.google.com/046c8e9074f9a9f2f4442dd53ce7ef94

    @param area: an Area of Interest - reads the last raw alerts fusion table ID.
    eps = 600 (eps): the radius to look for neighbours.
    """

    eps = 600 #(eps): the radius to look for neighbours.

    if not eeservice.initEarthEngineService():
        logging.error('Sorry, Server Credentials Error')
        return "Could not connect to Earth Engine"
    ft = area.last_alerts_raw_ft

    raw_alerts_fc = ee.FeatureCollection("ft:" + ft)

    num_alerts = raw_alerts_fc.size().getInfo()  # rows in ft = alerts for all dates.
    date_count = raw_alerts_fc.aggregate_count_distinct('date').getInfo()
    distinct_dates = raw_alerts_fc.distinct('date').sort('date', False) #false orders so first date is latest.
    latest_date_iso = distinct_dates.first().get("date").getInfo()
    latest_date = ee.Date(latest_date_iso).getInfo()

    #print 'latest_date_iso', latest_date_iso
    #print 'latest_date', latest_date

    alerts_fc = raw_alerts_fc.filterMetadata("date", "equals", latest_date_iso)

    latest_alerts = alerts_fc.size().getInfo() #number of alerts with latest date

    img = ee.Image(0).byte().paint(alerts_fc, 1)
    dist = img.distance(ee.Kernel.manhattan(eps * 6, "meters"), True)
    cluster_img = dist.lt(eps * 1)

    clusters = img.addBands(cluster_img).updateMask(cluster_img).reduceToVectors(
        reducer=ee.Reducer.first(),
        geometry=alerts_fc,
        geometryType='polygon', #or bb
        scale=eps,
        crs = "EPSG:3857",
        bestEffort = True
    )

    buffer = eps * 0.1
    clusters = clusters.map(lambda f: f.buffer(buffer, buffer).set({'AreaInHa': f.geometry().area(100).divide(100 * 100)}))

    #select removes unnecessary properties.
    clusters = clusters.select(['points', 'AlertsInCluster', 'AreaInHa'])

    #hulls = clusters.map(lambda f: f.convexHull(10)) # not using convex Hulls.


    """
    Join Cluster Feature Collection with List of Points
    """

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
    clustersWithPoints = clustersWithPoints.map(lambda f: f.set({
        'AlertsInCluster': ee.List(ee.Feature(f).get('points')).length(),
        'AlertsDate': ee.Feature(ee.List(ee.Feature(f).get('points')).get(0)).get('date'),
        # Add a pink border and no fill styling for geojson.io
        "stroke": "#ff6fb7",
        "stroke-width": 1,
        "fill-opacity": "0.0",
    }))

    most_populous_cluster = clustersWithPoints.reduceColumns(
        reducer=ee.Reducer.max(),
        selectors=['AlertsInCluster']
    )

    since_date = area.last_alerts_date.strftime('%Y-%m-%d')

    today_dt = datetime.datetime.today()
    today_str = today_dt.strftime('%Y-%m-%d')  #today_str = '2016-05-18'

    num_clusters = clusters.size().getInfo()

    foldername = area.name
    filename = area.name + "_GLADClusters_"
    if since_date:
        filename += "Since_" + since_date

    clusterProperties = {
        'name': 'gladclusters',
        'filename': filename,
        'epsilon': eps,
        'area': area.name,
        'ft': 'https://www.google.com/fusiontables/DataSource?docid=' + ft,
        'since_date': since_date,
        'clustered_date': today_str,
        'alerts_date': latest_date_iso, #iso format
        'num_alerts:': latest_alerts,  # Alerts with Latest Date only
        'num_clusters': num_clusters,
        'distinct_dates': date_count,
        'num_alerts_alldates': num_alerts,
        'most_alerts_in_cluster': most_populous_cluster.get('max').getInfo()
    }

    """
    clustersWithPoints = clustersWithPoints.set('name', 'gladclusters',
        'epsilon', eps,
        'area', area.name,
        'ft', 'https://www.google.com/fusiontables/DataSource?docid=' + ft,
        'since_date', since_date,
        'clustered_date', today_str,
        'alerts_date', latest_date_iso, #iso format
        'num_alerts:', latest_alerts,  # Alerts with Latest Date only
        'num_clusters', num_clusters,
        'distinct_dates', date_count,
        'num_alerts_alldates', num_alerts,
        'most_alerts_in_cluster', most_populous_cluster.get('max').getInfo()
    )
    """
    clustersWithPoints = clustersWithPoints.set(clusterProperties)

    clustersWithPoints = clustersWithPoints.map(
        lambda f:f.set('points', ee.Algorithms.GeometryConstructors.MultiPoint(
            ee.List(ee.Feature(f).get('points')).map(lambda p : ee.Feature(p).geometry()))))

    print clustersWithPoints.propertyNames().getInfo()


    task = ee.batch.Export.table.toDrive(clustersWithPoints, description=area.name + ' Clusters',
                                         folder=foldername, fileNamePrefix=filename, fileFormat='geoJSON')
    """@change drive to cloud?
        task = ee.batch.Export.table.toCloudStorage({
            'collection': test_fc,
            'description': 'clustersWithPoints',
            'bucket': 'bfw-ee-cluster-tables',
            'fileNamePrefix': 'cluster_with_alert_points ',
            'fileFormat': 'KML'
        })
    """
    task.start()

    if create_task:
        #wait for export to finish then create a task.
        deferred.defer(check_export_status, task.id, clusterProperties, _countdown=10, _queue="export-check-queue")
        logging.info("Started task to export GLAD Cluster")
    return "Exporting alerts to GLAD Cluster"


def check_export_status(task_id, clusterProperties):
    logging.debug("check_export_status() for area %s task %s", clusterProperties['area'], task_id)
    # Do your work here
    try:
        result = ee.data.getTaskStatus(task_id)[0]
    except:
        return "Exception task not found %s" %(task_id)

    state = result['state']
    msg = 'Export glad cluster for area %s is %s' %(clusterProperties['area'], state)
    if state in ['READY', 'RUNNING']:
        logging.debug(msg)
        deferred.defer(check_export_status, task_id, clusterProperties,
                       _countdown=10, _queue="export-check-queue")
    elif state in ['COMPLETED']:
        logging.info(msg)
        #CREATE A TASK
        try:
            area = cache.get_area(clusterProperties['area'])
            clusterProperties['file_id'] = area.get_gladcluster_file_id()
            createGladClusterEntries(area)
            new_observations = []
            obs = models.Observation.createGladAlertObservation(area, clusterProperties)
            if obs is not None:
                new_observations.append(obs.key)
                area_followers = models.AreaFollowersIndex.get_by_id(area.name, parent=area.key)
                if area_followers:
                    models.ObservationTask.createObsTask(area, new_observations, "GLADCLUSTER", area_followers.users)
        except Exception as e:
            msg = "Exception creating GLAD ObservationTask {0!s}".format(e)
            logging.error(msg)
            return msg
    else:
        logging.info(msg)
    return msg


def get_gladcluster_list(gladcluster_geojson_str):
    """
    returns a list of geojson objects each only containing one glad cluster.
    """
    gladcluster_geogjson_collection = []
    gladcluster_geojson_obj = json.loads(gladcluster_geojson_str)

    for cluster in gladcluster_geojson_obj["features"]:
        gladcluster_geojson_str = {
            "type": "FeatureCollection",
            "features": [
                cluster
            ]
        }
        gladcluster_geogjson_collection.append(gladcluster_geojson_str)

    return gladcluster_geogjson_collection

#TODO: rename this method so that it conveys that a case will also be created.
def createGladClusterEntries(area):
    """
    Creates an entry in the data store for each glad cluster in a given area
    """
    gladcluster_geogjson_collection = get_gladcluster_list(area.get_gladcluster())
    for cluster in gladcluster_geogjson_collection:
        cluster_key = models.GladCluster(area=area.Key, geo_json=cluster)
        cluster_key.put()
        #TODO: create cases for each cluster

def handleAlerts2Clusters(handler, area_name):
    """
    handleAlerts2Clusters() takes the latest ft and clusters it.
    This can be called separately by /admin/alerts/glad2clusters/<area_name>
    or as part of the call to handleCheckForGladAlertsInArea() if new alerts are found.

    @param: area_name
    Assumes area has a new fusion table
    It process the data in the table to clusters.
    not sure how to display the cluster yet.
    maybe a new FT.
    """

    area = cache.get_area(area_name)
    if not area:
        area = cache.get_area(area_name)
        logging.error('handleAlerts2Clusters: Area not found!')
        handler.response.set_status(400)
        return handler.response.write('handleCheckForGladAlertsInAllAreas() area not found!')
    else:
        logging.debug('handleAlerts2Clusters: Clustering latest fusion table for area_name %s', area.name)

    if area.last_alerts_raw_ft:
        cluster_msg = alerts2Clusters(area, True)
        return handler.response.write('handleAlerts2Clusters() %s' %cluster_msg)
    else:
        handler.response.set_status(400)
        return handler.response.write('handleCheckForGladAlertsInAllAreas() No fusion table in area!')

def handleCheckForGladAlertsInAllAreas(handler):
    handler.response.set_status(500)
    return handler.response.write('handleCheckForGladAlertsInAllAreas() Not implemented!')


def testupdate(tableid):
    """
    NOT CALLED
    # sql(sql=None, hdrs=None, typed=None)
    UPDATE <table_id>
    SET <column_name> = <value> {, <column_name> = <value> }*
    WHERE ROWID = <row_id>

    select p.name, p.id, l.id from
    """
    service = apiservices.create_table_service()
    rows =  service.query().sql(sql="SELECT *  FROM %s" % (tableid)).execute()
    newtable = service.query().sql(sql="UPDATE %s SET latlong = lat ' ' long WHERE ROWID=%s" % (tableid, rows)).execute()
    logging.info("Updated Table %s ", tableid)
    return

def geometryIsInGladAlertsFootprint(geom):
    """
     @returns: true if geom is in the glad footprint - 2016.
     @param: geom an ee.Geometry
    """
    return gladalerts_footprint_fc().geometry().intersects(geom, 100).getInfo()

def gladalerts_footprint_fc():
    """
     GLAD Alerts footprint.
     Geographic range of glad alerts in 2016
     @returns: an ee.FeatureCollection of the GLAD ALERT footprint- 2016.
     @FIXME - Currently the returned footprint includes all of Peru,
              not just 'humid tropical Peru'
    """

    if not eeservice.initEarthEngineService():
        logging.error('Sorry, Server Credentials Error')
        return False

    #outline is a polygon surrounding kalimantan and no other part of Indonesia.
    outline_fc = ee.FeatureCollection(ee.Feature({
        "type": "Polygon",
        "coordinates": [[
            [120.47607421874999, 4.23685605976896],
            [109.40185546874999, 4.784468966579375],
            [108.2373046875, -2.5479878714713835],
            [116.49902343749999, -4.8282597468669755],
            [120.47607421874999, 4.23685605976896]
        ]]
    }))
    countries = ee.FeatureCollection('ft:1tdSwUL7MVpOauSgRzqVTOwdfy17KDbw-1d9omPw')
    congo = countries.filterMetadata('Country', 'equals', 'Congo')
    peru = countries.filterMetadata('Country', 'equals', 'Peru')
    indonesia = countries.filterMetadata('Country', 'equals', 'Indonesia')
    kalimantan = indonesia.geometry().intersection(outline_fc)
    footprint = congo.merge(peru).merge(kalimantan)
    return footprint



def forestchange_stats(testfeature):
    """
    @returns a dictionary of forst stats from UMD forest change
    """
    umdImage = ee.Image('UMD/hansen/global_forest_change_2015').clip(testfeature).multiply(ee.Image.pixelArea())
    area = parseFloat(testfeature.area().getInfo())

    # calculate loss since 2000
    lossImage = umdImage.select(['loss'])
    loss_stats = lossImage.reduceRegion({
        reducer: ee.Reducer.sum(),
        geometry: testfeature,
        maxPixels: 5e9
    })

    loss_area = parseFloat(loss_stats.get('loss').getInfo())
    percent_loss = loss_area * 100 / area

    # calculate tree cover in  2000
    treecover2000Image = umdImage.select(['treecover2000']);
    treecover2000_stats = treecover2000Image.reduceRegion({
        reducer: ee.Reducer.sum(),
        geometry: testfeature,
        maxPixels: 5e9
    })
    treecover2000_area = parseFloat(treecover2000_stats.get('treecover2000').getInfo())
    percent_treecover2000 = treecover2000_area / area;  # @FIXME - why no *100 ?

    results = {
        'area': area,
        'treecover2000': treecover2000_area,
        'percent_treecover2000': percent_treecover2000,
        'loss_area': loss_area,
        'percent_loss': percent_loss,
    }
    return results


def testupdate(tableid):
    """
    NOT CALLED
    # sql(sql=None, hdrs=None, typed=None)
    UPDATE <table_id>
    SET <column_name> = <value> {, <column_name> = <value> }*
    WHERE ROWID = <row_id>

    select p.name, p.id, l.id from
    """
    service = apiservices.create_table_service()
    rows =  service.query().sql(sql="SELECT *  FROM %s" % (tableid)).execute()
    newtable = service.query().sql(sql="UPDATE %s SET latlong = lat ' ' long WHERE ROWID=%s" % (tableid, rows)).execute()
    logging.info("Updated Table %s ", tableid)
    return
