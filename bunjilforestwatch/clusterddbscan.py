'''
cluster.py cluster algorithm for GLAD alerts.
'''

import numpy as np
#from sklearn.cluster import DBSCAN
#from sklearn import metrics
#from sklearn.datasets.samples_generator import make_blobs
#from sklearn.preprocessing import StandardScaler
#import ddbscan

class GladCluster():
    # def __init__(self):
    #    pass
    X = 0

    def bounding_box(self, coords):
        min_x = 100000  # start with something much higher than expected min
        min_y = 100000
        max_x = -100000  # start with something much lower than expected max
        max_y = -100000

        for item in coords:
            if item[0] < min_x:
                min_x = item[0]

            if item[0] > max_x:
                max_x = item[0]

            if item[1] < min_y:
                min_y = item[1]

            if item[1] > max_y:
                max_y = item[1]

        return [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]

    ##############################################################################
    # Compute DBSCAN
    def scanToClusters(self, X):

        self.db = ddbscan(eps=0.016, min_samples=2).fit(X)
        #core_samples = self.db.core_sample_indices_
        labels = self.db.labels_

        # Number of clusters in labels, ignoring noise if present.
        unique_clusters = set(labels)

        self.n_clusters_ = len(unique_clusters) - (1 if -1 in labels else 0)
        print('Estimated number of clusters: %d' % self.n_clusters_)

        print ("unclustered", unique_clusters)

        if -1 in labels:
            # rint (unique_clusters[-1] )
            print ("unclustered points: %d." % labels[-1])

            # print("Silhouette Coefficient: %0.3f"
            #      % metrics.silhouette_score(X, labels))

    def printClusters(self, X):
        labels = self.db.labels_
        clusters = [X[labels == i] for i in xrange(self.n_clusters_)]
        for c in clusters:
            print 'cluster'
            print [p for p in c]
            print "cluster length:", len(c)
            for p in c:
                print p[0], p[1]

    def ClusterBoxes(self, X):
        # clusters = [X[labels == i] for i in xrange(n_clusters_)]
        boxes = []
        for i in xrange(self.n_clusters_):
            cluster = X[labels == i]
            polygon = Polygon(bounding_box(cluster), True)
        # print polygon
        boxes.append(polygon)
        return boxes


import math

'''
http://www.johndcook.com/blog/python_longitude_latitude/
Computing the distance between two locations on Earth from coordinates John D. Cook
'''
def distance_on_unit_sphere(lat1, long1, lat2, long2):

    # Convert latitude and longitude to
    # spherical coordinates in radians.
    degrees_to_radians = math.pi/180.0

    # phi = 90 - latitude
    phi1 = (90.0 - lat1)*degrees_to_radians
    phi2 = (90.0 - lat2)*degrees_to_radians

    # theta = longitude
    theta1 = long1*degrees_to_radians
    theta2 = long2*degrees_to_radians

    # Compute spherical distance from spherical coordinates.

    # For two locations in spherical coordinates
    # (1, theta, phi) and (1, theta', phi')
    # cosine( arc length ) =
    # sin phi sin phi' cos(theta-theta') + cos phi cos phi'
    # distance = rho * arc length

    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +
    math.cos(phi1)*math.cos(phi2))
    arc = math.acos( cos )

    # Remember to multiply arc by the radius of the earth
    # in your favorite set of units to get length.
    return arc