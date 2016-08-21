import json
import unittest

def get_gladcluster_list(gladcluster_geojson):
    """
    returns a list of geojson objects each only containing one glad cluster.
    """
    gladcluster_geogjson_collection = []
    gladcluster_geojson_obj = json.loads(gladcluster_geojson)

    for cluster in gladcluster_geojson_obj["features"]:
        gladcluster_geojson = {
            "type": "FeatureCollection",
            "features": [
                cluster
            ]
        }
        gladcluster_geogjson_collection.append(gladcluster_geojson)

    return gladcluster_geogjson_collection


class MyTestCase(unittest.TestCase):
    def test_something(self):
        # geojson = {
        #     "type": "FeatureCollection",
        #     "features": [
        #         {
        #             "geometry": {
        #                 "coordinates": [
        #                     [
        #                         [
        #                             -75.7067903513147,
        #                             -6.893250900913643
        #                         ],
        #                         [
        #                             -75.7068898855788,
        #                             -6.893422050521049
        #                         ],
        #                         [
        #                             -75.70641888752698,
        #                             -6.893692019369901
        #                         ]
        #                     ]
        #                 ],
        #                 "geodesic": True,
        #                 "type": "Polygon"
        #             },
        #             "id": "-14046-1282",
        #             "properties": {
        #                 "AlertsDate": 1465344000000,
        #                 "AlertsInCluster": 1,
        #                 "AreaInHa": 35.402560747915494,
        #                 "fill-opacity": "0.0",
        #                 "points": {
        #                     "coordinates": [
        #                         [
        #                             -75.702625,
        #                             -6.888375
        #                         ]
        #                     ],
        #                     "geodesic": True,
        #                     "type": "MultiPoint"
        #                 },
        #                 "stroke": "#ff6fb7",
        #                 "stroke-width": 1
        #             },
        #             "type": "Feature"
        #         },
        #         {
        #             "geometry": {
        #                 "coordinates": [
        #                     [
        #                         [
        #                             -75.73373986889115,
        #                             -6.968158006165677
        #                         ],
        #                         [
        #                             -75.73383941897868,
        #                             -6.968329155751826
        #                         ],
        #                         [
        #                             -75.73336834608426,
        #                             -6.968599124631752
        #                         ]
        #                     ]
        #                 ],
        #                 "geodesic": True,
        #                 "type": "Polygon"
        #             },
        #             "id": "-14051-1296",
        #             "properties": {
        #                 "AlertsDate": 1465344000000,
        #                 "AlertsInCluster": 2,
        #                 "AreaInHa": 35.391314629098225,
        #                 "fill-opacity": "0.0",
        #                 "points": {
        #                     "coordinates": [
        #                         [
        #                             -75.728625,
        #                             -6.967375
        #                         ],
        #                         [
        #                             -75.728625,
        #                             -6.967125
        #                         ]
        #                     ],
        #                     "geodesic": True,
        #                     "type": "MultiPoint"
        #                 },
        #                 "stroke": "#ff6fb7",
        #                 "stroke-width": 1
        #             },
        #             "type": "Feature"
        #         }
        #     ]
        # }

        geo = """{
            "type": "FeatureCollection",
            "features": [1, 2, 3]
        }"""
        print geo
        gladcluster_geojson_obj = json.loads(geo)

        print gladcluster_geojson_obj["features"]

        # result = get_gladcluster_list(geojson)
        # print result[1]
        # self.assertEqual(len(result), 2)


if __name__ == '__main__':
    unittest.main()