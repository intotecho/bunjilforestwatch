import wsgiref.handlers
import xml.dom.minidom
from urllib import quote
import geohash
import traceback
import sys
import time
import os
import logging
import pickle

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.api import memcache

MEMCACHE_GEORSSTEMPLATE = 'georss_template'
MEMCACHE_GEOMETRYBYDATE = 'geometry_bydate'
MEMCACHE_GEOMETRYALL = 'geometry_all'

class Geometry(db.Model):
  name = db.StringProperty()
  description = db.StringProperty(multiline=True)
  type = db.StringProperty()
  dateModified = db.DateProperty(auto_now=True)
  coordinates = db.ListProperty(db.GeoPt, default=None)
  timeStamp = db.DateProperty(auto_now_add=True)
  altitudes = db.ListProperty(float, default=None)
  userId = db.StringProperty(default=None)
  tags = db.ListProperty(unicode,default=None)
  bboxEast = db.FloatProperty()
  bboxWest = db.FloatProperty()
  bboxSouth = db.FloatProperty()
  bboxNorth = db.FloatProperty()
  geohash = db.StringProperty()

  def georssPoint(self):
    lat = float(self.coordinates[0].lat)
    lon = float(self.coordinates[0].lon)
    return ('%s %s' % (lat, lon))

  def georssBox(self):
    return ('%s %s %s %s' % (self.bboxSouth, self.bboxWest, self.bboxNorth,
                             self.bboxEast))

def getCoordinates(gp):
    lat,lon = 0.0,0.0
    try:
      lat = float(gp.lat)
      lon = float(gp.lon)
    except TypeError, ValueError:
      lat = 0.0
      lon = 0.0
    return lat,lon

def GetCurrentRfc822Time():
  now = time.gmtime()
  #YYYY-MM-DDTHH:MM:SSZ
  return time.strftime('%Y-%m-%dT%H:%M:%SZ', now)

def jsonOutput(geometries, operation): 
  geoJson = []
  geoJson.append("{operation: '%s', status: 'success', result:{geometries:{" % operation)
  geoJson.append('records:[')

  points = []
  for geometry in geometries:
    coords = []
    for gp in geometry.coordinates:
      lat, lon = getCoordinates(gp)
      coords.append('lat: %s, lng: %s' % (lat, lon))
    altitudes = '[0.0]'
    alt = geometry.altitudes
    bbox = ('{bboxWest: %s, bboxEast: %s, bboxSouth: %s, bboxNorth:%s}' % (geometry.bboxWest,geometry.bboxEast,geometry.bboxSouth,geometry.bboxNorth))
    if alt != []:
      altitudes = '[%s]' % (','.join('%f' % a for a in alt))
    coordinates = '[{%s}]' % ('},{'.join(coords))
    points.append("{key: '%s', userId: '%s', name: '%s', type: '%s', description: '%s', timeStamp: '%s', coordinates: %s, altitudes: %s, bbox: %s}" % (geometry.key(), geometry.userId, quote(geometry.name.encode('utf-8'),' '),geometry.type, quote(geometry.description.encode('utf-8'),' '),geometry.timeStamp, coordinates, altitudes,bbox))

  geoJson.append(','.join(points))
  geoJson.append(']}}}')
  geoJsonOutput = ''.join(geoJson)
  contentType = 'text/javascript'
  return geoJsonOutput, contentType

def georssOutput(geometries):
  georssTemplate = memcache.get(MEMCACHE_GEORSSTEMPLATE)
  if georssTemplate is None:
    template_values = {'geometries' : geometries,
                    'now' : GetCurrentRfc822Time() }
    path = os.path.join(os.path.dirname(__file__), 'georssfeed.xml')
    georssTemplate = template.render(path, template_values)
    memcache.set(MEMCACHE_GEORSSTEMPLATE, georssTemplate)

  contentType = 'text/xml'
  return georssTemplate, contentType

def kmlOutput(geometries,bboxWest=None,bboxSouth=None,bboxEast=None,bboxNorth=None):
  # This creates the core document.
  kmlDoc = xml.dom.minidom.Document()

  # This creates the root element in the KML namespace.
  kml = kmlDoc.createElementNS('http://earth.google.com/kml/2.2','kml')
  kml.setAttribute('xmlns','http://earth.google.com/kml/2.2')

  # This appends the root element to the document.
  kml = kmlDoc.appendChild(kml)

  # This creates the KML Document element and the styles.
  document = kmlDoc.createElement('Document')
    
  for geometry in geometries:
    createPlace = True
    if bboxWest != None:
      if geometry.bboxWest > bboxWest and  geometry.bboxEast < bboxEast and geometry.bboxNorth < bboxNorth and geometry.bboxSouth > bboxSouth:
        createPlace = True
      else:
        createPlace = False
    if createPlace == True:
      place = kmlDoc.createElement('Placemark')
      name = kmlDoc.createElement('name')
      textNode = kmlDoc.createTextNode(geometry.name)
      name.appendChild(textNode)
      place.appendChild(name)
      description = kmlDoc.createElement('description')
      textNode = kmlDoc.createTextNode(geometry.description)
      description.appendChild(textNode)
      place.appendChild(description)
      coordString = createCoordinateString(geometry.coordinates,geometry.altitudes)
      coords = kmlDoc.createElement('coordinates')
      coordsText = kmlDoc.createTextNode(coordString)
      coords.appendChild(coordsText)
    
      if geometry.type == 'point':
        point = kmlDoc.createElement('Point')
        point.appendChild(coords)
        place.appendChild(point)

      elif geometry.type == 'poly':
        polygon = kmlDoc.createElement('Polygon')
        outerBounds = kmlDoc.createElement('outerBoundaryIs')
        polygon.appendChild(outerBounds)
        outerBounds.appendChild(coords)
        place.appendChild(polygon)

      elif geometry.type == 'line':
        line = kmlDoc.createElement('LineString')
        line.appendChild(coords)
        place.appendChild(line)
     
      document.appendChild(place)
  kml.appendChild(document)
  contentType = 'application/vnd.google-earth.kml+xml' 
  return kmlDoc.toprettyxml(encoding="utf-8"), contentType

def createCoordinateString(gps, alts):
  coordinateString = []
  for gp in gps:
    altIterator = 0
    lat,lon = getCoordinates(gp)
    altitude = 0.0
    try:
      altitude = alts[altIterator]
    except IndexError:
      altitude = 0.00
    coordinateString.append('%s,%s,%s' % (lon, lat, altitude))
    altIterator += 1
  return ' '.join(coordinateString)

def computeBBox(lats,lngs):
  flats = map(float,lats)
  flngs = map(float,lngs)
  west = min(flngs)
  east = max(flngs)
  north = max(flats)
  south = min(flats)

  return west, south, east, north

def clearMemcache():
  memcache.delete(MEMCACHE_GEOMETRYBYDATE)
  memcache.delete(MEMCACHE_GEOMETRYALL)
  memcache.delete(MEMCACHE_GEORSSTEMPLATE)
  
class Request(webapp.RequestHandler):
  def post(self):
    self.operationPicker()

  def get(self):
    self.operationPicker()

  def operationPicker(self):
      operation = self.request.get('operation')
      out,contentType = '',''
      if operation == 'add':
        out,contentType = self.addGeometries()
      elif operation == 'edit':
        out,contentType = self.editGeometries()
      elif operation == 'delete':
        out,contentType = self.deleteGeometries()
      else:
        out,contentType = self.getGeometries()
      self.response.headers['Content-Type'] = contentType
      self.response.out.write(out)

  def getGeometries(self):
    limit = self.request.get('limit',default_value=10)
    output = self.request.get('output',default_value='json')
    userid = self.request.get('userid',default_value=None)
    
    query = []
    type = self.request.get('type',default_value=None)
    distance = self.request.get('distance',default_value=None)
    bbox = self.request.get('BBOX', default_value=None)
    qryString = ''
    argsString = ''
    if type: 
      query.append("type = '%s'" % type)
    if userid: 
      query.append("userId = '%s'" % userid)

    bboxWest = None
    bboxSouth = None
    bboxEast = None
    bboxNorth = None

    if bbox:
      bboxList = bbox.split(',')
      bboxWest = float(bboxList[0])
      bboxSouth = float(bboxList[1])
      bboxEast = float(bboxList[2])
      bboxNorth = float(bboxList[3])
    queryString = '' 
    if len(query) > 0:
      queryString = 'WHERE %s LIMIT %s' % (' and '.join(query), limit)

    if (output == 'georss'):
      geometriesPickled  = memcache.get(MEMCACHE_GEOMETRYBYDATE)
      if geometriesPickled is None:
        query = Geometry.all()
        query.order('-dateModified')
        geometries = query.fetch(limit=20)
        if not memcache.set(MEMCACHE_GEOMETRYBYDATE, pickle.dumps(geometries)):
          logging.debug('Memcache set failed')
      else:
        geometries = pickle.loads(geometriesPickled)
    elif (len(query) == 0):
      geometriesPickled  = memcache.get(MEMCACHE_GEOMETRYALL)
      if geometriesPickled is None:
        query = Geometry.all()
        geometries = query.fetch(limit=limit)
        if not memcache.set(MEMCACHE_GEOMETRYALL, pickle.dumps(geometries)):
          logging.debug('Memcache set failed')
      else:
        geometries = pickle.loads(geometriesPickled)
    else: 
      geometries = Geometry.gql(queryString)

    outputAction = {'json': jsonOutput(geometries,'get'),
                    'kml': kmlOutput(geometries,bboxWest,bboxSouth,bboxEast,bboxNorth),
                    'georss': georssOutput(geometries)}
    out,contentType = outputAction.get(output)
    return out,contentType

  def addGeometries(self):
    try:
      lat = self.request.get('lat',allow_multiple=True,default_value=0.0)
      lng = self.request.get('lng',allow_multiple=True,default_value=0.0)
      name = self.request.get('name',default_value = '')
      alts = self.request.get('alt', allow_multiple=True, default_value=0.0)
      tags = self.request.get('tag', allow_multiple=True, default_value=None)
      user = users.GetCurrentUser()
      userid=None
      if user:
        userid=user.email()
      west, south, east, north = computeBBox(lat,lng)
      coords = []
      for i in range(0, len(lat)):
        gp = db.GeoPt(lat[i], lng[i])
        coords.append(gp)
      altitudes = []
      for alt in alts:
        altitudes.append(float(alt))
      description = self.request.get('description')
      type = self.request.get('type',default_value='point')
      hash = None
      if type == 'point':
        hash = str(geohash.Geohash((float(lat[0]), float(lng[0]))))
      gp = Geometry(name=name, description=description, type=type,
                    coordinates=coords, altitudes=altitudes,
                    tags=tags, bboxEast=east, bboxWest=west,
                    bboxSouth=south, bboxNorth=north, userId=userid,
                    geohash=hash)

      gp.put()
      gps = []
      gps.append(gp)
      clearMemcache();
      jsonResponse,contentType = jsonOutput(gps,'add')

    except TypeError, ValueError:
      jsonResponse="{error:{type:'add',lat:'%s',lng:'%s'}}" % (lat[0], lng[0])
      contentType = 'text/javascript'
    return jsonResponse,contentType

  def editGeometries(self):
    try:
      lat = self.request.get('lat',allow_multiple=True,default_value=0.0)
      lng = self.request.get('lng',allow_multiple=True,default_value=0.0)
      name = self.request.get('name',default_value = '')
      alts = self.request.get('alt', allow_multiple=True, default_value=0.0)
      tags = self.request.get('tag', allow_multiple=True, default_value=None) 
      key = self.request.get('key')
      west, south, east, north = computeBBox(lat,lng)
      coords = []
      for i in range(0, len(lat)):
        gp = db.GeoPt(lat[i], lng[i])
        coords.append(gp)

      description = self.request.get('description')
      type = self.request.get('type',default_value='point')

      gp = Geometry.get(key)
      gp.name = name
      gp.description=description
      gp.type=type
      gp.coordinates=coords
      gp.altitudes=alts
      gp.tags=tags
      gp.bboxEast=east
      gp.bboxWest=west
      gp.bboxSouth=south
      gp.bboxNorth=north
      gp.put()
      gps = [gp]
      gps.append(gp)
      clearMemcache();
      jsonResponse,contentType = jsonOutput(gps, 'edit')

    except TypeError, ValueError:
      jsonResponse="{error:{type:'edit',key:'%s'}}" % self.request.get('key')
      contentType = 'text/javascript'
    return jsonResponse,contentType


  def deleteGeometries(self):
    success = "success"

    try:
      key = str(self.request.get('key'))
      gp = Geometry.get(key)
      gp.delete()
      jsonResponse = "{operation:'delete',status:'success',key:'%s'}" % key
    except:
      jsonResponse = "{error:{type:'delete',records:{key:'%s'}}}" % self.request.get('key')
    contentType = 'text/javascript'
    clearMemcache();
    return jsonResponse,contentType

application = webapp.WSGIApplication(
                                     [
                                      ('/gen/request', Request)
                                       ],
                                     debug=False)

wsgiref.handlers.CGIHandler().run(application)
