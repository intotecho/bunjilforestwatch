import ee
import math
import ee.mapclient
import datetime
import numpy
from Bio.Statistics import lowess
from datetime import date
from matplotlib import pyplot

MY_SERVICE_ACCOUNT = '###'  # replace with your service account
MY_PRIVATE_KEY_FILE = '###'       # replace with you private key file path

ee.Initialize(ee.ServiceAccountCredentials(MY_SERVICE_ACCOUNT, MY_PRIVATE_KEY_FILE))


point = ee.Feature.Point(-123.33,44.570)
dvals = []

interval = 8

for year in range(2001,2013):
 for day in range(0,365,interval):
  start = date.fromordinal(date(year, 1, 1).toordinal() + day)
  end = date.fromordinal(date(year, 1, 1).toordinal() + day + interval)
  collection = ee.ImageCollection('MOD09GA').filterDate(start, end)
  red = collection.sum().select('sur_refl_b01')
  nir = collection.sum().select('sur_refl_b02')
  ndvi = nir.normalized_difference(red)
  try :		
   value = ee.data.getValue({'image':ee.serializer.toJSON(ndvi),'points':ee.serializer.toJSON([point])})
   points = value['points']
   points = dict(points.pop())
   bands = points['bands']
   dvals.append(bands['sur_refl_b02'][0])
   print start, bands
  except:
   print 'Error:', start, end
   dvals.append(float('nan'))

#filter the list for nan values - only appear once in july, 2004 where the calls fail
for i in range(0,len(dvals)):
 if math.isnan(dvals[i]):
  print i, dvals[i]
  dvals[i] = (dvals[i-1] + dvals[i+1])/2

dvals = numpy.array(dvals, numpy.float)

#create an average years worth of data
inds = len(range(0,365,interval))
aveSig = []
for i in range(0,inds):
 aveSig.append(0)

for i in range(0,inds):
 for y in range(0,12):
  aveSig[i] += dvals[i+y*inds]

for i in range(0,inds):
 aveSig[i] = aveSig[i] / 12


#create an average signal the same length as actual
aveTrend = numpy.copy(dvals)
for y in range(0,12):
 for d in range(0, len(aveSig)):
  index = y*len(aveSig)+d
  aveTrend[index] = aveSig[d]

#subtract the average from the signal
ltTrend = numpy.copy(dvals)
for y in range(0,12):
 for d in range(0, len(aveSig)):
  index = y*len(aveSig)+d
  ltTrend[index] = dvals[index] - aveSig[d]

#loess smoothed trend (rough stuff)
x = numpy.array(range(0,len(dvals)), numpy.float)
y = numpy.array(ltTrend, numpy.float)
result = lowess.lowess(x,y, f=0.5/3.,iter=2)

#residuals
resids = ltTrend-result

#plots

pyplot.subplot(4,1,1)
pyplot.plot(x, dvals)
pyplot.subplot(4,1,2)
pyplot.plot(x, aveTrend)
pyplot.subplot(4,1,3)
pyplot.plot(x, result)
pyplot.subplot(4,1,4)
pyplot.plot(x, resids)
pyplot.show()




