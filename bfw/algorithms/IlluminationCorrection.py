# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <headingcell level=2>

# Illumination correction algorithm

# <markdowncell>

# <p>Implementation in GEE of an illumination correction algorithm based on the following article:</p>
# <p>Improved forest change detection with terrain illumination corrected Landsat images (2013)</p>
# <p>Bin Tan, Jeffrey G. Masek, Robert Wolfe, Feng Gao, Chengquan Huang, Eric F. Vermote, Joseph O. Sexton, Greg Ederer</p>
# <a href='http://www.sciencedirect.com/science/article/pii/S0034425713001673'>Article</a>
'''
Dear Qingling,
I havent tried L7 I'm afraid, but you should only need to change a few of the parameters to make it work with L7.
You may need to change the band combinations (from 432 to 321) and change the band cooeficients and offsets in the 
final corrected image. i.e. in the following change the values [12,9,25] to adjust the amount of illumination correction 
(for each band) and change the [770,0,-1230] values to adjust the colour balance in the composite. 

The best way to get the coefficients is to do them one band at a time. 

corrected_image = maliau_image.expression("((image * (cosZ + coeff)) / (ic + coeff)) + offsets", {'image': maliau_image.select('B4', 'B3', 'B2'),'ic': ic,'cosZ': cosZ,'coeff': [12, 9, 25],'offsets': [770, 0, -1230]})
corrected_thumbnail = corrected_image.getThumbUrl({
'bands': 'B4,B3,B2',
'min':7000,
'max':10000,
'size': '800',
'region': maliau_region

Good luck!
Cheers,
Andrew Cotham
a.cottam@gmail.com

'''


import ee,oauth2client.client, config, datetime, sys, json, math
from IPython.core.display import Image
ee.Initialize(ee.ServiceAccountCredentials(config.MY_SERVICE_ACCOUNT, config.MY_PRIVATE_KEY_FILE)) 
maliau_image = ee.Image("LC81170572013170LGN00")
maliau_region = [[116.676364283,4.95945957299],[116.676364283,4.64623224023],[117.100028398,4.64623224023],[117.100028398,4.95945957299]]
uncorrected_image = ee.Image.cat([maliau_image.expression("b('B4')+770"),maliau_image.select('B3'),maliau_image.expression("b('B2')-1230")]);
uncorrected_thumbnail = uncorrected_image.getThumbUrl({
'bands': 'B4,B3,B2',
'min':7000,
'max':10000,
'size': '800',
'region': maliau_region
})
Image(url=uncorrected_thumbnail)

# <rawcell>

# Get the Digital Terrain Model and the image metadata to help produce the Illumination Condition

# <codecell>

terrain = ee.call('Terrain', ee.Image('srtm90_v4'))
solar_zenith = (90-maliau_image.getInfo()['properties']['SUN_ELEVATION'])
solar_azimuth = maliau_image.getInfo()['properties']['SUN_AZIMUTH']
solar_zenith_radians = (solar_zenith*math.pi)/180
slope_radians = terrain.select(['slope']).expression("(b('slope')*" + str(math.pi) + ")/180")
aspect = terrain.select(['aspect'])

# <rawcell>

# Slope part of the illumination condition

# <codecell>

cosZ = math.cos(solar_zenith_radians)
cosS = slope_radians.cos()
slope_illumination = cosS.expression("b('slope')*(" + str(cosZ) + ")").select(['slope'],['b1'])

# <rawcell>

# Aspect part of the illumination condition

# <codecell>

sinZ = math.sin(solar_zenith_radians)
sinS = slope_radians.sin()
azimuth_diff_radians = aspect.expression("((b('aspect')-" + str(solar_azimuth) + ")*" + str(math.pi) + ")/180")
cosPhi = azimuth_diff_radians.cos()
aspect_illumination = cosPhi.multiply(sinS).expression("b('aspect')*" + str(sinZ)).select(['aspect'],['b1'])

# <rawcell>

# Get the illumination condition

# <codecell>

ic = slope_illumination.add(aspect_illumination)

# <rawcell>

# Apply the c model correction

# <codecell>

corrected_image = maliau_image.expression("((image * (cosZ + coeff)) / (ic + coeff)) + offsets", {'image': maliau_image.select('B4', 'B3', 'B2'),'ic': ic,'cosZ': cosZ,'coeff': [12, 9, 25],'offsets': [770, 0, -1230]})
corrected_thumbnail = corrected_image.getThumbUrl({
'bands': 'B4,B3,B2',
'min':7000,
'max':10000,
'size': '800',
'region': maliau_region
})
Image(url=corrected_thumbnail)

