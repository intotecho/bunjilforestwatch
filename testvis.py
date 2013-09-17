'''
Created on 25/05/2013
Wrappers for some Earth Engine Routines
Created on 25/05/2013
@author: cgoodman
'''


import eeservice
import unittest

class TestEEService(unittest.TestCase):
    coords = [
              [        145.3962206840515,        -37.71424496764925      ], 
              [        146.049907207489,        -37.705553487215816      ], 
              [        146.00733518600464,        -37.239075302021824    ], 
              [        145.29871702194214,        -37.233608599437034    ]
              ]  
    
    def setUp(self):
        eeservice.initEarthEngineService()
        
    def TestGetMap(self):
        #image = getLatestLandsatImage(self.coords, 'LANDSAT/LC8_L1T_TOA')
        #sharpimage = SharpenLandsat8HSVUpres(image)
        #byteimage = sharpimage.multiply(255).byte()
        #red = 'red'
        #green = 'green'
        #blue = 'blue'
        #mapid = getMap(byteimage,  red, green, blue)
        mapid = eeservice.GetMap(self.coords)
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
        
        image = eeservice.getLatestLandsat7HSVUpres(coords)
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
        sharpimage = eeservice.SharpenLandsat8HSVUpres(testimage)
        eeservice.getThumbnailPath(sharpimage)
        self.assertEqual(1, 1, 'L8 thumbs failed')
        pass
     
    def TestL7Overlay(self):
        image = eeservice.getLatestLandsatImage(self.coords, 'L7_L1T')
        #red = 'B4'
        #green = 'B3'
        #blue = 'B2'
        sharpimage = eeservice.SharpenLandsat7HSVUpres(image)
        red = 'red'
        green = 'green'
        blue = 'blue'    
        byteimage = eeservice.sharpimage.multiply(255).byte()
        path = eeservice.getOverlayPath(byteimage, "L7", red, green, blue)
        self.assertEqual(path.startswith("https://earthengine.googleapis.com//api/download?docid"), True, 'L7 overlay failed')
          
    def TestL8Overlay(self):
        image = eeservice.getLatestLandsatImage(self.coords, 'LANDSAT/LC8_L1T_TOA')
        sharpimage = eeservice.SharpenLandsat8HSVUpres(image)
        red = 'red'
        green = 'green'
        blue = 'blue'    
        byteimage = eeservice.sharpimage.multiply(255).byte()
        path = eeservice.getOverlayPath(byteimage, "L8TOA", red, green, blue)
        self.assertEqual(path.startswith("https://earthengine.googleapis.com//api/download?docid"), True, 'L8 overlay failed')

    def TestL8NDVIOverlay(self):
        image = eeservice.getLatestLandsatImage(self.coords, 'LANDSAT/LC8_L1T_TOA')
        ndvi = eeservice.getL8LatestNDVIImage(image)
        red = 'red'
        green = 'green'
        blue = 'blue'    
        #byteimage = eeservice.sharpimage.multiply(255).byte()
        #path = eeservice.getOverlayPath(ndvi, "L8TOA", red, green, blue)
        self.assertEqual(path.startswith("https://earthengine.googleapis.com//api/download?docid"), True, 'TestL8NDVIOverlay failed')

   
    def TestGetAlgorithms(self):
        algorithms = ee.data.getAlgorithms()
        #print type(algorithms) =Dictionary.
        for f in algorithms:
            print  f + ', \tDescr: ' + algorithms.get(f)['description']
        self.assertEqual(True, True, 'TestAlgorithms failed')
             
        